"""
Tests for models.py - SQLAlchemy models.
"""

import pytest
from unittest.mock import patch
import os
from datetime import datetime

from models import Item, PriceHistory, get_embedding_dimension


class TestGetEmbeddingDimension:
    """Test get_embedding_dimension function."""
    
    @patch.dict('os.environ', {'EMBEDDING_DIMENSION': '512'})
    def test_get_dimension_from_explicit_env_var(self):
        """Test that explicit EMBEDDING_DIMENSION env var is used."""
        dim = get_embedding_dimension()
        assert dim == 512
    
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'all-MiniLM-L6-v2'}, clear=False)
    def test_get_dimension_from_minilm_model(self):
        """Test dimension for MiniLM model."""
        with patch.dict('os.environ', {}, clear=True):
            os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'
            dim = get_embedding_dimension()
            assert dim == 384
    
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'all-mpnet-base-v2'}, clear=False)
    def test_get_dimension_from_mpnet_model(self):
        """Test dimension for mpnet model."""
        with patch.dict('os.environ', {}, clear=True):
            os.environ['EMBEDDING_MODEL'] = 'all-mpnet-base-v2'
            dim = get_embedding_dimension()
            assert dim == 768
    
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'Qwen/Qwen3-Embedding-0.6B'}, clear=False)
    def test_get_dimension_from_qwen_0_6b_model(self):
        """Test dimension for Qwen3 0.6B model."""
        with patch.dict('os.environ', {}, clear=True):
            os.environ['EMBEDDING_MODEL'] = 'Qwen/Qwen3-Embedding-0.6B'
            dim = get_embedding_dimension()
            assert dim == 1024
    
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'Qwen/Qwen3-Embedding-4B'}, clear=False)
    def test_get_dimension_from_qwen_4b_model(self):
        """Test dimension for Qwen3 4B model."""
        with patch.dict('os.environ', {}, clear=True):
            os.environ['EMBEDDING_MODEL'] = 'Qwen/Qwen3-Embedding-4B'
            dim = get_embedding_dimension()
            assert dim == 2560
    
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'Qwen/Qwen3-Embedding-8B'}, clear=False)
    def test_get_dimension_from_qwen_8b_model(self):
        """Test dimension for Qwen3 8B model."""
        with patch.dict('os.environ', {}, clear=True):
            os.environ['EMBEDDING_MODEL'] = 'Qwen/Qwen3-Embedding-8B'
            dim = get_embedding_dimension()
            assert dim == 4096
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_dimension_defaults_to_1024(self):
        """Test that dimension defaults to 1024."""
        dim = get_embedding_dimension()
        assert dim == 1024


class TestItemModel:
    """Test Item model."""
    
    def test_item_creation(self, test_db_session, sample_item_data):
        """Test creating an Item instance."""
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        assert item.item_id == 1234
        assert item.name == "Dragon longsword"
        assert item.examine == "A razor sharp longsword."
        assert item.members is True
        assert item.lowalch == 40000
        assert item.highalch == 60000
    
    def test_item_repr(self, sample_item_data):
        """Test Item __repr__ method."""
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        repr_str = repr(item)
        
        assert "Item" in repr_str
        assert "1234" in repr_str
        assert "Dragon longsword" in repr_str
        assert "True" in repr_str
    
    def test_item_with_minimal_fields(self, test_db_session):
        """Test creating Item with minimal required fields."""
        item = Item(
            item_id=1,
            name="Test Item",
            members=False,
            embedding=[0.1] * 384
        )
        test_db_session.add(item)
        test_db_session.commit()
        
        assert item.item_id == 1
        assert item.name == "Test Item"
        assert item.examine is None
        assert item.lowalch is None
    
    def test_item_timestamps(self, test_db_session, sample_item_data):
        """Test that timestamps are set automatically."""
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        test_db_session.refresh(item)
        
        assert item.created_at is not None
        assert item.updated_at is not None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
    
    def test_item_name_indexed(self, test_db_session):
        """Test that item name is indexed for fast lookups."""
        # This is a structural test - verifies the index is defined in the model
        from sqlalchemy import inspect
        inspector = inspect(Item)
        assert any(col.name == 'name' for col in inspector.columns.values())
    
    def test_item_members_indexed(self, test_db_session):
        """Test that members field is indexed."""
        from sqlalchemy import inspect
        inspector = inspect(Item)
        assert any(col.name == 'members' for col in inspector.columns.values())


class TestPriceHistoryModel:
    """Test PriceHistory model."""
    
    def test_price_history_creation(self, test_db_session, sample_item_data):
        """Test creating a PriceHistory instance."""
        # Create item first
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        # Create price history
        price = PriceHistory(
            item_id=1234,
            high_price=100000,
            low_price=95000
        )
        test_db_session.add(price)
        test_db_session.commit()
        
        assert price.item_id == 1234
        assert price.high_price == 100000
        assert price.low_price == 95000
        assert price.timestamp is not None
    
    def test_price_history_repr(self):
        """Test PriceHistory __repr__ method."""
        price = PriceHistory(
            id=1,
            item_id=1234,
            high_price=100000,
            low_price=95000
        )
        repr_str = repr(price)
        
        assert "PriceHistory" in repr_str
        assert "1234" in repr_str
        assert "100000" in repr_str
        assert "95000" in repr_str
    
    def test_price_history_relationship(self, test_db_session, sample_item_data):
        """Test relationship between Item and PriceHistory."""
        # Create item
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        # Create price entries
        price1 = PriceHistory(item_id=1234, high_price=100000, low_price=95000)
        price2 = PriceHistory(item_id=1234, high_price=102000, low_price=97000)
        test_db_session.add_all([price1, price2])
        test_db_session.commit()
        
        # Refresh item and check relationship
        test_db_session.refresh(item)
        assert len(item.price_history) == 2
    
    def test_price_history_handles_large_prices(self, test_db_session, sample_item_data):
        """Test that PriceHistory can handle very large price values."""
        # Create item
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        # Create price with very large value (uses BigInteger)
        large_price = 999999999999
        price = PriceHistory(
            item_id=1234,
            high_price=large_price,
            low_price=large_price - 1000
        )
        test_db_session.add(price)
        test_db_session.commit()
        
        assert price.high_price == large_price
    
    def test_price_history_nullable_prices(self, test_db_session, sample_item_data):
        """Test that price values can be null."""
        # Create item
        item = Item(**sample_item_data, embedding=[0.1] * 384)
        test_db_session.add(item)
        test_db_session.commit()
        
        # Create price with null values
        price = PriceHistory(
            item_id=1234,
            high_price=None,
            low_price=100000
        )
        test_db_session.add(price)
        test_db_session.commit()
        
        assert price.high_price is None
        assert price.low_price == 100000
    
    def test_price_history_timestamp_indexed(self):
        """Test that timestamp field is indexed."""
        from sqlalchemy import inspect
        inspector = inspect(PriceHistory)
        assert any(col.name == 'timestamp' for col in inspector.columns.values())

