#!/usr/bin/env python3
"""
Comprehensive sync of scan results with full detail import
- Imports scan_results
- Imports page_results
- Imports issue_details  
- Imports SEO/AEO data
- Calculates accurate metrics
"""

import os
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

def ensure_seo_tables(conn):
    """Create SEO tables if they don't exist"""
    cursor = conn.cursor()
    
    # Create seo_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seo_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_result_id INTEGER,
            page_url TEXT,
            seo_score REAL,
            issues_found INTEGER,
            total_checks INTEGER,
            title_tag_exists BOOLEAN,
            title_tag_optimal BOOLEAN,
            meta_description_exists BOOLEAN,
            meta_description_optimal BOOLEAN,
            canonical_exists BOOLEAN,
            h1_optimal BOOLEAN,
            alt_text_coverage REAL,
            json_ld_exists BOOLEAN,
            open_graph_complete BOOLEAN,
            twitter_card_complete BOOLEAN,
            robots_txt_exists BOOLEAN,
            sitemap_exists BOOLEAN,
            internal_links INTEGER,
            external_links INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_result_id) REFERENCES scan_results(id)
        )
    """)
    
    conn.commit()

def parse_scan_results_comprehensive(result_dir):
    """Parse scan results comprehensively from a result directory
    
    Returns a list of scan data dicts, one for each site in the scan
    """
    
    # Read config.json for metadata
    config_path = result_dir / 'config.json'
    if not config_path.exists():
        print(f"    ⚠️  No config.json found")
        return None
        
    with open(config_path, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)
    
    # Read pages_scanned.csv for site info
    pages_path = result_dir / 'pages_scanned.csv'
    pages_scanned = []
    if pages_path.exists():
        with open(pages_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            pages_scanned = list(reader)
    
    if not pages_scanned:
        print(f"    ⚠️  No pages scanned")
        return None
    
    # Get all unique organizations in this scan
    organizations = {p.get('organisation'): p.get('base_url') for p in pages_scanned}
    
    # If only one organization, process normally
    if len(organizations) == 1:
        site_info = pages_scanned[0]
        return [_process_single_site(result_dir, site_info, config, None)]
    
    # Multiple organizations - create separate records for each
    print(f"    ℹ️  Multi-site scan detected: {len(organizations)} organizations")
    results = []
    for org, base_url in organizations.items():
        site_info = {'organisation': org, 'base_url': base_url}
        result = _process_single_site(result_dir, site_info, config, org)
        if result:
            results.append(result)
    return results

def _process_single_site(result_dir, site_info, config, filter_org=None):
    """Process scan results for a single site
    
    Args:
        result_dir: Path to scan results directory
        site_info: Dict with organisation and base_url
        config: Scan configuration dict
        filter_org: If set, only count issues for this organization
    """
    
    # Read axe_core_audit.csv for accessibility issues
    axe_path = result_dir / 'axe_core_audit.csv'
    accessibility_issues = []
    unique_pages = {}  # Changed to dict to store page_url: page_title mapping
    if axe_path.exists():
        with open(axe_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by organization if specified
                if filter_org and row.get('organisation') != filter_org:
                    continue
                    
                page_url = row.get('url', '')
                page_title = row.get('page_title', '')
                
                # Track page with its title
                if page_url and page_url not in unique_pages:
                    unique_pages[page_url] = page_title
                
                # Skip rows with "No issues found"
                if row.get('description') == 'No issues found' or not row.get('impact'):
                    continue
                accessibility_issues.append(row)
    
    # Group issues by page URL and deduplicate
    # The CSV has one row per element, but we want one row per unique issue type
    issues_by_page = defaultdict(lambda: defaultdict(list))
    for issue in accessibility_issues:
        page_url = issue.get('url', issue.get('page_url', ''))
        # Create unique key for this issue type
        issue_key = (
            issue.get('id', 'unknown'),  # WCAG ID
            issue.get('description', ''),
            issue.get('impact', 'unknown')
        )
        issues_by_page[page_url][issue_key].append(issue)
    
    # Convert to final format with instance counts
    final_issues_by_page = defaultdict(list)
    for page_url, issues_dict in issues_by_page.items():
        for issue_key, issue_list in issues_dict.items():
            # Take first issue as template
            first_issue = issue_list[0]
            # Count instances (number of elements with this issue)
            instance_count = len(issue_list)
            # Create consolidated issue
            consolidated_issue = {
                'id': first_issue.get('id', 'unknown'),
                'wcag_id': first_issue.get('id', 'unknown'),
                'description': first_issue.get('description', ''),
                'impact': first_issue.get('impact', 'unknown'),
                'help': first_issue.get('help', ''),
                'help_url': first_issue.get('helpUrl', ''),
                'instances': instance_count
            }
            final_issues_by_page[page_url].append(consolidated_issue)
    
    issues_by_page = final_issues_by_page
    
    # Calculate overall statistics from deduplicated issues
    # Count unique issue types, not total element instances
    all_unique_issues = []
    for page_issues in final_issues_by_page.values():
        all_unique_issues.extend(page_issues)
    
    critical_issues = sum(1 for i in all_unique_issues if i.get('impact') == 'critical')
    serious_issues = sum(1 for i in all_unique_issues if i.get('impact') == 'serious')
    moderate_issues = sum(1 for i in all_unique_issues if i.get('impact') == 'moderate')
    minor_issues = sum(1 for i in all_unique_issues if i.get('impact') == 'minor')
    total_issues = len(all_unique_issues)
    
    # Calculate site score as average of individual page scores
    # This ensures consistency with page-level scoring displayed in UI
    page_scores = []
    for page_url, page_issues in final_issues_by_page.items():
        # Count issues by severity for this page
        page_critical = sum(1 for i in page_issues if i.get('impact') == 'critical')
        page_serious = sum(1 for i in page_issues if i.get('impact') == 'serious')
        page_moderate = sum(1 for i in page_issues if i.get('impact') == 'moderate')
        page_minor = sum(1 for i in page_issues if i.get('impact') == 'minor')
        
        # Calculate page score using linear formula (same as UI)
        penalty = (page_critical * 10) + (page_serious * 5) + (page_moderate * 2) + page_minor
        page_score = max(0, 100 - min(100, penalty))
        page_scores.append(page_score)
    
    # Site score is average of all page scores
    if page_scores:
        score = round(sum(page_scores) / len(page_scores), 1)
    else:
        score = 100.0
    
    # Determine WCAG level based on issues
    if critical_issues == 0 and serious_issues == 0 and moderate_issues == 0:
        wcag_level = 'WCAG 2.2 AAA'
    elif critical_issues == 0 and serious_issues == 0:
        wcag_level = 'WCAG 2.2 AA'
    elif critical_issues == 0:
        wcag_level = 'WCAG 2.2 A'
    else:
        wcag_level = 'Non-compliant'
    
    # Extract timestamp from directory name
    dir_name = result_dir.name
    # Format: 2025-10-31_08-54-44_WCAG_2.2_AA_scan
    try:
        date_str = dir_name.split('_')[0] + ' ' + dir_name.split('_')[1].replace('-', ':')
        scan_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        scan_date = datetime.now()
    
    # Read SEO data if exists
    seo_path = result_dir / 'seo_aeo_audit.csv'
    seo_data = []
    if seo_path.exists():
        with open(seo_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by organization if specified
                if filter_org and row.get('organisation') != filter_org:
                    continue
                seo_data.append(row)
    
    # Create scan_id with organization suffix if filtering
    dir_name = result_dir.name
    if filter_org:
        scan_id = f"{dir_name}_{filter_org.replace(' ', '_')}"
    else:
        scan_id = dir_name
    
    return {
        'scan_id': scan_id,
        'site_url': site_info.get('base_url', ''),
        'organisation': site_info.get('organisation', ''),
        'scan_date': scan_date.isoformat(),
        'score': score,
        'critical_issues': critical_issues,
        'serious_issues': serious_issues,
        'moderate_issues': moderate_issues,
        'minor_issues': minor_issues,
        'total_issues': total_issues,
        'wcag_level': wcag_level,
        'pages_scanned': len(unique_pages),
        'status': 'completed',
        'pages': [{'page_url': url, 'page_title': title} for url, title in sorted(unique_pages.items())],
        'issues_by_page': dict(issues_by_page),
        'all_issues': accessibility_issues,
        'seo_data': seo_data
    }

def sync_to_database_comprehensive(scan_data, conn):
    """Sync scan data comprehensively to analytics database"""
    
    cursor = conn.cursor()
    
    try:
        # Get or create site
        cursor.execute("""
            SELECT id FROM sites WHERE url = ?
        """, (scan_data['site_url'],))
        
        site = cursor.fetchone()
        if site:
            site_id = site[0]
        else:
            # Create site
            cursor.execute("""
                INSERT INTO sites (organisation, url, sector, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (scan_data['organisation'], scan_data['site_url'], 'Government'))
            site_id = cursor.lastrowid
        
        # Check if scan already exists
        cursor.execute("""
            SELECT id FROM scan_results WHERE scan_id = ?
        """, (scan_data['scan_id'],))
        
        existing = cursor.fetchone()
        if existing:
            print(f"    ℹ️  Scan already exists, updating...")
            scan_result_id = existing[0]
            
            # Update existing scan
            cursor.execute("""
                UPDATE scan_results SET
                    pages_scanned = ?,
                    a11y_score = ?,
                    a11y_critical_issues = ?,
                    a11y_serious_issues = ?,
                    a11y_moderate_issues = ?,
                    a11y_minor_issues = ?,
                    a11y_total_issues = ?,
                    wcag_level = ?
                WHERE id = ?
            """, (
                scan_data['pages_scanned'],
                scan_data['score'],
                scan_data['critical_issues'],
                scan_data['serious_issues'],
                scan_data['moderate_issues'],
                scan_data['minor_issues'],
                scan_data['total_issues'],
                scan_data['wcag_level'],
                scan_result_id
            ))
            
            # Delete old page results and issues
            cursor.execute("DELETE FROM a11y_issues WHERE scan_result_id = ?", (scan_result_id,))
            cursor.execute("DELETE FROM a11y_page_results WHERE scan_result_id = ?", (scan_result_id,))
            cursor.execute("DELETE FROM seo_results WHERE scan_result_id = ?", (scan_result_id,))
        else:
            # Insert new scan result
            cursor.execute("""
                INSERT INTO scan_results (
                    scan_id, site_id, scan_date, pages_scanned, a11y_score,
                    a11y_critical_issues, a11y_serious_issues, a11y_moderate_issues, a11y_minor_issues,
                    a11y_total_issues, wcag_level, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                scan_data['scan_id'],
                site_id,
                scan_data['scan_date'],
                scan_data['pages_scanned'],
                scan_data['score'],
                scan_data['critical_issues'],
                scan_data['serious_issues'],
                scan_data['moderate_issues'],
                scan_data['minor_issues'],
                scan_data['total_issues'],
                scan_data['wcag_level']
            ))
            
            scan_result_id = cursor.lastrowid
        
        # Insert page results
        page_results_count = 0
        for page in scan_data['pages']:
            page_url = page.get('page_url', page.get('url', ''))
            page_title = page.get('page_title', '')
            
            # Get issues for this page
            page_issues = scan_data['issues_by_page'].get(page_url, [])
            
            # Count by severity
            critical_count = sum(1 for i in page_issues if i.get('impact') == 'critical')
            serious_count = sum(1 for i in page_issues if i.get('impact') == 'serious')
            moderate_count = sum(1 for i in page_issues if i.get('impact') == 'moderate')
            minor_count = sum(1 for i in page_issues if i.get('impact') == 'minor')
            
            cursor.execute("""
                INSERT INTO a11y_page_results (
                    scan_result_id, page_url, page_title, issues_count,
                    critical_count, serious_count, moderate_count, minor_count,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                scan_result_id,
                page_url,
                page_title,
                len(page_issues),
                critical_count,
                serious_count,
                moderate_count,
                minor_count
            ))
            
            page_result_id = cursor.lastrowid
            page_results_count += 1
        
        # Aggregate and insert issues at scan level
        all_issues = scan_data.get('all_issues', [])
        if all_issues:
            # Group issues by issue_id to aggregate counts and pages
            from collections import defaultdict
            issues_aggregated = defaultdict(lambda: {
                'count': 0,
                'pages': set(),
                'impact': 'moderate',
                'description': '',
                'help_text': '',
                'help_url': '',
                'wcag_criterion': '',
                'tags': []
            })
            
            for issue in all_issues:
                issue_id = issue.get('id', issue.get('issue_id', 'unknown'))
                page_url = issue.get('url', issue.get('page_url', ''))
                
                agg = issues_aggregated[issue_id]
                agg['count'] += issue.get('instances', 1)
                agg['pages'].add(page_url)
                agg['impact'] = issue.get('impact', 'moderate')
                agg['description'] = issue.get('description', '')
                agg['help_text'] = issue.get('help', '')
                agg['help_url'] = issue.get('helpUrl', issue.get('help_url', ''))
                
                # Extract WCAG criterion from tags if available
                tags = issue.get('tags', [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.strip("[]'").split(',')]
                agg['tags'] = tags
                
                # Try to find WCAG criterion in tags
                for tag in tags:
                    if tag.startswith('wcag'):
                        agg['wcag_criterion'] = tag
                        break
            
            # Insert aggregated issues
            for issue_id, data in issues_aggregated.items():
                cursor.execute("""
                    INSERT INTO a11y_issues (
                        scan_result_id, issue_id, issue_type, wcag_criterion,
                        severity, impact, count, pages_affected,
                        description, help_text, help_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    scan_result_id,
                    issue_id,
                    'accessibility',
                    data['wcag_criterion'],
                    data['impact'],  # severity
                    data['impact'],  # impact (same for axe-core)
                    data['count'],
                    len(data['pages']),
                    data['description'][:500] if data['description'] else '',
                    data['help_text'][:500] if data['help_text'] else '',
                    data['help_url']
                ))
        
        # Insert SEO data
        seo_results_count = 0
        for seo_row in scan_data.get('seo_data', []):
            try:
                # Parse the metadata JSON if it exists
                metadata_str = seo_row.get('metadata', '{}')
                if metadata_str and metadata_str != '{}':
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                else:
                    metadata = {}
                
                cursor.execute("""
                    INSERT INTO seo_results (
                        scan_result_id, page_url, seo_score, issues_found, total_checks,
                        title_tag_exists, title_tag_optimal,
                        meta_description_exists, meta_description_optimal,
                        canonical_exists, h1_optimal, alt_text_coverage,
                        json_ld_exists, open_graph_complete, twitter_card_complete,
                        robots_txt_exists, sitemap_exists,
                        internal_links, external_links,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    scan_result_id,
                    seo_row.get('page_url', seo_row.get('url', '')),
                    float(seo_row.get('seo_score', 0)),
                    int(seo_row.get('issues_found', 0)),
                    int(seo_row.get('total_checks', 12)),
                    seo_row.get('title_exists', '').lower() == 'true',
                    seo_row.get('title_optimal', '').lower() == 'true',
                    seo_row.get('description_exists', '').lower() == 'true',
                    seo_row.get('description_optimal', '').lower() == 'true',
                    seo_row.get('canonical_exists', '').lower() == 'true',
                    seo_row.get('h1_optimal', '').lower() == 'true',
                    float(seo_row.get('image_alt_coverage', 0)),
                    seo_row.get('schema_exists', '').lower() == 'true',
                    seo_row.get('open_graph_complete', '').lower() == 'true',
                    seo_row.get('twitter_card_complete', '').lower() == 'true',
                    seo_row.get('robots_exists', '').lower() == 'true',
                    seo_row.get('sitemap_exists', '').lower() == 'true',
                    int(seo_row.get('internal_links', 0)),
                    int(seo_row.get('external_links', 0))
                ))
                seo_results_count += 1
            except Exception as e:
                print(f"      ⚠️  Error importing SEO row: {e}")
                continue
        
        conn.commit()
        print(f"    ✓ Synced: {page_results_count} pages, {len(scan_data['all_issues'])} issues, {seo_results_count} SEO results")
        return True
        
    except Exception as e:
        print(f"    ✗ Error syncing: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

def add_scan_id_to_a11y_issues(conn):
    """Add scan_id column to issue_details if it doesn't exist"""
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(a11y_issues)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'scan_id' not in columns:
            print("  Adding scan_id column to issue_details...")
            cursor.execute("ALTER TABLE a11y_issues ADD COLUMN scan_id TEXT")
            conn.commit()
            print("  ✓ Column added")
    except Exception as e:
        print(f"  ⚠️  Error adding column: {e}")

def main():
    """Main comprehensive sync function"""
    print("=" * 60)
    print("  COMPREHENSIVE SCAN RESULTS SYNC")
    print("=" * 60)
    
    # Change to bi_integration directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Connect to database
    db_path = 'cwac_analytics.db'
    conn = sqlite3.connect(db_path)
    
    # Ensure SEO tables exist
    print("\n📊 Checking database schema...")
    ensure_seo_tables(conn)
    add_scan_id_to_a11y_issues(conn)
    print("  ✓ Schema ready")
    
    # Find results directory - use absolute path from project root
    project_root = Path(__file__).parent.parent.parent.parent
    results_dir = project_root / 'cwac' / 'results'
    if not results_dir.exists():
        print(f"\n❌ Results directory not found: {results_dir}")
        conn.close()
        return
    
    # Find all result directories
    result_dirs = [d for d in results_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not result_dirs:
        print("\n❌ No scan results found")
        conn.close()
        return
    
    print(f"\n📁 Found {len(result_dirs)} scan result directories")
    
    synced = 0
    errors = 0
    skipped_failed = 0
    
    for result_dir in sorted(result_dirs):
        print(f"\n  Processing: {result_dir.name}")
        
        # Check for success marker - skip failed scans
        success_marker = result_dir / '.scan_success'
        if not success_marker.exists():
            print(f"    ⚠️  Skipping: No success marker (scan likely failed)")
            skipped_failed += 1
            continue
        
        # Parse results comprehensively (returns list of scan_data dicts)
        scan_data_list = parse_scan_results_comprehensive(result_dir)
        if not scan_data_list:
            print(f"    ⚠️  Could not parse results")
            errors += 1
            continue
        
        # Process each site in the scan
        for scan_data in scan_data_list:
            org = scan_data['organisation']
            print(f"    📄 {org}: {scan_data['pages_scanned']} pages, {scan_data['total_issues']} issues, Score: {scan_data['score']:.1f}")
            
            # Sync to database
            if sync_to_database_comprehensive(scan_data, conn):
                synced += 1
            else:
                errors += 1
    
    # Show final database stats
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM scan_results")
    total_scans = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM a11y_page_results")
    total_pages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM a11y_issues")
    total_issues = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM seo_results")
    total_seo = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT site_id) FROM scan_results")
    total_sites = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Sync Complete!")
    print(f"  - Successfully synced: {synced}")
    print(f"  - Errors: {errors}")
    print(f"  - Skipped (failed scans): {skipped_failed}")
    print(f"\n📊 Database Stats:")
    print(f"  - Total scans: {total_scans}")
    print(f"  - Total pages: {total_pages}")
    print(f"  - Total issues: {total_issues}")
    print(f"  - Total SEO results: {total_seo}")
    print(f"  - Sites with data: {total_sites}")
    print("=" * 60)

if __name__ == "__main__":
    main()
