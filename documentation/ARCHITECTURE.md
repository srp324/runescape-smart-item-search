# Architecture: RuneScape Smart Item Search

## Overview

This application enables semantic search across Old School RuneScape (OSRS) items using vector embeddings. The architecture uses **React + Vite** for the web frontend, **FastAPI** for the backend API, and **PostgreSQL with pgvector** for storing items and performing vector search. The system automatically polls the OSRS Wiki API to keep item data and prices up-to-date.

## Technology Stack

### Frontend: Web Application
- **Web**: React + Vite (Windows/macOS/Linux)
- Real-time search interface
- TypeScript for type safety
- Responsive design for desktop and tablet screens

### Backend: FastAPI
- High-performance Python web framework
- Async/await support
- Automatic API documentation (Swagger/OpenAPI)
- Type validation with Pydantic
- Background polling service for data updates

### Database: PostgreSQL + pgvector
- Relational database with vector search capabilities
- ACID compliance
- Combines structured queries with semantic search
- Mature, production-ready solution
- Automatic price history tracking

### Embedding Model
- **sentence-transformers/all-MiniLM-L6-v2** (default)
  - 384 dimensions
  - Fast inference
  - Good quality for semantic search
- **Alternative**: OpenAI text-embedding-ada-002 (1536 dimensions)
- Runs on the FastAPI server

### Data Source
- **OSRS Wiki API**: Automatic polling every 60 seconds
  - Item mapping: `https://prices.runescape.wiki/api/v1/osrs/mapping`
  - Latest prices: `https://prices.runescape.wiki/api/v1/osrs/latest`
- Only stores tradeable items (items with prices)

## Architecture Components

### 1. **Frontend (Web)**

#### Web Application (React + Vite)
- Search screen component
- Results display with similarity scores
- Filter UI (members-only items)
- API client for FastAPI backend
- Responsive design for desktop and tablet
- Location: `web/` directory

### 2. **Backend API (FastAPI)**

#### Core Endpoints
- `POST /api/items/search` - Vector similarity search
- `GET /api/items/{item_id}` - Get item details
- `GET /api/items` - List items with optional filters
- `POST /api/items` - Create a single item
- `POST /api/items/batch` - Bulk import items
- `GET /api/items/{item_id}/prices` - Get price history
- `GET /api/items/{item_id}/price/current` - Get current price
- `GET /health` - Health check endpoint

#### Services
- **Embedding Service**: Generates vector embeddings using sentence-transformers
- **Vector Search Service**: Performs cosine similarity search in PostgreSQL
- **Polling Service**: Background thread that updates items and prices every 60 seconds

### 3. **Database (PostgreSQL + pgvector)**

#### Tables

**game_items** - Main items table
- Stores OSRS item data with vector embeddings
- Only includes tradeable items (items with prices)
- Fields match OSRS Wiki API structure

**price_history** - Price tracking table
- Stores historical GE (Grand Exchange) prices
- Tracks high and low prices over time
- Automatically updated by polling service

#### Indexes
- Vector similarity index (IVFFlat) on `embedding` column
- Standard indexes on `item_id`, `name`, `members`
- Composite indexes on `price_history` for efficient queries

### 4. **Data Flow**

#### Search Flow
```
User Query: "dragon longsword"
       │
       │ HTTP POST /api/items/search
       ▼
FastAPI Backend
       │
       │ Generate Query Embedding
       ▼
Embedding Service (sentence-transformers)
       │
       │ Query Vector [384 dimensions]
       ▼
PostgreSQL + pgvector
       │
       │ Vector Similarity Search (cosine distance)
       │ Filter by Metadata (members_only, etc.)
       │ ORDER BY embedding <=> query_embedding
       ▼
Ranked Results with Similarity Scores
       │
       │ JSON Response
       ▼
Frontend (Web)
       │
       │ Display Results
       ▼
User sees ranked search results
```

#### Data Update Flow (Polling Service)
```
Background Thread (runs every 60 seconds)
       │
       │ Fetch from OSRS Wiki API
       ▼
OSRS Wiki API
       │
       │ Item Mapping + Latest Prices
       ▼
Polling Service
       │
       │ Process Items (only tradeable items)
       │ Generate Embeddings (for new/changed items)
       ▼
PostgreSQL
       │
       │ Update/Create Items
       │ Add Price History Entries
       ▼
Database Updated
```

## Database Schema

### game_items Table

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Items table (matches OSRS Wiki API structure)
CREATE TABLE game_items (
    item_id INTEGER PRIMARY KEY,  -- OSRS item ID
    name VARCHAR(255) NOT NULL,
    examine TEXT,  -- Item examine text (description)
    members BOOLEAN NOT NULL DEFAULT FALSE,
    lowalch INTEGER,  -- Low alchemy value
    highalch INTEGER,  -- High alchemy value
    "limit" INTEGER,  -- GE buy limit
    value INTEGER,  -- Base item value
    icon VARCHAR(255),  -- Icon filename
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(384)  -- For all-MiniLM-L6-v2 (384 dimensions)
    -- embedding vector(1536)  -- For OpenAI ada-002 (1536 dimensions)
);

