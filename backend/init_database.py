"""
Database initialization script.
Run this once to set up the database schema and pgvector extension.
"""

from sqlalchemy import text
import sys
import os

# Ensure we import the same modules that the app uses at runtime
# (__file__ is .../backend/init_database.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root or /app
backend_root = os.path.join(project_root, "backend")

# Add backend directory to sys.path so we can import `database` and `models`
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from database import engine, Base  # shared Base / engine with the app
from models import Item, PriceHistory  # registers models on that same Base


def init_database():
    """
    Initialize the database:
    1. Enable pgvector extension
    2. Create all tables (game_items and price_history)
    3. Create indexes
    """
    print("Initializing database...")
    # Show which database URL we're actually using (password is hidden by SQLAlchemy)
    try:
        from database import DATABASE_URL  # type: ignore
        print(f"Raw DATABASE_URL from environment: {DATABASE_URL}")
    except Exception:
        # Fallback: print engine URL (already sanitized by SQLAlchemy)
        print(f"Effective SQLAlchemy URL: {engine.url}")
    
    # Enable pgvector extension
    with engine.connect() as conn:
        print("Enabling pgvector extension...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✓ pgvector extension enabled")
    
    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created (game_items, price_history)")
    
    # Create indexes
    with engine.connect() as conn:
        print("Creating indexes...")
        
        # Vector similarity index (IVFFlat) for game_items
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS game_items_embedding_idx ON game_items 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """))
            print("✓ Vector index created for game_items")
        except Exception as e:
            print(f"⚠ Could not create vector index (may already exist): {e}")
        
        # Standard indexes for game_items
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_game_items_name ON game_items(name);
                CREATE INDEX IF NOT EXISTS idx_game_items_members ON game_items(members);
                CREATE INDEX IF NOT EXISTS idx_game_items_item_id ON game_items(item_id);
            """))
            print("✓ Filter indexes created for game_items")
        except Exception as e:
            print(f"⚠ Could not create filter indexes: {e}")
        
        # Indexes for price_history
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_price_history_item_id ON price_history(item_id);
                CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_price_history_item_timestamp ON price_history(item_id, timestamp DESC);
            """))
            print("✓ Indexes created for price_history")
        except Exception as e:
            print(f"⚠ Could not create price_history indexes: {e}")
        
        conn.commit()
    
    print("\n✅ Database initialization complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("   (The polling service will start automatically and update items every minute)")
    print("2. Or manually trigger update: python sample_data.py")
    print("3. Test search using the /api/items/search endpoint")
    print("4. View price history: GET /api/items/{item_id}/prices")


if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        print("\nMake sure:")
        print("- PostgreSQL is running")
        print("- pgvector extension is installed in PostgreSQL")
        print("- DATABASE_URL environment variable is set correctly")
        raise

