# Backend Tests

This directory contains comprehensive test suites for all backend Python modules.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and test configuration
├── test_database.py            # Tests for database.py
├── test_embeddings.py          # Tests for embeddings.py
├── test_init_database.py       # Tests for init_database.py
├── test_main.py                # Tests for main.py (API endpoints)
├── test_models.py              # Tests for models.py
├── test_polling_service.py     # Tests for polling_service.py
└── test_schemas.py             # Tests for schemas.py
```

## Installation

Install test dependencies:

```bash
cd backend
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest tests/test_embeddings.py
```

### Run specific test class
```bash
pytest tests/test_embeddings.py::TestEmbeddingService
```

### Run specific test function
```bash
pytest tests/test_embeddings.py::TestEmbeddingService::test_embedding_service_initialization
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Run only database tests
pytest -m db

# Run integration tests
pytest -m integration
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests and stop at first failure
```bash
pytest -x
```

## Test Markers

Tests are organized with the following markers:

- `unit` - Fast unit tests that don't require external dependencies
- `integration` - Integration tests that require database or external services
- `api` - API endpoint tests
- `db` - Tests that require database connection
- `slow` - Slow running tests

## Test Coverage

### Generate HTML coverage report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # On Mac
# or
start htmlcov/index.html  # On Windows
```

### Generate terminal coverage report
```bash
pytest --cov=. --cov-report=term-missing
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `test_engine` - SQLite in-memory database engine for fast unit tests
- `test_db_session` - Database session for tests
- `test_client` - FastAPI TestClient with mocked database
- `embedding_service` - Embedding service instance for tests
- `sample_item_data` - Sample item data for testing
- `sample_items_batch` - Batch of sample items
- `sample_price_data` - Sample price data
- `mock_osrs_mapping_response` - Mock OSRS mapping API response
- `mock_osrs_prices_response` - Mock OSRS prices API response

## Writing New Tests

### Test File Naming
- Test files must be named `test_*.py`
- Test classes must be named `Test*`
- Test functions must be named `test_*`

### Example Test
```python
import pytest
from models import Item

class TestItemModel:
    """Test Item model."""
    
    def test_item_creation(self, test_db_session, sample_item_data):
        """Test creating an Item instance."""
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        assert item.item_id == sample_item_data["item_id"]
        assert item.name == sample_item_data["name"]
```

### Using Markers
```python
@pytest.mark.unit
def test_fast_unit_test():
    """A fast unit test."""
    pass

@pytest.mark.integration
@pytest.mark.db
def test_database_integration():
    """An integration test that requires database."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """A slow test."""
    pass
```

## Test Database

### Unit Tests
Unit tests use SQLite in-memory database for speed. This is automatically configured in `conftest.py`.

### Integration Tests
For integration tests that require PostgreSQL with pgvector:

1. Set up a test PostgreSQL database:
```bash
createdb test_game_items
```

2. Install pgvector extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Update `POSTGRES_TEST_URL` in `conftest.py` if needed

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=. --cov-report=xml
```

## Code Quality

### Run linter
```bash
flake8 .
```

### Format code
```bash
black .
isort .
```

### Type checking
```bash
mypy .
```

## Troubleshooting

### Import Errors
Make sure you're in the `backend` directory when running tests:
```bash
cd backend
pytest
```

### Database Errors
If you get database connection errors:
1. Check that PostgreSQL is running (for integration tests)
2. Verify DATABASE_URL environment variable
3. Check that test database exists

### Embedding Model Errors
Tests use a smaller embedding model (`all-MiniLM-L6-v2`) for speed. If you get model download errors:
1. Check internet connection
2. Try clearing the model cache: `rm -rf ~/.cache/huggingface/`

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Use Fixtures**: Reuse common setup code through fixtures
3. **Mock External Services**: Mock API calls and external dependencies
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Keep Tests Fast**: Use mocks and in-memory databases for unit tests
6. **Document Tests**: Add docstrings explaining what each test does
7. **Use Descriptive Names**: Test names should clearly describe what they test

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Modules**: > 90%
  - `models.py`
  - `embeddings.py`
  - `main.py` (API endpoints)
- **Utility Modules**: > 70%

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

