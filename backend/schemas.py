"""
Pydantic schemas for request/response validation.
Matches OSRS Wiki API structure.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ItemBase(BaseModel):
    """Base item schema matching OSRS API structure."""
    item_id: int
    name: str
    examine: Optional[str] = None
    members: bool = False
    lowalch: Optional[int] = None
    highalch: Optional[int] = None
    limit: Optional[int] = None
    value: Optional[int] = None
    icon: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating an item."""
    pass


class ItemResponse(ItemBase):
    """Schema for item response."""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    """Base price history schema."""
    item_id: int
    high_price: Optional[int] = None
    low_price: Optional[int] = None


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating price history entry."""
    pass


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for price history response."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Schema for search request."""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    members_only: Optional[bool] = None  # Filter by members items
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "dragon longsword",
                "limit": 10,
                "members_only": True
            }
        }


class SearchResult(BaseModel):
    """Schema for search result with similarity score."""
    item: ItemResponse
    similarity: float = Field(..., ge=0, le=1)
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Schema for search response."""
    results: List[SearchResult]
    total: int
    query: str


class BatchItemCreate(BaseModel):
    """Schema for batch item creation."""
    items: List[ItemCreate]


class BatchItemResponse(BaseModel):
    """Schema for batch item creation response."""
    created: int
    failed: int
    errors: List[str] = []


class ItemPriceResponse(BaseModel):
    """Schema for current item price response."""
    item_id: int
    name: str
    high_price: Optional[int] = None
    low_price: Optional[int] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

