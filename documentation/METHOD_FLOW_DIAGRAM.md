# Method Flow Diagram - User Interactions

This document shows the complete flow of user interactions through the RuneScape Smart Item Search application, including specific methods, files, and data flows.

## 🔍 Flow 1: Search Items (Semantic Search)

```mermaid
sequenceDiagram
    actor User
    participant SearchScreen as SearchScreen.tsx
    participant ApiClient as apiClient.ts
    participant FastAPI as main.py
    participant EmbeddingService as embeddings.py
    participant Database as PostgreSQL

    User->>SearchScreen: Types query & clicks Search
    Note over SearchScreen: handleSearch() called
    SearchScreen->>SearchScreen: performSearch(query, filterValue)
    SearchScreen->>ApiClient: searchItems({query, limit, members_only})
    Note over ApiClient: POST /api/items/search
    
    ApiClient->>FastAPI: POST /api/items/search
    Note over FastAPI: search_items(search_query, db)
    
    FastAPI->>FastAPI: format_query_for_embedding(query)
    Note over FastAPI: Formats query as "Item Name: {query}"
    
    FastAPI->>EmbeddingService: get_embedding_service()
    FastAPI->>EmbeddingService: embed_text(formatted_query)
    Note over EmbeddingService: Uses SentenceTransformer<br/>Model: Qwen3-Embedding-0.6B
    EmbeddingService-->>FastAPI: query_embedding [1024D vector]
    
    FastAPI->>Database: Vector similarity search
    Note over Database: SELECT * FROM game_items<br/>ORDER BY embedding
    Database-->>FastAPI: vector_rows
    
    FastAPI->>Database: Keyword-based search
    Note over Database: WHERE name ILIKE word
    Database-->>FastAPI: keyword_rows
    
    FastAPI->>FastAPI: Combine & rank results
    Note over FastAPI: Calculate scores and boost exact matches
    
    FastAPI-->>ApiClient: SearchResponse {results, total, query}
    ApiClient-->>SearchScreen: SearchResponse
    
    SearchScreen->>SearchScreen: setResults(response.results)
    SearchScreen->>User: Display search results with similarity
    
    User->>SearchScreen: Clicks on item card
    Note over SearchScreen: navigate to item detail page
```

### Key Methods - Search Flow

| File | Method/Function | Purpose |
|------|----------------|---------|
| `SearchScreen.tsx` | `handleSearch()` | Triggers search, updates URL with query params |
| `SearchScreen.tsx` | `performSearch(query, filterValue)` | Calls API client with search parameters |
| `SearchScreen.tsx` | `setResults()` | Updates UI with search results |
| `apiClient.ts` | `searchItems(request)` | POST to `/api/items/search` endpoint |
| `main.py` | `search_items(search_query, db)` | Main search endpoint handler |
| `embeddings.py` | `format_query_for_embedding(query)` | Formats query to match item embedding structure |
| `embeddings.py` | `get_embedding_service()` | Returns singleton EmbeddingService instance |
| `embeddings.py` | `embed_text(text)` | Generates 1024D vector for text |
| `main.py` | Ranking algorithm | Combines vector similarity + keyword matching |

---

## 📊 Flow 2: View Item Details

