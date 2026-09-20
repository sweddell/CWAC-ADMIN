# CWAC Analytics Database

## Overview

This directory contains the SQLite analytics database and data synchronization tools for the CWAC-ADMIN Admin interface.

## Files

### Core Files
- **`cwac_analytics.db`** - SQLite database containing all analytics and scan data
- **`schema.sql`** - Complete database schema definition
- **`sync_single_scan.py`** - Sync individual scan results to the database
- **`comprehensive_sync.py`** - Core synchronization logic and parsing

## Database Schema

### Main Tables

**Sites & Organization**
- `sites` - Websites being monitored
- `site_groups` - Organizational groupings (Government, Education, etc.)
- `organisations` - Organization entities
- `groups` - Legacy group table

**Scan Results**
- `scan_results` - Main scan summary data with accessibility and SEO metrics
- `page_results` - Individual page-level results
- `issue_details` - Detailed accessibility issues

**Audit Results** (Special accessibility tests)
- `language_audit_results` - Language attribute testing
- `reflow_audit_results` - Responsive/reflow testing  
- `focus_indicator_audit_results` - Focus indicator visibility
- `screenshot_audit_results` - Visual regression data

**SEO/AEO Data**
- `seo_results` - SEO metrics and structured data

**System Management**
- `scan_schedules` - Automated scan scheduling configuration
- `activity_log` - User actions and system events
- `system_metadata` - Configuration and status data

## Usage

### Automatic Synchronization

Scans are automatically synced to the database after completion via:
- **Admin Interface**: Scans initiated through the web UI are auto-synced
- **Scheduler**: Scheduled scans are auto-synced after completion

### Manual Synchronization

To manually sync a specific scan directory:

```bash
cd cwac_admin_app/database/bi_integration
python3 sync_single_scan.py /path/to/scan/directory
```

### Database Initialization

The database is automatically initialized when the application starts. Tables are created via `CREATE TABLE IF NOT EXISTS` statements, so running the application will set up the database structure.

To manually initialize from schema:

```bash
cd cwac_admin_app/database/bi_integration
sqlite3 cwac_analytics.db < schema.sql
```

## Data Flow

```
CWAC Scanner
    ↓
CSV Results (results/scan_directory/)
    ↓
sync_single_scan.py
    ↓
comprehensive_sync.py (parsing logic)
    ↓
cwac_analytics.db (SQLite)
    ↓
Flask Admin API (admin_app.py)
    ↓
Web Dashboard (JavaScript/Chart.js)
```

## Key Features

### Automated Data Pipeline
- Scans are automatically detected and synced after completion
- Success markers (`.scan_success`) ensure only complete scans are processed
- Duplicate detection prevents re-syncing existing data

### Comprehensive Metrics
- **Accessibility**: WCAG compliance, issue counts by severity
- **SEO**: Metadata, structured data, technical SEO
- **Performance**: Page load times, scan duration
- **Audit Results**: Custom accessibility audits

### Historical Tracking
- All scan results are preserved for trend analysis
- Timestamps enable time-based filtering and reporting
- Activity log tracks user actions and system events

## Integration Points

### Used By
- `cwac_admin_app/app/admin_app.py` - Main Flask application
- `cwac_admin_app/app/scheduler.py` - Automated scan scheduler

### API Endpoints
The database is accessed through Flask API endpoints in `admin_app.py`:
- `/api/sites/*` - Site management
- `/api/analytics/*` - Dashboard data
- `/api/schedules/*` - Scan scheduling

## Requirements

- Python 3.9+
- SQLite3 (included with Python)
- No external database dependencies

## Notes

- The database file (`cwac_analytics.db`) should be gitignored
- Schema changes should be added to `schema.sql`
- All timestamps use ISO 8601 format
- Foreign key constraints ensure referential integrity
