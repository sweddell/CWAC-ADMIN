# Frequently Asked Questions

Common questions about CWAC-ADMIN.

## General Questions

### What is CWAC-ADMIN?

CWAC-ADMIN is a web-based platform for automated accessibility testing and monitoring. It helps organizations ensure their websites comply with WCAG (Web Content Accessibility Guidelines) standards.

### Who should use CWAC-ADMIN?

- **Organizations** monitoring multiple websites
- **Web developers** testing during development
- **Accessibility teams** conducting audits
- **QA teams** validating WCAG compliance
- **Anyone** responsible for web accessibility

### What standards does it test against?

- WCAG 2.0 (Levels A, AA, AAA)
- WCAG 2.1 (Levels A, AA, AAA)
- WCAG 2.2 (Levels A, AA, AAA - latest)

### How accurate are the results?

CWAC-ADMIN uses axe-core, an industry-leading accessibility engine by Deque Systems. It catches ~57% of WCAG issues automatically. Manual testing is still needed for comprehensive coverage.

## Installation & Setup

### What are the system requirements?

**Minimum:**
- Python 3.9+
- 2GB RAM
- Chrome/Chromium browser
- 5GB disk space

**Recommended:**
- Python 3.9+
- 8GB RAM
- Chrome/Chromium latest
- 20GB+ disk space (for scan results)

### Does it work on Windows?

Yes, but WSL2 (Windows Subsystem for Linux) is recommended for best compatibility.

### Can I use Firefox or Safari?

Currently only Chrome/Chromium is supported, as it's required by the scanner engine.

### Do I need a web server?

No external web server is required. Flask's built-in server works for small deployments. For production, use Nginx or Apache as a reverse proxy.

## Scanning

### How long does a scan take?

**Depends on:**
- Number of pages (1-2 pages per second typical)
- Page load times
- Custom audits enabled
- Server resources

**Examples:**
- Homepage only: ~30 seconds
- 20 pages: 5-10 minutes
- 100 pages: 30-60 minutes

### Can I scan password-protected sites?

Not automatically. The scanner cannot handle login forms. Options:
- Test public pages only
- Use temporary public access
- Scan pre-production environment without auth

### Can I scan dynamic (JavaScript) content?

Yes! CWAC-ADMIN uses Selenium with Chrome, which renders JavaScript before testing.

### Why are some pages skipped?

Pages may be skipped if:
- Blocked by robots.txt
- Match exclude patterns
- Return error status codes
- Timeout
- Maximum pages limit reached

### Can I scan multiple sites at once?

Yes, add multiple URLs to the `base_urls` array in your configuration. The scanner processes them sequentially.

### Do scans impact the target website?

Minimal impact. The scanner:
- Respects `crawl_delay` (default 1 second)
- Follows robots.txt rules
- Uses a single connection
- Sends standard HTTP requests

Use longer `crawl_delay` (2-5 seconds) for high-traffic production sites.

## Results & Reporting

### What do the scores mean?

**Accessibility Score (0-100):**
- **90-100**: Excellent accessibility
- **75-89**: Good, minor issues
- **60-74**: Fair, needs improvement
- **Below 60**: Poor, significant issues

Score is calculated based on number and severity of issues found.

### What's the difference between severity levels?

- **Critical**: Severe barriers, immediate action needed
- **Serious**: Significant impact on accessibility
- **Moderate**: Noticeable issues, should be fixed
- **Minor**: Best practice violations, low impact

### Can I export results?

Yes! Export options:
- **CSV**: Spreadsheet format
- **JSON**: Machine-readable format
- **PDF**: (planned feature)

### How do I share results with my team?

- Use multi-user accounts (create users in User Management)
- Export reports and share files
- Use API to build custom dashboards
- Screenshot results from browser

### Are results stored permanently?

Yes, all scan results are stored in the SQLite database until you delete them. Implement a data retention policy for your organization.

## Scheduling & Automation

### Can I schedule automated scans?