```mermaid
sequenceDiagram
    actor User
    participant ItemDetail as ItemDetail.tsx
    participant ApiClient as apiClient.ts
    participant FastAPI as main.py
    participant Database as PostgreSQL

    User->>ItemDetail: Navigates to /item/:itemId
    Note over ItemDetail: useEffect triggered - fetchItemData() called
    
    par Parallel API Calls
        ItemDetail->>ApiClient: getItem(itemId)
        ApiClient->>FastAPI: GET /api/items/{item_id}
        Note over FastAPI: get_item(item_id, db)
        FastAPI->>Database: SELECT * FROM game_items
        Database-->>FastAPI: Item data
        FastAPI-->>ApiClient: ItemResponse
        ApiClient-->>ItemDetail: Item
    and
        ItemDetail->>ApiClient: getCurrentItemPrice(itemId)
        ApiClient->>FastAPI: GET /api/items/{item_id}/price/current
        Note over FastAPI: get_current_item_price()
        FastAPI->>Database: SELECT * FROM price_history
        Database-->>FastAPI: Latest price
        FastAPI-->>ApiClient: ItemPriceResponse
        ApiClient-->>ItemDetail: Current price
    end
    
    ItemDetail->>ApiClient: getItemPriceHistory(itemId, 1000)
    ApiClient->>FastAPI: GET /api/items/{item_id}/prices?limit=1000
    Note over FastAPI: get_item_price_history()
    FastAPI->>Database: SELECT * FROM price_history<br/>ORDER BY timestamp DESC
    Database-->>FastAPI: Price history array
    FastAPI-->>ApiClient: PriceHistory[]
    ApiClient-->>ItemDetail: Price history
    
    ItemDetail->>ItemDetail: filteredPriceHistory (useMemo)
    Note over ItemDetail: Filter by timeRange
    
    ItemDetail->>ItemDetail: chartData (useMemo)
    Note over ItemDetail: Transform for Recharts
    
    ItemDetail->>ItemDetail: stats (useMemo)
    Note over ItemDetail: Calculate margin, profit, ROI
    
    ItemDetail->>User: Display charts & statistics
    
    User->>ItemDetail: Changes time range
    ItemDetail->>ItemDetail: setTimeRange(newRange)
    Note over ItemDetail: Re-filters and updates charts
    ItemDetail->>User: Updated charts
    
    User->>ItemDetail: Clicks "Back to Search"
    ItemDetail->>SearchScreen: navigate('/', {state})
    Note over SearchScreen: Restores previous search state
```

### Key Methods - Item Detail Flow

| File | Method/Function | Purpose |
|------|----------------|---------|
| `ItemDetail.tsx` | `useEffect` hook | Fetches item data on component mount |
| `ItemDetail.tsx` | `fetchItemData()` | Orchestrates parallel API calls |
| `apiClient.ts` | `getItem(itemId)` | GET single item by ID |
| `apiClient.ts` | `getCurrentItemPrice(itemId)` | GET latest price for item |
| `apiClient.ts` | `getItemPriceHistory(itemId, limit)` | GET price history array |
| `main.py` | `get_item(item_id, db)` | Retrieves item from database |
| `main.py` | `get_current_item_price(item_id, db)` | Gets most recent price entry |
| `main.py` | `get_item_price_history(item_id, limit, db)` | Gets historical prices |
| `ItemDetail.tsx` | `filteredPriceHistory` (useMemo) | Filters prices by time range |
| `ItemDetail.tsx` | `chartData` (useMemo) | Transforms data for charts |
| `ItemDetail.tsx` | `stats` (useMemo) | Calculates trading statistics |

---

## 🔄 Flow 3: Background Data Polling

```mermaid
sequenceDiagram
    participant FastAPI as main.py
    participant PollingThread as polling_service.py
    participant WikiAPI as OSRS Wiki API
    participant EmbeddingService as embeddings.py
    participant Database as PostgreSQL

    FastAPI->>FastAPI: startup_event()
    FastAPI->>PollingThread: Start thread run_polling_loop()
    Note over PollingThread: Daemon thread started
    
    loop Every 60 seconds
        PollingThread->>PollingThread: update_items_and_prices()
        
        PollingThread->>WikiAPI: GET /api/v1/osrs/mapping
        Note over WikiAPI: fetch_item_mapping()
        WikiAPI-->>PollingThread: Item metadata array
        
        PollingThread->>WikiAPI: GET /api/v1/osrs/latest
        Note over WikiAPI: fetch_latest_prices()
        WikiAPI-->>PollingThread: Price data dictionary
        
        PollingThread->>PollingThread: Filter items with prices
        Note over PollingThread: Only process items with prices
        
        PollingThread->>Database: Check existing items
        Note over Database: SELECT * FROM game_items
        Database-->>PollingThread: Existing items
        
        PollingThread->>PollingThread: Determine which need embeddings
        Note over PollingThread: New items, missing embeddings,<br/>or changed text
        
        PollingThread->>PollingThread: create_searchable_text(item_data)
        Note over PollingThread: Format searchable text
        
        PollingThread->>EmbeddingService: embed_texts(batch_texts, batch_size=500)
        Note over EmbeddingService: Batch generate embeddings
        EmbeddingService-->>PollingThread: embeddings array [1024D vectors]
        
        PollingThread->>Database: INSERT/UPDATE game_items
        Note over Database: Create/update items with embeddings
        
        PollingThread->>Database: INSERT price_history
        Note over Database: INSERT INTO price_history
        
        PollingThread->>PollingThread: db.commit()
        Note over PollingThread: Log statistics
        
        PollingThread->>PollingThread: time.sleep(60)
    end
```

