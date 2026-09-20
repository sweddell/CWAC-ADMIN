# Scan Scheduling Guide

Automate accessibility scans with the CWAC-ADMIN scheduler.

## Overview

The CWAC-ADMIN scheduler allows you to automate regular accessibility scans. This guide covers:

- Setting up automated scans
- Schedule types and configuration
- Managing existing schedules
- Troubleshooting scheduler issues

## How the Scheduler Works

```
┌──────────────────┐
│   APScheduler    │  ← Background service
│    (Python)      │
└────────┬─────────┘
         │ Checks schedules every minute
         ▼
┌──────────────────┐
│ scan_schedules   │  ← Database table
│     table        │
└────────┬─────────┘
         │ When trigger time matches
         ▼
┌──────────────────┐
│  Start Scan      │  ← Executes configured scan
│  (CWAC Scanner)  │
└────────┬─────────┘
         │ On completion
         ▼
┌──────────────────┐
│ Sync to Database │  ← Results stored
│  (admin_app.py)  │
└──────────────────┘
```

**Key Points:**
- Scheduler runs as part of the Flask application
- Checks for due scans every 60 seconds
- Executes scans in the background
- Automatically syncs results to database
- Logs all activity

## Creating a Schedule

### Via Admin Interface

1. **Navigate to Scan page**
   - Click **"Scan"** in the navigation menu
   - Click the **"Schedules"** tab

2. **Click "+ Add Schedule"**

3. **Fill in the form:**

   ```
   Config Name: [Daily Homepage Scan]
   Config File: [Select from dropdown]
   Schedule Type: [Daily ▼]
   Schedule Value: [09:00]
   ☑ Enabled
   ```

4. **Click "Save"**

Your scan will now run automatically according to the schedule!

## Schedule Types

### 1. Hourly

Run scan every N hours.

**Schedule Value Format:** `"N"` (integer)

**Examples:**
- `"1"` - Every hour
- `"2"` - Every 2 hours
- `"6"` - Every 6 hours
- `"12"` - Twice daily

**Use Cases:**
- Critical production sites
- Continuous integration testing
- Real-time monitoring

**Configuration:**
```json
{
  "schedule_type": "hourly",
  "schedule_value": "2"
}
```

### 2. Daily

Run scan at specific time each day.

**Schedule Value Format:** `"HH:MM"` (24-hour format)

**Examples:**
- `"09:00"` - 9:00 AM daily
- `"15:30"` - 3:30 PM daily
- `"00:00"` - Midnight daily
- `"23:59"` - 11:59 PM daily

**Use Cases:**
- Regular monitoring
- Off-peak scanning
- Daily compliance checks

**Configuration:**
```json
{
  "schedule_type": "daily",
  "schedule_value": "09:00"
}
```

### 3. Weekly

Run scan on specific day(s) and time.

**Schedule Value Format:** `"DAY,HH:MM"` or `"DAY1|DAY2,HH:MM"`

**Days:** monday, tuesday, wednesday, thursday, friday, saturday, sunday

**Examples:**
- `"monday,09:00"` - Mondays at 9 AM
- `"friday,17:00"` - Fridays at 5 PM
- `"monday|wednesday|friday,12:00"` - MWF at noon
- `"sunday,00:30"` - Sundays at 12:30 AM

**Use Cases:**
- Weekly audits
- End-of-week reports
- Regular maintenance windows

**Configuration:**
```json
{
  "schedule_type": "weekly",
  "schedule_value": "monday,09:00"
}
```

### 4. Monthly

Run scan on specific day of month and time.

**Schedule Value Format:** `"DAY,HH:MM"`

**Day:** 1-31 (day of month)

**Examples:**
- `"1,09:00"` - 1st of month at 9 AM
- `"15,12:00"` - 15th of month at noon
- `"28,00:00"` - 28th of month at midnight

