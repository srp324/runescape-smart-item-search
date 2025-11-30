"""
Tests for database.py - Database configuration and connection management.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import (
    get_db,
    init_db,
    check_pgvector_extension,
    DATABASE_URL
)


class TestDatabaseConfiguration:
    """Test database configuration and URL handling."""
    
    def test_database_url_defaults_to_local_when_empty(self):
        """Test that DATABASE_URL defaults to local when env var is empty."""
        with patch.dict('os.environ', {'DATABASE_URL': ''}, clear=False):
            from importlib import reload
            import database
            reload(database)
            assert "localhost" in database.DATABASE_URL or "postgresql://" in database.DATABASE_URL
    
    def test_database_url_normalizes_postgres_scheme(self):
        """Test that postgres:// scheme is converted to postgresql://."""
        test_url = "postgres://user:pass@host:5432/dbname"
        with patch.dict('os.environ', {'DATABASE_URL': test_url}, clear=False):
            from importlib import reload
            import database
            reload(database)
            assert database.DATABASE_URL.startswith("postgresql://")
            assert "user:pass@host:5432/dbname" in database.DATABASE_URL
    
    def test_database_url_preserves_postgresql_scheme(self):
        """Test that postgresql:// scheme is preserved."""
        test_url = "postgresql://user:pass@host:5432/dbname"
        with patch.dict('os.environ', {'DATABASE_URL': test_url}, clear=False):
            from importlib import reload
            import database
            reload(database)
            assert database.DATABASE_URL == test_url


class TestGetDb:
    """Test get_db dependency function."""
    
    def test_get_db_yields_session(self, test_db_session):
        """Test that get_db yields a database session."""
        db_generator = get_db()
        db = next(db_generator)
        assert isinstance(db, Session)
        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass
    
    def test_get_db_closes_session_after_use(self):
        """Test that get_db closes the session after use."""
        from database import SessionLocal
        
        mock_session = MagicMock()
        # Mock SessionLocal to return our mock session when called
        with patch('database.SessionLocal', return_value=mock_session):
            db_generator = get_db()
            session = next(db_generator)
            
            # Verify we got a session
            assert session is mock_session
            
            # Trigger the finally block
            try:
                next(db_generator)
            except StopIteration:
                pass
            
            # Verify close was called
            mock_session.close.assert_called_once()


@pytest.mark.db
class TestInitDb:
    """Test database initialization."""
    
    @patch('database.engine')
    def test_init_db_creates_extension(self, mock_engine):
        """Test that init_db creates pgvector extension."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        with patch('database.Base') as mock_base:
            init_db()
            
            # Verify extension creation was attempted
            mock_conn.execute.assert_called()
            call_args = mock_conn.execute.call_args[0][0]
            assert "CREATE EXTENSION IF NOT EXISTS vector" in str(call_args)
    
    @patch('database.engine')
    @patch('database.Base')
    def test_init_db_creates_tables(self, mock_base, mock_engine):
        """Test that init_db creates database tables."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_db()
        
        # Verify tables were created
        mock_base.metadata.create_all.assert_called_once()


@pytest.mark.db
class TestCheckPgvectorExtension:
    """Test pgvector extension checking."""
    
    @patch('database.engine')
    def test_check_pgvector_extension_returns_true_when_installed(self, mock_engine):
        """Test that check_pgvector_extension returns True when extension is installed."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        result = check_pgvector_extension()
        
        assert result is True
    
    @patch('database.engine')
    def test_check_pgvector_extension_returns_false_when_not_installed(self, mock_engine):
        """Test that check_pgvector_extension returns False when extension is not installed."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = False
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        result = check_pgvector_extension()
        
        assert result is False
    
    @patch('database.engine')
    def test_check_pgvector_extension_handles_errors(self, mock_engine):
        """Test that check_pgvector_extension handles errors gracefully."""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Database error")
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        result = check_pgvector_extension()
        
        assert result is False

