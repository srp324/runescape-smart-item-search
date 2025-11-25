# API Reference

Complete API documentation for the Game Item Vector Search API.

Base URL: `http://localhost:8000` (development)

## Endpoints

### Health Check

#### GET `/health`

Check API and database status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "pgvector": "installed"
}
```

---

### Search Items

#### POST `/api/items/search`

Search items using vector similarity based on natural language queries.

**Request Body:**
```json
{
  "query": "red dragon sword",
  "limit": 10,
  "members_only": true
}
```

**Parameters:**
- `query` (string, required): Natural language search query (1-500 characters)
- `limit` (integer, optional): Maximum results to return (1-100, default: 10)
- `members_only` (boolean, optional): Filter by members-only items. Set to `true` for members-only, `false` for free-to-play, or omit for both

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
        "icon": "Dragon_longsword.png",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
      },
      "similarity": 0.89
    }
  ],
  "total": 1,
  "query": "red dragon sword"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/items/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "red dragon sword",
    "limit": 10
  }'
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/api/items/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'red dragon sword',
    limit: 10,
    members_only: true
  })
});

const data = await response.json();
console.log(data.results);
```

---

### Get Item

#### GET `/api/items/{item_id}`

Get a specific item by ID.

**Path Parameters:**
- `item_id` (integer, required): OSRS item ID

**Response:**
```json
{
  "item_id": 1305,
  "name": "Dragon longsword",
  "examine": "A very powerful sword.",
  "members": true,
  "lowalch": 48000,
  "highalch": 72000,
  "limit": 8,
  "value": 60000,
  "icon": "Dragon_longsword.png",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Error Responses:**
- `404`: Item not found

---

### List Items

#### GET `/api/items`

List items with optional filters and pagination.

**Query Parameters:**
- `members_only` (boolean, optional): Filter by members-only items. Set to `true` for members-only, `false` for free-to-play, or omit for both
- `limit` (integer, optional): Results per page (1-100, default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Example:**
```
GET /api/items?members_only=true&limit=20&offset=0
```

**Response:**
```json
[
  {
    "item_id": 1305,
    "name": "Dragon longsword",
    "examine": "A very powerful sword.",
    "members": true,
    "lowalch": 48000,
    "highalch": 72000,
    "limit": 8,
    "value": 60000,
    "icon": "Dragon_longsword.png",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

### Create Item

#### POST `/api/items`

Create a new item. Embedding is automatically generated.

**Request Body:**
```json
{
  "item_id": 1305,
  "name": "Dragon longsword",
  "examine": "A very powerful sword.",
  "members": true,
  "lowalch": 48000,
  "highalch": 72000,
  "limit": 8,
  "value": 60000,
  "icon": "Dragon_longsword.png"
}
```

**Response:**
```json
{
  "item_id": 1305,
  "name": "Dragon longsword",
  "examine": "A very powerful sword.",
  "members": true,
  "lowalch": 48000,
  "highalch": 72000,
  "limit": 8,
  "value": 60000,
  "icon": "Dragon_longsword.png",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Note:** Embedding is automatically generated from searchable text combining item name, examine text, and members status. The item structure matches the OSRS Wiki API mapping format.

---

### Batch Create Items

#### POST `/api/items/batch`

Create multiple items in a single request. Useful for initial data import.

**Request Body:**
```json
{
  "items": [
    {
      "item_id": 1305,
      "name": "Dragon longsword",
      "examine": "A very powerful sword.",
      "members": true,
      "lowalch": 48000,
      "highalch": 72000,
      "limit": 8,
      "value": 60000,
      "icon": "Dragon_longsword.png"
    },
    {
      "item_id": 4151,
      "name": "Abyssal whip",
      "examine": "A weapon from the abyss.",
      "members": true,
      "lowalch": 72000,
      "highalch": 108000,
      "limit": 8,
      "value": 90000,
      "icon": "Abyssal_whip.png"
    }
  ]
}
```

**Response:**
```json
{
  "created": 2,
  "failed": 0,
  "errors": []
}
```

**Error Handling:**
- Items are processed individually
- Failed items are reported in `errors` array
- Successful items are still created even if some fail

---

### Get Price History

#### GET `/api/items/{item_id}/prices`

Get price history for a specific item.

**Path Parameters:**
- `item_id` (integer, required): OSRS item ID

**Query Parameters:**
- `limit` (integer, optional): Number of price points to return (1-1000, default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "item_id": 1305,
    "timestamp": "2024-01-01T12:00:00",
    "high_price": 60000,
    "low_price": 58000
  },
  {
    "id": 2,
    "item_id": 1305,
    "timestamp": "2024-01-01T11:00:00",
    "high_price": 61000,
    "low_price": 59000
  }
]
```

**Error Responses:**
- `404`: Item not found

---

### Get Current Price

#### GET `/api/items/{item_id}/price/current`

Get the most recent price for a specific item.

**Path Parameters:**
- `item_id` (integer, required): OSRS item ID

**Response:**
```json
{
  "item_id": 1305,
  "name": "Dragon longsword",
  "high_price": 60000,
  "low_price": 58000,
  "timestamp": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404`: Item not found or no price data available

---

## Data Models

### Item Schema

Matches OSRS Wiki API mapping structure:

```typescript
interface Item {
  item_id: number;           // OSRS item ID
  name: string;
  examine: string | null;    // Item examine text (description)
  members: boolean;          // Whether item is members-only
  lowalch: number | null;   // Low alchemy value
  highalch: number | null;  // High alchemy value
  limit: number | null;     // Grand Exchange buy limit
  value: number | null;     // Base item value
  icon: string | null;      // Icon filename
  created_at: string;       // ISO 8601 timestamp
  updated_at: string;       // ISO 8601 timestamp
}
```

### Search Result Schema

```typescript
interface SearchResult {
  item: Item;
  similarity: number;  // 0.0 to 1.0, higher is more similar
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable (database connection issues)

---

## Example Use Cases

### 1. Basic Search

```javascript
// Search for items matching query
const results = await apiClient.searchItems({
  query: "red dragon sword",
  limit: 10
});
```

### 2. Filtered Search

```javascript
// Search with members-only filter
const results = await apiClient.searchItems({
  query: "dragon sword",
  limit: 10,
  members_only: true
});
```

### 3. Free-to-Play Items Only

```javascript
// Search for free-to-play items only
const results = await apiClient.searchItems({
  query: "sword",
  limit: 20,
  members_only: false
});
```

### 4. Vague/Descriptive Queries

```javascript
// Natural language queries work well with semantic search
const results = await apiClient.searchItems({
  query: "powerful melee weapon",
  limit: 10
});
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production:
- Implement rate limiting per IP/user
- Consider caching popular queries
- Monitor API usage

---

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These are automatically generated from the FastAPI code and include:
- Interactive testing interface
- Request/response schemas
- Example requests


