# CWAC-ADMIN Testing Quick Start Guide

## 🚀 Quick Start (2 minutes)

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. View Coverage Report

```bash
pytest --cov --cov-report=html
open htmlcov/index.html  # macOS
```

That's it! You now have 107 tests running automatically.

---

## 📊 What's Included

### Test Suite Overview

- **107 total tests** across all components
- **~1,900 lines** of test code
- **4 test categories**: Admin, Database, Scanner, Integration
- **Comprehensive fixtures** for easy test writing
- **Full documentation** in `tests/README.md`

### Test Breakdown

| Category | Tests | What It Tests |
|----------|-------|---------------|
| **Admin App** | 67 | API endpoints, authentication, routes |
| **Database** | 15 | CRUD operations, queries, integrity |
| **Scanner** | 15 | Configuration, results, validation |
| **Integration** | 10 | End-to-end workflows, data flow |

---

## 🎯 Common Commands

```bash
# Run all tests
pytest

# Run with details
pytest -v

# Run specific category
pytest -m api           # API tests only
pytest -m database      # Database tests only
pytest -m auth          # Authentication tests only

# Run specific file
pytest tests/admin_app/test_api_endpoints.py

# Run with coverage
pytest --cov

# Run fast tests only (skip slow ones)
pytest -m "not slow"

# Re-run only failed tests
pytest --lf

# Stop on first failure
pytest -x
```

---

## 📝 Test Organization

```
tests/
├── admin_app/          # Flask admin interface tests
│   ├── test_api_endpoints.py     # 67 API tests
│   └── test_authentication.py    # Auth & session tests
│
├── database/           # Database operation tests
│   └── test_database_operations.py  # 15 CRUD tests
│
├── scanner/            # Scanner engine tests
│   ├── test_configuration.py     # Config tests
│   └── test_scan_results.py      # Result processing
│
└── test_integration.py            # 10 integration tests
```

---

## ✅ Example Test Run

```bash
$ pytest -v

tests/admin_app/test_api_endpoints.py::TestPublicEndpoints::test_login_page_loads PASSED
tests/admin_app/test_api_endpoints.py::TestPublicEndpoints::test_register_page_loads PASSED
tests/admin_app/test_authentication.py::TestUserAuthentication::test_admin_user_can_login PASSED
tests/database/test_database_operations.py::TestSitesTable::test_insert_site PASSED
...

========================== 107 passed in 12.34s ==========================
```

---

## 📈 Coverage Report

After running with coverage:

```bash
pytest --cov --cov-report=html
```

You'll see:

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
cwac_admin_app/app/admin_app.py          1234    234    81%
cwac_admin_app/database/comprehensive     456     89    80%
cwac/config.py                            123     23    81%
-----------------------------------------------------------
TOTAL                                    3456    567    84%
```

Open `htmlcov/index.html` to see detailed line-by-line coverage.

---

## 🧪 Writing Your First Test

### 1. Create Test File

Create `tests/admin_app/test_my_feature.py`:

```python
import pytest

@pytest.mark.api
@pytest.mark.unit
class TestMyFeature:
    """Test my new feature."""
    
    def test_feature_works(self, authenticated_client):
        """Test feature returns expected data."""
        response = authenticated_client.get('/api/my-endpoint')
        
        assert response.status_code == 200
        data = response.json
        assert 'expected_key' in data
```

### 2. Run Your Test

```bash
pytest tests/admin_app/test_my_feature.py -v
```

### 3. Check Coverage

```bash
pytest tests/admin_app/test_my_feature.py --cov
```

---

## 🔧 Available Fixtures

Use these in your tests (defined in `conftest.py`):

```python
def test_example(client):
    """Use unauthenticated Flask client."""
    pass

def test_with_auth(authenticated_client):
    """Use logged-in Flask client."""
    pass

def test_with_db(temp_db):
    """Use temporary test database."""
    pass

def test_with_data(sample_site_data, sample_scan_data):
    """Use sample test data."""
    pass

def test_with_results(mock_scan_results):
    """Use mock scan result files."""
    pass
```

---

## 🎨 Test Markers

Organize and filter tests:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Multi-component tests
@pytest.mark.api           # API endpoint tests
@pytest.mark.database      # Database tests
@pytest.mark.scanner       # Scanner tests
@pytest.mark.auth          # Authentication tests
@pytest.mark.slow          # Long-running tests
```

Run filtered tests:

```bash
pytest -m unit              # Only unit tests
pytest -m "api and not slow"  # API tests, skip slow ones
```

---

## 🐛 Debugging Tests

### Print Output

```bash
pytest -s  # Show print statements
```

### Full Tracebacks

```bash
pytest --tb=long  # Detailed error info
```

### Debug on Failure

```bash
pytest --pdb  # Drop into debugger on failure
```

### Specific Test

```bash
pytest tests/path/test_file.py::TestClass::test_method -v
```

---

## 📚 More Information

- **Full Documentation**: See `tests/README.md`
- **pytest Docs**: https://docs.pytest.org/
- **pytest-flask**: https://pytest-flask.readthedocs.io/

---

## ✨ Benefits of This Test Suite

### 🛡️ Safety Net
- Catch bugs before production
- Prevent regressions
- Refactor with confidence

### 📖 Documentation
- Tests show how code should work
- Examples of API usage
- Expected behavior documented

### 🚀 Development Speed
- Find issues immediately
- Less manual testing
- Faster debugging

### 💯 Quality Assurance
- Consistent behavior
- Edge cases covered
- Error handling verified

---

## 🎯 Next Steps

1. ✅ **Install dependencies**: `pip install -r requirements-test.txt`
2. ✅ **Run tests**: `pytest -v`
3. ✅ **Check coverage**: `pytest --cov --cov-report=html`
4. 📝 **Read full docs**: `tests/README.md`
5. 🧪 **Write new tests** for your features
6. 🔄 **Set up CI/CD** to run tests automatically

---

**Happy Testing!** 🎉

For questions or issues, see the full test documentation in `tests/README.md`.
