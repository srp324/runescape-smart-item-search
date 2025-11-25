# Architecture Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Web Application                                         │   │
│  │  (React + Vite + TypeScript)                            │   │
│  │                                                          │   │
│  │  - Search UI                                            │   │
│  │  - Results Display                                      │   │
│  │  - Filter UI (Members-only)                             │   │
│  └──────────────────────┬──────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          │ HTTP Requests
                          │ (POST /api/items/search, GET /api/items, etc.)
                          │
                          ▼
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                             │  │
│  │  - POST /api/items/search                                 │  │
│  │  - GET /api/items/{id}                                    │  │
│  │  - GET /api/items/{id}/prices                             │  │
│  │  - GET /api/items/{id}/price/current                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Embedding  │      │  Vector      │      │  Polling     │  │
│  │  Service     │      │  Search      │      │  Service     │  │
│  │              │      │  Service     │      │              │  │
│  │ - Generate   │      │ - Query      │      │ - Fetch OSRS │  │
│  │   embeddings │      │   vectors   │      │   Wiki API   │  │
│  │ - Batch proc │      │ - Similarity│      │ - Update DB  │  │
│  └──────┬───────┘      │   search    │      │ - Every 60s  │  │
│         │              └──────┬───────┘      └──────┬───────┘  │
│         │                     │                      │         │
└─────────┼─────────────────────┼──────────────────────┼─────────┘
          │                     │                      │
          │ Query Embedding     │ Vector Query         │ Item/Price Data
          ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL + pgvector Database                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  game_items Table                                        │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │ Item 1       │  │ Item 2       │  │ Item N       │ │  │
│  │  │ - item_id    │  │ - item_id    │  │ ...         │ │  │
│  │  │ - name       │  │ - name       │  │             │ │  │
│  │  │ - examine    │  │ - examine    │  │             │ │  │
│  │  │ - members    │  │ - members    │  │             │ │  │
│  │  │ - embedding  │  │ - embedding  │  │ - embedding  │ │  │
│  │  │   [384 dims] │  │   [384 dims] │  │   [384 dims] │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │  │
│  │                                                           │  │
│  │  Vector Index (IVFFlat) for similarity search            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  price_history Table                                     │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Price Entry  │  │ Price Entry  │  │ Price Entry  │   │  │
│  │  │ - item_id    │  │ - item_id    │  │ ...         │   │  │
│  │  │ - timestamp  │  │ - timestamp  │  │             │   │  │
│  │  │ - high_price │  │ - high_price │  │             │   │  │
│  │  │ - low_price  │  │ - low_price  │  │             │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                                                           │  │
│  │  Indexes on (item_id, timestamp) for efficient queries   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Search Query

```
User Query: "dragon longsword"
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend (Web)                     │
│  - User types query                 │
│  - Sends POST /api/items/search     │
└────────┬────────────────────────────┘
         │
         │ HTTP POST Request
         │ {query: "dragon longsword", limit: 10}
         ▼
┌─────────────────────────────────────┐
│  FastAPI Backend                     │
│  - Receives search request           │
│  - Validates with Pydantic           │
└────────┬────────────────────────────┘
         │
         │ Generate Embedding
         ▼
┌─────────────────────────────────────┐
│  Embedding Service                  │
│  (sentence-transformers)            │
│                                     │
│  Input: "dragon longsword"          │
│  Output: [0.123, -0.456, ..., 384] │
└────────┬────────────────────────────┘
         │
         │ Query Vector
         ▼
┌─────────────────────────────────────┐
│  PostgreSQL + pgvector               │
│                                     │
│  SQL Query:                         │
│  SELECT item_id, name, examine,     │
│         1 - (embedding <=>          │
│         query_vector) as similarity │
│  FROM game_items                    │
│  WHERE embedding IS NOT NULL       │
│    AND members = true (if filter)   │
│  ORDER BY embedding <=> query_vector │
│  LIMIT 10                           │
└────────┬────────────────────────────┘
         │
         │ Ranked Results
         │ [{item: {...}, similarity: 0.89}, ...]
         ▼
┌─────────────────────────────────────┐
│  FastAPI Response                   │
│  {                                  │
│    results: [...],                 │
│    total: 10,                      │
│    query: "dragon longsword"       │
│  }                                  │
└────────┬────────────────────────────┘
         │
         │ JSON Response
         ▼
┌─────────────────────────────────────┐
│  Frontend (Web)                     │
│  - Display results                  │
│  - Show similarity scores           │
│  - Render item details              │
└─────────────────────────────────────┘
```

