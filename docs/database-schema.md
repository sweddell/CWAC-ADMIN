# Database Schema Documentation

This document describes the SQLite database schema used by CWAC-ADMIN for storing scan results and analytics.

## Overview

**Database**: `cwac_analytics.db`  
**Location**: `cwac_admin_app/database/bi_integration/`  
**Type**: SQLite 3  
**Schema File**: `schema.sql`

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐
│    sites     │───┬───│ scan_results │
│              │   │   │              │
│ * id         │   │   │ * id         │
│   url        │   │   │   scan_id    │
│   org        │   │   │   a11y_score │
└──────────────┘   │   │   seo_score  │
                   │   └──────┬───────┘
                   │          │
                   │      ┌───┴──────────────┐
                   │      │                  │
                   │   ┌──▼───────────┐  ┌──▼──────────────┐
                   │   │page_results  │  │  issue_details  │
                   │   │              │  │                 │
                   │   │ * id         │  │ * id            │
                   │   │   page_url   │  │   issue_type    │
                   │   │   score      │  │   severity      │
                   │   │   issues     │  │   wcag_criterion│
                   │   └──────────────┘  └─────────────────┘
                   │
                   └───┐
                       │
           ┌───────────▼──────────┐
           │ audit results tables │
           │ (language, reflow,   │
           │  focus, screenshots, │
           │  seo_results)        │
           └──────────────────────┘
```

## Core Tables

### sites

Websites being monitored for accessibility.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique site identifier |
| `url` | TEXT UNIQUE NOT NULL | Website URL |
| `organisation` | TEXT | Organization name |
| `sector` | TEXT | Industry sector |
| `group_id` | INTEGER | Foreign key to site_groups |
| `created_at` | TIMESTAMP | When site was added |
| `updated_at` | TIMESTAMP | Last modification time |

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE on `url`
- Index on `group_id`

**Example**:
```sql
INSERT INTO sites (url, organisation, sector)
VALUES ('https://www.harvard.edu', 'Harvard University', 'Education');
```

### scan_results

Summary data for each scan run.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique scan result ID |
| `site_id` | INTEGER NOT NULL | Foreign key to sites |
| `scan_id` | TEXT UNIQUE NOT NULL | Scan directory name |
| `scan_date` | TIMESTAMP NOT NULL | When scan was run |
| `config_name` | TEXT | Configuration file used |
| `pages_scanned` | INTEGER | Number of pages tested |
| `scan_duration` | INTEGER | Time taken (seconds) |
| `a11y_score` | REAL | Accessibility score (0-100) |
| `a11y_total_issues` | INTEGER | Total accessibility issues |
| `a11y_critical_issues` | INTEGER | Critical severity issues |
| `a11y_serious_issues` | INTEGER | Serious severity issues |
| `a11y_moderate_issues` | INTEGER | Moderate severity issues |
| `a11y_minor_issues` | INTEGER | Minor severity issues |
| `wcag_level` | TEXT | WCAG level tested (A, AA, AAA) |
| `wcag_version` | TEXT | WCAG version (2.0, 2.1, 2.2) |
| `seo_score` | REAL | SEO score (0-100) |
| `seo_issues_found` | INTEGER | SEO issues count |
| `combined_score` | REAL | Combined A11y + SEO score |
| `created_at` | TIMESTAMP | Record creation time |

**Foreign Keys**:
- `site_id` → `sites.id`

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE on `scan_id`
- Index on `site_id`
- Index on `scan_date`

**Example**:
```sql
SELECT 
    s.organisation,
    sr.scan_date,
    sr.a11y_score,
    sr.a11y_total_issues