**Use Cases:**
- Monthly compliance reports
- Quarterly audits (every 3 months)
- Annual reviews

**Configuration:**
```json
{
  "schedule_type": "monthly",
  "schedule_value": "1,09:00"
}
```

**Note:** For months with fewer days (e.g., February), schedules set for days 29-31 will not run.

### 5. Custom (Cron)

Advanced scheduling using cron expressions.

**Schedule Value Format:** Cron expression (5 fields)

**Cron Format:** `"minute hour day month day_of_week"`

**Examples:**
- `"0 */6 * * *"` - Every 6 hours
- `"30 8-17 * * 1-5"` - Every hour from 8:30 AM to 5:30 PM, weekdays
- `"0 0 1 */3 *"` - First day of every 3rd month
- `"0 2 * * 0"` - 2 AM every Sunday

**Use Cases:**
- Complex schedules
- Multiple times per day
- Business hours only
- Specific date patterns

**Configuration:**
```json
{
  "schedule_type": "cron",
  "schedule_value": "0 */6 * * *"
}
```

**Cron Quick Reference:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, Sunday=0)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

## Managing Schedules

### View All Schedules

1. Go to **Scan** → **Schedules** tab
2. See table with all configured schedules:

| Config | Schedule | Last Run | Next Run | Status | Actions |
|--------|----------|----------|----------|--------|---------|
| Daily Full | Daily 09:00 | 2024-11-12 09:00 | 2024-11-13 09:00 | ✓ Enabled | Edit, Disable, Delete |

### Edit a Schedule

1. Click **"Edit"** button on the schedule
2. Modify settings
3. Click **"Save"**

Changes take effect immediately.

### Enable/Disable a Schedule

**To disable:**
1. Click **"Disable"** button
2. Schedule will not run until re-enabled
3. Status changes to "⊘ Disabled"

**To re-enable:**
1. Click **"Enable"** button
2. Schedule resumes according to configuration

**Use cases for disabling:**
- Temporary maintenance
- Site unavailable
- Testing configuration changes

### Delete a Schedule

1. Click **"Delete"** button
2. Confirm deletion
3. Schedule is permanently removed

**⚠️ Warning:** Deletion cannot be undone. Past scan results are preserved.

### Run Schedule Manually

To test a schedule or run it ahead of schedule:

1. Click **"Run Now"** button on the schedule
2. Scan starts immediately
3. Next scheduled time is not affected

## Schedule Examples

### Example 1: Standard Business Website

**Goal:** Daily monitoring during off-peak hours

```
Config Name: Production Daily Scan
Config File: config_standard_scan.json
Schedule Type: Daily
Time: 02:00
Enabled: ✓
```

**Rationale:**
- Runs at 2 AM when traffic is low
- Daily frequency catches issues quickly
- Off-peak timing doesn't impact users

### Example 2: E-Commerce Site

**Goal:** Frequent monitoring during business hours

```
Config Name: Homepage Check
Config File: config_homepage_only.json
Schedule Type: Hourly
Interval: 2
Enabled: ✓
```

**Rationale:**
- Every 2 hours catches issues fast
- Homepage is most critical page
- Quick scans (1 page) minimize impact

### Example 3: Government Site

**Goal:** Weekly comprehensive audit for compliance

```
Config Name: Weekly Comprehensive Audit
Config File: config_full_site_wcag_aa.json
Schedule Type: Weekly
Day & Time: sunday,00:30
Enabled: ✓
```

**Rationale:**
- Sundays at 12:30 AM = minimal traffic
- Weekly frequency balances thoroughness and resources
- Comprehensive scan covers all pages

### Example 4: Multiple Scans for Same Site

**Set up layered monitoring:**

```
Schedule 1: Quick Check
- Config: homepage_only.json
- Type: Hourly (2)
- Catches critical homepage issues

Schedule 2: Standard Scan
- Config: top_20_pages.json
- Type: Daily (09:00)
- Covers key pages daily

Schedule 3: Full Audit
- Config: comprehensive_scan.json
- Type: Weekly (sunday,02:00)
- Deep dive weekly
```

