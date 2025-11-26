"""
SQLAlchemy models for game items with vector embeddings.
Matches OSRS Wiki API structure.
"""

import os
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_embedding_dimension() -> int:
    """
    Get the embedding dimension from environment variable or embedding service.
    Supports: 384 (MiniLM), 768 (mpnet), 1024 (Qwen3-0.6B), 2560 (Qwen3-4B), 4096 (Qwen3-8B)
    """
    # Check for explicit dimension in environment
    env_dim = os.getenv("EMBEDDING_DIMENSION")
    if env_dim:
        try:
            return int(env_dim)
        except ValueError:
            pass
    
    # Otherwise, determine from model name
    model_name = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    
    # Known model dimensions
    dimension_map = {
        "Qwen/Qwen3-Embedding-0.6B": 1024,
        "Qwen/Qwen3-Embedding-4B": 2560,
        "Qwen/Qwen3-Embedding-8B": 4096,
        "all-MiniLM-L6-v2": 384,
        "all-MiniLM-L12-v2": 384,
        "all-mpnet-base-v2": 768,
    }
    
    # Check for exact match
    if model_name in dimension_map:
        return dimension_map[model_name]
    
    # Check for partial matches
    if "Qwen3" in model_name or "Qwen" in model_name:
        if "0.6B" in model_name:
            return 1024
        elif "4B" in model_name:
            return 2560
        elif "8B" in model_name:
            return 4096
    elif "MiniLM" in model_name:
        return 384
    elif "mpnet" in model_name:
        return 768
    
    # Default to 1024 (Qwen3-0.6B)
    return 1024


class Item(Base):
    """
    Item model matching OSRS Wiki API mapping structure.
    Only stores items that have prices (tradeable items).
    """
    __tablename__ = "game_items"

    item_id = Column(Integer, primary_key=True, index=True)  # OSRS item ID
    name = Column(String(255), nullable=False, index=True)
    examine = Column(Text)  # Item examine text (description)
    members = Column(Boolean, nullable=False, default=False, index=True)
    lowalch = Column(Integer)  # Low alchemy value
    highalch = Column(Integer)  # High alchemy value
    limit = Column(Integer)  # GE buy limit
    value = Column(Integer)  # Base item value
    icon = Column(String(255))  # Icon filename
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Vector embedding - dimensions depend on embedding model
    # Supports: 384 (MiniLM), 768 (mpnet), 1024 (Qwen3-0.6B), 2560 (Qwen3-4B), 4096 (Qwen3-8B)
    # Dimension is determined from EMBEDDING_MODEL or EMBEDDING_DIMENSION env var
    embedding = Column(Vector(get_embedding_dimension()))
    
    # Relationship to price history
    price_history = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Item(item_id={self.item_id}, name='{self.name}', members={self.members})>"


class PriceHistory(Base):
    """
    Price history table for tracking GE prices over time.
    Stores high and low prices for each item at each timestamp.
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("game_items.item_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    high_price = Column(BigInteger)  # GE high price (can be very large)
    low_price = Column(BigInteger)  # GE low price (can be very large)
    
    # Relationship to item
    item = relationship("Item", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(id={self.id}, item_id={self.item_id}, timestamp={self.timestamp}, high={self.high_price}, low={self.low_price})>"

