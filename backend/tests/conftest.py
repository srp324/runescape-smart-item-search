"""
Pytest configuration and shared fixtures.
"""

import pytest
import os
import sys
from pathlib import Path

# Add the backend directory to Python path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test environment variables before importing app modules
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_game_items"
os.environ["EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"  # Use smaller model for tests

from database import Base, get_db
from main import app
from models import Item, PriceHistory
from embeddings import EmbeddingService


# Test database URL - use in-memory SQLite for fast unit tests
# For integration tests, use a real PostgreSQL with pgvector
SQLITE_TEST_URL = "sqlite:///:memory:"
POSTGRES_TEST_URL = "postgresql://test:test@localhost:5432/test_game_items"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine (SQLite in-memory)."""
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client for the FastAPI app."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def embedding_service():
    """Create an embedding service instance for tests."""
    # Use a smaller, faster model for tests
    return EmbeddingService(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "item_id": 1234,
        "name": "Dragon longsword",
        "examine": "A razor sharp longsword.",
        "members": True,
        "lowalch": 40000,
        "highalch": 60000,
        "limit": 10,
        "value": 59999,
        "icon": "dragon_longsword.png"
    }


@pytest.fixture
def sample_items_batch():
    """Sample batch of items for testing."""
    return [
        {
            "item_id": 1,
            "name": "Bronze sword",
            "examine": "A basic sword.",
            "members": False,
            "lowalch": 1,
            "highalch": 2,
            "limit": 100,
            "value": 2,
            "icon": "bronze_sword.png"
        },
        {
            "item_id": 2,
            "name": "Iron sword",
            "examine": "A slightly better sword.",
            "members": False,
            "lowalch": 5,
            "highalch": 10,
            "limit": 100,
            "value": 10,
            "icon": "iron_sword.png"
        },
        {
            "item_id": 3,
            "name": "Steel sword",
            "examine": "A good sword.",
            "members": False,
            "lowalch": 25,
            "highalch": 50,
            "limit": 100,
            "value": 50,
            "icon": "steel_sword.png"
        }
    ]


@pytest.fixture
def sample_price_data():
    """Sample price data for testing."""
    return {
        "high": 100000,
        "low": 95000
    }


@pytest.fixture
def mock_osrs_mapping_response():
    """Mock response from OSRS mapping API."""
    return [
        {
            "id": 1234,
            "name": "Dragon longsword",
            "examine": "A razor sharp longsword.",
            "members": True,
            "lowalch": 40000,
            "highalch": 60000,
            "limit": 10,
            "value": 59999,
            "icon": "dragon_longsword.png"
        },
        {
            "id": 1235,
            "name": "Rune platebody",
            "examine": "A platebody made of rune.",
            "members": False,
            "lowalch": 38400,
            "highalch": 64000,
            "limit": 8,
            "value": 65000,
            "icon": "rune_platebody.png"
        }
    ]


@pytest.fixture
def mock_osrs_prices_response():
    """Mock response from OSRS prices API."""
    return {
        "data": {
            "1234": {
                "high": 100000,
                "low": 95000
            },
            "1235": {
                "high": 45000,
                "low": 43000
            }
        }
    }