FROM scan_results sr
JOIN sites s ON sr.site_id = s.id
WHERE sr.scan_date > date('now', '-30 days')
ORDER BY sr.scan_date DESC;
```

### page_results

Individual page-level scan results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique page result ID |
| `scan_result_id` | INTEGER NOT NULL | Foreign key to scan_results |
| `page_url` | TEXT NOT NULL | Full URL of page |
| `page_title` | TEXT | Page title |
| `page_load_time` | REAL | Load time (seconds) |
| `violations_found` | INTEGER | Number of violations |
| `critical_count` | INTEGER | Critical issues |
| `serious_count` | INTEGER | Serious issues |
| `moderate_count` | INTEGER | Moderate issues |
| `minor_count` | INTEGER | Minor issues |
| `load_time` | REAL | Page load time |
| `response_code` | INTEGER | HTTP response code |
| `created_at` | TIMESTAMP | Record creation time |

**Foreign Keys**:
- `scan_result_id` → `scan_results.id`

**Indexes**:
- PRIMARY KEY on `id`
- Index on `scan_result_id`
- Index on `page_url`

**Example**:
```sql
SELECT page_url, violations_found, critical_count
FROM page_results
WHERE scan_result_id = 42
ORDER BY critical_count DESC;
```

### issue_details

Detailed information about each accessibility issue found.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique issue ID |
| `scan_result_id` | INTEGER NOT NULL | Foreign key to scan_results |
| `issue_id` | TEXT NOT NULL | axe-core rule ID |
| `issue_type` | TEXT NOT NULL | Issue category |
| `wcag_criterion` | TEXT | WCAG success criterion (e.g., "1.3.1") |
| `wcag_level` | TEXT | WCAG level (A, AA, AAA) |
| `wcag_version` | TEXT | WCAG version |
| `severity` | TEXT NOT NULL | critical, serious, moderate, minor |
| `impact` | TEXT | Impact description |
| `count` | INTEGER | Number of occurrences |
| `pages_affected` | INTEGER | Pages with this issue |
| `description` | TEXT | Issue description |
| `help_text` | TEXT | How to fix |
| `help_url` | TEXT | Link to guidance |
| `created_at` | TIMESTAMP | Record creation time |

**Foreign Keys**:
- `scan_result_id` → `scan_results.id` ON DELETE CASCADE

**Indexes**:
- PRIMARY KEY on `id`
- Index on `scan_result_id`
- Index on `severity`
- Index on `wcag_criterion`

**Example**:
```sql
SELECT 
    issue_type,
    wcag_criterion,
    severity,
    COUNT(*) as occurrence_count,
    SUM(pages_affected) as total_pages
