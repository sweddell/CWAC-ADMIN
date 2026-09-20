# Security Best Practices

Security guidelines for deploying and operating CWAC-ADMIN.

## Authentication Security

### Default Credentials

⚠️ **CRITICAL**: Change default credentials immediately after installation.

**Default Login:**
- Username: `admin`
- Password: `admin`

**To Change:**
1. Log in to admin interface
2. Click username → "Change Password"
3. Enter strong new password
4. Click "Save"

### Password Requirements

**Minimum Requirements:**
- 8+ characters
- Mix of letters and numbers recommended
- Avoid common passwords

**Strong Password Best Practices:**
- 12+ characters
- Mix of uppercase, lowercase, numbers, symbols
- Unique to this application
- Use password manager

### Session Management

**Configuration:**
- Sessions expire after 24 hours of inactivity
- Session secret key must be changed in production

**Set SECRET_KEY:**

Create `.env` file:
```bash
SECRET_KEY=your-long-random-string-here-change-this
```

Generate secure key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**In production:**
- Use environment variables
- Never commit `.env` to Git
- Rotate keys periodically

## Application Security

### HTTPS/SSL

**Always use HTTPS in production.**

**With Nginx:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

**Redirect HTTP to HTTPS:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration

**Allow only necessary ports:**

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5001/tcp   # Block direct Flask access
sudo ufw enable
```

**iptables:**
```bash
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 5001 -j DROP
```

### File Permissions

**Set appropriate permissions:**

```bash
# Application files
chmod 755 cwac_admin_app/app/
chmod 644 cwac_admin_app/app/*.py

# Database directory
chmod 700 cwac_admin_app/database/
chmod 600 cwac_admin_app/database/bi_integration/cwac_analytics.db

# Configuration files
chmod 600 .env
chmod 600 admin/users.json

# Logs
chmod 700 logs/
chmod 600 logs/*.log
```

## Database Security

### SQLite Security

**Protect database file:**
```bash
# Restrict access
chmod 600 cwac_analytics.db

# Only application user should access
chown app-user:app-group cwac_analytics.db
```

**Backups:**
- Store backups in secure location
- Encrypt sensitive backups
- Restrict backup access

**Backup script:**
```bash
#!/bin/bash
DB_PATH="cwac_admin_app/database/bi_integration/cwac_analytics.db"
BACKUP_DIR="/secure/backups/"
DATE=$(date +%Y%m%d_%H%M%S)

# Create encrypted backup
sqlite3 $DB_PATH ".backup /tmp/backup.db"
openssl enc -aes-256-cbc -salt -in /tmp/backup.db -out $BACKUP_DIR/db_$DATE.db.enc
rm /tmp/backup.db
```

### SQL Injection Prevention

**Already implemented:**
- All queries use parameterized statements
- No user input directly in SQL
- SQLite 3 with Python binding

**Example (already in code):**
```python
# ✓ Safe - parameterized query
cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))

# ✗ Unsafe - don't do this
cursor.execute(f"SELECT * FROM sites WHERE id = {site_id}")
```

## User Management Security

### Role-Based Access

**User Roles:**
- **Admin**: Full access (user management, system settings)
- **User**: Standard access (sites, scans, results)

**Principle of Least Privilege:**
- Grant minimum necessary permissions
- Regular users don't need admin rights
- Review user roles periodically

### User Registration

**Options:**
1. **Admin approval required** (recommended)
2. **Auto-approve** (only for trusted environments)

**Configure in admin_app.py:**
```python
AUTO_APPROVE_USERS = False  # Require admin approval
```

### Account Deactivation

**Disable compromised accounts:**
1. Go to User Management
2. Click "Deactivate" on user
3. User cannot log in until reactivated

**For emergencies:**
```bash
# Directly in database
sqlite3 cwac_analytics.db "UPDATE users SET status='deactivated' WHERE username='compromised_user';"
```

## Network Security

### Scanner Security

**Respect rate limits:**
- Use appropriate `crawl_delay` (1-2 seconds minimum)
- Don't overwhelm target sites
- Respect robots.txt for external sites

**User Agent:**
- Use identifiable user agent
- Include contact information
- Don't impersonate other bots

**Configuration:**
```json
{
  "user_agent": "CWAC-ADMIN/1.0 (contact@your-domain.com)",
  "crawl_delay": 2.0,
  "respect_robots_txt": true
}
```

### Proxy Configuration

**Use proxy for external scans:**

```python
# In scanner configuration
PROXIES = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}
```

## Logging and Monitoring

### Secure Logging

**What to log:**
- Authentication attempts
- Failed logins
- Permission denied errors
- Configuration changes
- System errors

**What NOT to log:**
- Passwords
- Session tokens
- Sensitive user data
- Full request bodies with credentials

**Log Rotation:**
```bash
# /etc/logrotate.d/cwac-admin
/path/to/cwac-admin/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0640 app-user app-group
}
```

### Monitoring

**Monitor for:**
- Failed login attempts (potential brute force)
- Unusual API activity
- Database errors
- Disk space issues
- High memory/CPU usage

**Alerting:**
Set up alerts for:
- 5+ failed logins in 10 minutes
- Database connection failures
- Disk space < 10%
- Scanner crashes

## Deployment Security

### Environment Variables

**Never commit secrets:**

`.env` file:
```bash
SECRET_KEY=your-secret-key
DATABASE_PATH=/secure/path/to/db
ADMIN_EMAIL=admin@your-domain.com
```

**Add to `.gitignore`:**
```
.env
.env.*
*.key
*.pem
```

### Docker Security

**Dockerfile best practices:**
```dockerfile
# Use specific version
FROM python:3.9-slim

# Don't run as root
RUN useradd -m -u 1000 cwac
USER cwac

# Copy only necessary files
COPY --chown=cwac:cwac . /app

# Set secure permissions
RUN chmod 700 /app/data
```

### System Updates

**Keep system updated:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Python packages
pip install --upgrade pip
pip list --outdated
pip install --upgrade [package]
```

**Update schedule:**
- Security updates: Weekly
- Package updates: Monthly
- Major version updates: Quarterly (with testing)

## Backup Strategy

### What to Backup

**Critical:**
- Database (`cwac_analytics.db`)
- Configuration files (`config/`)
- User data (`admin/users.json`)
- Environment variables (`.env`)

**Optional:**
- Scan results (`results/`)
- Logs (`logs/`)

### Backup Schedule

**Frequency:**
- **Database**: Daily
- **Configuration**: After changes
- **Full backup**: Weekly

**Retention:**
- Daily: 7 days
- Weekly: 4 weeks
- Monthly: 12 months

**Script:**
```bash
#!/bin/bash
BACKUP_DIR="/secure/backups"
DATE=$(date +%Y%m%d)

# Backup database
cp cwac_analytics.db $BACKUP_DIR/db_$DATE.db

# Backup configs
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# Backup user data
cp admin/users.json $BACKUP_DIR/users_$DATE.json

# Remove old backups (>30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
```

### Backup Security

**Encrypt backups:**
```bash
openssl enc -aes-256-cbc -salt -in backup.db -out backup.db.enc
```

**Store offsite:**
- Use cloud storage (encrypted)
- Different physical location
- Test restore procedures regularly

## Incident Response

### Security Breach

**Immediate actions:**
1. **Isolate system**
   ```bash
   sudo ufw deny all
   ```

2. **Change all passwords**

3. **Review logs**
   ```bash
   grep -i "failed\|error\|unauthorized" logs/admin_app.log
   ```

4. **Check database for unauthorized changes**

5. **Restore from backup if compromised**

### Failed Login Attempts

**Investigate:**
```bash
# Check recent failed logins
grep "Failed login" logs/admin_app.log | tail -20

# Check IP addresses
grep "Failed login" logs/admin_app.log | awk '{print $5}' | sort | uniq -c
```

**Block attacking IP:**
```bash
sudo ufw deny from <IP_ADDRESS>
```

## Compliance

### Data Protection

**GDPR Compliance:**
- Document data processing
- Implement data retention policies
- Provide data export/deletion
- Maintain privacy policy

**Data Retention:**
- Scan results: 90 days default
- User data: Until account deletion
- Logs: 30 days

### Audit Trail

**Track:**
- User actions
- Data access
- Configuration changes
- System modifications

**Already implemented:**
- `activity_log` table
- Timestamps on all records
- User attribution

## Security Checklist

### Initial Setup
- [ ] Change default admin password
- [ ] Generate new SECRET_KEY
- [ ] Set up HTTPS/SSL
- [ ] Configure firewall
- [ ] Set file permissions
- [ ] Create backup strategy

### Production Deployment
- [ ] Use environment variables
- [ ] Enable HTTPS only
- [ ] Restrict database access
- [ ] Set up monitoring
- [ ] Configure log rotation
- [ ] Test backup restore
- [ ] Document procedures

### Regular Maintenance
- [ ] Weekly: Review failed logins
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Annually: Penetration test

## Reporting Vulnerabilities

**Found a security issue?**

Please report responsibly:
1. **Do NOT** open public GitHub issue
2. Email: security@your-domain.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

We will respond within 48 hours.

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [SQLite Security](https://www.sqlite.org/security.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Reference

- [Installation Guide](installation.md)
- [Admin Interface Guide](admin-interface.md)
- [Troubleshooting](troubleshooting.md)
