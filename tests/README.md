# CWAC-ADMIN Test Suite

Comprehensive test suite for the Centralised Web Accessibility Checker Admin Platform.

## 📋 Test Structure

```
tests/
├── __init__.py                      # Test package initialization
├── conftest.py                      # Shared pytest fixtures
├── pytest.ini                       # Pytest configuration
├── README.md                        # This file
│
├── admin_app/                       # Flask admin interface tests
│   ├── test_api_endpoints.py       # API endpoint tests
│   └── test_authentication.py      # Auth and session tests
│
├── database/                        # Database operation tests
│   └── test_database_operations.py # CRUD and query tests
│
├── scanner/                         # Scanner engine tests
│   ├── test_configuration.py       # Config loading tests
│   └── test_scan_results.py        # Result processing tests
│
├── fixtures/                        # Shared test utilities
│   └── __init__.py
│
└── test_integration.py             # End-to-end integration tests
```

## 🚀 Running Tests

### Install Test Dependencies

```bash
# Install pytest and coverage tools
pip install pytest pytest-flask pytest-cov
```

### Run All Tests

```bash
# Run complete test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=cwac_admin_app --cov=cwac --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Run only database tests
pytest -m database

# Run only authentication tests
pytest -m auth

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Run API endpoint tests
pytest tests/admin_app/test_api_endpoints.py

# Run authentication tests
pytest tests/admin_app/test_authentication.py

# Run database tests
pytest tests/database/test_database_operations.py

# Run integration tests
pytest tests/test_integration.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/admin_app/test_api_endpoints.py::TestPublicEndpoints

# Run a specific test function
pytest tests/admin_app/test_authentication.py::TestUserAuthentication::test_admin_user_can_login
```

## 📊 Test Markers

Tests are organized with markers for easy filtering:

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Unit tests (fast, isolated) |
| `@pytest.mark.integration` | Integration tests (multiple components) |
| `@pytest.mark.api` | API endpoint tests |
| `@pytest.mark.database` | Database operation tests |
| `@pytest.mark.scanner` | Scanner/audit engine tests |
| `@pytest.mark.auth` | Authentication tests |
| `@pytest.mark.slow` | Tests that take significant time |

## 🧪 Test Coverage

### Current Test Categories

**✅ Admin App (67 tests)**
- Public endpoints (login, register, favicon)
- Protected routes (dashboard, sites, scan)
- API endpoints (sites, results, system status)
- Authentication flow (login, logout, sessions)
- Access control and route protection
- Error handling and validation

**✅ Database (15 tests)**
- Schema validation (tables, columns, constraints)
- CRUD operations (create, read, update, delete)
- Foreign key relationships
- Complex queries (aggregations, joins)
- Data integrity

**✅ Scanner (15 tests)**
- Configuration loading and validation
- Result file structure
- axe-core CSV parsing
- Pages scanned tracking
- Score calculation
- Result validation

**✅ Integration (10 tests)**
- Scan-to-database workflow
- API-to-database flow
- Complete authentication workflow
- End-to-end user journeys
- Error handling across components

**Total: 107 test cases**

## 📝 Writing New Tests

### Test File Naming

- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
import pytest

@pytest.mark.unit
@pytest.mark.api
class TestNewFeature:
    """Test description."""
    
    def test_specific_behavior(self, authenticated_client):
        """Test a specific behavior."""
        response = authenticated_client.get('/api/endpoint')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'expected_key' in data
```

### Using Fixtures

Common fixtures available from `conftest.py`:

```python
def test_with_client(client):
    """Use unauthenticated test client."""
    pass

def test_with_auth(authenticated_client):
    """Use authenticated test client."""
    pass

def test_with_database(temp_db):
    """Use temporary test database."""
    pass

def test_with_sample_data(sample_site_data, sample_scan_data):
    """Use sample test data."""
    pass

def test_with_mock_results(mock_scan_results):
    """Use mock scan result files."""
    pass
```

## 🎯 Test Best Practices

### 1. Follow AAA Pattern

```python
def test_example():
    # Arrange - Set up test data
    data = {'key': 'value'}
    
    # Act - Perform the action
    result = process_data(data)
    
    # Assert - Verify the result
    assert result == expected_value
```

### 2. Test One Thing

```python
# ✅ Good - Tests one specific behavior
def test_user_can_login_with_valid_credentials():
    pass

# ❌ Bad - Tests multiple things
def test_login_and_access_dashboard_and_logout():
    pass
```

### 3. Use Descriptive Names

```python
# ✅ Good - Clear what it tests
def test_api_returns_404_for_nonexistent_site():
    pass

# ❌ Bad - Unclear purpose
def test_api():
    pass
```

### 4. Isolate Tests

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order
- Clean up after tests

### 5. Mock External Dependencies

```python
@pytest.fixture
def mock_browser(monkeypatch):
    """Mock browser for faster tests."""
    def fake_scan():
        return {'score': 100}
    
    monkeypatch.setattr('scanner.scan_url', fake_scan)
```

## 📈 Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=cwac_admin_app --cov=cwac --cov-report=html
```

View report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Check Coverage Threshold

```bash
pytest --cov=cwac_admin_app --cov-fail-under=80
```

## 🐛 Debugging Tests

### Run with Debug Output

```bash
# Print statements
pytest -s

# Full traceback
pytest --tb=long

# Drop into debugger on failure
pytest --pdb
```

### Run Specific Failed Tests

```bash
# Re-run only failed tests
pytest --lf

# Re-run failed first, then others
pytest --ff
```

## 🔧 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-flask pytest-cov
    
    - name: Run tests
      run: pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Test-Driven Development](https://testdriven.io/)

## 🤝 Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Test happy path** - Normal successful operation
3. **Test edge cases** - Boundary conditions
4. **Test error cases** - Invalid inputs, failures
5. **Update this README** - Document new test categories

## ✅ Test Checklist

Before committing code:

- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Test coverage hasn't decreased
- [ ] Tests are properly marked
- [ ] No skipped tests without reason
- [ ] Documentation updated

---

**Questions?** Check the [main documentation](../docs/) or create an issue.
