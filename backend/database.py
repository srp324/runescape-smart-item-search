"""
Database configuration and connection management for PostgreSQL + pgvector.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variables
# Note:
# - Some platforms (like Railway / Heroku-style URLs) may:
#   - Define DATABASE_URL but leave it blank, or
#   - Use the legacy "postgres://" scheme instead of "postgresql://",
#     which SQLAlchemy cannot load directly ("postgres" dialect is unknown).
raw_database_url = os.getenv("DATABASE_URL")

if raw_database_url is None or raw_database_url.strip() == "":
    # Fall back to a safe local default for development
    DATABASE_URL = "postgresql://user:password@localhost:5432/game_items"
else:
    DATABASE_URL = raw_database_url.strip()
    # Normalize legacy postgres scheme to postgresql for SQLAlchemy
    # Example: postgres://user:pass@host:port/db -> postgresql://user:pass@host:port/db
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for FastAPI to get database session.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database: create tables and enable pgvector extension.
    Call this once when setting up the database.
    """
    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def check_pgvector_extension():
    """
    Check if pgvector extension is installed.
    Returns True if installed, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            )
            return result.scalar()
    except Exception as e:
        print(f"Error checking pgvector extension: {e}")
        return False