### Key Methods - Polling Flow

| File | Method/Function | Purpose |
|------|----------------|---------|
| `main.py` | `startup_event()` | Initializes app, starts polling thread |
| `polling_service.py` | `run_polling_loop()` | Infinite loop that runs every 60 seconds |
| `polling_service.py` | `update_items_and_prices()` | Main update orchestration function |
| `polling_service.py` | `fetch_item_mapping()` | GET item metadata from Wiki API |
| `polling_service.py` | `fetch_latest_prices()` | GET current prices from Wiki API |
| `embeddings.py` | `create_searchable_text(item_data)` | Formats item data for embedding |
| `embeddings.py` | `embed_texts(texts, batch_size)` | Batch generates embeddings (500 at a time) |
| `database.py` | Database operations | INSERT/UPDATE items and price history |

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Frontend - React/TypeScript"
        A[User] -->|Types query| B[SearchScreen.tsx]
        B -->|Navigate| C[ItemDetail.tsx]
        C -->|Navigate back| B
        B -->|API calls| D[apiClient.ts]
        C -->|API calls| D
    end
    
    subgraph "API Layer"
        D -->|HTTP/JSON| E[main.py<br/>FastAPI Endpoints]
    end
    
    subgraph "Backend Services - Python"
        E -->|Search queries| F[embeddings.py<br/>EmbeddingService]
        E -->|CRUD operations| G[Database<br/>SQLAlchemy ORM]
        
        H[polling_service.py<br/>Background Thread] -->|60s interval| I[OSRS Wiki API]
        H -->|Generate embeddings| F
        H -->|Update data| G
        
        F -->|Uses| J[SentenceTransformer<br/>Qwen3-Embedding-0.6B]
    end
    
    subgraph "Data Layer"
        G -->|pgvector queries| K[(PostgreSQL<br/>with pgvector)]
    end
    
    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#fff3cd
    style D fill:#d4edda
    style E fill:#f8d7da
    style F fill:#f8d7da
    style H fill:#f8d7da
    style K fill:#d1ecf1
```

---

## 📦 Component Method Details

### Frontend Components

#### SearchScreen.tsx
```typescript
// State Management
const [query, setQuery] = useState('')
const [results, setResults] = useState<SearchResult[]>([])
const [membersOnly, setMembersOnly] = useState<boolean | null>(null)

// Core Methods
handleSearch()               // Triggers search, updates URL
performSearch(query, filter) // Calls API client
handleKeyPress(e)           // Enter key triggers search

// Navigation
navigate('/item/:id', {state}) // Preserves search state
```

#### ItemDetail.tsx
```typescript
// State Management
const [item, setItem] = useState<Item | null>(null)
const [currentPrice, setCurrentPrice] = useState<ItemPriceResponse | null>(null)
const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([])
const [timeRange, setTimeRange] = useState<TimeRange>('24h')

// Data Fetching
useEffect(() => fetchItemData())
fetchItemData()              // Parallel Promise.all for item + price

// Computed Values (useMemo)
filteredPriceHistory         // Filter by timeRange
chartData                    // Transform for Recharts
stats                        // Calculate margin, profit, ROI