-- Vector similarity index
CREATE INDEX game_items_embedding_idx ON game_items 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Standard indexes for filtering
CREATE INDEX idx_game_items_name ON game_items(name);
CREATE INDEX idx_game_items_members ON game_items(members);
CREATE INDEX idx_game_items_item_id ON game_items(item_id);
```

### price_history Table

```sql
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES game_items(item_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    high_price BIGINT,  -- GE high price
    low_price BIGINT,  -- GE low price
    INDEX idx_price_history_item_id (item_id),
    INDEX idx_price_history_timestamp (timestamp),
    INDEX idx_price_history_item_timestamp (item_id, timestamp DESC)
);
```

## API Endpoints

### POST `/api/items/search`

Semantic search using vector similarity.

**Request:**
```json
{
  "query": "dragon longsword",
  "limit": 10,
  "members_only": true
}
```

**Response:**
```json
{
  "results": [
    {
      "item": {
        "item_id": 1305,
        "name": "Dragon longsword",
        "examine": "A very powerful sword.",
        "members": true,
        "lowalch": 48000,
        "highalch": 72000,
        "limit": 8,
        "value": 60000,
        "icon": "dragon_longsword.png",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
      },
      "similarity": 0.89
    }
  ],
  "total": 10,
  "query": "dragon longsword"
}
```

### GET `/api/items/{item_id}`

Get a specific item by OSRS item ID.

### GET `/api/items`

List items with optional filters:
- `members_only`: Filter by members-only items
- `limit`: Maximum results (default: 50, max: 100)
- `offset`: Pagination offset

### GET `/api/items/{item_id}/prices`

Get price history for an item.

**Query Parameters:**
- `limit`: Number of price points to return (default: 100, max: 1000)

### GET `/api/items/{item_id}/price/current`

Get the most recent price for an item.

### POST `/api/items/batch`

Bulk import items (useful for initial data load).

## Search Strategy

### 1. **Vector Search**
   - Convert query text to embedding using sentence-transformers
   - Use cosine similarity search in PostgreSQL
   - SQL: `ORDER BY embedding <=> query_embedding::vector`
   - Returns top K most similar items

### 2. **Metadata Filtering**
   - Apply filters in SQL WHERE clause
   - Currently supports: `members_only` filter
   - Filters applied before vector search for efficiency

### 3. **Searchable Text Generation**

For each item, the searchable text combines:
```
"Item Name: {name} | Description: {examine} | Members only item"
```

This text is embedded once during indexing and stored in the `embedding` column.

## Polling Service

The polling service runs in a background thread and:

1. **Fetches Data** from OSRS Wiki API every 60 seconds:
   - Item mapping (all item metadata)
   - Latest prices (current GE prices)

2. **Processes Items**:
   - Only stores tradeable items (items with prices)
   - Creates new items or updates existing ones
   - Generates embeddings for new/changed items

3. **Updates Prices**:
   - Adds price history entries for all items
   - Tracks high and low prices over time

4. **Error Handling**:
   - Continues running even if individual updates fail
   - Logs errors for monitoring
   - Retries on next cycle

## Performance Considerations

### 1. **Indexing**
   - IVFFlat index for fast approximate vector search
   - `lists` parameter tuned for dataset size (default: 100)
   - Standard indexes for metadata filtering

### 2. **Query Optimization**
   - Embeddings generated on-demand for queries
   - Vector search uses indexed cosine similarity
   - Connection pooling (SQLAlchemy)

### 3. **Batch Processing**
   - Embeddings generated in batches of 500 for initial load
   - Polling service processes items in batches
   - Efficient bulk inserts for price history

### 4. **Caching Opportunities**
   - Cache popular query embeddings (future enhancement)
   - Cache search results for common queries (future enhancement)
   - Use Redis for query result caching (future enhancement)

## Security Considerations

- **CORS**: Configured for web app origins (configurable via environment variables)
- **Input Validation**: Pydantic models for all requests
- **SQL Injection**: Parameterized queries via SQLAlchemy
- **Rate Limiting**: Can be added for production (future enhancement)
- **Authentication**: Can be added for admin endpoints (future enhancement)

## Scalability

### Current Architecture
- Single FastAPI instance
- Single PostgreSQL database
- Background polling thread

### Future Scaling Options
- **Horizontal Scaling**: Multiple FastAPI instances behind load balancer
- **Database Scaling**: PostgreSQL read replicas for search queries
- **Connection Pooling**: SQLAlchemy connection pool (already implemented)
- **Caching Layer**: Redis for frequently accessed data
- **CDN**: For static assets (web frontend)

## Development Setup

### 1. **Database Setup**
   ```bash
   # Install PostgreSQL with pgvector
   # Create database
   createdb game_items
   
   # Initialize schema
   python backend/init_database.py
   ```

### 2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Set DATABASE_URL in .env
   uvicorn main:app --reload
   ```

### 3. **Web Frontend Setup**
   ```bash
   cd web
   npm install
   npm run dev
   ```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

### Key Deployment Points
- Backend: FastAPI with uvicorn/gunicorn
- Database: PostgreSQL with pgvector extension
- Web: Static build (Vite) deployed to CDN/hosting (Vercel, Netlify, etc.)
- Polling Service: Runs automatically in backend process

## Data Model

### Item Fields (OSRS Wiki API Structure)
- `item_id`: Unique OSRS item identifier
- `name`: Item name
- `examine`: Item examine text (description)
- `members`: Whether item is members-only
- `lowalch`: Low alchemy value
- `highalch`: High alchemy value
- `limit`: Grand Exchange buy limit
- `value`: Base item value
- `icon`: Icon filename
- `embedding`: Vector embedding (384 dimensions)

### Price History Fields
- `item_id`: Reference to game_items
- `timestamp`: When price was recorded
- `high_price`: Grand Exchange high price
- `low_price`: Grand Exchange low price