## Data Flow: Polling Service (Background Updates)

```
Background Thread (runs every 60 seconds)
         │
         │ Fetch from OSRS Wiki API
         ▼
┌─────────────────────────────────────┐
│  OSRS Wiki API                      │
│                                     │
│  1. Item Mapping API               │
│     /api/v1/osrs/mapping            │
│     Returns: [{id, name, examine,  │
│                members, ...}, ...]  │
│                                     │
│  2. Latest Prices API              │
│     /api/v1/osrs/latest             │
│     Returns: {item_id: {high, low}} │
└────────┬────────────────────────────┘
         │
         │ Item Data + Prices
         ▼
┌─────────────────────────────────────┐
│  Polling Service                    │
│                                     │
│  1. Filter items (only tradeable)   │
│  2. Check for new/changed items     │
│  3. Generate embeddings for new     │
│     items (batch of 500)            │
│  4. Update/Create items in DB      │
│  5. Add price history entries      │
└────────┬────────────────────────────┘
         │
         │ Database Updates
         ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│                                     │
│  game_items:                        │
│  - INSERT new items                 │
│  - UPDATE existing items            │
│  - Store embeddings                 │
│                                     │
│  price_history:                     │
│  - INSERT price entries             │
│  - Track price over time            │
└─────────────────────────────────────┘
```

## Data Flow: Item Indexing (Embedding Generation)

