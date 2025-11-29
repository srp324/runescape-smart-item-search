"""
FastAPI application for game item vector search.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import Optional, List
import os
import threading

from database import get_db, init_db, check_pgvector_extension
from models import Item, PriceHistory
from schemas import (
    ItemResponse, ItemCreate, SearchQuery, SearchResponse, SearchResult,
    BatchItemCreate, BatchItemResponse, PriceHistoryResponse, ItemPriceResponse
)
from embeddings import get_embedding_service, create_searchable_text, format_query_for_embedding

# Initialize FastAPI app
app = FastAPI(
    title="Game Item Vector Search API",
    description="Semantic search API for game items using vector embeddings",
    version="1.0.0"
)

# CORS middleware for web application
# Support environment variable for CORS origins (comma-separated)
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # Parse comma-separated origins from environment variable
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Default development origins
    cors_origins = [
        "http://localhost:3000",  # Web app (Vite dev server)
        "http://localhost:3001",  # Alternative web port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Set to False when using specific origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup and start polling service."""
    print("=" * 60)
    print("Starting FastAPI application...")
    print("=" * 60)
    
    if not check_pgvector_extension():
        print("Warning: pgvector extension not found. Please install it.")
    # Uncomment to auto-initialize database (use with caution in production)
    # init_db()
    
    # Start polling service in background thread
    print("Starting polling service in background thread...")
    try:
        from polling_service import run_polling_loop
        polling_thread = threading.Thread(target=run_polling_loop, daemon=True, name="PollingService")
        polling_thread.start()
        print("✓ Polling service thread started successfully")
        print("  - Initial update will run immediately")
        print("  - Subsequent updates will run every 60 seconds")
    except Exception as e:
        print(f"✗ Failed to start polling service: {e}")
        import traceback
        traceback.print_exc()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Game Item Vector Search API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        pgvector_installed = check_pgvector_extension()

        # Check that required tables exist in the connected database
        game_items_exists = db.execute(
            text("SELECT to_regclass('public.game_items') IS NOT NULL")
        ).scalar()
        price_history_exists = db.execute(
            text("SELECT to_regclass('public.price_history') IS NOT NULL")
        ).scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
            "pgvector": "installed" if pgvector_installed else "not installed",
            "tables": {
                "game_items": bool(game_items_exists),
                "price_history": bool(price_history_exists),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.post("/api/items/search", response_model=SearchResponse)
async def search_items(
    search_query: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    Search items using hybrid vector similarity and keyword matching.
    
    - **query**: Natural language search query (e.g., "dragon longsword")
    - **limit**: Maximum number of results to return (1-100)
    - **members_only**: Optional filter for members-only items
    """
    embedding_service = get_embedding_service()
    
    # Format query to match item embedding format for better semantic similarity
    formatted_query = format_query_for_embedding(search_query.query)
    
    # Generate embedding for query
    try:
        query_embedding = embedding_service.embed_text(formatted_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")
    
    # Build filters
    where_clauses = ["embedding IS NOT NULL"]
    # Format the embedding as a PostgreSQL array string
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    if search_query.members_only is not None:
        where_clauses.append("members = :members_only")
    
    where_clause = " AND ".join(where_clauses)
    
    # Build SQL for vector search with filters
    # Note: "limit" is a reserved keyword in PostgreSQL, so we need to quote it
    # Use string formatting for the vector embedding and LIMIT to avoid parameter binding issues
    # The embedding is already validated as a list of floats, so it's safe
    # Increase limit to get more candidates for re-ranking
    candidate_limit = min(search_query.limit * 3, 100)
    sql = text(f"""
        SELECT item_id, name, examine, members, lowalch, highalch, "limit", value, icon,
               created_at, updated_at,
               1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM game_items
        WHERE {where_clause}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT {candidate_limit}
    """)
    
    # Build params dict for any other parameters
    params = {}
    if search_query.members_only is not None:
        params["members_only"] = search_query.members_only
    
    # Execute query
    try:
        result = db.execute(sql, params)
        vector_rows = result.fetchall()
        
        # Normalize query for keyword matching (lowercase, split into words)
        query_lower = search_query.query.lower()
        query_words = set(word for word in query_lower.split() if len(word) > 1)
        
        # Also do a keyword-based search to ensure exact/near-exact matches are found
        # This is a fallback for cases where vector similarity doesn't rank exact matches highly
        keyword_rows = []
        if query_words:
            # Build keyword search: find items where name contains all query words
            keyword_where_clauses = ["embedding IS NOT NULL"]
            keyword_params = {}
            
            # Add ILIKE conditions for each query word (case-insensitive)
            for i, word in enumerate(query_words):
                keyword_where_clauses.append(f"name ILIKE :keyword_{i}")
                keyword_params[f"keyword_{i}"] = f"%{word}%"
            
            if search_query.members_only is not None:
                keyword_where_clauses.append("members = :members_only")
                keyword_params["members_only"] = search_query.members_only
            
            keyword_where = " AND ".join(keyword_where_clauses)
            
            # Get keyword matches (limit to reasonable number to avoid performance issues)
            keyword_sql = text(f"""
                SELECT item_id, name, examine, members, lowalch, highalch, "limit", value, icon,
                       created_at, updated_at,
                       1 - (embedding <=> '{embedding_str}'::vector) as similarity
                FROM game_items
                WHERE {keyword_where}
                LIMIT 50
            """)
            
            keyword_result = db.execute(keyword_sql, keyword_params)
            keyword_rows = keyword_result.fetchall()
        
        # Combine vector and keyword results, deduplicate by item_id
        seen_item_ids = set()
        all_rows = []
        
        # Add vector results first
        for row in vector_rows:
            if row.item_id not in seen_item_ids:
                all_rows.append(row)
                seen_item_ids.add(row.item_id)
        
        # Add keyword results that weren't already included
        for row in keyword_rows:
            if row.item_id not in seen_item_ids:
                all_rows.append(row)
                seen_item_ids.add(row.item_id)
        
        # Calculate combined scores with keyword boost
        scored_results = []
        for row in all_rows:
            semantic_similarity = float(row.similarity)
            
            # Calculate keyword match score
            name_lower = row.name.lower()
            # Count how many query words appear in the item name
            matching_words = sum(1 for word in query_words if word in name_lower)
            # Also check if the query is a substring of the name (for "dragon long" -> "dragon longsword")
            query_in_name = query_lower in name_lower
            name_in_query = name_lower in query_lower
            
            # Calculate keyword score (0.0 to 1.0)
            if query_in_name or name_in_query:
                # Exact or substring match gets high boost
                keyword_score = 0.5
            elif matching_words > 0:
                # Partial word match gets proportional boost
                keyword_score = 0.2 * (matching_words / len(query_words))
            else:
                keyword_score = 0.0
            
            # Combine semantic similarity (0.0 to 1.0) with keyword boost
            # Weight: 70% semantic, 30% keyword (but keyword can boost significantly)
            combined_score = semantic_similarity * 0.7 + keyword_score * 0.3
            
            # Additional boost for exact/close matches
            if query_in_name:
                combined_score = min(1.0, combined_score + 0.15)
            elif matching_words == len(query_words) and len(query_words) > 0:
                # All query words match
                combined_score = min(1.0, combined_score + 0.1)
            
            item = ItemResponse(
                item_id=row.item_id,
                name=row.name,
                examine=row.examine,
                members=row.members,
                lowalch=row.lowalch,
                highalch=row.highalch,
                limit=row.limit,
                value=row.value,
                icon=row.icon,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            scored_results.append((combined_score, SearchResult(item=item, similarity=combined_score)))
        
        # Sort by combined score (descending) and take top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [result for _, result in scored_results[:search_query.limit]]
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=search_query.query
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by item_id."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/api/items", response_model=List[ItemResponse])
async def list_items(
    members_only: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """List items with optional filters."""
    query = db.query(Item)
    
    if members_only is not None:
        query = query.filter(Item.members == members_only)
    
    items = query.limit(limit).offset(offset).all()
    return items


@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item with automatic embedding generation."""
    # Check if item already exists
    existing_item = db.query(Item).filter(Item.item_id == item.item_id).first()
    if existing_item:
        raise HTTPException(status_code=400, detail=f"Item with item_id {item.item_id} already exists")
    
    embedding_service = get_embedding_service()
    
    # Create searchable text and generate embedding
    item_dict = item.model_dump()
    item_name = item_dict.get("name", "Unknown")
    print(f"Generating embedding for item {item.item_id} ({item_name})")
    
    searchable_text = create_searchable_text(item_dict)
    embedding = embedding_service.embed_text(searchable_text)
    
    print(f"✓ Embedding generated for {item_name} (ID: {item.item_id})")
    
    # Create database item
    db_item = Item(
        **item_dict,
        embedding=embedding
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@app.post("/api/items/batch", response_model=BatchItemResponse)
async def create_items_batch(
    batch: BatchItemCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple items in batch with automatic embedding generation.
    Useful for initial data import.
    """
    embedding_service = get_embedding_service()
    
    created = 0
    failed = 0
    errors = []
    
    # Process items in batches for embedding generation
    items_to_create = []
    searchable_texts = []
    
    for item_data in batch.items:
        item_dict = item_data.model_dump()
        # Check if item already exists
        existing = db.query(Item).filter(Item.item_id == item_dict.get("item_id")).first()
        if existing:
            failed += 1
            errors.append(f"Item {item_dict.get('item_id')} ({item_dict.get('name', 'unknown')}) already exists")
            continue
        
        searchable_text = create_searchable_text(item_dict)
        searchable_texts.append(searchable_text)
        items_to_create.append(item_dict)
    
    if not items_to_create:
        return BatchItemResponse(created=0, failed=failed, errors=errors)
    
    # Generate embeddings in batch
    print(f"Generating embeddings for {len(items_to_create)} items...")
    item_names = [item_dict.get("name", "Unknown") for item_dict in items_to_create]
    for i, name in enumerate(item_names, 1):
        print(f"  [{i}/{len(item_names)}] {name}")
    
    try:
        embeddings = embedding_service.embed_texts(searchable_texts)
        print(f"✓ Successfully generated {len(embeddings)} embeddings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")
    
    # Create database items
    for item_dict, embedding in zip(items_to_create, embeddings):
        try:
            db_item = Item(**item_dict, embedding=embedding)
            db.add(db_item)
            created += 1
        except Exception as e:
            failed += 1
            errors.append(f"Item {item_dict.get('item_id')} ({item_dict.get('name', 'unknown')}): {str(e)}")
    
    db.commit()
    
    return BatchItemResponse(
        created=created,
        failed=failed,
        errors=errors
    )


@app.get("/api/items/{item_id}/prices", response_model=List[PriceHistoryResponse])
async def get_item_price_history(
    item_id: int,
    limit: int = Query(default=100, le=1000, ge=1),
    db: Session = Depends(get_db)
):
    """Get price history for a specific item."""
    # Verify item exists
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get price history
    prices = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id
    ).order_by(
        PriceHistory.timestamp.desc()
    ).limit(limit).all()
    
    return prices


@app.get("/api/items/{item_id}/price/current", response_model=ItemPriceResponse)
async def get_current_item_price(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get the most recent price for a specific item."""
    # Verify item exists
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get most recent price
    latest_price = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id
    ).order_by(
        PriceHistory.timestamp.desc()
    ).first()
    
    if not latest_price:
        raise HTTPException(status_code=404, detail="No price data available for this item")
    
    return ItemPriceResponse(
        item_id=item.item_id,
        name=item.name,
        high_price=latest_price.high_price,
        low_price=latest_price.low_price,
        timestamp=latest_price.timestamp
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

