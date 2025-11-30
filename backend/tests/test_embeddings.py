"""
Tests for embeddings.py - Embedding generation and text processing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from embeddings import (
    EmbeddingService,
    get_embedding_service,
    create_searchable_text,
    format_query_for_embedding,
    _embedding_service
)


class TestEmbeddingService:
    """Test EmbeddingService class."""
    
    def test_embedding_service_initialization(self):
        """Test that EmbeddingService initializes correctly."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.dimension == 384
        assert service.model is not None
    
    def test_get_model_dimension_known_models(self):
        """Test dimension detection for known models."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service._get_model_dimension("all-MiniLM-L6-v2") == 384
        assert service._get_model_dimension("all-mpnet-base-v2") == 768
        assert service._get_model_dimension("Qwen/Qwen3-Embedding-0.6B") == 1024
        assert service._get_model_dimension("Qwen/Qwen3-Embedding-4B") == 2560
        assert service._get_model_dimension("Qwen/Qwen3-Embedding-8B") == 4096
    
    def test_get_model_dimension_partial_matches(self):
        """Test dimension detection for partial model name matches."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service._get_model_dimension("custom-MiniLM-model") == 384
        assert service._get_model_dimension("custom-mpnet-model") == 768
        assert service._get_model_dimension("Qwen3-0.6B-custom") == 1024
    
    def test_get_model_dimension_defaults_to_1024(self):
        """Test that unknown models default to 1024 dimensions."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service._get_model_dimension("unknown-model") == 1024
    
    @patch('embeddings.SentenceTransformer')
    def test_load_model_success(self, mock_transformer):
        """Test successful model loading."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        assert service.model is not None
        mock_transformer.assert_called_once_with("all-MiniLM-L6-v2")
    
    @patch('embeddings.SentenceTransformer')
    def test_load_model_updates_dimension_if_different(self, mock_transformer):
        """Test that model dimension is updated if reported dimension differs."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 512
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        # Should update from 384 to 512
        assert service.dimension == 512
    
    @patch('embeddings.SentenceTransformer')
    def test_load_model_failure(self, mock_transformer):
        """Test that model loading failure raises RuntimeError."""
        mock_transformer.side_effect = Exception("Model not found")
        
        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            EmbeddingService(model_name="invalid-model")
    
    def test_embed_text_returns_list_of_floats(self, embedding_service):
        """Test that embed_text returns a list of floats."""
        text = "Dragon longsword"
        embedding = embedding_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_text_without_loaded_model_raises_error(self):
        """Test that embed_text raises error when model is not loaded."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        service.model = None
        
        with pytest.raises(RuntimeError, match="Embedding model not loaded"):
            service.embed_text("test")
    
    def test_embed_texts_batch(self, embedding_service):
        """Test batch embedding generation."""
        texts = ["Dragon longsword", "Rune platebody", "Iron sword"]
        embeddings = embedding_service.embed_texts(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(x, float) for emb in embeddings for x in emb)
    
    def test_embed_texts_with_custom_batch_size(self, embedding_service):
        """Test batch embedding with custom batch size."""
        texts = ["Item " + str(i) for i in range(10)]
        embeddings = embedding_service.embed_texts(texts, batch_size=5)
        
        assert len(embeddings) == 10
    
    def test_embed_texts_without_loaded_model_raises_error(self):
        """Test that embed_texts raises error when model is not loaded."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        service.model = None
        
        with pytest.raises(RuntimeError, match="Embedding model not loaded"):
            service.embed_texts(["test1", "test2"])
    
    def test_get_dimension(self, embedding_service):
        """Test get_dimension returns correct value."""
        dimension = embedding_service.get_dimension()
        assert dimension == 384


class TestGetEmbeddingService:
    """Test get_embedding_service singleton function."""
    
    @patch('embeddings._embedding_service', None)
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'all-MiniLM-L6-v2'})
    def test_get_embedding_service_creates_singleton(self):
        """Test that get_embedding_service creates a singleton instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2
        assert isinstance(service1, EmbeddingService)
    
    @patch('embeddings._embedding_service', None)
    @patch.dict('os.environ', {'EMBEDDING_MODEL': 'all-mpnet-base-v2'})
    def test_get_embedding_service_uses_env_model(self):
        """Test that get_embedding_service uses model from environment."""
        service = get_embedding_service()
        assert service.model_name == "all-mpnet-base-v2"


class TestCreateSearchableText:
    """Test create_searchable_text function."""
    
    def test_create_searchable_text_with_full_data(self, sample_item_data):
        """Test searchable text creation with complete item data."""
        text = create_searchable_text(sample_item_data)
        
        assert "Item Name: Dragon longsword" in text
        assert "Description: A razor sharp longsword." in text
        assert "Members only item" in text
    
    def test_create_searchable_text_with_minimal_data(self):
        """Test searchable text creation with minimal data."""
        item_data = {
            "item_id": 1,
            "name": "Test item",
            "members": False
        }
        text = create_searchable_text(item_data)
        
        assert "Item Name: Test item" in text
        assert "Members only item" not in text
    
    def test_create_searchable_text_without_name(self):
        """Test searchable text creation without name."""
        item_data = {
            "item_id": 1,
            "examine": "A mysterious item.",
            "members": True
        }
        text = create_searchable_text(item_data)
        
        assert "Description: A mysterious item." in text
        assert "Members only item" in text
    
    def test_create_searchable_text_empty_data(self):
        """Test searchable text creation with empty data."""
        text = create_searchable_text({})
        assert text == ""
    
    def test_create_searchable_text_free_to_play_item(self):
        """Test that free-to-play items don't have members tag."""
        item_data = {
            "name": "Bronze sword",
            "examine": "A basic sword.",
            "members": False
        }
        text = create_searchable_text(item_data)
        
        assert "Members only item" not in text


class TestFormatQueryForEmbedding:
    """Test format_query_for_embedding function."""
    
    def test_format_plain_query_as_item_name(self):
        """Test that plain queries are formatted as item name searches."""
        query = "dragon longsword"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: dragon longsword"
    
    def test_format_description_query_preserved(self):
        """Test that description queries are preserved."""
        query = "Description: a sharp sword"
        formatted = format_query_for_embedding(query)
        assert formatted == "Description: a sharp sword"
    
    def test_format_description_query_case_insensitive(self):
        """Test that description query detection is case-insensitive."""
        query = "description: a sharp sword"
        formatted = format_query_for_embedding(query)
        assert formatted == "Description: a sharp sword"
    
    def test_format_item_name_query_preserved(self):
        """Test that item name queries are preserved."""
        query = "Item Name: dragon longsword"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: dragon longsword"
    
    def test_format_item_name_query_case_insensitive(self):
        """Test that item name query detection is case-insensitive."""
        query = "item name: dragon longsword"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: dragon longsword"
    
    def test_format_empty_description_prefix(self):
        """Test handling of empty description prefix."""
        query = "Description:"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: "
    
    def test_format_empty_item_name_prefix(self):
        """Test handling of empty item name prefix."""
        query = "Item Name:"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: "
    
    def test_format_query_with_whitespace(self):
        """Test that whitespace is handled correctly."""
        query = "  dragon longsword  "
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: dragon longsword"
    
    def test_format_complex_query(self):
        """Test formatting of complex queries."""
        query = "weapon with high damage"
        formatted = format_query_for_embedding(query)
        assert formatted == "Item Name: weapon with high damage"

