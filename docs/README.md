# CWAC-ADMIN Documentation

Welcome to the CWAC-ADMIN (Comprehensive Web Accessibility Checker - Admin Platform) documentation.

## Documentation Index

### Getting Started
- [Installation Guide](installation.md) - Setup and installation instructions
- [Quick Start Guide](quickstart.md) - Get up and running in 10 minutes
- [FAQ](faq.md) - Frequently asked questions

### User Guides
- [Admin Interface Guide](admin-interface.md) - Complete web dashboard guide
- [Scoring System](SCORING.md) - How accessibility scores are calculated
- [Configuration Guide](configuration.md) - Scan configuration reference
- [Scheduling Guide](scheduling.md) - Automated scan scheduling

### Technical Documentation
- [Architecture Overview](architecture.md) - System architecture and components
- [Database Schema](database-schema.md) - Analytics database structure
- [API Reference](api-reference.md) - REST API endpoints
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

### For Contributors
- [Contributing Guide](contributing.md) - How to contribute
- [Security Best Practices](security.md) - Security guidelines

## What is CWAC-ADMIN?

CWAC-ADMIN is a comprehensive web accessibility testing and monitoring platform that helps organizations ensure their websites meet WCAG (Web Content Accessibility Guidelines) standards.

It is powered by [CWAC](https://github.com/GOVTNZ/cwac) — the [Centralised Web Accessibility Checker](https://www.digital.govt.nz/standards-and-guidance/nz-government-web-standards/centralised-web-accessibility-checker-cwac) developed by Te Tari Taiwhenua | New Zealand Department of Internal Affairs (GPL v3, installed separately). Development of this codebase was assisted by [Perplexity](https://www.perplexity.ai) and [Devin](https://devin.ai).

### Key Features

- **Automated Scanning**: Schedule automatic accessibility scans of your websites
- **WCAG Compliance**: Test against WCAG 2.0, 2.1, and 2.2 standards (A, AA, AAA levels)
- **Custom Audits**: Specialized tests for focus indicators, language attributes, and responsive design
- **SEO Integration**: Combined accessibility and SEO analysis
- **Admin Dashboard**: Web-based interface for managing sites and viewing results
- **Historical Tracking**: Monitor accessibility improvements over time
- **Multi-Site Management**: Manage and compare multiple websites

### System Components

1. **CWAC Scanner** (`cwac/`) - Python-based accessibility scanner using axe-core and Selenium
2. **Admin Interface** (`cwac_admin_app/`) - Flask web application for management and reporting
3. **Analytics Database** - SQLite database for storing scan results and trends
4. **Scheduler** - Automated scan scheduling service

## Quick Links

- [GitHub Repository](https://github.com/yourusername/CWAC-ADMIN)
- [Issue Tracker](https://github.com/yourusername/CWAC-ADMIN/issues)
- [License](../LICENSE)

## Getting Help

- Check the [FAQ](faq.md) for common questions
- Review [Troubleshooting](troubleshooting.md) for solutions to common issues
- Open an issue on GitHub for bug reports or feature requests

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](../LICENSE) file for details.