### Example 5: Pre-Deployment Testing

**Goal:** Scan staging before each deployment

```
Config Name: Staging Pre-Deploy
Config File: config_staging_full.json
Schedule Type: Daily
Time: 08:00
Enabled: ✓ (enable only during release cycles)
```

**Workflow:**
1. Enable schedule during release preparation
2. Review results each morning
3. Fix issues before production deployment
4. Disable schedule after release

## Best Practices

### Timing

**Choose off-peak hours:**
- Midnight to 6 AM for most sites
- Weekend nights for high-traffic sites
- Avoid peak business hours

**Consider time zones:**
- If site serves global users, choose appropriate time
- Schedule based on server location, not your location

**Stagger multiple scans:**
```
Site A: 01:00
Site B: 01:30
Site C: 02:00
Site D: 02:30
```

Prevents resource contention.

### Frequency

**Homepage/Critical Pages:**
- Hourly or every 2 hours
- Use quick configs (1-5 pages)

**Main Pages (20-50 pages):**
- Daily
- Standard scan configuration

**Full Site (100+ pages):**
- Weekly or monthly
- Comprehensive configuration

### Configuration Selection

**Match schedule to config:**
- Frequent schedules → quick configs
- Infrequent schedules → comprehensive configs

**Example:**
```
❌ Bad: Hourly full-site scan (100 pages)
   → Excessive load, slow completion

✓ Good: Hourly homepage scan (1 page)
   → Fast, catches critical issues

✓ Good: Weekly full-site scan (100 pages)
   → Thorough, manageable frequency
```

### Resource Management

**Limit concurrent scans:**
- Don't schedule multiple scans at same time
- Scanner runs one scan at a time
- Second scan will wait for first to complete

**Monitor scan duration:**
- Check how long scans take
- Ensure completion before next scheduled run
- Adjust frequency if scans overlap

### Maintenance

**Regular review:**
- Monthly: Review all schedules
- Quarterly: Audit schedule effectiveness
- Annually: Revisit strategy

**Update configurations:**
- When site structure changes
- After major site updates
- When WCAG requirements change

## Troubleshooting

### Schedule Not Running

**Problem:** Schedule is enabled but scan doesn't start

**Check:**
1. **Scheduler service running**
   ```bash
   # Check if admin_app.py is running
   ps aux | grep admin_app.py
   ```

2. **Schedule configuration**
   - Verify schedule type and value
   - Check "Next Run" time is in the future
   - Ensure "Enabled" is checked

3. **Configuration file exists**
   - Verify config file in `config/` directory
   - Check file permissions

4. **System logs**
   ```bash
   tail -f logs/admin_app.log
   tail -f logs/scheduler.log
   ```

**Solutions:**
- Restart admin application
- Verify system time is correct
- Check for errors in logs

### Scan Starts But Fails

**Problem:** Scheduled scan starts but doesn't complete

**Check:**
1. **Scanner logs**
   ```bash
   tail -f logs/audit.log
   ```

2. **Site accessibility**
   - Can server reach target site?
   - Is site blocking scanner?

3. **Resource limits**
   - Enough disk space for results?
   - Enough memory for Chrome/Selenium?

**Solutions:**
- Review scan configuration
- Increase timeout values
- Check network connectivity
- Verify ChromeDriver is working

### Results Not Syncing

**Problem:** Scan completes but results don't appear in database

**Check:**
1. **Sync scripts**
   ```bash
   ls -la cwac_admin_app/database/bi_integration/sync_single_scan.py
   ```

2. **Database connection**
   ```bash
   sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db ".tables"
   ```

3. **Sync logs**
   - Check admin_app.log for sync errors
   - Look for database lock messages

