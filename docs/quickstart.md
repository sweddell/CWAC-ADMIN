# Quick Start Guide

Get up and running with CWAC-ADMIN in under 10 minutes!

## Prerequisites

Before starting, ensure you've completed the [Installation Guide](installation.md).

## Step 1: Start the Admin Interface

```bash
cd CWAC-ADMIN
source .venv/bin/activate  # Activate virtual environment
cd cwac_admin_app/app
python3 admin_app.py
```

You should see:
```
* Running on http://127.0.0.1:5001
⚠️  Default admin user created: username='admin', password='admin'
⚠️  PLEASE CHANGE THE PASSWORD IMMEDIATELY!
```

Open your browser to: **http://localhost:5001**

## Step 2: Log In

1. Navigate to http://localhost:5001
2. Log in with default credentials:
   - **Username**: `admin`
   - **Password**: `admin`

**⚠️ Security**: Change this password immediately in production!

## Step 3: Add a Website to Monitor

1. Click **"Sites"** in the navigation menu
2. Click the **"+ Add Site"** button
3. Fill in the form:
   ```
   Organization: Mozilla
   URL: https://www.mozilla.org
   Sector: Technology
   ```
4. Click **"Add Site"**

Your site will now appear in the sites list!

## Step 4: Run Your First Scan

### Option A: Quick Scan via UI

1. Click **"Scan"** in the navigation menu
2. Under "Quick Scan", enter: `https://www.mozilla.org`
3. Select settings:
   - **Max Pages**: 5 (for a quick test)
   - **WCAG Version**: WCAG 2.2
   - **WCAG Level**: AA
   - **Custom Audits**: Check all boxes
4. Click **"Start Scan"**

The scan will run and you'll see real-time progress updates!

### Option B: Scan via Configuration File

If you prefer more control, create a configuration file:

```bash
cd ../../config
cat > quickstart_scan.json << 'EOF'
{
  "base_urls": [
    "https://www.mozilla.org"
  ],
  "user_agent": "CWAC-ADMIN/1.0",
  "max_pages": 5,
  "crawl_delay": 1.0,
  "respect_robots_txt": true,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  },
  "screenshot_audits": {
    "enabled": true
  }
}
EOF
```

Then run from the UI:
1. Go to **Scan** page
2. Select **"quickstart_scan.json"** from the dropdown
3. Click **"Start Scan"**

## Step 5: Monitor Scan Progress

While the scan runs, you'll see:

- ✅ **Status**: Running
- 📊 **Progress**: Percentage complete
- 📄 **Current Action**: Page being scanned
- ⏱️ **Elapsed Time**: Time since scan started

The scan completes when you see: **"✅ Scan completed and synced to database!"**

## Step 6: View Results

### Site Dashboard

1. Click **"Sites"** in navigation
2. Click on **"Mozilla"** in the list
3. You'll see the **Site Detail Dashboard** with:
   - **Overview Tab**: List of scanned pages with scores
   - **Accessibility Tab**: Detailed issues breakdown
   
### Individual Page Results

1. In the site dashboard, click **"View Details"** on any page
2. You'll see the **Page Detail Dashboard** with:
   - **Accessibility Score**: Overall score out of 100
   - **Issues Tab**: All accessibility violations found
   - **Rule Breakdown**: Issues grouped by WCAG criterion

### Understanding the Results

**Issue Severity Levels**:
- 🔴 **Critical**: Severe accessibility barriers
- 🟠 **Serious**: Significant issues affecting usability
- 🟡 **Moderate**: Noticeable problems, but not blockers
- 🔵 **Minor**: Best practice violations, minimal impact

**WCAG Levels**:
- **A**: Minimum level of accessibility
- **AA**: Standard for most organizations (recommended)
- **AAA**: Enhanced accessibility

## Step 7: Set Up Automated Scanning (Optional)

To automatically scan your sites on a schedule:

1. Click **"Scan"** → **"Schedules"** tab
2. Click **"+ Add Schedule"**
3. Configure:
   ```
   Config Name: Daily Mozilla Scan
   Config Path: config/quickstart_scan.json
   Schedule Type: Daily
   Time: 09:00
   Enabled: ✓
   ```
4. Click **"Save Schedule"**

The site will now scan automatically every day at 9:00 AM!

## Common First-Time Tasks

### Task 1: Scan Multiple Pages from One Site

Edit your config to increase `max_pages`:

```json
{
  "base_urls": ["https://www.mozilla.org"],
  "max_pages": 20,  // Scan up to 20 pages
  "crawl_delay": 1.0
}
```

### Task 2: Scan Multiple Sites at Once

Add multiple URLs to `base_urls`:

```json
{
  "base_urls": [
    "https://www.mozilla.org",
    "https://www.w3.org",
    "https://www.google.com"
  ],
  "max_pages": 10
}
```

### Task 3: Export Results

From any results page:
1. Click the **"Export"** button
2. Choose format: **CSV** or **JSON**
3. Results download automatically

### Task 4: Compare Scans Over Time

1. Go to **Site Detail** page
2. Click **"Score Trends"** section
3. View the chart showing accessibility score changes over time

### Task 5: Filter Issues by Severity

On the **Page Detail** page:
1. Go to **"Issues"** tab
2. Use the **"Filter by Severity"** dropdown
3. Select: Critical, Serious, Moderate, or Minor

## Next Steps

Now that you've run your first scan, here are some recommended next steps:

### Learn More About the System

- **[Architecture Overview](architecture.md)** - Understand how CWAC works
- **[Admin Interface Guide](admin-interface.md)** - Explore all features
- **[Configuration Guide](configuration.md)** - Advanced scan settings
- **[Scheduling Guide](scheduling.md)** - Automation options

### Improve Your Accessibility

- **[Accessibility Rules](accessibility-rules.md)** - Understand WCAG criteria
- **[Common Issues](common-issues.md)** - How to fix typical problems
- **[Best Practices](best-practices.md)** - Accessibility guidelines

### Configure for Your Organization

- **Add all your websites** to the Sites list
- **Create site groups** for organization (Government, Marketing, etc.)
- **Set up schedules** for regular monitoring
- **Configure notifications** (if implemented)
- **Create user accounts** for your team

## Troubleshooting

### Scan Fails Immediately

**Check**:
- Is the URL accessible? (Try in browser)
- Is robots.txt blocking CWAC? (Set `respect_robots_txt: false`)
- Is ChromeDriver running? (`chromedriver --version`)

### No Results Appear After Scan

**Check**:
- Did the scan complete? (Look for ✅ completion message)
- Check logs: `tail -f ../../logs/admin_app.log`
- Verify database exists: `ls -la cwac_admin_app/database/bi_integration/cwac_analytics.db`

### "Database Locked" Error

```bash
# Stop all instances
pkill -f admin_app.py

# Restart
python3 admin_app.py
```

### Scan Hangs on a Page

- Some pages may take longer to load
- Default timeout is 30 seconds per page
- Check `logs/audit.log` for details
- You can skip problematic pages in config:
  ```json
  {
    "exclude_patterns": ["*/slow-page/*"]
  }
  ```

## Quick Reference

### URLs
- **Admin Interface**: http://localhost:5001
- **Login**: http://localhost:5001/login
- **Dashboard**: http://localhost:5001/
- **Sites**: http://localhost:5001/sites
- **Scan**: http://localhost:5001/scan

### Default Credentials
- **Username**: admin
- **Password**: admin (change immediately!)

### Important Files
- **Config**: `config/*.json`
- **Results**: `results/*/`
- **Database**: `cwac_admin_app/database/bi_integration/cwac_analytics.db`
- **Logs**: `logs/admin_app.log`, `logs/scheduler.log`

### CLI Commands

```bash
# Start admin interface
python3 cwac_admin_app/app/admin_app.py

# Run scanner directly
python3 cwac/cwac.py config/my_scan.json

# Check scanner help
python3 cwac/cwac.py --help

# Sync scan results manually
python3 cwac_admin_app/database/bi_integration/sync_single_scan.py results/scan_directory/
```

## Example Workflows

### Workflow 1: Weekly Site Audit

1. Add all your sites to the Sites list
2. Create a config for each site (or one config with all URLs)
3. Set up weekly schedule for each
4. Review results every Monday
5. Track trends over time

### Workflow 2: Pre-Release Testing

1. Run scan on staging environment
2. Review critical and serious issues
3. Fix issues
4. Re-scan to verify fixes
5. Deploy to production
6. Scan production to confirm

### Workflow 3: Continuous Monitoring

1. Set up daily scans for production sites
2. Configure site groups (by department/team)
3. Monitor dashboard daily
4. Investigate any score drops
5. Generate monthly reports

## Getting Help

- **Documentation**: Check the [docs](README.md) directory
- **Troubleshooting**: See [troubleshooting.md](troubleshooting.md)
- **FAQ**: Common questions in [faq.md](faq.md)
- **Issues**: Open a GitHub issue
- **Logs**: Check `logs/` directory for detailed errors

## Congratulations!

You've successfully:
- ✅ Started the CWAC-ADMIN admin interface
- ✅ Added a website to monitor
- ✅ Run your first accessibility scan
- ✅ Viewed the results

You're now ready to use CWAC-ADMIN for comprehensive web accessibility testing!
