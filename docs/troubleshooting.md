# Troubleshooting Guide

Common issues and solutions for CWAC-ADMIN.

## Installation Issues

### ChromeDriver Version Mismatch

**Problem**: `SessionNotCreatedException: Chrome version mismatch`

**Solution**:
```bash
# Check Chrome version
google-chrome --version

# Download matching ChromeDriver
# Visit: https://chromedriver.chromium.org/downloads

# Or use automated download script
./download_browser.sh
```

### Module Not Found Errors

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Scanner Fails with `ModuleNotFoundError: No module named 'selenium'`

**Problem**: Scans fail immediately with `ModuleNotFoundError` from `cwac/cwac.py`

**Cause**: The web app spawns the scanner with `.venv/bin/python`, so the CWAC
scanner's dependencies must be installed into the same virtual environment.
Installing only the top-level `requirements.txt` is not enough.

**Solution**:
```bash
source .venv/bin/activate
pip install -r cwac/requirements.txt
```

### Database Initialization Fails

**Problem**: Database schema errors on first run

**Solution**:
```bash
cd cwac_admin_app/database/bi_integration
sqlite3 cwac_analytics.db < schema.sql
```

## Scanner Issues

### Scan Hangs or Times Out

**Problem**: Scanner gets stuck on certain pages

**Solutions**:
1. Increase timeout in configuration:
   ```json
   {
     "timeout": 60
   }
   ```

2. Add problematic URLs to exclude list:
   ```json
   {
     "exclude_patterns": ["*/slow-page/*"]
   }
   ```

3. Check logs:
   ```bash
   tail -f logs/audit.log
   ```

### "Connection Refused" Errors

**Problem**: Scanner cannot reach target site

**Check**:
- Site is accessible from server
- Firewall not blocking requests
- robots.txt not blocking user agent

**Solution**:
```bash
# Test connectivity
curl -I https://www.target-site.com

# Test with scanner user agent
curl -A "CWAC-ADMIN/1.0" https://www.target-site.com
```

### Pages Not Being Crawled

**Problem**: Scanner only finds homepage

**Solutions**:
- Increase `max_depth`:
  ```json
  {"max_depth": 3}
  ```
- Check `include_patterns` aren't too restrictive
- Verify site has working internal links
- Check JavaScript-rendered content

## Admin Interface Issues

### Cannot Log In

**Problem**: Invalid credentials error

**Solutions**:
1. Use default credentials: `admin`/`admin`
2. Reset password:
   ```bash
   rm admin/users.json
   # Restart application to regenerate
   ```

3. Check logs:
   ```bash
   tail -f logs/admin_app.log
   ```

### Dashboard Not Loading

**Problem**: Dashboard shows loading spinner indefinitely

**Solutions**:
1. Check browser console (F12) for errors
2. Verify Flask server is running
3. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)
4. Check database has data:
   ```bash
   sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db "SELECT COUNT(*) FROM scan_results;"
   ```

### Charts Not Displaying

**Problem**: Empty chart areas or JavaScript errors

**Solutions**:
1. Check Chart.js is loading (browser console)
2. Verify data exists in database
3. Clear browser cache
4. Check for JavaScript errors in console

## Scheduler Issues

### Scans Not Running on Schedule

**Problem**: Schedule enabled but scans don't start

**Check**:
1. Scheduler is running:
   ```bash
   ps aux | grep admin_app.py
   ```

2. Check logs:
   ```bash
   tail -f logs/admin_app.log | grep -i schedule
   ```

3. Verify "Next Run" time is correct
4. Check system time/timezone

**Solutions**:
- Restart application
- Verify schedule configuration
- Check for errors in logs

### Schedule Runs at Wrong Time

**Problem**: Scans execute at unexpected times

**Solutions**:
1. Check server timezone:
   ```bash
   date
   timedatectl  # Linux
   ```

2. Verify schedule value format:
   - Daily: "HH:MM" (24-hour format)
   - Weekly: "day,HH:MM" (lowercase day names)

3. Update schedule configuration

## Database Issues

### Database Locked

**Problem**: `database is locked` error

**Solutions**:
1. Stop all running instances:
   ```bash
   pkill -f admin_app.py
   ```

2. Remove lock file:
   ```bash
   rm -f cwac_admin_app/database/bi_integration/.cwac_analytics.db-lock
   ```

3. Restart application

### Results Not Syncing

**Problem**: Scan completes but no results in dashboard

**Solutions**:
1. Check sync logs:
   ```bash
   grep -i sync logs/admin_app.log
   ```

2. Manually sync:
   ```bash
   cd cwac_admin_app/database/bi_integration
   python3 sync_single_scan.py /path/to/scan/directory
   ```

3. Verify database permissions:
   ```bash
   ls -la cwac_admin_app/database/bi_integration/cwac_analytics.db
   ```

### Corrupted Database

**Problem**: Database errors or inconsistent data

**Solutions**:
1. Check integrity:
   ```bash
   sqlite3 cwac_analytics.db "PRAGMA integrity_check;"
   ```

2. Backup and rebuild:
   ```bash
   # Backup current database
   cp cwac_analytics.db cwac_analytics.db.backup
   
   # Rebuild from schema
   rm cwac_analytics.db
   sqlite3 cwac_analytics.db < schema.sql
   ```

