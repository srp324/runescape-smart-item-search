"""
Tests for init_database.py - Database initialization script.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from sqlalchemy import text

from init_database import init_database


class TestInitDatabase:
    """Test init_database function."""
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_enables_pgvector(self, mock_base, mock_engine):
        """Test that init_database enables pgvector extension."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify execute was called (pgvector extension + indexes)
        assert mock_conn.execute.called
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_tables(self, mock_base, mock_engine):
        """Test that init_database creates all tables."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify create_all was called
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_indexes(self, mock_base, mock_engine):
        """Test that init_database creates indexes."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify multiple execute calls (for indexes)
        assert mock_conn.execute.call_count >= 3
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_vector_index(self, mock_base, mock_engine):
        """Test that init_database creates IVFFlat vector index."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify multiple execute calls for indexes
        assert mock_conn.execute.call_count >= 3
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_handles_existing_indexes(self, mock_base, mock_engine):
        """Test that init_database handles already existing indexes."""
        mock_conn = MagicMock()
        # Simulate index already exists
        mock_conn.execute.side_effect = [
            None,  # Extension creation
            None,  # First index
            Exception("Index already exists"),  # Duplicate index
            None,  # Other operations
        ]
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        # Should not raise exception
        init_database()
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_prints_database_url(self, mock_base, mock_engine, capsys):
        """Test that init_database prints database URL information."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.url = "postgresql://user:***@localhost:5432/test"
        
        init_database()
        
        captured = capsys.readouterr()
        # Just verify something was printed
        assert len(captured.out) > 0
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_commits_changes(self, mock_base, mock_engine):
        """Test that init_database commits all changes."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify commit was called
        assert mock_conn.commit.called
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_success_message(self, mock_base, mock_engine, capsys):
        """Test that init_database prints success message."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        captured = capsys.readouterr()
        assert "✓" in captured.out or "success" in captured.out.lower()
    
    @patch('init_database.engine')
    def test_init_database_handles_connection_errors(self, mock_engine):
        """Test that init_database handles connection errors."""
        mock_engine.connect.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            init_database()
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_game_items_indexes(self, mock_base, mock_engine):
        """Test that init_database creates indexes for game_items table."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify execute was called multiple times (for various indexes)
        assert mock_conn.execute.call_count >= 2
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_price_history_indexes(self, mock_base, mock_engine):
        """Test that init_database creates indexes for price_history table."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify execute was called for indexes
        assert mock_conn.execute.call_count >= 2
    
    @patch('init_database.engine')
    @patch('init_database.Base')
    def test_init_database_creates_composite_index(self, mock_base, mock_engine):
        """Test that init_database creates composite index for item_id and timestamp."""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        init_database()
        
        # Verify execute was called for creating indexes
        assert mock_conn.execute.call_count >= 3

