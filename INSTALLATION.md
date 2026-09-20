# CWAC-ADMIN Installation Guide

Quick start guide for setting up CWAC-ADMIN after cloning the repository.

---

## Prerequisites

Before installing CWAC-ADMIN, ensure you have:

- **Python 3.10+** installed (3.12+ recommended)
- **Git** installed
- **Chrome or Chromium** browser
- **pip** package manager
- **Node.js and npm** (for Chrome for Testing)
- **Virtual environment** (recommended)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/sweddell/CWAC-ADMIN.git
cd CWAC-ADMIN
```

### 2. Create Virtual Environment (Recommended)

```bash
# Check Python version (must be 3.10+, 3.12+ recommended)
python3 --version

# Create virtual environment
# If your python3 is older than 3.10, use: python3.12 -m venv .venv
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

⚠️ **Important:** If `python3 --version` shows Python 3.9 or older, you must install Python 3.10+ first or use a specific version like `python3.12 -m venv .venv`

### 3. Install CWAC-ADMIN Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask web framework
- Database libraries (SQLite built-in)
- Scheduling system (APScheduler)
- Authentication components (Flask-Login)
- Data processing tools (pandas)
- **python-dotenv** for environment variables

### 4. Install CWAC Scanner (GPL v3)

The CWAC scanner is **not included** in the repository due to its GPL v3 license. Install it separately:

```bash
# Run the installation script
./install_cwac.sh
```

This script will:
- Clone the CWAC scanner from the official NZ Government repository
- Verify the GPL v3 license
- Set up the scanner in the `cwac/` directory

### 5. Install CWAC Scanner Dependencies

```bash
cd cwac
pip install -r requirements.txt
cd ..
```

### 6. Install Chrome for Testing

The scanner requires Chrome for Testing. This is installed via npm:

```bash
cd cwac
npm install
cd ..
```

This will download Chrome for Testing and ChromeDriver automatically.

### 7. Copy Configuration Files

Copy scan configuration files to the CWAC scanner directory:

```bash
cp config/*.json cwac/config/
```

### 8. Initialize the Database

The database must be initialized before first run:

```bash
sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db < cwac_admin_app/database/bi_integration/schema.sql
```

This creates all required tables and views for the analytics database.

### 9. Start the Application

```bash
cd cwac_admin_app/app
python3 admin_app.py
```

The application will start on: **http://localhost:5001**

---

## First Login

**Default Credentials:**
- Username: `admin`
- Password: `admin`

⚠️ **IMPORTANT:** Change the password immediately after first login!

---

## Configuration

### Scan Configuration

Edit scan configurations in `config/`:
- `config_default.json` - Default scan settings
- `config_wcag22_aa.json` - WCAG 2.2 AA focused scan
- `config_test.json` - Test configuration

### WCAG Rules

Edit accessibility rules in `admin/`:
- `wcag22_aa_rules.json` - WCAG 2.2 Level AA rules

### Sites to Scan

Add sites via the web interface:
1. Navigate to **Manage Sites** page
2. Click **Add New Site**
3. Enter organization name and URL
4. Save

---

## Verify Installation

### Test the Scanner

```bash
cd cwac
python3 cwac.py --help
```

You should see the CWAC help menu.

### Test the Admin Interface

1. Visit http://localhost:5001
2. Login with admin/admin
3. Navigate to Dashboard
4. Check that all pages load correctly

### Run a Test Scan

1. Go to **Scan** page
2. Select a configuration (e.g., "config_default")
3. Click **Start Scan**
4. Monitor progress
5. View results when complete

---

## Directory Structure After Installation

```
CWAC-ADMIN/
├── cwac/                          # CWAC scanner (installed via script)
│   ├── src/                       # Scanner source code (GPL v3)
│   ├── config/                    # Scanner configurations
│   ├── LICENSE                    # GPL v3 license
│   ├── README.md                  # Scanner documentation
│   └── requirements.txt           # Scanner dependencies
│
├── cwac_admin_app/                # Admin application
│   ├── app/
│   │   ├── admin_app.py           # Main Flask application
│   │   └── scheduler.py           # Automated scheduling
│   ├── database/
│   │   └── bi_integration/
│   │       ├── schema.sql         # Database schema
│   │       └── comprehensive_sync.py
│   └── templates/                 # HTML templates
│
├── config/                        # Scan configurations
├── results/                       # Scan results (created)
├── logs/                          # Application logs (created)
├── admin/                         # Admin data
│
├── tests/                         # Test suite (107 tests)
├── docs/                          # Documentation
│
├── install_cwac.sh               # CWAC installation script
├── requirements.txt              # Admin dependencies
└── README.md                     # Main documentation
```

---

## Testing the Installation

### Run the Test Suite

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest -v

# Expected: 88-107 tests passing
```

See [TESTING.md](TESTING.md) for complete testing guide.

---

## Troubleshooting

### Port 5001 Already in Use

```bash
# Check what's using port 5001
lsof -i :5001

# Kill the process or change port in admin_app.py
# Look for: app.run(host='0.0.0.0', port=5001)
```

### Database Errors

```bash
# Remove and recreate database
rm cwac_admin_app/database/bi_integration/cwac_analytics.db

# Restart application (database will be recreated from schema)
cd cwac_admin_app/app
python3 admin_app.py
```

### CWAC Scanner Not Found

```bash
# Reinstall CWAC scanner
./install_cwac.sh

# Follow prompts to reinstall if already exists
```

### Chrome/ChromeDriver Issues

```bash
# Re-download Chrome for Testing
cd cwac
python3 download_chrome.py

# Verify Chrome path in cwac/config.py
```

### Permission Errors

```bash
# Make scripts executable
chmod +x install_cwac.sh
chmod +x prepare_for_commit.sh

# Fix directory permissions
chmod -R 755 cwac_admin_app
```

---

## Environment Variables (Optional)

Create a `.env` file for custom configuration:

```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_PATH=cwac_admin_app/database/bi_integration/cwac_analytics.db

# Server
HOST=0.0.0.0
PORT=5001
```

---

## Production Deployment

For production deployment:

1. **Change admin password**
2. **Generate new SECRET_KEY**
3. **Enable HTTPS/SSL**
4. **Set up reverse proxy** (nginx/Apache)
5. **Configure firewall** rules
6. **Set up automated backups**
7. **Use production WSGI server** (gunicorn/uWSGI)

See [docs/](docs/) for detailed production deployment guide.

---

## Getting Help

- **Documentation**: [docs/README.md](docs/README.md)
- **Quick Start**: [docs/quickstart.md](docs/quickstart.md)
- **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **FAQ**: [docs/faq.md](docs/faq.md)
- **Testing**: [TESTING.md](TESTING.md)
- **Scoring**: [docs/SCORING.md](docs/SCORING.md)
- **Issues**: Open an issue on GitHub

---

## License

- **CWAC-ADMIN**: BSD 3-Clause License
- **CWAC Scanner**: GPL v3 (installed separately)

See [LICENSE](LICENSE) for details.

---

## Next Steps

After installation:

1. ✅ Change admin password
2. ✅ Add your websites to monitor
3. ✅ Configure scan schedules
4. ✅ Run first accessibility scan
5. ✅ Review dashboard and reports
6. ✅ Set up automated scans

**Ready to make the web more accessible!** 🌐♿
