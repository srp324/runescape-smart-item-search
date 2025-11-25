"""
Embedding generation service for converting text to vectors.
"""

import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    """
    Service for generating embeddings using sentence-transformers.
    Can be easily extended to support OpenAI or other providers.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model to use
                - 'all-MiniLM-L6-v2': 384 dimensions, fast, good quality
                - 'all-mpnet-base-v2': 768 dimensions, slower, better quality
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.dimension = 384 if "MiniLM" in model_name else 768
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print(f"Model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.dimension


# Global embedding service instance
# Initialize on module import or use dependency injection in FastAPI
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    Creates it if it doesn't exist (singleton pattern).
    """
    global _embedding_service
    if _embedding_service is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _embedding_service = EmbeddingService(model_name=model_name)
    return _embedding_service


def create_searchable_text(item_data: dict) -> str:
    """
    Create searchable text from item data.
    This text will be embedded for semantic search.
    Uses OSRS API structure: name and examine text.
    
    Args:
        item_data: Dictionary containing item fields (OSRS API structure)
        
    Returns:
        Combined searchable text string
    """
    parts = []
    
    if item_data.get("name"):
        parts.append(f"Item Name: {item_data['name']}")
    
    if item_data.get("examine"):
        parts.append(f"Description: {item_data['examine']}")
    
    # Add members status for context
    if item_data.get("members"):
        parts.append("Members only item")
    
    return " | ".join(parts) if parts else ""

