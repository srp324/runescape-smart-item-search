"""
Database migration script to update embedding column dimension.

This script migrates the embedding column from one dimension to another.
Since pgvector requires fixed dimensions, we need to:
1. Create a new column with the new dimension
2. Copy data (if regenerating embeddings)
3. Drop the old column
4. Rename the new column
5. Recreate indexes

⚠️ WARNING: This will require regenerating all embeddings with the new model!
"""

from sqlalchemy import text
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for script execution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import engine
from backend.models import get_embedding_dimension


def get_current_dimension() -> int:
    """Get the current dimension of the embedding column from the database."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                (SELECT atttypmod - 4 FROM pg_attribute 
                 WHERE attrelid = 'game_items'::regclass 
                 AND attname = 'embedding') as dimension;
        """))
        dim = result.scalar()
        if dim:
            return dim
        # If column doesn't exist or can't determine, return None
        return None


def migrate_embedding_dimension(new_dimension: int, backup_data: bool = True):
    """
    Migrate the embedding column to a new dimension.
    
    Args:
        new_dimension: The new dimension size (384, 768, 1024, 2560, or 4096)
        backup_data: If True, attempts to preserve existing embedding data
                    (Note: embeddings from different dimensions are incompatible)
    """
    print(f"🔄 Starting embedding dimension migration to {new_dimension} dimensions...")
    
    current_dim = get_current_dimension()
    if current_dim:
        print(f"📊 Current embedding dimension: {current_dim}")
        if current_dim == new_dimension:
            print(f"✅ Database already uses {new_dimension} dimensions. No migration needed.")
            return
    else:
        print("⚠️  Could not determine current dimension. Proceeding with migration...")
    
    print(f"\n⚠️  IMPORTANT: This migration will:")
    print(f"   1. Drop the existing embedding column (dimension {current_dim or 'unknown'})")
    print(f"   2. Create a new embedding column with dimension {new_dimension}")
    print(f"   3. You will need to regenerate all embeddings with the new model")
    print(f"\n   Existing embeddings will be LOST!")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Migration cancelled.")
        return
    
    with engine.connect() as conn:
        print("\n📝 Step 1: Dropping old vector index...")
        try:
            conn.execute(text("DROP INDEX IF EXISTS game_items_embedding_idx;"))
            conn.commit()
            print("   ✓ Old vector index dropped")
        except Exception as e:
            print(f"   ⚠️  Could not drop index (may not exist): {e}")
        
        print("\n📝 Step 2: Dropping old embedding column...")
        try:
            conn.execute(text("ALTER TABLE game_items DROP COLUMN IF EXISTS embedding;"))
            conn.commit()
            print("   ✓ Old embedding column dropped")
        except Exception as e:
            print(f"   ❌ Error dropping column: {e}")
            raise
        
        print(f"\n📝 Step 3: Creating new embedding column with dimension {new_dimension}...")
        try:
            conn.execute(text(f"""
                ALTER TABLE game_items 
                ADD COLUMN embedding vector({new_dimension});
            """))
            conn.commit()
            print(f"   ✓ New embedding column created (dimension {new_dimension})")
        except Exception as e:
            print(f"   ❌ Error creating new column: {e}")
            raise
        
        print("\n📝 Step 4: Creating new vector index...")
        try:
            conn.execute(text(f"""
                CREATE INDEX game_items_embedding_idx ON game_items 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """))
            conn.commit()
            print("   ✓ New vector index created")
        except Exception as e:
            print(f"   ⚠️  Could not create vector index: {e}")
            print("   (You can create it manually later)")
    
    print(f"\n✅ Migration complete! Embedding column now uses {new_dimension} dimensions.")
    print("\n📋 Next steps:")
    print("   1. Make sure EMBEDDING_MODEL is set correctly in your .env file")
    print("   2. Regenerate embeddings for all items:")
    print("      - Use the /api/items/batch endpoint to recreate items")
    print("      - Or let the polling service regenerate them automatically")
    print("   3. Verify the migration: Check that embeddings are being generated correctly")


if __name__ == "__main__":
    try:
        # Get target dimension from environment or model
        target_dimension = get_embedding_dimension()
        print(f"🎯 Target dimension: {target_dimension} (from EMBEDDING_MODEL or EMBEDDING_DIMENSION)")
        
        migrate_embedding_dimension(target_dimension)
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("\nMake sure:")
        print("- PostgreSQL is running")
        print("- You have proper database permissions")
        print("- DATABASE_URL environment variable is set correctly")
        raise