3. Re-sync scan results if needed

## Performance Issues

### Slow Dashboard Loading

**Problem**: Dashboard takes long time to load

**Solutions**:
1. Optimize database:
   ```bash
   sqlite3 cwac_analytics.db "VACUUM; ANALYZE;"
   ```

2. Archive old results:
   ```bash
   # Backup and delete scans older than 90 days
   sqlite3 cwac_analytics.db "DELETE FROM scan_results WHERE scan_date < date('now', '-90 days');"
   ```

3. Add database indexes (already in schema)

### High Memory Usage During Scans

**Problem**: Scanner consumes excessive RAM

**Solutions**:
1. Reduce `max_pages` in configuration
2. Close unnecessary browser tabs
3. Increase system swap space
4. Run scans during off-peak hours

### Disk Space Running Low

**Problem**: Results directory growing too large

**Solutions**:
1. Archive old scan results:
   ```bash
   # Move to archive
   mkdir -p archive/$(date +%Y)
   mv results/old_scan_* archive/$(date +%Y)/
   ```

2. Clean up result files:
   ```bash
   # Remove scans older than 90 days
   find results -type d -mtime +90 -exec rm -rf {} +
   ```

3. Configure automated cleanup

## Common Error Messages

### "Port 5001 already in use"

**Problem**: Cannot start admin application

**Solution**:
```bash
# Find and kill process using port 5001
lsof -ti:5001 | xargs kill -9

# Or change port in admin_app.py
```

### "No module named 'psutil'"

**Problem**: Missing optional dependency

**Solution**:
```bash
pip install psutil
```

### "Failed to fetch robots.txt"

**Problem**: Warning messages in logs

**Solution**: This is normal for sites without robots.txt. Ignore or reduce log level in `crawler.py`.

### "AttributeError: module 'hashlib' has no attribute 'scrypt'"

**Problem**: Python version compatibility issue

**Solution**: Already fixed - using `pbkdf2:sha256` instead. If still occurs, update `admin_app.py`.

## Browser/Chrome Issues

### Chrome Fails to Start: `DevToolsActivePort file doesn't exist`

**Problem**: `SessionNotCreatedException: Chrome failed to start: exited normally.
(DevToolsActivePort file doesn't exist)`

**Cause**: Chrome cannot create its sandbox — typically because the service is
running as root (Chrome refuses to run sandboxed as root) or the kernel
restricts unprivileged user namespaces.

**Solution**: The systemd service runs as a dedicated unprivileged user
(`cwacadmin`) so Chrome's sandbox works normally. Verify the service is not
running as root: `systemctl show cwac-admin -p User`.

Extra flags can be passed via `CHROME_EXTRA_ARGS` in `.env` (comma-separated):

```bash
CHROME_EXTRA_ARGS=--disable-dev-shm-usage,--disable-gpu
```

⚠️ Only as a last resort (e.g. a kernel that forbids user namespaces), add
`--no-sandbox` — it disables Chrome's process sandbox against every site you
scan. Never combine `--no-sandbox` with running the service as root.

Then restart the service: `systemctl restart cwac-admin`

### Chrome Crashes During Scans

**Problem**: `chrome not reachable` errors

**Solutions**:
1. Increase system resources
2. Enable headless mode in config
3. Update Chrome and ChromeDriver
4. Check system logs for crashes

### Screenshots Not Capturing

**Problem**: No screenshots in results

**Solutions**:
1. Verify `screenshot_audits.enabled: true`
2. Check disk space
3. Review scanner logs for errors
4. Ensure Chrome has display permissions

## Network Issues

### SSL Certificate Errors

**Problem**: Scanner fails on HTTPS sites

**Solutions**:
1. Add to configuration:
   ```json
   {
     "verify_ssl": false
   }
   ```
   ⚠️ Only for development/testing!

2. Install proper SSL certificates on target site

### Timeout on Large Sites

**Problem**: Scanner times out on slow sites

**Solutions**:
1. Increase timeout values
2. Reduce `max_pages`
3. Increase `crawl_delay`
4. Check network bandwidth

## Debug Mode

Enable debug logging for troubleshooting:

**In admin_app.py:**
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

**In configuration:**
```json
{
  "debug": true,
  "verbose": true
}
```

**View logs:**
```bash
# Application logs
tail -f logs/admin_app.log

# Scanner logs
tail -f logs/audit.log

# Scheduler logs
grep -i schedule logs/admin_app.log
```

## Getting Help

If issues persist:

1. **Check Logs**: Most issues are explained in log files
2. **Search Issues**: Check GitHub issues for similar problems
3. **Ask for Help**: Open a new GitHub issue with:
   - CWAC-ADMIN version
   - Operating system
   - Python version
   - Chrome/ChromeDriver versions
   - Error messages (from logs)
   - Steps to reproduce

## Preventive Maintenance

### Daily
- Monitor scan completion rates
- Check disk space
- Review error logs

### Weekly
- Vacuum database
- Archive old results
- Review scheduler performance

### Monthly
- Update dependencies
- Update Chrome/ChromeDriver
- Review and optimize configurations

### Quarterly
- Full system audit
- Database backup
- Update documentation

## Reference

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Admin Interface Guide](admin-interface.md)
- [API Reference](api-reference.md)
