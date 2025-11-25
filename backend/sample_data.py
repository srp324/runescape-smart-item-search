"""
Script to manually trigger item and price update from OSRS API.
This is useful for initial data load or manual updates.
The polling service runs automatically when the FastAPI app starts.
"""

import sys
import os

# Add project root to path for script execution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.polling_service import update_items_and_prices


if __name__ == "__main__":
    print("=" * 60)
    print("OSRS Item and Price Update Script")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Fetch item mapping from OSRS Wiki API")
    print("2. Fetch latest prices from OSRS Wiki API")
    print("3. Update the database with items that have prices")
    print("4. Add price history entries")
    print("\nNote: The polling service runs automatically when the FastAPI app starts.")
    print("This script is for manual updates or initial data load.")
    print("-" * 60)
    print()
    
    try:
        update_items_and_prices()
        print("\n✅ Update completed successfully!")
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        raise

