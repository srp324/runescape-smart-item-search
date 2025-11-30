"""
Tests for polling_service.py - OSRS API polling and data update service.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from polling_service import (
    fetch_item_mapping,
    fetch_latest_prices,
    update_items_and_prices,
    run_polling_loop,
    MAPPING_API_URL,
    LATEST_PRICES_API_URL
)
from models import Item, PriceHistory


class TestFetchItemMapping:
    """Test fetch_item_mapping function."""
    
    @patch('polling_service.requests.get')
    def test_fetch_item_mapping_success(self, mock_get, mock_osrs_mapping_response):
        """Test successful fetch of item mapping."""
        mock_response = Mock()
        mock_response.json.return_value = mock_osrs_mapping_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_item_mapping()
        
        assert len(result) == 2
        assert result[0]["id"] == 1234
        assert result[0]["name"] == "Dragon longsword"
        # Just verify it was called with the URL and timeout
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == MAPPING_API_URL
        assert call_args[1]["timeout"] == 30
    
    @patch('polling_service.requests.get')
    def test_fetch_item_mapping_network_error(self, mock_get):
        """Test fetch_item_mapping handles network errors."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_item_mapping()
        
        assert result == []
    
    @patch('polling_service.requests.get')
    def test_fetch_item_mapping_http_error(self, mock_get):
        """Test fetch_item_mapping handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_get.return_value = mock_response
        
        result = fetch_item_mapping()
        
        assert result == []


class TestFetchLatestPrices:
    """Test fetch_latest_prices function."""
    
    @patch('polling_service.requests.get')
    def test_fetch_latest_prices_success(self, mock_get, mock_osrs_prices_response):
        """Test successful fetch of latest prices."""
        mock_response = Mock()
        mock_response.json.return_value = mock_osrs_prices_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_latest_prices()
        
        assert len(result) == 2
        assert result[1234]["high"] == 100000
        assert result[1234]["low"] == 95000
        assert result[1235]["high"] == 45000
        assert result[1235]["low"] == 43000
    
    @patch('polling_service.requests.get')
    def test_fetch_latest_prices_filters_null_prices(self, mock_get):
        """Test that items with no prices are filtered out."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "1": {"high": 100, "low": 90},
                "2": {"high": None, "low": None},  # Should be filtered
                "3": {"high": 200, "low": None}  # Should be included
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_latest_prices()
        
        assert len(result) == 2
        assert 1 in result
        assert 2 not in result  # Filtered out
        assert 3 in result
    
    @patch('polling_service.requests.get')
    def test_fetch_latest_prices_network_error(self, mock_get):
        """Test fetch_latest_prices handles network errors."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_latest_prices()
        
        assert result == {}
    
    @patch('polling_service.requests.get')
    def test_fetch_latest_prices_invalid_data(self, mock_get):
        """Test fetch_latest_prices handles invalid data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "invalid": {"high": 100, "low": 90},  # Invalid item_id
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_latest_prices()
        
        # Should handle invalid item_id gracefully
        assert isinstance(result, dict)


