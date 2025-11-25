# RuneScape Smart Item Search

A semantic search application for Old School RuneScape (OSRS) items using vector embeddings. Available as a **web application** that works on all desktop platforms.

## 🎯 Features

- **Semantic Search**: Find OSRS items using natural language queries
- **Real-time Price Updates**: Automatically fetches item prices from OSRS Wiki API every minute
- **Price History**: Track price changes over time
- **Vector Embeddings**: Uses pgvector for efficient similarity search
- **Web Interface**: Responsive React web app that works on Windows, macOS, and Linux

## 📁 Project Structure

```
runescape-smart-item-search/
├── backend/          # FastAPI backend with PostgreSQL + pgvector
├── web/              # React + Vite web app
├── documentation/    # Documentation files and diagrams
└── README.md         # This file
```

## 🚀 Quick Start

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure database:**
   - Create a `.env` file based on `env.example`
   - Set your `DATABASE_URL` for PostgreSQL

3. **Initialize database:**
   ```bash
   python init_database.py
   ```

4. **Start the server:**
   ```bash
   uvicorn main:app --reload
   ```
   The server will run at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Polling service starts automatically and updates items every minute

### Web App Setup

1. **Install dependencies:**
   ```bash
   cd web
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```
   Opens at `http://localhost:3000`

## 🌐 Platform Support

### ✅ Web Application
- **Technology**: React + Vite + TypeScript
- **Platforms**: Windows, macOS, Linux
- **Browser**: Any modern browser (Chrome, Firefox, Safari, Edge)
- **Location**: `web/` directory
- **Responsive**: Works on desktop and tablet screens

## 🔧 Configuration

### Backend
- Database: PostgreSQL with pgvector extension
- API: FastAPI
- Polling: Updates from OSRS Wiki API every minute
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)

### API Endpoints
- `POST /api/items/search` - Semantic search
- `GET /api/items/{item_id}` - Get item details
- `GET /api/items/{item_id}/prices` - Price history
- `GET /api/items/{item_id}/price/current` - Current price
- `GET /health` - Health check

## 📚 Documentation

- [API Reference](documentation/API_REFERENCE.md)
- [Architecture](documentation/ARCHITECTURE.md)
- [Architecture Diagram](documentation/ARCHITECTURE_DIAGRAM.md)
- [Embedding & Vector Store Overview](documentation/embedding_vector_store_overview.mmd)
- [Embedding & Vector Store Diagram](documentation/EMBEDDING_VECTOR_STORE_DIAGRAM.md)
- [Setup Guide](documentation/SETUP.md) - Local development setup
- [Quick Deploy Guide](documentation/QUICK_DEPLOY.md) - Fast deployment options
- [Deployment Guide](documentation/DEPLOYMENT.md) - Complete production deployment guide

## 🛠️ Development

### Backend
- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- FastAPI, SQLAlchemy, sentence-transformers

### Frontend (Web)
- Node.js 18+
- React 18
- Vite
- TypeScript

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]
