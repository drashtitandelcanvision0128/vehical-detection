# Testing Guide for Vehicle Detection App

## Running Tests

### Run All Tests
```bash
# Using pytest directly
pytest

# Using the test runner script
python run_tests.py

# With coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only authentication tests
pytest -m auth

# Run only API tests
pytest -m api

# Run only detection tests
pytest -m detection
```

### Run Specific Test File
```bash
# Run authentication tests only
pytest tests/test_auth.py

# Run database tests only
pytest tests/test_database.py

# Run API tests only
pytest tests/test_api.py
```

### Run Specific Test Function
```bash
# Run a single test
pytest tests/test_auth.py::test_user_registration

# Run with verbose output
pytest tests/test_auth.py::test_user_registration -v
```

## Test Structure

```
tests/
├── __init__.py           # Test package init
├── conftest.py           # Pytest fixtures and configuration
├── test_auth.py          # Authentication tests
├── test_api.py           # API endpoint tests
└── test_database.py      # Database operations tests
```

## Test Fixtures

Available fixtures in `conftest.py`:
- `test_db` - In-memory database for each test
- `test_user` - Pre-created test user
- `test_client` - Flask test client
- `authenticated_client` - Authenticated Flask client
- `sample_image` - Sample image for testing
- `sample_image_bytes` - Image as bytes
- `temp_dir` - Temporary directory
- `mock_model` - Mock YOLO model

## Writing New Tests

### Example Test
```python
import pytest

@pytest.mark.unit
def test_my_feature(test_client):
    """Test my feature"""
    response = test_client.get('/my-route')
    assert response.status_code == 200
```

### Test Markers
Use markers to categorize tests:
- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - Slower tests that may use DB
- `@pytest.mark.auth` - Authentication related
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.detection` - Detection related
- `@pytest.mark.slow` - Slow running tests

## Continuous Integration

Add this to your CI/CD pipeline:
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=. --cov-fail-under=70
```

## Troubleshooting

### Import Errors
Make sure you're running from the project root:
```bash
cd /path/to/vehicle-detection
pytest
```

### Database Lock Issues
Tests use in-memory database, so no cleanup needed. If you see lock issues, ensure tests are isolated.

### Model Not Found
The tests use mock models for detection, so actual YOLO model isn't required for most tests.

## Coverage Goals

Target coverage: 70% minimum
- Critical paths (auth, database): 90%+
- API endpoints: 80%+
- Utility functions: 70%+