class TestUpdateItemsAndPrices:
    """Test update_items_and_prices function."""
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    @patch('polling_service.get_embedding_service')
    @patch('polling_service.SessionLocal')
    def test_update_items_and_prices_creates_new_items(
        self, mock_session_local, mock_get_embedding, mock_fetch_mapping, mock_fetch_prices,
        mock_osrs_mapping_response, mock_osrs_prices_response
    ):
        """Test that update creates new items with embeddings and prices."""
        # Setup mocks
        mock_fetch_mapping.return_value = mock_osrs_mapping_response
        mock_fetch_prices.return_value = {
            1234: {"high": 100000, "low": 95000},
            1235: {"high": 45000, "low": 43000}
        }
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing items
        mock_session_local.return_value = mock_db
        
        mock_embedding_service = Mock()
        mock_embedding_service.embed_texts.return_value = [[0.1] * 384, [0.2] * 384]
        mock_get_embedding.return_value = mock_embedding_service
        
        # Run update
        update_items_and_prices()
        
        # Verify embeddings were generated
        assert mock_embedding_service.embed_texts.called
        
        # Verify items were added
        assert mock_db.add.called
        
        # Verify commit was called
        assert mock_db.commit.called
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    @patch('polling_service.SessionLocal')
    def test_update_items_and_prices_skips_items_without_prices(
        self, mock_session_local, mock_fetch_mapping, mock_fetch_prices,
        mock_osrs_mapping_response
    ):
        """Test that items without prices are skipped."""
        # Setup mocks - mapping has 2 items but prices has only 1
        mock_fetch_mapping.return_value = mock_osrs_mapping_response
        mock_fetch_prices.return_value = {
            1234: {"high": 100000, "low": 95000}
            # 1235 has no price
        }
        
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        with patch('polling_service.get_embedding_service'):
            update_items_and_prices()
        
        # Should process fewer items than mapping has
        # Verify through logs or mock calls
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    def test_update_items_and_prices_no_mapping_data(self, mock_fetch_mapping, mock_fetch_prices):
        """Test that update skips when no mapping data is available."""
        mock_fetch_mapping.return_value = []
        mock_fetch_prices.return_value = {}
        
        # Should return early without errors
        update_items_and_prices()
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    def test_update_items_and_prices_no_price_data(self, mock_fetch_mapping, mock_fetch_prices):
        """Test that update skips when no price data is available."""
        mock_fetch_mapping.return_value = [{"id": 1, "name": "Test"}]
        mock_fetch_prices.return_value = {}
        
        # Should return early without errors
        update_items_and_prices()
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    @patch('polling_service.get_embedding_service')
    @patch('polling_service.SessionLocal')
    def test_update_items_and_prices_updates_existing_items(
        self, mock_session_local, mock_get_embedding, mock_fetch_mapping, mock_fetch_prices
    ):
        """Test that update updates existing items."""
        mock_fetch_mapping.return_value = [{
            "id": 1234,
            "name": "Updated Dragon longsword",
            "examine": "Updated description",
            "members": True
        }]
        mock_fetch_prices.return_value = {
            1234: {"high": 100000, "low": 95000}
        }
        
        # Mock existing item
        existing_item = Mock(spec=Item)
        existing_item.item_id = 1234
        existing_item.name = "Old name"
        existing_item.examine = "Old description"
        existing_item.embedding = [0.1] * 384
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_item
        mock_session_local.return_value = mock_db
        
        mock_embedding_service = Mock()
        mock_embedding_service.embed_texts.return_value = [[0.1] * 384]
        mock_get_embedding.return_value = mock_embedding_service
        
        update_items_and_prices()
        
        # Verify commit was called
        assert mock_db.commit.called
    
    @patch('polling_service.fetch_latest_prices')
    @patch('polling_service.fetch_item_mapping')
    @patch('polling_service.SessionLocal')
    def test_update_items_and_prices_handles_database_errors(
        self, mock_session_local, mock_fetch_mapping, mock_fetch_prices
    ):
        """Test that update handles database errors gracefully."""
        mock_fetch_mapping.return_value = [{"id": 1, "name": "Test"}]
        mock_fetch_prices.return_value = {1: {"high": 100, "low": 90}}
        
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db
        
        with patch('polling_service.get_embedding_service'):
            with pytest.raises(Exception):
                update_items_and_prices()
        
        # Verify rollback was called
        assert mock_db.rollback.called


class TestRunPollingLoop:
    """Test run_polling_loop function."""
    
    @patch('polling_service.update_items_and_prices')
    @patch('time.sleep')  # Patch time.sleep directly, not polling_service.time
    def test_run_polling_loop_initial_update(self, mock_sleep, mock_update):
        """Test that polling loop runs initial update immediately."""
        # Make sleep raise exception to exit loop after first iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        try:
            run_polling_loop()
        except KeyboardInterrupt:
            pass
        
        # Verify initial update was called
        assert mock_update.called
    
    @patch('polling_service.update_items_and_prices')
    @patch('time.sleep')
    def test_run_polling_loop_continues_on_error(self, mock_sleep, mock_update):
        """Test that polling loop continues even if update fails."""
        # First call fails, second call succeeds, then exit
        mock_update.side_effect = [
            Exception("Update failed"),
            None,
            KeyboardInterrupt()
        ]
        mock_sleep.side_effect = [None, KeyboardInterrupt()]
        
        try:
            run_polling_loop()
        except KeyboardInterrupt:
            pass
        
        # Should have attempted update multiple times
        assert mock_update.call_count >= 2
    
    @patch('polling_service.update_items_and_prices')
    @patch('time.sleep')
    def test_run_polling_loop_waits_between_updates(self, mock_sleep, mock_update):
        """Test that polling loop waits 60 seconds between updates."""
        # Exit after first iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        try:
            run_polling_loop()
        except KeyboardInterrupt:
            pass
        
        # Verify sleep was called with 60 seconds
        mock_sleep.assert_any_call(60)