FROM issue_details
WHERE scan_result_id = 42
GROUP BY issue_type, wcag_criterion, severity
ORDER BY severity, total_pages DESC;
```

## Audit Result Tables

### language_audit_results

Results from language attribute testing.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique record ID |
| `scan_result_id` | INTEGER | Foreign key to scan_results |
| `page_url` | TEXT | Page tested |
| `lang_present` | BOOLEAN | Has lang attribute |
| `lang_value` | TEXT | Language code (e.g., "en") |
| `lang_valid` | BOOLEAN | Valid language code |
| `is_correct` | BOOLEAN | Appropriate for content |
| `recommendations` | TEXT | Suggested improvements |
| `created_at` | TIMESTAMP | Record creation time |

### reflow_audit_results

Responsive design / reflow testing results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique record ID |
| `scan_result_id` | INTEGER | Foreign key to scan_results |
| `page_url` | TEXT | Page tested |
| `viewport_width` | INTEGER | Test viewport width |
| `viewport_height` | INTEGER | Test viewport height |
| `horizontal_scroll` | BOOLEAN | Has horizontal scroll |
| `content_fits` | BOOLEAN | Content fits viewport |
| `layout_breaks` | BOOLEAN | Layout issues detected |
| `recommendations` | TEXT | Suggested improvements |
| `created_at` | TIMESTAMP | Record creation time |

### focus_indicator_audit_results

Focus visibility testing results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique record ID |
| `scan_result_id` | INTEGER | Foreign key to scan_results |
| `page_url` | TEXT | Page tested |
| `element_selector` | TEXT | CSS selector of element |
| `element_type` | TEXT | Element type (button, link, etc.) |
| `focus_visible` | BOOLEAN | Focus indicator visible |
| `contrast_ratio` | REAL | Contrast ratio of focus indicator |
| `meets_contrast` | BOOLEAN | Meets WCAG contrast requirements |
| `screenshot_before` | TEXT | Path to before screenshot |
| `screenshot_after` | TEXT | Path to after screenshot |
| `recommendations` | TEXT | Suggested improvements |
| `created_at` | TIMESTAMP | Record creation time |

### screenshot_audit_results

Visual audit results with screenshots.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique record ID |
| `scan_result_id` | INTEGER | Foreign key to scan_results |
| `page_url` | TEXT | Page captured |
| `screenshot_path` | TEXT | Path to screenshot file |
| `screenshot_type` | TEXT | Type (full-page, viewport, element) |
| `viewport_width` | INTEGER | Screenshot width |
| `viewport_height` | INTEGER | Screenshot height |
| `file_size` | INTEGER | File size in bytes |
| `created_at` | TIMESTAMP | Capture time |

## SEO Table

### seo_results

SEO and structured data metrics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique record ID |
| `scan_result_id` | INTEGER | Foreign key to scan_results |
| `page_url` | TEXT | Page analyzed |
| `seo_score` | REAL | SEO score (0-100) |
| `issues_found` | INTEGER | SEO issues count |
| `total_checks` | INTEGER | Total checks performed |
| `title_tag_exists` | BOOLEAN | Has title tag |
| `title_tag_optimal` | BOOLEAN | Title length optimal |
| `meta_description_exists` | BOOLEAN | Has meta description |
| `meta_description_optimal` | BOOLEAN | Description length optimal |
| `canonical_exists` | BOOLEAN | Has canonical URL |
| `h1_optimal` | BOOLEAN | H1 tag present and appropriate |
| `alt_text_coverage` | REAL | % images with alt text |
| `json_ld_exists` | BOOLEAN | Has JSON-LD structured data |
| `open_graph_complete` | BOOLEAN | Complete Open Graph tags |
| `twitter_card_complete` | BOOLEAN | Complete Twitter Card tags |
| `robots_txt_exists` | BOOLEAN | Site has robots.txt |
| `sitemap_exists` | BOOLEAN | Site has sitemap.xml |
| `internal_links` | INTEGER | Internal link count |
| `external_links` | INTEGER | External link count |
| `created_at` | TIMESTAMP | Record creation time |

## System Management Tables

### scan_schedules

Configuration for automated scan scheduling.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique schedule ID |
| `config_name` | TEXT NOT NULL | Display name |
| `config_path` | TEXT NOT NULL | Path to config file |
| `schedule_type` | TEXT NOT NULL | hourly, daily, weekly, monthly, cron |
| `schedule_value` | TEXT NOT NULL | Schedule specification |
| `enabled` | INTEGER | 1 = enabled, 0 = disabled |
| `last_run` | TEXT | Last execution time (ISO 8601) |
| `next_run` | TEXT | Next scheduled time (ISO 8601) |
| `created_at` | TEXT | Schedule creation time |
| `updated_at` | TEXT | Last modification time |

**Indexes**:
- PRIMARY KEY on `id`
- Index on `enabled`
- Index on `next_run`

**Schedule Value Examples**:
- Hourly: `"2"` (every 2 hours)
- Daily: `"09:00"` (9 AM every day)
- Weekly: `"monday,09:00"` (Mondays at 9 AM)
- Monthly: `"1,09:00"` (1st of month at 9 AM)
- Cron: `"0 */6 * * *"` (every 6 hours)

**Example**:
```sql
INSERT INTO scan_schedules (config_name, config_path, schedule_type, schedule_value, enabled)
VALUES ('Daily Full Scan', 'config/full_scan.json', 'daily', '09:00', 1);
```

### activity_log

Audit trail of user actions and system events.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique log entry ID |
| `timestamp` | TIMESTAMP | When event occurred |
| `event_type` | TEXT NOT NULL | Event category |
| `event_name` | TEXT | Event description |
| `details` | TEXT | Additional information |
| `scan_id` | TEXT | Related scan ID (if applicable) |
| `created_at` | TIMESTAMP | Record creation time |

**Event Types**:
- `scan_start` - Scan initiated
- `scan_complete` - Scan finished successfully
- `scan_failed` - Scan encountered error
- `user_login` - User authentication
- `user_logout` - User session end
- `site_added` - New site created
- `site_modified` - Site details changed
- `site_deleted` - Site removed
- `config_change` - System configuration modified
- `schedule_created` - Scan schedule added
- `schedule_modified` - Schedule updated
- `schedule_deleted` - Schedule removed

**Indexes**:
- PRIMARY KEY on `id`
- Index on `timestamp DESC`
- Index on `event_type`
- Index on `scan_id`

**Example**:
```sql
SELECT 
    timestamp,
    event_type,
    event_name,
    details
FROM activity_log
WHERE event_type IN ('scan_start', 'scan_complete', 'scan_failed')
ORDER BY timestamp DESC
LIMIT 50;
```

### system_metadata

Key-value store for system configuration and state.

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT PRIMARY KEY | Setting name |
| `value` | TEXT | Setting value (JSON string) |
| `updated_at` | TIMESTAMP | Last update time |

**Common Keys**:
- `last_sync_time` - Last database sync timestamp
- `app_version` - Application version
- `db_schema_version` - Database schema version
- `system_status` - Overall system health
- `maintenance_mode` - Maintenance flag

**Example**:
```sql
INSERT OR REPLACE INTO system_metadata (key, value)
VALUES ('last_sync_time', '2024-11-12T10:30:00');

