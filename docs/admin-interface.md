# Admin Interface Guide

Complete guide to using the CWAC-ADMIN web admin interface.

## Overview

The CWAC-ADMIN admin interface is a Flask-based web application that provides:

- **Dashboard**: Overview of all sites and recent scans
- **Site Management**: Add, edit, and delete websites to monitor
- **Scan Management**: Run scans manually or on a schedule
- **Results Viewing**: Detailed accessibility reports
- **User Management**: Multi-user support with authentication
- **System Monitoring**: Activity logs and system status

**URL**: http://localhost:5001

## Navigation

### Main Menu (Left Sidebar)

- **Dashboard** - Overview and quick stats
- **Sites** - Manage monitored websites
- **Scan** - Run scans and manage schedules
- **Profile** - User settings and password change
- **User Management** (Admin only) - Manage user accounts
- **System Status** (Admin only) - System health and logs

### Top Bar

- **User Menu** (top right) - Profile, settings, logout
- **Activity Indicator** - Recent system activity
- **Search** (if available) - Search sites and issues

## Pages and Features

### 1. Dashboard Page

**URL**: `/` or `/dashboard`

**Purpose**: High-level overview of accessibility status across all monitored sites

**Sections**:

#### Key Metrics Cards
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total Sites  │ Total Scans  │ Avg Score    │ Total Issues │
│      15      │      127     │    78.5      │     2,345    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

#### Recent Scans Table
- Site name
- Scan date/time
- Score (with trend indicator ↑↓)
- Issues count by severity
- Quick action buttons

#### Activity Feed
- Recent scan completions
- Site additions/changes
- System events
- User actions

#### Charts (if available)
- Score trends over time
- Issues by severity distribution
- Compliance rate

### 2. Sites Page

**URL**: `/sites`

**Purpose**: Manage all websites being monitored

#### Sites List View

**Columns**:
- **Organization**: Company/entity name
- **URL**: Website URL
- **Last Scan**: Date of most recent scan
- **Score**: Latest accessibility score
- **Issues**: Count by severity (Critical/Serious/Moderate/Minor)
- **Actions**: View, Edit, Delete buttons

**Features**:
- **Add Site** button (top right)
- **Search/Filter** by organization or URL
- **Sort** by any column
- **Bulk Actions** (if implemented)

#### Add/Edit Site Form

**Fields**:
- **Organization** (required): Name of the organization
- **URL** (required): Full URL including https://
- **Sector**: Dropdown - Government, Education, Commercial, Healthcare, etc.
- **Group** (optional): Site group for organization
- **Notes** (optional): Additional information

**Validation**:
- URL must be valid and accessible
- Duplicate URLs not allowed
- Organization name required

**Example**:
```
Organization: Harvard University
URL: https://www.harvard.edu
Sector: Education
Group: Education Institutions
```

### 3. Site Detail Page

**URL**: `/sites/{site_id}`

**Purpose**: Detailed view of a specific website's accessibility status

#### Overview Tab

**Content**:
- Site information card (URL, organization, sector)
- Latest scan summary
- Score trend chart (last 30 days)
- Quick scan button

**Table: Scanned Pages**

| Page URL | Score | Issues | Last Scan | Actions |
|----------|-------|--------|-----------|---------|
| / (Homepage) | 85 | 12 | 2024-11-12 | View Details |
| /about | 78 | 18 | 2024-11-12 | View Details |
| /contact | 92 | 5 | 2024-11-12 | View Details |

**Features**:
- Sort by score, issues, or date
- Filter by score range
- Export to CSV/JSON
- Search pages

#### Accessibility Tab

**Sub-tabs**:

**Issues Sub-tab**:
- Issues by severity (pie chart)
- Issues by WCAG criterion (bar chart)
- Detailed issues table with:
  - Issue type
  - WCAG criterion (e.g., 1.3.1)
  - Severity
  - Pages affected count
  - Description
  - How to fix

**Passed Sub-tab**:
- WCAG criteria that passed
- Best practices followed
- Positive indicators

**Pages Sub-tab**:
- All scanned pages with individual scores
- Click to view page-specific results

### 4. Page Detail Page

**URL**: `/sites/{site_id}/page?url={page_url}`

**Purpose**: Detailed accessibility report for a specific page

#### Page Information Card
```
┌─────────────────────────────────────────────────────────┐
│ Page: https://www.example.com/about                     │
│ Last Scanned: 2024-11-12 10:30 AM                      │
│ Score: 78/100                         Trend: ↑ +5      │
└─────────────────────────────────────────────────────────┘
```

#### Score Trends Chart
- Line chart showing score changes over time
- Hover for specific data points
- Zoom and pan controls

#### Issues Tab

**Issues by Impact Level**:
```
Critical  [■■■   ] 3
Serious   [■■■■■ ] 8
Moderate  [■■    ] 4
Minor     [■     ] 2
```

**Detailed Issues Table**:

