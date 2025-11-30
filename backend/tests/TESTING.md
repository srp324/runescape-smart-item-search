# Testing Guide for RuneScape Smart Item Search Backend

This document provides a comprehensive guide to the test suite for the backend application.

## Overview

The test suite provides comprehensive coverage for all backend Python modules:

- ✅ **database.py** - Database configuration and connection management
- ✅ **embeddings.py** - Embedding generation and text processing
- ✅ **init_database.py** - Database initialization
- ✅ **main.py** - FastAPI application and API endpoints
- ✅ **models.py** - SQLAlchemy models
- ✅ **polling_service.py** - OSRS API polling service
- ✅ **schemas.py** - Pydantic schemas
- ✅ **sample_data.py** - Manual data update script

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### 4. View Coverage Report

```bash
# Open in browser
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## Test Files

### `test_database.py`
Tests for database connection, configuration, and initialization:
- Database URL handling and normalization
- `get_db()` dependency function
- Database initialization
- pgvector extension checking

**Key Test Classes:**
- `TestDatabaseConfiguration` - Database URL and configuration
- `TestGetDb` - Database session management
- `TestInitDb` - Database initialization
- `TestCheckPgvectorExtension` - Extension checking

### `test_embeddings.py`
Tests for embedding generation and text processing:
- Embedding service initialization
- Model dimension detection
- Text embedding generation
- Batch embedding generation
- Searchable text creation
- Query formatting

**Key Test Classes:**
- `TestEmbeddingService` - Core embedding functionality
- `TestGetEmbeddingService` - Singleton pattern
- `TestCreateSearchableText` - Text preparation
- `TestFormatQueryForEmbedding` - Query formatting

### `test_models.py`
Tests for SQLAlchemy models:
- Item model creation and validation
- PriceHistory model creation
- Model relationships
- Timestamp handling
- Embedding dimension detection

**Key Test Classes:**
- `TestGetEmbeddingDimension` - Dimension configuration
- `TestItemModel` - Item model functionality
- `TestPriceHistoryModel` - Price history functionality

### `test_schemas.py`
Tests for Pydantic schemas:
- Request/response validation
- Field validation rules
- Default values
- Schema inheritance

**Key Test Classes:**
- `TestItemBase` - Base item schema
- `TestSearchQuery` - Search request validation
- `TestSearchResult` - Search result validation
- `TestBatchItemCreate` - Batch operations
- `TestPriceHistoryResponse` - Price data schemas

### `test_main.py`
Tests for FastAPI application and API endpoints:
- Root and health check endpoints
- Search functionality
- Item CRUD operations
- Batch item creation
- Price history endpoints
- Error handling

**Key Test Classes:**
- `TestRootEndpoint` - Root endpoint
- `TestHealthCheck` - Health check functionality
- `TestSearchItems` - Search API
- `TestGetItem` - Item retrieval
- `TestListItems` - Item listing
- `TestCreateItem` - Item creation
- `TestCreateItemsBatch` - Batch operations
- `TestPriceEndpoints` - Price history API

### `test_polling_service.py`
Tests for OSRS API polling service:
- API data fetching
- Item and price updates
- Batch processing
- Error handling
- Polling loop

**Key Test Classes:**
- `TestFetchItemMapping` - Item mapping API
- `TestFetchLatestPrices` - Price API
- `TestUpdateItemsAndPrices` - Update logic
- `TestRunPollingLoop` - Continuous polling

### `test_init_database.py`
Tests for database initialization script:
- Extension creation
- Table creation
- Index creation
- Error handling

**Key Test Classes:**
- `TestInitDatabase` - Database initialization

### `test_sample_data.py`
Tests for manual data update script:
- Script execution
- Error handling

## Running Specific Tests

### By File
```bash
pytest tests/test_embeddings.py
pytest tests/test_main.py
```

### By Class
```bash
pytest tests/test_embeddings.py::TestEmbeddingService
pytest tests/test_main.py::TestSearchItems
```

### By Function
```bash
pytest tests/test_embeddings.py::TestEmbeddingService::test_embed_text_returns_list_of_floats
```

### By Marker
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m api           # API tests only
pytest -m db            # Database tests only
pytest -m slow          # Slow tests only
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.db` - Database tests
- `@pytest.mark.slow` - Slow running tests

