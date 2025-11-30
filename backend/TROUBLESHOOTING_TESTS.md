# Troubleshooting Test Issues

## Common Issues and Solutions

### 1. ModuleNotFoundError: No module named 'database'

**Error:**
```
ImportError while loading conftest
tests\conftest.py:16: in <module>
    from database import Base, get_db
E   ModuleNotFoundError: No module named 'database'
```

**Solutions:**

#### Solution A: Run pytest from the backend directory (Recommended)
```bash
cd backend
pytest
```

#### Solution B: Install the backend package in development mode
```bash
cd backend
pip install -e .
pytest
```

#### Solution C: Set PYTHONPATH environment variable
```bash
# Linux/Mac
cd backend
PYTHONPATH=. pytest

# Windows (PowerShell)
cd backend
$env:PYTHONPATH="."
pytest

# Windows (CMD)
cd backend
set PYTHONPATH=.
pytest
```

### 2. Module Import Errors After Fix

If you still get import errors after the fix, try:

```bash
cd backend
# Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__

# Reinstall in development mode
pip install -e .

# Run tests
pytest
```

### 3. Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'pytest'
```

**Solution:**
```bash
cd backend
pip install -r requirements-test.txt
```

### 4. Database Connection Errors

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
Unit tests use SQLite in-memory database and don't need PostgreSQL. If you see this error:

1. Check that you're running unit tests (they should use in-memory DB)
2. For integration tests, ensure PostgreSQL is running:
   ```bash
   # Check PostgreSQL status
   # Linux
   sudo systemctl status postgresql
   
   # Mac
   brew services list
   
   # Windows (check services)
   ```

### 5. Embedding Model Download Issues

**Error:**
```
OSError: Can't load tokenizer for 'all-MiniLM-L6-v2'
```

**Solution:**
```bash
# Ensure internet connection is available
# Model will download automatically on first run (~90MB)

# If download fails, clear cache and retry:
rm -rf ~/.cache/huggingface/
pytest
```

### 6. Coverage Report Not Generated

**Error:**
```
Coverage.py warning: No data was collected.
```

**Solution:**
```bash
cd backend
# Ensure coverage is installed
pip install pytest-cov

# Run with explicit source
pytest --cov=. --cov-report=html

# Or use make command
make test-cov
```

### 7. Tests Pass Locally but Fail in CI

**Common Causes:**
1. Environment variables not set in CI
2. Database not available in CI
3. Model download issues in CI

**Solution:**
```yaml
# GitHub Actions example
- name: Set up Python
  uses: actions/setup-python@v2
  with:
    python-version: '3.10'
    
- name: Cache Hugging Face models
  uses: actions/cache@v2
  with:
    path: ~/.cache/huggingface
    key: ${{ runner.os }}-huggingface
    
- name: Install dependencies
  run: |
    cd backend
    pip install -r requirements-test.txt
    
- name: Run tests
  run: |
    cd backend
    pytest --cov=. --cov-report=xml
  env:
    DATABASE_URL: "sqlite:///:memory:"
    EMBEDDING_MODEL: "all-MiniLM-L6-v2"
```

### 8. Slow Test Execution

**Problem:** Tests taking too long

**Solution:**
```bash
# Skip slow tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Run only fast unit tests
pytest -m unit
```

### 9. Test Isolation Issues

**Problem:** Tests pass individually but fail when run together

**Solution:**
1. Check for shared state between tests
2. Ensure fixtures are properly scoped
3. Clear test database between tests:

```python
@pytest.fixture(autouse=True)
def reset_db(test_db_session):
    """Reset database between tests."""
    yield
    test_db_session.rollback()
```

### 10. Windows Path Issues

**Error:**
```
OSError: [WinError 123] The filename, directory name, or volume label syntax is incorrect
```

**Solution:**
Update conftest.py to use Path objects:
```python
from pathlib import Path
backend_dir = Path(__file__).parent.parent
```

This is already implemented in the fixed version.

## Verification Steps

After fixing issues, verify everything works:

```bash
cd backend

# 1. Check imports work
python -c "from database import Base; print('✓ Imports work')"

# 2. Run a single test
pytest tests/test_database.py::TestDatabaseConfiguration::test_database_url_defaults_to_local_when_empty -v

# 3. Run all tests
pytest

# 4. Check coverage
pytest --cov=. --cov-report=term

# 5. Run with verbose output
pytest -v

# 6. Run specific markers
pytest -m unit
```

## Getting Help

If you still have issues:

1. **Check Python version**: `python --version` (requires 3.9+)
2. **Check pytest version**: `pytest --version` (requires 7.4+)
3. **Check working directory**: `pwd` (should be in backend directory)
4. **List installed packages**: `pip list | grep -E "pytest|fastapi|sqlalchemy"`
5. **Check pytest configuration**: `pytest --collect-only` (shows discovered tests)

## Quick Fix Script

Create this script as `backend/fix_tests.sh` (Linux/Mac) or `backend/fix_tests.bat` (Windows):

### Linux/Mac (fix_tests.sh)
```bash
#!/bin/bash
echo "Fixing test environment..."

# Clear caches
rm -rf .pytest_cache __pycache__ tests/__pycache__

# Reinstall dependencies
pip install -r requirements-test.txt

# Install in development mode
pip install -e .

# Run tests
pytest

echo "Done!"
```

### Windows (fix_tests.bat)
```batch
@echo off
echo Fixing test environment...

REM Clear caches
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist __pycache__ rmdir /s /q __pycache__
if exist tests\__pycache__ rmdir /s /q tests\__pycache__

REM Reinstall dependencies
pip install -r requirements-test.txt

REM Install in development mode
pip install -e .

REM Run tests
pytest

echo Done!
```

Make executable and run:
```bash
# Linux/Mac
chmod +x fix_tests.sh
./fix_tests.sh

# Windows
fix_tests.bat
```