// Utilities
formatTime(timestamp)        // Format for display
formatCurrency(value)        // Format numbers as GP
formatTimeAgo(timestamp)     // Relative time (e.g., "2 hours ago")
```

#### apiClient.ts
```typescript
class ApiClient {
  // Core API Methods
  searchItems(request: SearchRequest): Promise<SearchResponse>
  getItem(itemId: number): Promise<Item>
  getCurrentItemPrice(itemId: number): Promise<ItemPriceResponse>
  getItemPriceHistory(itemId: number, limit: number): Promise<PriceHistory[]>
  listItems(options): Promise<Item[]>
  
  // Private Helper
  private async fetch<T>(endpoint, options): Promise<T>
}

// Singleton export
export const apiClient = new ApiClient()
```

### Backend Endpoints

#### main.py (FastAPI)
```python
# Startup
@app.on_event("startup")
async def startup_event()
    # Starts polling service thread

# API Endpoints
@app.get("/health")
async def health_check(db)
    # Returns DB status, pgvector status, table existence

@app.post("/api/items/search")
async def search_items(search_query, db)
    # 1. format_query_for_embedding(query)
    # 2. embedding_service.embed_text(formatted_query)
    # 3. Vector search: ORDER BY embedding <=> query_vector
    # 4. Keyword search: ILIKE '%word%'
    # 5. Combine, rank, boost exact matches
    # 6. Return top results

@app.get("/api/items/{item_id}")
async def get_item(item_id, db)
    # Query single item by ID

@app.get("/api/items/{item_id}/prices")
async def get_item_price_history(item_id, limit, db)
    # Query price_history ORDER BY timestamp DESC

@app.get("/api/items/{item_id}/price/current")
async def get_current_item_price(item_id, db)
    # Query latest price (LIMIT 1)

@app.post("/api/items")
async def create_item(item, db)
    # Create with embedding generation

@app.post("/api/items/batch")
async def create_items_batch(batch, db)
    # Batch create with bulk embedding generation
```

#### embeddings.py
```python
class EmbeddingService:
    def __init__(model_name: str = "Qwen/Qwen3-Embedding-0.6B")
        # Loads SentenceTransformer model
        # Dimension: 1024
    
    def embed_text(text: str) -> List[float]
        # Single text embedding
    
    def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]
        # Batch embedding generation
    
    def get_dimension() -> int
        # Returns 1024

# Utility Functions
def get_embedding_service() -> EmbeddingService
    # Singleton pattern

def create_searchable_text(item_data: dict) -> str
    # Format: "Item Name: {name} | Description: {examine} | Members only item"

def format_query_for_embedding(query: str) -> str
    # Format query to match item embedding structure
    # Default: "Item Name: {query}"
```

#### polling_service.py
```python
def fetch_item_mapping() -> List[Dict]
    # GET https://prices.runescape.wiki/api/v1/osrs/mapping

def fetch_latest_prices() -> Dict[int, Dict]
    # GET https://prices.runescape.wiki/api/v1/osrs/latest

def update_items_and_prices()
    # 1. Fetch mapping and prices from Wiki API
    # 2. Filter items with prices
    # 3. Check existing items in DB
    # 4. Determine which need embeddings
    # 5. Batch generate embeddings (500 at a time)
    # 6. INSERT/UPDATE game_items
    # 7. INSERT price_history
    # 8. Commit transaction

def run_polling_loop()
    # Infinite loop: update_items_and_prices() every 60s
```

---

## 🔍 Search Algorithm Details

### Hybrid Search Strategy

The search combines **vector similarity** and **keyword matching** for optimal results:

```python
# 1. Vector Search (Semantic)
SELECT *, 1 - (embedding <=> query_vector) as similarity
FROM game_items
ORDER BY embedding <=> query_vector
LIMIT (limit * 3)

# 2. Keyword Search (Exact/Partial)
SELECT *, 1 - (embedding <=> query_vector) as similarity
FROM game_items
WHERE name ILIKE '%word1%' AND name ILIKE '%word2%'
LIMIT 50

# 3. Combine & Score
combined_score = semantic_similarity * 0.7 + keyword_score * 0.3

# 4. Boost exact matches
if query in name.lower():
    combined_score += 0.15
elif all_words_match:
    combined_score += 0.10