```
OSRS Item Data
{item_id: 1305, name: "Dragon longsword", examine: "A very powerful sword.", ...}
         │
         ▼
┌─────────────────────────────────────┐
│  Create Searchable Text             │
│                                     │
│  "Item Name: Dragon longsword |     │
│   Description: A very powerful       │
│   sword. | Members only item"        │
└────────┬────────────────────────────┘
         │
         │ Searchable Text
         ▼
┌─────────────────────────────────────┐
│  Embedding Service                  │
│  (sentence-transformers)            │
│  Model: all-MiniLM-L6-v2            │
│                                     │
│  Input: Searchable text string      │
│  Output: Vector [384 dimensions]    │
│  [0.123, -0.456, 0.789, ..., 384]  │
└────────┬────────────────────────────┘
         │
         │ Embedding Vector
         ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│                                     │
│  INSERT INTO game_items (           │
│    item_id, name, examine,          │
│    embedding, ...                   │
│  ) VALUES (                         │
│    1305,                            │
│    'Dragon longsword',              │
│    'A very powerful sword.',        │
│    '[0.123, -0.456, ...]'::vector, │
│    ...                              │
│  )                                  │
│                                     │
│  Vector Index (IVFFlat)             │
│  automatically updated               │
└─────────────────────────────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Embedding  │      │   Vector     │      │   Polling    │  │
│  │   Service    │      │   Search    │      │   Service    │  │
│  │              │      │   Service    │      │              │  │
│  │ - Generate   │      │ - Query      │      │ - Fetch OSRS │  │
│  │   embeddings │      │   vectors   │      │   Wiki API   │  │
│  │ - Batch proc │      │ - Similarity │      │ - Update DB  │  │
│  │ - Model mgmt │      │   search    │      │ - Background │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   FastAPI    │      │   Database   │      │   API        │  │
│  │   Routes     │      │   Models     │      │   Schemas    │  │
│  │              │      │              │      │              │  │
│  │ - REST       │      │ - SQLAlchemy │      │ - Pydantic   │  │
│  │   endpoints  │      │ - Models      │      │ - Validation  │  │
│  │ - CORS       │      │ - Relations  │      │ - Serialize  │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Web Application                                      │  │
│  │  React + Vite + TypeScript                           │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                                   │ HTTP
┌───────────────────────┴───────────────────────┴─────────────┐
│                    API Layer                                 │
│  FastAPI (Python)                                            │
│  - REST endpoints                                            │
│  - CORS middleware                                           │
│  - Request validation (Pydantic)                             │
│  - Automatic API docs (Swagger)                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  Embedding │  │  Vector     │  │  Polling   │          │
│  │  Service   │  │  Search     │  │  Service   │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  PostgreSQL│  │  pgvector   │  │  SQLAlchemy│          │
│  │  Database  │  │  Extension  │  │  ORM       │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OSRS Wiki API                                        │  │
│  │  - Item Mapping                                       │  │
│  │  - Latest Prices                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    game_items                               │
├─────────────────────────────────────────────────────────────┤
│  item_id (PK)        INTEGER                                │
│  name                VARCHAR(255) NOT NULL                  │
│  examine             TEXT                                   │
│  members             BOOLEAN NOT NULL                       │
│  lowalch             INTEGER                               │
│  highalch            INTEGER                               │
│  limit               INTEGER                               │
│  value               INTEGER                               │
│  icon                VARCHAR(255)                          │
│  created_at          TIMESTAMP                             │
│  updated_at          TIMESTAMP                             │
│  embedding           vector(384)                            │
│                                                             │
│  Indexes:                                                   │
│  - PRIMARY KEY (item_id)                                    │
│  - idx_game_items_name (name)                              │
│  - idx_game_items_members (members)                        │
│  - game_items_embedding_idx (IVFFlat on embedding)        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ 1:N
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    price_history                            │
├─────────────────────────────────────────────────────────────┤
│  id (PK)            SERIAL                                 │
│  item_id (FK)       INTEGER → game_items.item_id           │
│  timestamp          TIMESTAMP NOT NULL                     │
│  high_price         BIGINT                                 │
│  low_price          BIGINT                                 │
│                                                             │
│  Indexes:                                                   │
│  - PRIMARY KEY (id)                                         │
│  - idx_price_history_item_id (item_id)                     │
│  - idx_price_history_timestamp (timestamp)                  │
│  - idx_price_history_item_timestamp (item_id, timestamp)  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Web Application                                      │  │
│  │  (CDN/Static Hosting - Vercel, Netlify, etc.)       │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         │ HTTPS                             │
│                    ▼                                │        │
│         ┌─────────────────────┐                    │        │
│         │  Load Balancer      │                    │        │
│         │  (Optional)         │                    │        │
│         └──────────┬──────────┘                    │        │
│                    │                                │        │
│         ┌──────────┴──────────┐                    │        │
│         │                     │                     │        │
│         ▼                     ▼                     │        │
│  ┌──────────────┐      ┌──────────────┐            │        │
│  │  FastAPI      │      │  FastAPI     │            │        │
│  │  Instance 1   │      │  Instance 2  │            │        │
│  │               │      │              │            │        │
│  │  - API        │      │  - API       │            │        │
│  │  - Embeddings │      │  - Embeddings│            │        │
│  │  - Polling    │      │  - Polling   │            │        │
│  └──────┬────────┘      └──────┬───────┘            │        │
│         │                       │                     │        │
│         └───────────┬───────────┘                   │        │
│                     │                                 │        │
│                     ▼                                 │        │
│         ┌─────────────────────┐                       │        │
│         │  PostgreSQL        │                       │        │
│         │  + pgvector        │                       │        │
│         │                    │                       │        │
│         │  - game_items      │                       │        │
│         │  - price_history   │                       │        │
│         │  - Vector indexes  │                       │        │
│         └────────────────────┘                       │        │
│                                                       │        │
│  ┌─────────────────────────────────────────────────┐ │        │
│  │  External: OSRS Wiki API                       │ │        │
│  │  (Polled every 60 seconds)                     │ │        │
│  └─────────────────────────────────────────────────┘ │        │
└───────────────────────────────────────────────────────┘
```
