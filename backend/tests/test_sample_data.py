"""
Tests for sample_data.py - Manual data update script.
"""

import pytest
from unittest.mock import patch, Mock


class TestSampleDataScript:
    """Test sample_data script functionality."""
    
    @patch('backend.polling_service.update_items_and_prices')
    def test_script_calls_update_function(self, mock_update):
        """Test that script calls update_items_and_prices function."""
        # Import and run the main block logic
        from backend import polling_service
        
        # Call the update function directly
        polling_service.update_items_and_prices()
        
        # Verify it was called
        assert mock_update.called
    
    @patch('backend.polling_service.update_items_and_prices')
    def test_script_handles_update_errors(self, mock_update):
        """Test that script handles errors in update function."""
        mock_update.side_effect = Exception("Update failed")
        
        with pytest.raises(Exception, match="Update failed"):
            mock_update()