| Severity | Issue Type | WCAG | Element | Description | Help |
|----------|------------|------|---------|-------------|------|
| Critical | color-contrast | 1.4.3 | button.submit | Insufficient contrast ratio | [View] |
| Serious | label | 1.3.1 | input#email | Form input missing label | [View] |

**For each issue**:
- Click "View" to see:
  - Full description
  - WCAG success criterion details
  - How to fix (step-by-step)
  - Code example
  - Related resources

#### Rule Breakdown Tab

Issues organized by WCAG criterion:

```
1.1.1 Non-text Content (Level A)
  └─ 5 issues across 3 elements
     • Missing alt text on images

1.3.1 Info and Relationships (Level A)
  └─ 12 issues across 8 elements
     • Missing form labels
     • Improper heading hierarchy

1.4.3 Contrast (Level AA)
  └─ 3 issues across 2 elements
     • Insufficient color contrast
```

### 5. Scan Page

**URL**: `/scan`

**Purpose**: Run accessibility scans and manage scanning

#### Tabs

##### Quick Scan Tab

**Simple scan interface for immediate testing**:

```
┌─────────────────────────────────────────────────┐
│ URL to Scan: [https://www.example.com        ] │
│                                                 │
│ ☐ Scan only homepage                           │
│ ☐ Scan entire site (max 20 pages)              │
│                                                 │
│ Settings:                                       │
│   Max Pages: [5    ▼]                          │
│   WCAG Version: [WCAG 2.2 ▼]                   │
│   WCAG Level: [AA ▼]                           │
│                                                 │
│ Custom Audits:                                  │
│   ☑ Language Audit                             │
│   ☑ Reflow Audit                               │
│   ☑ Focus Indicator Audit                      │
│                                                 │
│          [Start Scan]                          │
└─────────────────────────────────────────────────┘
```

**Progress Display** (during scan):
```
Scanning: https://www.example.com
Status: In Progress (45%)
Current: Scanning page 9 of 20
Time Elapsed: 2m 15s
```

##### Configurations Tab

**Manage saved scan configurations**:

| Name | Base URLs | Max Pages | WCAG | Actions |
|------|-----------|-----------|------|---------|
| Full Site Scan | example.com | 100 | 2.2 AA | Edit, Delete, Run |
| Homepage Only | example.com | 1 | 2.2 AAA | Edit, Delete, Run |

**Add Configuration**:
- Upload JSON file
- Or use configuration editor (form-based)

##### Schedules Tab

**Automated scan scheduling**:

| Config | Schedule | Last Run | Next Run | Status | Actions |
|--------|----------|----------|----------|--------|---------|
| Full Site Scan | Daily 9:00 | 2024-11-12 09:00 | 2024-11-13 09:00 | ✓ Enabled | Edit, Disable |
| Weekly Deep Scan | Mon 02:00 | 2024-11-11 02:00 | 2024-11-18 02:00 | ✓ Enabled | Edit, Disable |

**Add Schedule Form**:
```
Config Name: [My Daily Scan            ]
Config File: [config/my_scan.json ▼    ]
Schedule Type: [Daily ▼                 ]
Time: [09:00                           ]
☑ Enabled
```

**Schedule Types**:
- **Hourly**: Every N hours
- **Daily**: Specific time each day
- **Weekly**: Specific day and time
- **Monthly**: Specific date and time
- **Custom (Cron)**: Cron expression

### 6. Profile Page

**URL**: `/profile`

**Purpose**: Manage user account settings

**Sections**:

#### User Information
- Username (read-only)
- Email address
- Organization
- Role (User or Admin)
- Account status
- Registration date

#### Change Password
```
Current Password: [****************]
New Password: [****************]
Confirm Password: [****************]

Requirements:
- Minimum 8 characters
- Mix of letters and numbers recommended

[Change Password]
```

#### Preferences (if implemented)
- Email notifications
- Dashboard default view
- Results per page
- Theme (light/dark)

### 7. User Management Page

**URL**: `/users` (Admin only)

**Purpose**: Manage user accounts

**User List**:

| Username | Email | Role | Status | Registered | Actions |
|----------|-------|------|--------|------------|---------|
| admin | admin@cwac.org | Admin | Active | 2024-01-01 | Edit |
| john.doe | john@example.com | User | Active | 2024-02-15 | Edit, Deactivate |
| jane.smith | jane@example.com | User | Pending | 2024-11-12 | Approve, Deny |

**Actions**:
- **Approve**: Activate pending user
- **Deactivate**: Disable user account
- **Edit**: Change user role or details
- **Delete**: Remove user (confirmation required)

**User Status**:
- **Active**: Can log in and use system
- **Pending**: Awaiting admin approval
- **Deactivated**: Cannot log in

**Add User**:
- Username
- Email
- Initial password (or send email)
- Role (User or Admin)
- Auto-approve or require approval

### 8. System Status Page

**URL**: `/system` (Admin only)

**Purpose**: Monitor system health and activity