**Solutions:**
- Manually run sync script:
  ```bash
  cd cwac_admin_app/database/bi_integration
  python3 sync_single_scan.py /path/to/scan/results/
  ```
- Restart admin application
- Check database permissions

### Schedule Running at Wrong Time

**Problem:** Scans running at unexpected times

**Check:**
1. **Server time**
   ```bash
   date
   ```

2. **Time zone**
   ```bash
   timedatectl  # Linux
   date         # macOS
   ```

3. **Schedule value format**
   - Verify time is in 24-hour format
   - Check day names are lowercase
   - Ensure cron syntax is correct

**Solutions:**
- Correct server time/timezone
- Update schedule value
- Use cron type for complex schedules

## Scheduler Management

### Start Scheduler

The scheduler starts automatically with the admin application:

```bash
cd cwac_admin_app/app
python3 admin_app.py
```

Look for message:
```
Scheduler started successfully
```

### Stop Scheduler

Stop the admin application:

```bash
# Find process
ps aux | grep admin_app.py

# Kill process
kill <PID>

# Or use Ctrl+C if running in foreground
```

### Restart Scheduler

```bash
# Stop
pkill -f admin_app.py

# Start
cd cwac_admin_app/app
python3 admin_app.py &
```

### Check Scheduler Status

Via Admin Interface:
1. Go to **System** → **Status**
2. Check "Scheduler Status" card
3. Shows: Running, Stopped, or Error

Via Command Line:
```bash
ps aux | grep admin_app.py
```

## Advanced Scheduling

### Conditional Schedules

Create schedules that run only during specific periods:

**Business Hours Only (M-F, 9 AM - 5 PM):**
```
Schedule Type: Custom (Cron)
Schedule Value: 0 9-17 * * 1-5
```

**First Monday of Each Month:**
```
Schedule Type: Custom (Cron)
Schedule Value: 0 9 1-7 * 1
```

**Every 15 Minutes:**
```
Schedule Type: Custom (Cron)
Schedule Value: */15 * * * *
```

### Chained Scans

Run multiple configs in sequence:

**Implementation:**
1. Create config files: `scan_1.json`, `scan_2.json`, `scan_3.json`
2. Schedule them with staggered start times:
   - Schedule 1: 02:00 (scan_1.json, ~30 min duration)
   - Schedule 2: 02:35 (scan_2.json, starts after first completes)
   - Schedule 3: 03:10 (scan_3.json, starts after second completes)

### Environment-Based Schedules

Create schedules for different environments:

```
Development:
- Config: dev_quick_test.json
- Type: Hourly (1)
- Time: Every hour

Staging:
- Config: staging_full_scan.json
- Type: Daily
- Time: 08:00 (before business hours)

Production:
- Config: prod_comprehensive.json
- Type: Weekly
- Time: sunday,02:00
```

## Integration with CI/CD

### Via API

Trigger scans programmatically:

```bash
curl -X POST http://localhost:5001/api/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "ci_automated_scan",
    "site_url": "https://staging.example.com"
  }'
```

### Via Script

```bash
#!/bin/bash
# run_accessibility_scan.sh

# Trigger scan via API
response=$(curl -s -X POST http://localhost:5001/api/scans/start \
  -H "Content-Type: application/json" \
  -d '{"config_name": "ci_automated_scan"}')

# Wait for completion
scan_id=$(echo $response | jq -r '.scan_id')

# Check results
curl http://localhost:5001/api/scans/$scan_id
```

## Next Steps

- Set up your first schedule using examples above
- Review [Configuration Guide](configuration.md) for scan settings
- Check [System Status](system-status.md) to monitor scheduler health
- See [API Reference](api-reference.md) for programmatic access

## Reference

- [Configuration Guide](configuration.md)
- [Admin Interface Guide](admin-interface.md)
- [System Status Monitoring](system-status.md)
- [Troubleshooting Guide](troubleshooting.md)
