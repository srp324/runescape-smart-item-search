"""
SQLAlchemy models for game items with vector embeddings.
Matches OSRS Wiki API structure.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base


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
    # 384 for all-MiniLM-L6-v2, 1536 for OpenAI ada-002
    embedding = Column(Vector(384))  # Change to 1536 for OpenAI
    
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