#### System Health
```
┌────────────────────────┐  ┌────────────────────────┐
│ Database Status        │  │ Scanner Status         │
│ ✓ Connected            │  │ ✓ ChromeDriver found   │
│ Size: 45.2 MB          │  │ ✓ Chrome v119.0        │
└────────────────────────┘  └────────────────────────┘

┌────────────────────────┐  ┌────────────────────────┐
│ Scheduler Status       │  │ Disk Space            │
│ ✓ Running              │  │ Available: 125 GB      │
│ Active Jobs: 5         │  │ Results: 2.3 GB        │
└────────────────────────┘  └────────────────────────┘
```

#### Activity Log

Recent system events:

| Time | Event | Details |
|------|-------|---------|
| 10:30 AM | Scan Complete | Harvard University |
| 09:00 AM | Scheduled Scan Started | MIT |
| 08:45 AM | User Login | john.doe |

**Filters**:
- Event type (scan, login, config, etc.)
- Date range
- User

#### System Logs

**View logs in real-time**:
- Admin app log
- Scheduler log
- Latest scan logs

**Features**:
- Live tail
- Search/filter
- Download log files

## Common Tasks

### Task: Run a Quick Test Scan

1. Go to **Scan** page
2. Enter URL in "Quick Scan" tab
3. Select "Scan only homepage"
4. Click "Start Scan"
5. Wait for completion (~30 seconds)
6. View results

### Task: Set Up Daily Automated Scanning

1. Create a scan configuration file in `config/` directory
2. Go to **Scan** → **Schedules** tab
3. Click **"+ Add Schedule"**
4. Fill in:
   - Config name: "Daily Full Scan"
   - Config file: Select your file
   - Schedule: "Daily" at "09:00"
   - Enable: ✓
5. Click **"Save"**

### Task: Compare Two Scans

1. Go to **Site Detail** page
2. View **"Score Trends"** chart
3. Hover over data points to see specific values
4. Or export data and compare in Excel

### Task: Export All Issues

1. Go to **Site Detail** → **Accessibility** tab
2. Click **Issues** sub-tab
3. Click **"Export"** button
4. Choose CSV or JSON
5. File downloads automatically

### Task: Find All Critical Issues Across Sites

1. Go to **Dashboard**
2. Use search/filter: "Severity: Critical"
3. Or go to each Site Detail page
4. Filter issues by "Critical" severity

## Keyboard Shortcuts

- **`/`** - Focus search bar
- **`d`** - Go to Dashboard
- **`s`** - Go to Sites
- **`n`** - Start new scan
- **`Esc`** - Close modal/dialog
- **`?`** - Show keyboard shortcuts help

## Tips and Best Practices

### Performance

- **Limit max pages** for faster scans (5-20 pages)
- **Schedule heavy scans** during off-hours
- **Archive old results** to keep database small

### Accuracy

- **Use consistent settings** for comparable results
- **Re-scan after fixes** to verify improvements
- **Test multiple pages** not just homepage

### Organization

- **Use site groups** to organize by department/team
- **Name configs clearly**: "Marketing-Weekly", "Product-Full"
- **Document custom settings** in config file comments

### Monitoring

- **Check dashboard daily** for score changes
- **Review activity log** for failed scans
- **Set up schedules** for all critical sites

## Troubleshooting UI Issues

### Page Not Loading

- Check browser console (F12) for errors
- Verify Flask server is running
- Check logs: `tail -f logs/admin_app.log`

### Scan Button Disabled

- Ensure URL is valid
- Check ChromeDriver is installed
- Verify no other scan is running

### Results Not Updating

- Hard refresh browser (Cmd+Shift+R / Ctrl+F5)
- Check if scan completed successfully
- Verify database sync ran (check logs)

### Charts Not Displaying

- Enable JavaScript in browser
- Check Chart.js is loading (browser console)
- Verify data exists (check database)

## Security Best Practices

- **Change default password** immediately
- **Use strong passwords** (12+ characters)
- **Log out** when finished
- **Don't share credentials**
- **Review activity log** for suspicious activity
- **Keep software updated**

## Mobile/Responsive View

The admin interface is responsive and works on:

- **Desktop**: Full featured (recommended)
- **Tablet**: Most features available
- **Mobile**: Basic features only

For best experience, use desktop browser with screen width 1280px+.

## Browser Compatibility

**Fully Supported**:
- Chrome 90+
- Firefox 90+
- Safari 14+
- Edge 90+

**Limited Support**:
- IE 11 (not recommended)

## Customization

### Changing Port

Edit `admin_app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)  # Change port here
```

### Custom Branding

Edit templates in `cwac_admin_app/templates/`:
- `base.html` - Main layout and navigation
- `dashboard.html` - Dashboard page
- Logo/favicon in `cwac_admin/img/`

### Custom Styles

Add CSS in `cwac_admin/css/admin.css`

## Next Steps

- Review [Configuration Guide](configuration.md) for advanced scan settings
- Set up [Automated Scheduling](scheduling.md)
- Read [Architecture](architecture.md) to understand the system
- Check [API Reference](api-reference.md) for programmatic access

## Getting Help

- **Documentation**: [docs/README.md](README.md)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
- **FAQ**: [faq.md](faq.md)
- **Issues**: GitHub issue tracker
