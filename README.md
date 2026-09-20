# CWAC-ADMIN

**Comprehensive Web Accessibility Checker - Admin Platform**

A professional web accessibility compliance management platform for auditing and monitoring websites against WCAG standards.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-BSD--3--Clause-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![WCAG](https://img.shields.io/badge/WCAG-2.0%20%7C%202.1%20%7C%202.2-blue)

> **Powered by [CWAC](https://github.com/GOVTNZ/cwac)** — the [Centralised Web Accessibility Checker](https://www.digital.govt.nz/standards-and-guidance/nz-government-web-standards/centralised-web-accessibility-checker-cwac) developed by Te Tari Taiwhenua | New Zealand Department of Internal Affairs.
> CWAC-ADMIN provides the management interface, database, scheduling, and reporting layer around the CWAC scanning engine. The scanner itself is installed separately via `install_cwac.sh` and remains under its own GPL v3 license (see [License](#-license)).

---

## 📚 Documentation

**Complete documentation is available in the [`docs/`](docs/) directory:**

- **[Installation Guide](docs/installation.md)** - Setup instructions for all platforms
- **[Quick Start](docs/quickstart.md)** - Get started in 10 minutes
- **[Architecture Overview](docs/architecture.md)** - System design and components
- **[Admin Interface Guide](docs/admin-interface.md)** - Complete UI reference
- **[Database Schema](docs/database-schema.md)** - Database structure and queries
- **[Testing Guide](TESTING.md)** - Test suite documentation with 107 tests

---

## ✨ Key Features

### 🎯 Comprehensive Accessibility Testing
- **WCAG 2.0, 2.1, 2.2** compliance testing
- **Levels A, AA, AAA** support
- **axe-core** powered accessibility engine
- **Custom audits** for focus indicators, language, and responsive design

### 📊 Professional Dashboard
- Real-time accessibility metrics
- Score trends and historical tracking
- Site comparison and leaderboard
- Issues breakdown by severity

### 🌐 Multi-Site Management
- Monitor unlimited websites
- Organize by groups and sectors
- Detailed per-page analysis
- Export results to CSV/JSON

### 📅 Automated Scheduling
- Schedule scans (hourly, daily, weekly, monthly, cron)
- Background task processing
- Automatic result synchronization
- Activity logging and monitoring

### 👥 User Management
- Multi-user authentication
- Role-based access control
- User registration and approval workflow
- Password management

### 🔌 Extensible Architecture
- Custom audit plugins
- REST API endpoints
- SQLite database with comprehensive schema
- Clean separation of concerns

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10 or higher (3.12+ recommended)
- **Chrome/Chromium** browser
- **ChromeDriver** (matching Chrome version)
- **Git** (for cloning)

### Installation

```bash
# Clone the repository
git clone https://github.com/sweddell/CWAC-ADMIN.git
cd CWAC-ADMIN

# Check Python version (must be 3.10+, 3.12+ recommended)
python3 --version

# Create virtual environment with Python 3.10+
# If your python3 is older, use: python3.12 -m venv .venv
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install CWAC Scanner (GPL v3 licensed)
./install_cwac.sh

# Install admin interface dependencies
pip install -r requirements.txt

# Install CWAC scanner dependencies
pip install -r cwac/requirements.txt

# Install Chrome for Testing (in cwac directory)
cd cwac
npm install
cd ..

# Copy configuration files to scanner directory
cp config/*.json cwac/config/

# Initialize the database
sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db < cwac_admin_app/database/bi_integration/schema.sql

# Start the admin interface
cd cwac_admin_app/app
python3 admin_app.py
```

**Visit:** http://localhost:5001

**Default Login:**
- Username: `admin`
- Password: `admin` (⚠️ change immediately!)

**Next Steps:** Follow the [Quick Start Guide](docs/quickstart.md) for your first scan.

---

## 📁 Project Structure

```
CWAC-ADMIN/
├── docs/                          # 📚 Complete documentation
│   ├── README.md                  # Documentation index
│   ├── installation.md            # Setup guide
│   ├── quickstart.md              # Getting started
│   ├── architecture.md            # System design
│   ├── admin-interface.md         # UI guide
│   └── database-schema.md         # Database reference
│
├── cwac_admin_app/               # 🎯 Admin application
│   ├── app/
│   │   ├── admin_app.py           # Flask application
│   │   └── scheduler.py           # Automated scanning
│   ├── templates/                 # Jinja2 templates
│   ├── database/
│   │   └── bi_integration/        # Database & sync
│   │       ├── schema.sql         # Database schema
│   │       ├── sync_single_scan.py
│   │       └── comprehensive_sync.py
│   └── plugins/                   # Custom audit plugins
│
├── cwac/                          # 🔍 CWAC scanner (cloned from
│   │                              #    github.com/GOVTNZ/cwac by
│   │                              #    install_cwac.sh — not tracked here)
│   ├── src/                       # Core scanner code
│   └── cwac.py                    # Scanner CLI entry point
│
├── cwac_admin/                     # 🎨 Static assets
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript
│   └── img/                       # Images
│
├── config/                        # ⚙️ Scan configurations
├── results/                       # 📂 Scan outputs
├── logs/                          # 📝 Application logs
├── admin/                         # 👤 User data
│
├── LICENSE                        # BSD 3-Clause License
└── README.md                      # This file
```

---

## 🛠️ Technology Stack

### Backend
- **Flask 3.0+** - Web framework
- **SQLite3** - Database
- **APScheduler** - Task scheduling
- **Flask-Login** - Authentication
- **Werkzeug** - Password hashing

### Frontend
- **Bootstrap 5.3** - UI framework
- **Chart.js** - Data visualization
- **jQuery** - DOM manipulation
- **Jinja2** - Template engine

### Scanner
- **Selenium WebDriver** - Browser automation
- **axe-core** - Accessibility testing
- **BeautifulSoup4** - HTML parsing
- **Chrome/Chromium** - Headless browser

---

## 📊 How It Works

```
┌──────────────┐
│    User      │
│  Dashboard   │
└──────┬───────┘
       │ 1. Configure scan
       ▼
┌──────────────┐
│   Flask      │
│   Admin      │◄──────────┐
└──────┬───────┘           │
       │ 2. Start scan     │
       ▼                   │ 5. Display
┌──────────────┐           │    results
│    CWAC      │           │
│   Scanner    │           │
└──────┬───────┘           │
       │ 3. Test pages     │
       ▼                   │
┌──────────────┐           │
│  CSV Results │           │
└──────┬───────┘           │
       │ 4. Sync to DB     │
       ▼                   │
┌──────────────┐           │
│   SQLite     │───────────┘
│   Database   │
└──────────────┘
```

1. **Configure** - Set up site and scan parameters
2. **Scan** - CWAC scanner tests pages for accessibility
3. **Parse** - Results are parsed from CSV files
4. **Sync** - Data is synchronized to SQLite database
5. **Report** - Admin dashboard displays comprehensive reports

---

## 📐 Accessibility Scoring System

### Score Calculation

CWAC-ADMIN uses a weighted penalty system to calculate accessibility scores:

```
Page Score Formula:
─────────────────
penalty = (critical × 10) + (serious × 5) + (moderate × 2) + (minor × 1)
page_score = max(0, 100 - min(100, penalty))

Site Score:
───────────
site_score = average of all page scores
```

**Example Calculation:**
```
Page with 2 critical, 3 serious, 5 moderate, 8 minor issues:
penalty = (2 × 10) + (3 × 5) + (5 × 2) + (8 × 1)
        = 20 + 15 + 10 + 8
        = 53
page_score = 100 - 53 = 47

Site with 3 pages scoring 85, 92, 78:
site_score = (85 + 92 + 78) / 3 = 85.0
```

### Issue Severity Weights

| Severity | Weight | Impact on Score | Example Issues |
|----------|--------|-----------------|----------------|
| **Critical** | 10 points | Major WCAG violations | Missing alt text, keyboard traps, poor color contrast |
| **Serious** | 5 points | Significant barriers | Missing form labels, inadequate focus indicators |
| **Moderate** | 2 points | Obstacles for some users | Missing page titles, unclear link text |
| **Minor** | 1 point | Best practice violations | Missing language attributes, redundant links |

### WCAG Compliance Levels

Compliance levels are automatically determined based on issue severity:

| WCAG Level | Requirements | Score Range |
|------------|--------------|-------------|
| **WCAG 2.2 AAA** | No critical, serious, or moderate issues | Typically 95+ |
| **WCAG 2.2 AA** | No critical or serious issues | Typically 90-94 |
| **WCAG 2.2 A** | No critical issues | Typically 80-89 |
| **Non-compliant** | Has critical issues | Below 80 |

**Note:** WCAG levels are cumulative. A site meeting WCAG 2.2 AA also meets:
- WCAG 2.2 A
- WCAG 2.1 AA and A
- WCAG 2.0 AA and A

### Score Interpretation

| Score Range | Status | Recommendation |
|-------------|--------|----------------|
| **95-100** | Excellent | Maintain current accessibility standards |
| **90-94** | Good | Review moderate issues, aim for AAA |
| **80-89** | Fair | Address serious issues immediately |
| **70-79** | Poor | Significant accessibility barriers exist |
| **Below 70** | Critical | Urgent remediation required |

### Why This Scoring System?

1. **Severity-Weighted**: Critical issues have 10× the impact of minor issues
2. **Intuitive Scale**: 0-100 scale is universally understood
3. **WCAG-Aligned**: Directly correlates to WCAG conformance levels
4. **Actionable**: Clear prioritization based on issue severity
5. **Fair Averaging**: Site score reflects overall accessibility across all pages

---

## 🎯 Use Cases

### For Organizations
- **Monitor** multiple websites for WCAG compliance
- **Track** accessibility improvements over time
- **Identify** critical issues requiring immediate attention
- **Schedule** regular automated audits
- **Generate** reports for stakeholders

### For Developers
- **Test** websites during development
- **Validate** WCAG compliance before deployment
- **Debug** specific accessibility issues
- **Integrate** with CI/CD pipelines (via API)
- **Extend** with custom audit plugins

### For Accessibility Teams
- **Audit** entire site portfolios
- **Compare** accessibility across sites
- **Prioritize** issues by severity
- **Document** compliance efforts
- **Collaborate** with multi-user access

---

## 🔌 API Endpoints

CWAC-ADMIN provides REST API endpoints for programmatic access:

```
GET  /api/sites                    # List all sites
POST /api/sites                    # Add new site
GET  /api/sites/{id}               # Get site details
GET  /api/sites/{id}/scans         # Get scan history

GET  /api/scans/{scan_id}          # Get scan results
POST /api/scans/start              # Start manual scan

GET  /api/schedules                # List schedules
POST /api/schedules                # Create schedule
PUT  /api/schedules/{id}           # Update schedule
DELETE /api/schedules/{id}         # Delete schedule

GET  /api/dashboard/metrics        # Dashboard data
GET  /api/system/status            # System health
```

**Authentication:** All API endpoints require authentication via session cookies or API tokens.

---

## 🔒 Security

### Default Credentials
⚠️ **Change immediately after first login:**
- Username: `admin`
- Password: `admin`

### Production Checklist
- [ ] Change admin password
- [ ] Generate new `SECRET_KEY` in `.env`
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up regular database backups
- [ ] Review user permissions
- [ ] Monitor application logs

**Note:** Always use HTTPS in production and regularly update passwords.

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for details on:
- Code style guidelines
- Testing requirements  
- Pull request process
- Development workflow

### Development Setup

```bash
# Clone and install
git clone https://github.com/yourusername/CWAC-ADMIN.git
cd CWAC-ADMIN
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt

# Run tests (107 tests)
pytest -v

# Start development server
cd cwac_admin_app/app
python3 admin_app.py
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

### CWAC-ADMIN
**BSD 3-Clause License**

Copyright (c) 2025, Shane Weddell. All rights reserved.

The CWAC-ADMIN admin interface, database layer, and custom plugins are licensed under the BSD 3-Clause License.
See [LICENSE](LICENSE) for the full license text.

### CWAC Scanner (GPL v3)

The scanning engine is **[CWAC](https://github.com/GOVTNZ/cwac) — the [Centralised Web Accessibility Checker](https://www.digital.govt.nz/standards-and-guidance/nz-government-web-standards/centralised-web-accessibility-checker-cwac)** — developed by Te Tari Taiwhenua | New Zealand Department of Internal Affairs and licensed under **GPL v3**.

CWAC is **not** distributed as part of this repository. The `cwac/` directory is populated by cloning the upstream GOVTNZ repository via `install_cwac.sh` at install time, and CWAC-ADMIN invokes it as a **separate subprocess** (`python cwac/cwac.py <config>`), exchanging data only through its CLI and CSV output files. This preserves a clear GPL/BSD boundary: modifications to CWAC itself belong upstream and remain GPL v3; the admin platform remains BSD 3-Clause.

### Other Third-Party Components

**Backend:**
- Flask (BSD 3-Clause)
- Flask-Login (MIT)
- APScheduler (MIT)
- BeautifulSoup4 (MIT)

**Frontend:**
- Bootstrap 5 (MIT)
- Chart.js (MIT)
- jQuery (MIT)

**Scanner dependencies:**
- Selenium (Apache 2.0)
- axe-core (MPL 2.0)
- Chrome/Chromium (BSD)

---

## 🗺️ Roadmap

### Planned Features
- [ ] PDF/Excel report export
- [ ] Email notifications for scan completion
- [ ] API authentication with tokens
- [ ] Real-time scan progress updates (WebSockets)
- [ ] Integration with CI/CD pipelines
- [ ] Multi-tenancy support
- [ ] Custom branding options
- [ ] Advanced filtering and search
- [ ] Bulk site import from CSV
- [ ] Accessibility statement generator

### Future Enhancements
- [ ] PostgreSQL support for large deployments
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] Distributed scanning (multiple workers)
- [ ] Plugin marketplace
- [ ] Mobile app for monitoring

---

## 📞 Support

### Documentation
Complete documentation is available in the [`docs/`](docs/) directory.

### Getting Help
- **Quick Start:** [docs/quickstart.md](docs/quickstart.md)
- **Troubleshooting:** [docs/troubleshooting.md](docs/troubleshooting.md)
- **FAQ:** [docs/faq.md](docs/faq.md)
- **Testing:** [TESTING.md](TESTING.md) - Run the test suite
- **Issues:** Open an issue on GitHub

### Community
- Report bugs via GitHub Issues
- Request features via GitHub Issues
- Contribute via Pull Requests

---

## 🙏 Acknowledgments

### Scanner Engine
- **[CWAC](https://github.com/GOVTNZ/cwac)** — the [Centralised Web Accessibility Checker](https://www.digital.govt.nz/standards-and-guidance/nz-government-web-standards/centralised-web-accessibility-checker-cwac), developed and maintained by **Te Tari Taiwhenua | New Zealand Department of Internal Affairs**. CWAC-ADMIN builds on their work to make web accessibility auditing easier to manage and report on.

### Core Technologies
- **Flask** - Pallets (Web framework)
- **axe-core** - Deque Systems (Accessibility testing)
- **Bootstrap** - Twitter, Inc. (UI framework)
- **Chart.js** - Chart.js Contributors (Data visualization)
- **Selenium** - Selenium Project (Browser automation)

### Standards
- **WCAG** - W3C Web Accessibility Initiative
- **ARIA** - W3C Accessible Rich Internet Applications

### Development
Development of this codebase was assisted by AI tools, including **[Perplexity](https://www.perplexity.ai)** and **[Devin](https://devin.ai)** (Cognition).

### Special Thanks
- Te Tari Taiwhenua | NZ Department of Internal Affairs for CWAC
- The W3C for accessibility standards
- Deque Systems for axe-core
- All open-source contributors

---

## 📊 Platform Stats

- **107 automated tests** with 98.9% pass rate
- **15+ database tables** for comprehensive tracking
- **50+ API endpoints** for programmatic access
- **WCAG 2.0, 2.1, 2.2** support (Levels A, AA, AAA)
- **100+ accessibility rules** checked via axe-core
- **Unlimited sites** monitored simultaneously  
- **Automated scheduling** (hourly, daily, weekly, monthly, cron)
- **Multi-user support** with role-based access
- **SEO integration** for combined accessibility/SEO audits
- **Comprehensive documentation** with test coverage

---

**Built with ❤️ for better web accessibility**

*Making the web accessible, one site at a time.*