SELECT value FROM system_metadata WHERE key = 'app_version';
```

## Organization Tables

### site_groups

Groupings for organizing sites (e.g., by department).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique group ID |
| `name` | TEXT UNIQUE NOT NULL | Group name |
| `description` | TEXT | Group purpose |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last modification |

**Example**:
```sql
INSERT INTO site_groups (name, description)
VALUES ('Education Institutions', 'University and college websites');
```

### organisations

Organization entities (legacy table).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique organization ID |
| `name` | TEXT UNIQUE NOT NULL | Organization name |
| `created_at` | TIMESTAMP | Creation time |

### groups

Legacy group table (consider consolidating with site_groups).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique group ID |
| `name` | TEXT | Group name |
| `description` | TEXT | Group description |
| `created_at` | TIMESTAMP | Creation time |

## Common Queries

### Get Latest Scan Results for a Site

```sql
SELECT 
    sr.scan_date,
    sr.a11y_score,
    sr.a11y_total_issues,
    sr.a11y_critical_issues,
    sr.a11y_serious_issues
FROM scan_results sr
JOIN sites s ON sr.site_id = s.id
WHERE s.url = 'https://www.example.com'
ORDER BY sr.scan_date DESC
LIMIT 1;
```

### Get Score Trends Over Time

```sql
SELECT 
    DATE(scan_date) as date,
    AVG(a11y_score) as avg_score,
    SUM(a11y_total_issues) as total_issues
FROM scan_results
WHERE site_id = 1
  AND scan_date > date('now', '-30 days')
GROUP BY DATE(scan_date)
ORDER BY date;
```

### Get Most Common Issues Across All Sites

```sql
SELECT 
    issue_type,
    wcag_criterion,
    severity,
    COUNT(*) as scan_count,
    SUM(pages_affected) as total_pages,
    AVG(count) as avg_per_scan
FROM issue_details
GROUP BY issue_type, wcag_criterion, severity
ORDER BY total_pages DESC
LIMIT 20;
```

### Get Pages with Most Critical Issues

```sql
SELECT 
    pr.page_url,
    pr.critical_count,
    pr.violations_found,
    s.organisation
FROM page_results pr
JOIN scan_results sr ON pr.scan_result_id = sr.id
JOIN sites s ON sr.site_id = s.id
WHERE pr.critical_count > 0
ORDER BY pr.critical_count DESC
LIMIT 50;
```

### Get Recent Activity

```sql
SELECT 
    timestamp,
    event_type,
    event_name,
    details
FROM activity_log
ORDER BY timestamp DESC
LIMIT 100;
```

## Maintenance

### Backup Database

```bash
cp cwac_analytics.db cwac_analytics_backup_$(date +%Y%m%d).db
```

### Vacuum Database (Reclaim Space)

```sql
VACUUM;
```

### Analyze for Query Optimization

```sql
ANALYZE;
```

### Check Database Integrity

```bash
sqlite3 cwac_analytics.db "PRAGMA integrity_check;"
```

### Database Statistics

```sql
-- Table sizes
SELECT 
    name,
    (SELECT COUNT(*) FROM sqlite_master sm WHERE sm.name = m.name) as row_count
FROM sqlite_master m
WHERE type = 'table'
ORDER BY name;

-- Database file size
SELECT page_count * page_size as size_bytes
FROM pragma_page_count(), pragma_page_size();
```

## Schema Evolution

When updating the schema:

1. **Create migration script**: Document changes in SQL
2. **Update schema.sql**: Modify the master schema file
3. **Test migration**: On a backup database first
4. **Version control**: Commit schema changes
5. **Document**: Update this documentation

**Example Migration**:
```sql
-- Add new column
ALTER TABLE sites ADD COLUMN last_scan_date TEXT;

-- Update system metadata
INSERT OR REPLACE INTO system_metadata (key, value)
VALUES ('db_schema_version', '2.1.0');
```

## Performance Tuning

### Index Usage

```sql
-- Check if indexes are being used
EXPLAIN QUERY PLAN
SELECT * FROM scan_results WHERE site_id = 1;
```

### Query Performance

```sql
-- Enable query timing
.timer ON

-- Run your query
SELECT * FROM issue_details WHERE severity = 'critical';
```

### Optimize Queries

- Use indexes on frequently queried columns
- Avoid `SELECT *`, specify needed columns
- Use `LIMIT` for large result sets
- Use `JOIN` instead of subqueries when possible
- Use prepared statements to prevent SQL injection

## Reference

- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **Schema File**: `cwac_admin_app/database/bi_integration/schema.sql`
- **Sync Scripts**: `comprehensive_sync.py`, `sync_single_scan.py`