Yes! The built-in scheduler supports:
- Hourly (e.g., every 2 hours)
- Daily (e.g., 9:00 AM)
- Weekly (e.g., Mondays at 9:00 AM)
- Monthly (e.g., 1st of month)
- Custom (cron expressions)

### Do scheduled scans run automatically?

Yes, as long as the admin application is running, the scheduler executes scans in the background.

### Can I run scans via API?

Yes! Use the REST API:
```bash
curl -X POST http://localhost:5001/api/scans/start \
  -H "Content-Type: application/json" \
  -d '{"config_name": "my_scan.json"}'
```

See [API Reference](api-reference.md) for details.

### Can I integrate with CI/CD?

Yes! Call the API from your CI/CD pipeline to trigger scans automatically on deployment.

## Configuration

### What configuration options are available?

Key options:
- `max_pages` - Number of pages to scan
- `crawl_delay` - Delay between requests
- `wcag_version` - WCAG 2.0, 2.1, or 2.2
- `wcag_level` - A, AA, or AAA
- `audits` - Enable/disable custom audits
- `exclude_patterns` - Skip certain URLs
- `timeout` - Page load timeout

See [Configuration Guide](configuration.md) for complete reference.

### Can I test only specific sections of a site?

Yes! Use `include_patterns` to limit crawling:
```json
{
  "base_urls": ["https://www.example.com"],
  "include_patterns": ["*/products/*"]
}
```

### Can I exclude certain pages?

Yes! Use `exclude_patterns`:
```json
{
  "exclude_patterns": [
    "*/admin/*",
    "*/api/*",
    "*.pdf"
  ]
}
```

## Troubleshooting

### Why won't the scanner start?

Common causes:
- ChromeDriver not installed or version mismatch
- Target site not accessible
- Invalid configuration file
- Port 5001 already in use

See [Troubleshooting Guide](troubleshooting.md) for solutions.

### Why is the dashboard empty?

Possible reasons:
- No scans have been run yet
- Scans completed but results didn't sync
- Database connection issue

**Solutions:**
- Run a test scan
- Check logs for errors
- Manually sync results

### Why don't I see any issues?

Possible reasons:
- Site is highly accessible (great!)
- Scanner couldn't access pages
- JavaScript-heavy site with loading issues

**Verify:**
- Check pages were actually scanned
- Review scan logs
- Try scanning a known-problematic site to verify scanner works

### Scans are taking too long

**Solutions:**
- Reduce `max_pages`
- Increase `crawl_delay` (may seem counter-intuitive, but prevents rate limiting)
- Disable non-essential audits
- Scan during off-peak hours
- Upgrade server resources

## Database & Storage

### What database does it use?

SQLite 3 - a serverless, file-based database. No separate database server needed!

### Can I use PostgreSQL or MySQL?

Not currently. SQLite is sufficient for most deployments (tested with 100+ sites, 1000+ scans).

### How much disk space do I need?

**Database:**
- ~1-5MB per scan (depending on pages and issues)
- 100 scans ≈ 100-500MB

**Scan results (CSV files):**
- ~100KB-1MB per scan
- 100 scans ≈ 10-100MB

**Recommendation:** 20GB+ for comfortable operation.

### Can I clean up old data?

Yes! Options:
1. **Manual deletion** via admin interface
2. **SQL query**:
   ```sql
   DELETE FROM scan_results WHERE scan_date < date('now', '-90 days');
   ```
3. **Automated cleanup** script (implement as needed)

## Users & Permissions

### How many users can I have?

Unlimited! Create as many users as needed.

### What's the difference between Admin and User roles?

**Admin:**
- User management (create, edit, delete users)
- System configuration
- All User permissions

**User:**
- View sites and scans
- Run scans
- View results
- Manage own profile

### Can users see each other's work?

Yes, all users see all sites and results. CWAC-ADMIN is designed for team collaboration, not data isolation.

### How do I reset a password?

**As admin:**
1. Go to User Management
2. Click Edit on user
3. Reset password

**As user:**
1. Go to Profile
2. Click "Change Password"
3. Enter new password

**If locked out:**
Delete `admin/users.json` and restart application to regenerate default admin account.