# 5. Sort by combined_score DESC
# 6. Return top N results
```

### Why Hybrid Search?

1. **Vector similarity** understands semantic meaning (e.g., "dlong" → "dragon longsword")
2. **Keyword matching** ensures exact matches rank high
3. **Combined scoring** balances both approaches
4. **Boosting** gives preference to exact substring matches

---

## 📊 Data Models

### Database Schema

```python
# models.py

class Item(Base):
    __tablename__ = "game_items"
    
    item_id: int          # Primary key
    name: str             # Item name
    examine: str          # Description
    members: bool         # Members-only flag
    lowalch: int          # Low alchemy value
    highalch: int         # High alchemy value
    limit: int            # GE buy limit
    value: int            # Shop value
    icon: str             # Icon URL
    embedding: Vector     # 1024D vector (pgvector)
    created_at: datetime
    updated_at: datetime

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id: int               # Primary key
    item_id: int          # Foreign key to Item
    high_price: int       # Buy price
    low_price: int        # Sell price
    timestamp: datetime   # When price was recorded
```

### API Response Types

```typescript
// apiClient.ts

interface Item {
  item_id: number
  name: string
  examine: string | null
  members: boolean
  lowalch: number | null
  highalch: number | null
  limit: number | null
  value: number | null
  icon: string | null
  created_at: string
  updated_at: string
}

interface SearchResult {
  item: Item
  similarity: number      // 0.0 to 1.0 (search relevance)
}

interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
}

interface PriceHistory {
  id: number
  item_id: number
  high_price: number | null
  low_price: number | null
  timestamp: string
}

interface ItemPriceResponse {
  item_id: number
  name: string
  high_price: number | null
  low_price: number | null
  timestamp: string
}
```

---

## 🎯 Key Features

### 1. Semantic Search with Vector Embeddings
- **Model**: Qwen3-Embedding-0.6B (1024 dimensions)
- **Technology**: SentenceTransformers + pgvector
- **Benefit**: Understands meaning, not just keywords

### 2. Hybrid Search Algorithm
- **Vector similarity**: Semantic understanding
- **Keyword matching**: Exact/partial text matches
- **Combined scoring**: Best of both worlds
- **Boost exact matches**: Ensures high relevance

### 3. Real-time Price Tracking
- **Polling interval**: 60 seconds
- **Data source**: OSRS Wiki API
- **Storage**: PostgreSQL with time-series price history

### 4. Interactive Charts
- **Library**: Recharts
- **Time ranges**: 1h, 6h, 24h, 7d, 30d
- **Metrics**: Price, margin, ROI, potential profit

### 5. State Preservation
- **Search state**: Preserved when navigating to item details
- **URL parameters**: Support for bookmarkable searches
- **Navigation**: Seamless back-and-forth with state restoration

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React + TypeScript | UI components |
| | React Router | Client-side routing |
| | Recharts | Data visualization |
| | Vite | Build tool |
| **Backend** | FastAPI | REST API framework |
| | SQLAlchemy | ORM for database |
| | Uvicorn | ASGI server |
| | Threading | Background polling |
| **ML/AI** | SentenceTransformers | Embedding generation |
| | Qwen3-Embedding-0.6B | Embedding model (1024D) |
| **Database** | PostgreSQL | Relational database |
| | pgvector | Vector similarity search |
| **APIs** | OSRS Wiki API | Item data + prices |

---

## 🚀 Performance Optimizations

1. **Batch Embedding Generation**: Process 500 items at a time
2. **Parallel API Calls**: Fetch item + price data simultaneously
3. **useMemo Hooks**: Cache computed values (charts, stats)
4. **Vector Indexing**: pgvector HNSW index for fast similarity search
5. **Candidate Expansion**: Search top 3x results, then re-rank
6. **Background Polling**: Non-blocking data updates via daemon thread

---

## 📝 Notes

- All timestamps are in UTC
- Prices are in OSRS gold pieces (gp)
- Search results are capped at configured limit (default: 20)
- Price history is capped at 1000 entries per request
- Embeddings are regenerated when item text changes
- Items without prices are excluded from the database

