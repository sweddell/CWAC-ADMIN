# Installation Guide

This guide will walk you through installing and setting up CWAC-ADMIN on your system.

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ (recommended)
- **macOS**: 10.15+ (Catalina or later)
- **Windows**: Windows 10/11 (via WSL2 recommended)

### Software Requirements
- **Python**: 3.10 or higher (3.12+ recommended)
- **Node.js and npm**: For Chrome for Testing installation
- **Git**: For cloning the repository

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB for application + 10-50GB for scan results
- **Network**: Internet connection for scanning external sites

## Installation Steps

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git nodejs npm sqlite3
```

#### macOS (using Homebrew)
```bash
brew install python@3.12 git node sqlite3
```

#### Windows (WSL2)
```bash
# First install WSL2 with Ubuntu
wsl --install

# Then run the Ubuntu commands above
```

### 2. Clone the Repository

```bash
git clone https://github.com/sweddell/CWAC-ADMIN.git
cd CWAC-ADMIN
```

### 3. Create Virtual Environment

**Important:** Verify Python 3.10+ before creating venv:

```bash
# Check Python version (must be 3.10+)
python3 --version

# If version is too old, use a specific version
# python3.12 -m venv .venv  # Use this if python3 is < 3.10

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

If you see `Python 3.9.x` or older, install a newer version:
- **macOS**: `brew install python@3.12`
- **Ubuntu**: `sudo apt install python3.12 python3.12-venv`

### 4. Install CWAC Scanner

The CWAC scanner is GPL v3 licensed and must be installed separately:

```bash
./install_cwac.sh
```

This script will clone the scanner from the official NZ Government repository.

### 5. Install Python Dependencies

```bash
# Upgrade pip (optional)
pip install --upgrade pip

# Install admin interface dependencies
pip install -r requirements.txt

# Install CWAC scanner dependencies
pip install -r cwac/requirements.txt
```

### 6. Install Chrome for Testing

Chrome for Testing and ChromeDriver are installed automatically via npm:

```bash
cd cwac
npm install
cd ..
```

This will download the correct versions of Chrome and ChromeDriver for the scanner.

### 7. Copy Configuration Files

Copy scan configuration files to the CWAC scanner directory:

```bash
cp config/*.json cwac/config/
```

### 8. Initialize Database

The database must be initialized before first run:

```bash
sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db < cwac_admin_app/database/bi_integration/schema.sql
```

### 9. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development

# Scanner Configuration
CWAC_USER_AGENT=CWAC-ADMIN-Scanner/1.0

# Database Path (auto-configured if not set)
# DATABASE_PATH=cwac_admin_app/database/bi_integration/cwac_analytics.db
EOF
```

**Important**: Change the `SECRET_KEY` to a random string in production!

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 10. Test the Installation

#### Test Scanner
```bash
# Run the scanner help command
python3 cwac/cwac.py --help
```

Expected output:
```
Usage: cwac.py <config_file>
```

#### Test Admin Application
```bash
cd cwac_admin_app/app
python3 admin_app.py
```

Expected output:
```
* Running on http://127.0.0.1:5001
```

Open your browser to: http://localhost:5001

**Default Login Credentials**:
- Username: `admin`
- Password: `admin`

**⚠️ Important**: Change the admin password immediately after first login!

## Post-Installation Setup

### 1. Change Admin Password

1. Log in to the admin interface (http://localhost:5001)
2. Click your username in the top right
3. Select "Change Password"
4. Enter a strong new password

### 2. Add Your First Site

1. Click "Sites" in the navigation
2. Click "+ Add Site"
3. Enter:
   - **Organization**: Your organization name
   - **URL**: The website to scan (e.g., https://example.com)
   - **Sector**: Government, Education, Commercial, etc.
4. Click "Add Site"

### 3. Create a Scan Configuration

1. Click "Scan" in the navigation
2. Click "Configurations" tab
3. Create a new config file or use an existing one
4. Set your preferences:
   - WCAG version and level
   - Max pages to scan
   - Crawler settings
   - Custom audits to run

### 4. Run Your First Scan

1. Go to the "Scan" page
2. Select your configuration
3. Click "Start Scan"
4. Monitor progress in the UI

## Configuration Files

### Scanner Configuration

Create a scan configuration in `config/my_scan.json`:

```json
{
  "base_urls": [
    "https://example.com"
  ],
  "user_agent": "CWAC-ADMIN/1.0",
  "max_pages": 20,
  "crawl_delay": 1.0,
  "respect_robots_txt": true,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  }
}
```

### Base URLs File

Create a list of sites in `base_urls/my_sites.txt`:

```
https://example.com
https://another-site.org
```

## Troubleshooting Installation

### ChromeDriver Not Found

```bash
# Download ChromeDriver manually
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
VERSION=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### Module Not Found Errors

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, create it:

```txt
flask>=3.0.0
flask-cors>=4.0.0
flask-login>=0.6.3
werkzeug>=3.0.0
selenium>=4.15.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
python-dotenv>=1.0.0
apscheduler>=3.10.0
```

### Permission Denied on ChromeDriver

```bash
chmod +x /path/to/chromedriver
```

### Database Locked Error

```bash
# Stop all running instances
pkill -f admin_app.py

# Remove lock file if exists
rm -f cwac_admin_app/database/bi_integration/.cwac_analytics.db-lock
```

### Port 5001 Already in Use

Change the port in `admin_app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)  # Changed to 5002
```

Or kill the process using the port:

```bash
# Find the process
lsof -i :5001

# Kill it
kill -9 <PID>
```

## Verification Checklist

After installation, verify:

- [ ] Python 3.9+ installed: `python3 --version`
- [ ] Chrome/Chromium installed: `google-chrome --version`
- [ ] ChromeDriver installed: `chromedriver --version`
- [ ] Virtual environment created and activated
- [ ] All Python packages installed: `pip list`
- [ ] Scanner runs: `python3 cwac/cwac.py --help`
- [ ] Admin app starts: `python3 cwac_admin_app/app/admin_app.py`
- [ ] Can log in to admin interface (http://localhost:5001)
- [ ] Can create a site
- [ ] Can run a scan

## Next Steps

- Read the [Quick Start Guide](quickstart.md) to run your first scan
- Review [Configuration Guide](configuration.md) for advanced options
- Set up [Automated Scheduling](scheduling.md) for regular scans
- Explore the [Admin Interface Guide](admin-interface.md)

## Updating CWAC-ADMIN

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart admin application
pkill -f admin_app.py
python3 cwac_admin_app/app/admin_app.py &
```

## Uninstallation

To completely remove CWAC-ADMIN:

```bash
# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf CWAC-ADMIN

# Remove system packages (optional)
# sudo apt remove chromium-browser chromium-chromedriver  # Ubuntu
# brew uninstall google-chrome chromedriver  # macOS
```

## Getting Help

- Check [Troubleshooting Guide](troubleshooting.md)
- Review [FAQ](faq.md)
- Open an issue on GitHub
- Contact support

## Production Deployment

For production deployment, see:
- [Production Deployment Guide](production-deployment.md)
- [Security Best Practices](security.md)
- [Performance Tuning](performance-tuning.md)
