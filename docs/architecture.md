# System Architecture

## Overview

CWAC-ADMIN is built as a modular system with three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                  (Web Browser / Dashboard)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
┌──────────────────────────▼──────────────────────────────────┐
│                     Admin Application                        │
│                  (Flask / Python 3.9+)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Web UI      │  │  Scheduler   │  │  API Routes  │    │
│  │  Templates   │  │  Service     │  │  /api/*      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
┌───────────▼────┐  ┌──────▼──────┐  ┌──▼──────────┐
│  CWAC Scanner  │  │  Analytics  │  │   Config    │
│  (cwac.py)     │  │  Database   │  │   Files     │
│  Python/       │  │  SQLite     │  │   JSON      │
│  Selenium      │  │             │  │             │
└───────┬────────┘  └──────▲──────┘  └─────────────┘
        │                  │
        │ CSV Results      │ Sync
        ▼                  │
┌─────────────────┐       │
│  Results/       │───────┘
│  Scan Outputs   │
└─────────────────┘
```

## Component Details

### 1. CWAC Scanner (`cwac/`)

**Purpose**: Automated accessibility testing engine

**Technology Stack**:
- Python 3.9+
- Selenium WebDriver
- axe-core (via JavaScript injection)
- Chrome/Chromium browser

**Key Files**:
- `cwac.py` - Main scanner entry point
- `src/crawler.py` - Website crawling logic
- `src/scanner.py` - Accessibility testing coordination
- `src/audits/` - Custom accessibility audits

**Responsibilities**:
- Crawl websites and discover pages
- Run axe-core accessibility tests
- Execute custom audits (focus, reflow, language)
- Generate CSV result files
- Capture screenshots for visual audits

**Output**: CSV files in `results/{timestamp}/` directory containing:
- `audit_log.csv` - All accessibility issues found
- `pages_scanned.csv` - Summary of pages tested
- `seo_results.csv` - SEO metrics
- `language_audit.csv` - Language testing results
- `reflow_audit.csv` - Responsive design results
- `focus_indicator_audit.csv` - Focus visibility results

### 2. Admin Application (`cwac_admin_app/`)

**Purpose**: Web interface for management, scheduling, and reporting

**Technology Stack**:
- Flask 3.0+
- SQLite3
- Jinja2 templates
- Bootstrap 5.3
- Chart.js for visualizations

**Key Files**:
- `app/admin_app.py` - Main Flask application (4300+ lines)
- `app/scheduler.py` - Automated scan scheduling
- `templates/` - HTML templates for UI
- `database/bi_integration/` - Database sync scripts

**Responsibilities**:
- Provide web UI for viewing scan results
- Manage sites and scan configurations
- Schedule automated scans
- Sync scan results to database
- Generate analytics and trends
- User authentication and management

**Features**:
- Dashboard with key metrics
- Site management (add, edit, delete)
- Individual site and page detail views
- Scan scheduling with cron-like configuration
- Activity logging
- User management with role-based access

### 3. Analytics Database

**Purpose**: Persistent storage for scan results and system data

**Technology**: SQLite3

**Location**: `cwac_admin_app/database/bi_integration/cwac_analytics.db`

**Schema**: See [Database Schema](database-schema.md)

**Key Tables**:
- `sites` - Websites being monitored
- `scan_results` - Scan summaries with metrics
- `page_results` - Per-page results
- `issue_details` - Detailed accessibility issues
- `scan_schedules` - Automated scan configuration

**Sync Process**:
```
1. Scanner completes → Creates .scan_success marker
2. Admin app detects completion
3. sync_single_scan.py is called
4. comprehensive_sync.py parses CSV files
5. Data is inserted into database
6. Dashboard displays updated results
```

## Data Flow

### Scan Execution Flow

```
1. User/Scheduler triggers scan
   ↓
2. Admin app calls cwac.py with config
   ↓
3. CWAC Scanner:
   - Reads config file
   - Crawls website
   - Runs accessibility tests
   - Generates CSV results
   ↓
4. Scanner creates .scan_success marker
   ↓
5. Admin app detects completion
   ↓
6. sync_single_scan.py:
   - Parses CSV files
   - Transforms data
   - Inserts into database
   ↓
7. Dashboard displays updated results
```

### API Request Flow

```
Browser → HTTP Request → Flask Router → Route Handler
                                            ↓
                                     SQLite Query
                                            ↓
                                    JSON Response
                                            ↓
                               Browser renders data
```

## Key Design Patterns

### 1. Separation of Concerns

- **Scanner**: Only responsible for testing, outputs raw data
- **Admin App**: Manages UI, scheduling, and persistence
- **Database**: Single source of truth for reporting

This allows:
- Scanner to be used independently via CLI
- Admin interface to be optional
- Easy testing and maintenance

### 2. File-Based Communication

Scanner and admin app communicate via:
- CSV result files (scanner → admin)
- Success markers (scanner signals completion)
- JSON config files (admin → scanner)

Benefits:
- No direct coupling between components
- Easy to debug (inspect CSV files)
- Scanner can be distributed/containerized

### 3. Auto-Sync Architecture

```python
# In admin_app.py after scan completes:
if (scan_dir / '.scan_success').exists():
    subprocess.run([python, 'sync_single_scan.py', scan_dir])
```

Benefits:
- Automatic database updates
- No manual intervention needed
- Resilient to failures (can re-sync)

### 4. Progressive Enhancement

The admin interface works with or without:
- Database (falls back to CSV files)
- Scheduler (manual scans still work)
- JavaScript (server-side rendering)

## Deployment Architecture

### Single Server Deployment

```
┌─────────────────────────────────────┐
│         Server (Linux/Mac)          │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Flask Admin (Port 5001)    │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Scheduler Service          │  │
│  │  (Background Process)       │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  CWAC Scanner               │  │
│  │  (Called by Flask/Scheduler)│  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  SQLite Database            │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  Chrome/Chromium            │  │
│  └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Recommended Setup

1. **Application Server**: Ubuntu 20.04+ or macOS
2. **Web Server**: Nginx reverse proxy to Flask
3. **Process Manager**: systemd for Flask and scheduler
4. **Browser**: Headless Chrome/Chromium

## Security Considerations

### Authentication

- Flask-Login for session management
- Password hashing with pbkdf2:sha256
- User status (active, pending, deactivated)

### File System

- Scanner runs in isolated directory
- Results stored outside web root
- Config files validated before execution

### Database

- Parameterized queries prevent SQL injection
- Foreign key constraints enforce integrity
- Regular backups recommended

### Network

- CORS configured for API endpoints
- HTTPS recommended for production
- Secret key for session encryption

## Performance Characteristics

### Scanning Performance

- **Speed**: ~1-2 pages per second (depends on page size)
- **Concurrency**: Single-threaded Selenium driver
- **Memory**: ~500MB per scan process
- **CPU**: Moderate (Chrome rendering)

### Database Performance

- **Storage**: ~1-5MB per complete site scan
- **Query Speed**: Sub-second for most queries
- **Indexes**: On frequently queried columns
- **Optimization**: Bulk inserts during sync

### Admin Interface

- **Response Time**: <100ms for most pages
- **Caching**: Browser caching for static assets
- **Pagination**: Large result sets paginated
- **Charts**: Client-side rendering with Chart.js

## Scalability

### Current Limits

- **Sites**: Tested with 100+ sites
- **Scans**: 1000+ scans per database
- **Concurrent Users**: 5-10 simultaneous users
- **Scheduled Scans**: 50+ scheduled jobs

### Scaling Options

1. **Horizontal Scaling**: Run multiple scanner instances
2. **Database Upgrade**: Migrate to PostgreSQL for high load
3. **Caching**: Add Redis for session/query caching
4. **Queue System**: Add Celery for async task processing

## Technology Choices

### Why Flask?

- Lightweight and flexible
- Easy to deploy
- Rich ecosystem
- Built-in development server

### Why SQLite?

- Zero configuration
- Single file database
- Sufficient for medium-scale deployments
- Easy backups and migrations

### Why Selenium?

- Industry standard for browser automation
- Comprehensive browser API
- Works with real browsers
- Good documentation

### Why axe-core?

- Industry-leading accessibility engine
- Actively maintained by Deque
- Comprehensive WCAG coverage
- Fast and accurate

## Extension Points

The system is designed for extensibility:

### Adding Custom Audits

Create new audit files in `cwac/src/audits/`:

```python
class MyCustomAudit(BaseAudit):
    def run(self, driver, page_state):
        # Your custom testing logic
        return results
```

### Adding API Endpoints

Add routes in `admin_app.py`:

```python
@app.route('/api/my-endpoint')
@login_required
def my_endpoint():
    return jsonify({'data': 'value'})
```

### Custom Reports

Add templates in `templates/`:

```html
{% extends "base.html" %}
{% block content %}
    <!-- Your report HTML -->
{% endblock %}
```

## Maintenance

### Regular Tasks

- **Daily**: Monitor scan completion and errors
- **Weekly**: Review disk space (results directory)
- **Monthly**: Database backup
- **Quarterly**: Update dependencies and browser driver

### Monitoring

Check logs in:
- `logs/admin_app.log` - Flask application logs
- `logs/scheduler.log` - Scheduled scan logs
- `logs/audit.log` - Scanner logs (per scan)

### Backup Strategy

1. **Database**: `cp cwac_analytics.db cwac_analytics_backup.db`
2. **Configs**: Backup `config/` directory
3. **Results**: Archive old scan results periodically
