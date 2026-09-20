#!/usr/bin/env python3
"""
Sync a single scan directory to the database.
Used for automatic sync after each scan completes.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import traceback

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bi_integration.comprehensive_sync import (
    parse_scan_results_comprehensive,
    sync_to_database_comprehensive,
    ensure_seo_tables
)

def sync_single_scan(scan_dir_path):
    """
    Sync a single scan directory to the database.
    
    Args:
        scan_dir_path: Path to the scan directory (can be string or Path)
    
    Returns:
        True if sync successful, False otherwise
    """
    scan_dir = Path(scan_dir_path)
    
    if not scan_dir.exists():
        print(f"❌ Directory does not exist: {scan_dir}")
        return False
    
    if not scan_dir.is_dir():
        print(f"❌ Not a directory: {scan_dir}")
        return False
    
    # Check for required files
    required_files = ['audit_log.csv', 'pages_scanned.csv']
    for file in required_files:
        if not (scan_dir / file).exists():
            print(f"❌ Missing required file: {file}")
            return False
    
    print(f"\n📂 Syncing scan: {scan_dir.name}")
    
    try:
        # Connect to database
        db_path = Path(__file__).parent / 'cwac_analytics.db'
        conn = sqlite3.connect(str(db_path))
        
        # Ensure tables exist
        ensure_seo_tables(conn)
        
        # Parse scan results
        print("  📊 Parsing scan results...")
        results = parse_scan_results_comprehensive(scan_dir)
        
        if not results:
            print("  ⚠️ No results to sync")
            conn.close()
            return False
        
        # Sync to database
        synced_count = 0
        for result in results:
            if result:
                site_info = result.get('site_info', {})
                org = site_info.get('organisation', 'Unknown')
                issues = result.get('issue_summary', {}).get('total_issues', 0)
                score = result.get('metrics', {}).get('score', 0)
                
                print(f"  📝 {org}: {issues} issues, Score: {score:.1f}")
                
                success = sync_to_database_comprehensive(result, conn)
                if success:
                    synced_count += 1
                    print(f"  ✅ Synced {org} data")
                else:
                    print(f"  ⚠️ Failed to sync {org}")
        
        conn.commit()
        conn.close()
        
        if synced_count > 0:
            print(f"\n✅ Successfully synced {synced_count} site(s) from {scan_dir.name}")
            return True
        else:
            print(f"\n⚠️ No data synced from {scan_dir.name}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error syncing scan: {e}")
        traceback.print_exc()
        return False

def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python sync_single_scan.py <scan_directory>")
        print("Example: python sync_single_scan.py ../../../cwac/results/2025-10-31_14-55-40_Minimal_Test_Audit")
        sys.exit(1)
    
    scan_dir = sys.argv[1]
    success = sync_single_scan(scan_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
