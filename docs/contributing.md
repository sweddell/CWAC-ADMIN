# Contributing Guide

Thank you for considering contributing to CWAC-ADMIN!

## Ways to Contribute

- **Report bugs** via GitHub Issues
- **Suggest features** or enhancements
- **Improve documentation**
- **Fix bugs** in the code
- **Add new features**
- **Create custom audit plugins**
- **Improve tests**

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/CWAC-ADMIN.git
cd CWAC-ADMIN
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest black flake8 mypy
```

### 3. Create a Branch

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/issue-123
```

## Development Guidelines

### Code Style

**Python Code:**
- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

**Format with Black:**
```bash
black cwac_admin_app/
```

**Lint with flake8:**
```bash
flake8 cwac_admin_app/ --max-line-length=100
```

### Documentation

- Update documentation for new features
- Add docstrings to functions and classes
- Include inline comments for complex logic
- Update README.md if needed

### Testing

**Run tests:**
```bash
pytest
```

**Add tests for:**
- New features
- Bug fixes
- Edge cases

### Commit Messages

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks

**Examples:**
```
feat: Add PDF export for scan results

Implement PDF generation using ReportLab library.
Results can now be exported as PDF from the dashboard.

Closes #123
```

```
fix: Resolve database lock error on concurrent scans

Add connection pooling to prevent database locks when
multiple scans complete simultaneously.

Fixes #456
```

## Pull Request Process

### 1. Update Your Fork

```bash
# Add upstream remote
git remote add upstream https://github.com/original-owner/CWAC-ADMIN.git

# Fetch and merge latest changes
git fetch upstream
git checkout main
git merge upstream/main
```

### 2. Make Your Changes

- Write clear, concise code
- Add tests for new functionality
- Update documentation
- Ensure all tests pass

### 3. Push to Your Fork

```bash
git push origin feature/my-new-feature
```

### 4. Open Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Fill in the PR template:
   - **Title**: Clear, descriptive title
   - **Description**: What does this PR do?
   - **Issue**: Reference related issue (if any)
   - **Testing**: How was this tested?
   - **Screenshots**: For UI changes
4. Submit the pull request

### 5. Code Review

- Maintainers will review your PR
- Address feedback and make changes as needed
- Push updates to the same branch
- Once approved, PR will be merged

## Project Structure

```
CWAC-ADMIN/
├── cwac_admin_app/      # Main application
│   ├── app/              # Flask application
│   ├── templates/        # Jinja2 templates
│   ├── database/         # Database & sync
│   └── plugins/          # Custom audits
├── cwac/                 # Scanner engine
├── cwac_admin/            # Static assets
├── docs/                 # Documentation
├── config/               # Scan configs
└── tests/                # Test suite
```

## Feature Development

### Adding a New Audit Plugin

1. Create plugin file in `cwac_admin_app/plugins/`:
```python
# my_audit.py
from cwac.src.audits.base import BaseAudit

class MyAudit(BaseAudit):
    def run(self, driver, page_url):
        # Your audit logic
        return {
            "passed": True,
            "issues": []
        }
```

2. Register plugin in configuration
3. Add tests
4. Update documentation

### Adding an API Endpoint

1. Add route in `admin_app.py`:
```python
@app.route('/api/my-endpoint', methods=['GET'])
@login_required
def my_endpoint():
    # Your logic
    return jsonify({'data': 'value'})
```

2. Add to API documentation
3. Add tests
4. Update API reference

### Adding a Template

1. Create HTML in `templates/`:
```html
{% extends "base.html" %}
{% block content %}
  <!-- Your content -->
{% endblock %}
```

2. Add route in `admin_app.py`
3. Add navigation link (if needed)
4. Test responsiveness

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scanner.py

# Run with coverage
pytest --cov=cwac_admin_app
```

### Writing Tests

```python
import pytest
from cwac_admin_app.app import admin_app

def test_site_list():
    """Test that site list endpoint returns data"""
    client = admin_app.test_client()
    
    # Login
    client.post('/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    
    # Test endpoint
    response = client.get('/api/sites')
    assert response.status_code == 200
    assert 'sites' in response.json
```

## Bug Reports

### Before Reporting

1. Search existing issues
2. Try latest version
3. Check documentation

### Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 20.04]
 - Python version: [e.g. 3.9]
 - Browser: [e.g. Chrome 119]
 - CWAC-ADMIN version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

## Feature Requests

### Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other context or screenshots.
```

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

## Questions?

- Open a GitHub issue
- Check documentation
- Review existing issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the BSD 3-Clause License.

Thank you for contributing to CWAC-ADMIN!