## Coverage Goals

| Module | Target Coverage | Status |
|--------|----------------|--------|
| database.py | 90% | ✅ |
| embeddings.py | 90% | ✅ |
| models.py | 95% | ✅ |
| schemas.py | 95% | ✅ |
| main.py | 85% | ✅ |
| polling_service.py | 80% | ✅ |
| init_database.py | 80% | ✅ |
| **Overall** | **85%** | ✅ |

## Test Fixtures

Shared fixtures in `conftest.py`:

### Database Fixtures
- `test_engine` - SQLite in-memory database
- `test_db_session` - Database session
- `test_client` - FastAPI test client

### Service Fixtures
- `embedding_service` - Embedding service instance

### Data Fixtures
- `sample_item_data` - Single item data
- `sample_items_batch` - Multiple items
- `sample_price_data` - Price data
- `mock_osrs_mapping_response` - Mock API response
- `mock_osrs_prices_response` - Mock price response

## Using Make Commands

The `Makefile` provides convenient commands:

```bash
make install        # Install production dependencies
make install-test   # Install test dependencies
make test           # Run all tests
make test-cov       # Run with coverage
make test-verbose   # Run with verbose output
make test-unit      # Run unit tests only
make test-api       # Run API tests only
make clean          # Clean generated files
make lint           # Run linter
make format         # Format code
make type-check     # Run type checker
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

### 1. Test Isolation
Each test should be independent and not rely on other tests.

```python
def test_create_item(test_db_session):
    """Each test gets a fresh database session."""
    item = Item(item_id=1, name="Test", members=False, embedding=[0.1]*384)
    test_db_session.add(item)
    test_db_session.commit()
    assert item.item_id == 1
```

### 2. Use Fixtures
Reuse common setup code through fixtures.

```python
@pytest.fixture
def sample_item(test_db_session):
    item = Item(item_id=1, name="Test", members=False, embedding=[0.1]*384)
    test_db_session.add(item)
    test_db_session.commit()
    return item

def test_get_item(test_client, sample_item):
    response = test_client.get(f"/api/items/{sample_item.item_id}")
    assert response.status_code == 200
```

### 3. Mock External Services
Mock API calls and external dependencies.

```python
@patch('polling_service.requests.get')
def test_fetch_items(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1}]
    result = fetch_item_mapping()
    assert len(result) == 1
```

### 4. Test Edge Cases
Include tests for error conditions and edge cases.

```python
def test_search_empty_query(test_client):
    """Test that empty query returns validation error."""
    response = test_client.post("/api/items/search", json={"query": ""})
    assert response.status_code == 422
```

### 5. Use Descriptive Names
Test names should clearly describe what they test.

```python
# Good
def test_search_items_filters_by_members_only_flag()

# Bad
def test_search()
```

## Troubleshooting

### Import Errors
Ensure you're in the backend directory:
```bash
cd backend
pytest
```

### Database Connection Errors
For integration tests requiring PostgreSQL:
1. Ensure PostgreSQL is running
2. Create test database: `createdb test_game_items`
3. Install pgvector: `CREATE EXTENSION vector;`

### Model Download Errors
Tests use `all-MiniLM-L6-v2` model which downloads on first run:
- Ensure internet connection
- Model caches to `~/.cache/huggingface/`
- Clear cache if needed: `rm -rf ~/.cache/huggingface/`

### Slow Test Execution
To skip slow tests:
```bash
pytest -m "not slow"
```

## Contributing

When adding new code:

1. **Write tests first** (TDD approach)
2. **Aim for >80% coverage** for new code
3. **Use appropriate markers** (@pytest.mark.unit, etc.)
4. **Add docstrings** to test functions
5. **Update this documentation** if adding new test patterns

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

