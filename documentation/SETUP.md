# Setup Guide

Complete setup instructions for the React + Vite web application with FastAPI backend and PostgreSQL vector search.

## Prerequisites

### Required Software

1. **PostgreSQL 12+** with pgvector extension
   - macOS: `brew install postgresql` then `brew install pgvector`
   - Ubuntu: Follow [pgvector installation guide](https://github.com/pgvector/pgvector#installation)
   - Windows: Use PostgreSQL installer + compile pgvector

2. **Python 3.9+**
   - Check: `python --version`

3. **Node.js 18+**
   - Check: `node --version`
   - npm or yarn package manager

## Step-by-Step Setup

### 1. Database Setup

#### Install PostgreSQL

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Install pgvector Extension

**macOS:**
```bash
brew install pgvector
```

**Ubuntu:**
```bash
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Windows:**
Follow [Windows installation instructions](https://github.com/pgvector/pgvector#windows)

#### Create Database

**Note**: `createuser` needs to connect to PostgreSQL first. It will use your current system username by default. If you get a password authentication error, use the `postgres` superuser instead.

**macOS/Linux:**
```bash
# Option 1: Use postgres superuser (recommended)
sudo -u postgres createuser -P game_user  # Set a password when prompted
sudo -u postgres createdb -U postgres -O game_user game_items

# Option 2: If postgres user has a password
createuser -U postgres -P game_user  # Enter postgres password, then game_user password
createdb -U postgres -O game_user game_items
```

**Windows:**
```bash
# Use postgres superuser (default Windows installation)
# You'll be prompted for the postgres user password (set during installation)
createuser -U postgres -P game_user  # Enter postgres password when prompted, then game_user password
createdb -U postgres -O game_user game_items

# Alternative: If you don't know postgres password, use psql as postgres user
psql -U postgres
# Then in psql prompt:
# CREATE USER game_user WITH PASSWORD 'your_password_here';
# CREATE DATABASE game_items OWNER game_user;
# \q
```

**Verify pgvector is available:**
```bash
# macOS/Linux:
sudo -u postgres psql -d game_items -c "CREATE EXTENSION vector;"

# Windows (you'll be prompted for postgres password):
psql -U postgres -d game_items -c "CREATE EXTENSION vector;"
```

**Expected output:**
```
Password for user postgres: [enter your postgres password]
CREATE EXTENSION
```

If you see `CREATE EXTENSION`, the pgvector extension is successfully installed and enabled!

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp env.example .env

# Edit .env file with your database credentials
# DATABASE_URL=postgresql://game_user:your_password@localhost:5432/game_items
```

#### Initialize Database Schema

```bash
# Make sure PostgreSQL is running and DATABASE_URL is set correctly
python init_database.py
```

You should see:
```
✓ pgvector extension enabled
✓ Tables created
✓ Vector index created
✓ Filter indexes created
✅ Database initialization complete!
```

#### Start FastAPI Server

```bash
uvicorn main:app --reload
```

The API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

#### Load Sample Data (Optional)

In another terminal:

```bash
cd backend
source venv/bin/activate  # Activate venv if needed
python sample_data.py
```

### 3. Test Backend

Visit `http://localhost:8000/docs` and try the search endpoint:

```json
POST /api/items/search
{
  "query": "red dragon sword",
  "limit": 10
}
```

You should get search results with similarity scores.

### 4. Web App Setup

```bash
cd web

# Install dependencies
npm install
# or
yarn install

# Start development server
npm run dev
# or
yarn dev
```

The web app will open at `http://localhost:3000` and automatically connect to the backend API at `http://localhost:8000`.

**Note**: If your backend is running on a different URL, update the API base URL in `web/src/apiClient.ts` or set the `VITE_API_URL` environment variable.

## Troubleshooting

### Database Connection Issues

**Error: "connection refused"**
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in `.env` file
- Check firewall settings

**Error: "extension vector does not exist"**
- Install pgvector extension (see step 1)
- Verify installation: `psql -d game_items -c "\dx"`

### Backend Issues

**Error: "Module not found"**
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Error: "Embedding model not loading"**
- First run downloads the model (~80MB for all-MiniLM-L6-v2)
- Check internet connection
- Wait for download to complete

### Web App Issues

**Cannot connect to API**
- Check API URL in `apiClient.ts` or `VITE_API_URL` environment variable
- Verify FastAPI server is running on `http://localhost:8000`
- Check browser console for errors
- Ensure CORS is properly configured in the backend

**CORS errors**
- FastAPI CORS is configured for `http://localhost:3000` by default
- If using a different port, update CORS origins in backend `main.py`
- For production, set `CORS_ORIGINS` environment variable

### Performance Issues

**Slow search queries**
- Ensure vector index is created (check `init_database.py` output)
- Reduce `limit` parameter
- Use smaller embedding model for development

**Slow embedding generation**
- This is normal for first-time item creation
- Consider batch processing for large imports
- Use GPU if available

## Environment Variables Reference

### Backend (.env file)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/game_items

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2  # or all-mpnet-base-v2

# Optional: OpenAI
# OPENAI_API_KEY=your-key-here
```

## Next Steps

1. **Customize Embedding Model**: Edit `EMBEDDING_MODEL` in `.env`
2. **Import Real Data**: The polling service automatically fetches data, or use `/api/items/batch` endpoint
3. **Customize UI**: Modify `web/src/components/SearchScreen.tsx` to match your design
4. **Add Authentication**: Implement JWT tokens for API access (future enhancement)
5. **Deploy**: Follow deployment guides for FastAPI and web application

## Production Checklist

- [ ] Set strong database passwords
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS for API
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Use production PostgreSQL instance
- [ ] Optimize vector index parameters
- [ ] Implement rate limiting
- [ ] Add API authentication

## Support

For issues:
1. Check the troubleshooting section
2. Review error logs in FastAPI console
3. Check PostgreSQL logs
4. Verify all prerequisites are installed