## Performance

### Can it handle 100+ sites?

Yes! CWAC-ADMIN has been tested with:
- 100+ sites
- 1000+ scans in database
- 10+ concurrent users

### How do I improve performance?

**Database:**
```bash
sqlite3 cwac_analytics.db "VACUUM; ANALYZE;"
```

**Archive old results:**
- Move old scan directories
- Delete old scan_results records

**Upgrade resources:**
- More RAM helps with large scans
- Faster disk (SSD) helps with database

### Can I run multiple scanners in parallel?

Not currently. The scanner processes one scan at a time. However, you can schedule multiple scans back-to-back with staggered start times.

## Integrations

### Does it integrate with Jira?

Not natively, but you can:
- Use API to fetch issues
- Create Jira tickets programmatically
- Export CSV and import to Jira

### Does it integrate with Slack?

Not natively, but you can:
- Use Slack webhooks with API
- Send notifications via custom script
- Post results to channels

### Does it have a mobile app?

No, but the web interface is responsive and works on mobile browsers (with limited functionality).

## Security

### Is it secure?

When properly configured, yes. Follow the [Security Best Practices](security.md):
- Change default password
- Use HTTPS in production
- Set strong SECRET_KEY
- Keep software updated
- Restrict file permissions

### Where is user data stored?

All data is stored locally:
- Database: `cwac_admin_app/database/bi_integration/cwac_analytics.db`
- User accounts: `admin/users.json`
- Scan results: `results/` directory

No data is sent to external services.

### Are passwords encrypted?

Yes, passwords are hashed using pbkdf2:sha256 with salt. Plain-text passwords are never stored.

## Licensing

### What license is CWAC-ADMIN under?

BSD 3-Clause License - a permissive open-source license.

### Can I use it commercially?

Yes! The BSD license allows commercial use.

### Can I modify it?

Yes! You can modify, extend, and customize CWAC-ADMIN for your needs.

### Do I need to open-source my modifications?

No, the BSD license doesn't require you to share modifications (unlike GPL).

## Support

### Where can I get help?

- **Documentation**: [`docs/`](README.md) directory
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
- **Issues**: GitHub issue tracker
- **Community**: GitHub Discussions (if available)

### How do I report bugs?

Open a GitHub issue with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information
- Error messages/logs

### Can I request features?

Yes! Open a GitHub issue with:
- Feature description
- Use case
- Why it's useful
- Potential implementation ideas

### Is professional support available?

Check the project repository for information about commercial support options.

## Getting Started

### I'm new to accessibility. Where do I start?

1. **Learn WCAG basics**:
   - [WCAG Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
   - [WebAIM Introduction](https://webaim.org/intro/)

2. **Run your first scan**:
   - Follow [Quick Start Guide](quickstart.md)
   - Start with homepage only
   - Review results and learn

3. **Fix issues**:
   - Start with Critical issues
   - Use "How to Fix" guidance
   - Re-scan to verify

4. **Expand**:
   - Scan more pages
   - Set up schedules
   - Monitor trends

### What should I scan first?

**Priority order:**
1. Homepage
2. Key landing pages
3. Navigation menus
4. Forms and checkouts
5. Content pages

### How often should I scan?

**Recommendations:**
- **During development**: After each significant change
- **Production sites**: Daily or weekly
- **Critical pages**: Hourly or daily
- **Full site audits**: Weekly or monthly

### What issues should I fix first?

**Priority:**
1. **Critical** - Blocks users with disabilities
2. **Serious** - Significant barriers
3. **Moderate** - Noticeable issues
4. **Minor** - Best practices

Also prioritize by:
- **Page importance** - Fix homepage before minor pages
- **User impact** - Fix frequently-used features first
- **Ease of fix** - Quick wins build momentum

## Still Have Questions?

- Check [Documentation Index](README.md)
- Review [Troubleshooting Guide](troubleshooting.md)
- Open a GitHub issue
- Contact support

---

**Can't find your question?** Open an issue to suggest additions to this FAQ!
