"""
Tests for schemas.py - Pydantic schemas for request/response validation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas import (
    ItemBase,
    ItemCreate,
    ItemResponse,
    PriceHistoryBase,
    PriceHistoryCreate,
    PriceHistoryResponse,
    SearchQuery,
    SearchResult,
    SearchResponse,
    BatchItemCreate,
    BatchItemResponse,
    ItemPriceResponse
)


class TestItemBase:
    """Test ItemBase schema."""
    
    def test_item_base_with_all_fields(self, sample_item_data):
        """Test ItemBase with all fields."""
        item = ItemBase(**sample_item_data)
        
        assert item.item_id == 1234
        assert item.name == "Dragon longsword"
        assert item.examine == "A razor sharp longsword."
        assert item.members is True
        assert item.lowalch == 40000
        assert item.highalch == 60000
        assert item.limit == 10
        assert item.value == 59999
        assert item.icon == "dragon_longsword.png"
    
    def test_item_base_with_minimal_fields(self):
        """Test ItemBase with minimal required fields."""
        item = ItemBase(
            item_id=1,
            name="Test Item"
        )
        
        assert item.item_id == 1
        assert item.name == "Test Item"
        assert item.members is False  # Default value
        assert item.examine is None
    
    def test_item_base_missing_required_fields(self):
        """Test that ItemBase raises error when required fields are missing."""
        with pytest.raises(ValidationError):
            ItemBase(item_id=1)  # Missing name
        
        with pytest.raises(ValidationError):
            ItemBase(name="Test")  # Missing item_id


class TestItemCreate:
    """Test ItemCreate schema."""
    
    def test_item_create_inherits_from_item_base(self, sample_item_data):
        """Test that ItemCreate inherits from ItemBase."""
        item = ItemCreate(**sample_item_data)
        assert isinstance(item, ItemBase)


class TestItemResponse:
    """Test ItemResponse schema."""
    
    def test_item_response_with_timestamps(self, sample_item_data):
        """Test ItemResponse includes timestamps."""
        now = datetime.utcnow()
        item = ItemResponse(
            **sample_item_data,
            created_at=now,
            updated_at=now
        )
        
        assert item.created_at == now
        assert item.updated_at == now
    
    def test_item_response_config_from_attributes(self):
        """Test that ItemResponse has from_attributes config."""
        assert ItemResponse.model_config.get('from_attributes') is True


class TestPriceHistoryBase:
    """Test PriceHistoryBase schema."""
    
    def test_price_history_base_with_all_fields(self):
        """Test PriceHistoryBase with all fields."""
        price = PriceHistoryBase(
            item_id=1234,
            high_price=100000,
            low_price=95000
        )
        
        assert price.item_id == 1234
        assert price.high_price == 100000
        assert price.low_price == 95000
    
    def test_price_history_base_with_null_prices(self):
        """Test PriceHistoryBase with null price values."""
        price = PriceHistoryBase(
            item_id=1234,
            high_price=None,
            low_price=100000
        )
        
        assert price.item_id == 1234
        assert price.high_price is None
        assert price.low_price == 100000
    
    def test_price_history_base_missing_item_id(self):
        """Test that PriceHistoryBase requires item_id."""
        with pytest.raises(ValidationError):
            PriceHistoryBase(high_price=100000, low_price=95000)


class TestPriceHistoryCreate:
    """Test PriceHistoryCreate schema."""
    
    def test_price_history_create_inherits_from_base(self):
        """Test that PriceHistoryCreate inherits from PriceHistoryBase."""
        price = PriceHistoryCreate(
            item_id=1234,
            high_price=100000,
            low_price=95000
        )
        assert isinstance(price, PriceHistoryBase)


class TestPriceHistoryResponse:
    """Test PriceHistoryResponse schema."""
    
    def test_price_history_response_with_id_and_timestamp(self):
        """Test PriceHistoryResponse includes id and timestamp."""
        now = datetime.utcnow()
        price = PriceHistoryResponse(
            id=1,
            item_id=1234,
            high_price=100000,
            low_price=95000,
            timestamp=now
        )
        
        assert price.id == 1
        assert price.timestamp == now


class TestSearchQuery:
    """Test SearchQuery schema."""
    
    def test_search_query_with_defaults(self):
        """Test SearchQuery with default values."""
        query = SearchQuery(query="dragon longsword")
        
        assert query.query == "dragon longsword"
        assert query.limit == 10  # Default
        assert query.members_only is None  # Default
    
    def test_search_query_with_custom_values(self):
        """Test SearchQuery with custom values."""
        query = SearchQuery(
            query="dragon longsword",
            limit=20,
            members_only=True
        )
        
        assert query.query == "dragon longsword"
        assert query.limit == 20
        assert query.members_only is True
    
    def test_search_query_validates_min_length(self):
        """Test that SearchQuery validates minimum query length."""
        with pytest.raises(ValidationError):
            SearchQuery(query="")  # Empty query
    
    def test_search_query_validates_max_length(self):
        """Test that SearchQuery validates maximum query length."""
        with pytest.raises(ValidationError):
            SearchQuery(query="x" * 501)  # Too long
    
    def test_search_query_validates_limit_min(self):
        """Test that SearchQuery validates minimum limit."""
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=0)
    
    def test_search_query_validates_limit_max(self):
        """Test that SearchQuery validates maximum limit."""
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=101)
    
    def test_search_query_accepts_valid_limit(self):
        """Test that SearchQuery accepts valid limit values."""
        query1 = SearchQuery(query="test", limit=1)
        query2 = SearchQuery(query="test", limit=100)
        
        assert query1.limit == 1
        assert query2.limit == 100


class TestSearchResult:
    """Test SearchResult schema."""
    
    def test_search_result_with_item_and_similarity(self, sample_item_data):
        """Test SearchResult with item and similarity score."""
        now = datetime.utcnow()
        item = ItemResponse(**sample_item_data, created_at=now, updated_at=now)
        result = SearchResult(item=item, similarity=0.95)
        
        assert result.item == item
        assert result.similarity == 0.95
    
    def test_search_result_validates_similarity_range(self, sample_item_data):
        """Test that SearchResult validates similarity is between 0 and 1."""
        now = datetime.utcnow()
        item = ItemResponse(**sample_item_data, created_at=now, updated_at=now)
        
        with pytest.raises(ValidationError):
            SearchResult(item=item, similarity=-0.1)
        
        with pytest.raises(ValidationError):
            SearchResult(item=item, similarity=1.1)
    
    def test_search_result_accepts_valid_similarity(self, sample_item_data):
        """Test that SearchResult accepts valid similarity values."""
        now = datetime.utcnow()
        item = ItemResponse(**sample_item_data, created_at=now, updated_at=now)
        
        result1 = SearchResult(item=item, similarity=0.0)
        result2 = SearchResult(item=item, similarity=1.0)
        
        assert result1.similarity == 0.0
        assert result2.similarity == 1.0


class TestSearchResponse:
    """Test SearchResponse schema."""
    
    def test_search_response_with_results(self, sample_item_data):
        """Test SearchResponse with search results."""
        now = datetime.utcnow()
        item = ItemResponse(**sample_item_data, created_at=now, updated_at=now)
        result = SearchResult(item=item, similarity=0.95)
        
        response = SearchResponse(
            results=[result],
            total=1,
            query="dragon longsword"
        )
        
        assert len(response.results) == 1
        assert response.total == 1
        assert response.query == "dragon longsword"
    
    def test_search_response_empty_results(self):
        """Test SearchResponse with no results."""
        response = SearchResponse(
            results=[],
            total=0,
            query="nonexistent item"
        )
        
        assert len(response.results) == 0
        assert response.total == 0


class TestBatchItemCreate:
    """Test BatchItemCreate schema."""
    
    def test_batch_item_create_with_multiple_items(self, sample_items_batch):
        """Test BatchItemCreate with multiple items."""
        items = [ItemCreate(**item_data) for item_data in sample_items_batch]
        batch = BatchItemCreate(items=items)
        
        assert len(batch.items) == 3
        assert all(isinstance(item, ItemCreate) for item in batch.items)
    
    def test_batch_item_create_empty_list(self):
        """Test BatchItemCreate with empty list."""
        batch = BatchItemCreate(items=[])
        assert len(batch.items) == 0


class TestBatchItemResponse:
    """Test BatchItemResponse schema."""
    
    def test_batch_item_response_success(self):
        """Test BatchItemResponse with successful creation."""
        response = BatchItemResponse(
            created=10,
            failed=0,
            errors=[]
        )
        
        assert response.created == 10
        assert response.failed == 0
        assert len(response.errors) == 0
    
    def test_batch_item_response_with_errors(self):
        """Test BatchItemResponse with errors."""
        response = BatchItemResponse(
            created=8,
            failed=2,
            errors=["Item 1 already exists", "Item 2 validation failed"]
        )
        
        assert response.created == 8
        assert response.failed == 2
        assert len(response.errors) == 2
    
    def test_batch_item_response_default_errors(self):
        """Test that errors defaults to empty list."""
        response = BatchItemResponse(created=10, failed=0)
        assert response.errors == []


class TestItemPriceResponse:
    """Test ItemPriceResponse schema."""
    
    def test_item_price_response_with_all_fields(self):
        """Test ItemPriceResponse with all fields."""
        now = datetime.utcnow()
        response = ItemPriceResponse(
            item_id=1234,
            name="Dragon longsword",
            high_price=100000,
            low_price=95000,
            timestamp=now
        )
        
        assert response.item_id == 1234
        assert response.name == "Dragon longsword"
        assert response.high_price == 100000
        assert response.low_price == 95000
        assert response.timestamp == now
    
    def test_item_price_response_with_null_prices(self):
        """Test ItemPriceResponse with null prices."""
        now = datetime.utcnow()
        response = ItemPriceResponse(
            item_id=1234,
            name="Test Item",
            high_price=None,
            low_price=100000,
            timestamp=now
        )
        
        assert response.high_price is None
        assert response.low_price == 100000
    
    def test_item_price_response_config_from_attributes(self):
        """Test that ItemPriceResponse has from_attributes config."""
        assert ItemPriceResponse.model_config.get('from_attributes') is True

