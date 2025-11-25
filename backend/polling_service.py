"""
Polling service to fetch OSRS item data and prices from the Wiki API.
Runs every minute to keep the database updated.
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import SessionLocal
from models import Item, PriceHistory
from embeddings import get_embedding_service, create_searchable_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OSRS Wiki API endpoints
MAPPING_API_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"
LATEST_PRICES_API_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"

# User agent for API requests (required by OSRS Wiki API)
USER_AGENT = "RuneScape-Smart-Item-Search/1.0 (https://github.com/yourusername/runescape-smart-item-search)"


def fetch_item_mapping() -> List[Dict]:
    """
    Fetch item mapping data from OSRS Wiki API.
    
    Returns:
        List of item dictionaries from the API
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(MAPPING_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch item mapping: {e}")
        return []


def fetch_latest_prices() -> Dict[int, Dict]:
    """
    Fetch latest prices from OSRS Wiki API.
    
    Returns:
        Dictionary mapping item_id to price data {high, low}
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(LATEST_PRICES_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Transform the response to a more usable format
        # API returns: {"data": {item_id: {"high": x, "low": y, ...}, ...}}
        prices = {}
        if "data" in data:
            for item_id_str, price_data in data["data"].items():
                try:
                    item_id = int(item_id_str)
                    high = price_data.get("high")
                    low = price_data.get("low")
                    # Only include if at least one price exists
                    if high is not None or low is not None:
                        prices[item_id] = {
                            "high": high,
                            "low": low
                        }
                except (ValueError, KeyError):
                    continue
        return prices
    except Exception as e:
        logger.error(f"Failed to fetch latest prices: {e}")
        return {}


def update_items_and_prices():
    """
    Main function to update items and prices in the database.
    Fetches from both APIs and only stores items that have prices.
    """
    logger.info("Starting item and price update...")
    
    # Fetch data from APIs
    mapping_data = fetch_item_mapping()
    prices_data = fetch_latest_prices()
    
    if not mapping_data:
        logger.warning("No mapping data received, skipping update")
        return
    
    if not prices_data:
        logger.warning("No price data received, skipping update")
        return
    
    db: Session = SessionLocal()
    embedding_service = get_embedding_service()
    
    try:
        items_updated = 0
        items_created = 0
        prices_added = 0
        items_skipped = 0
        embeddings_generated = 0
        
        # First pass: collect items that need processing and embeddings
        items_to_process = []
        items_needing_embeddings = []
        searchable_texts_for_embedding = []
        item_indices_for_embedding = []  # Track which items need embeddings
        
        for item_data in mapping_data:
            item_id = item_data.get("id")
            
            # Skip if item doesn't have an ID
            if not item_id:
                continue
            
            # Only process items that have prices
            if item_id not in prices_data:
                items_skipped += 1
                continue
            
            price_info = prices_data[item_id]
            
            # Skip if both high and low prices are None
            if price_info.get("high") is None and price_info.get("low") is None:
                items_skipped += 1
                continue
            
            # Check if item exists
            existing_item = db.query(Item).filter(Item.item_id == item_id).first()
            
            # Prepare item data
            item_dict = {
                "item_id": item_id,
                "name": item_data.get("name", ""),
                "examine": item_data.get("examine"),
                "members": item_data.get("members", False),
                "lowalch": item_data.get("lowalch"),
                "highalch": item_data.get("highalch"),
                "limit": item_data.get("limit"),
                "value": item_data.get("value"),
                "icon": item_data.get("icon"),
                "existing_item": existing_item,
                "price_info": price_info
            }
            
            # Check if embedding is needed
            needs_embedding = False
            if not existing_item:
                needs_embedding = True
            elif (existing_item.name != item_dict["name"] or 
                  existing_item.examine != item_dict["examine"]):
                needs_embedding = True
            
            if needs_embedding:
                searchable_text = create_searchable_text(item_dict)
                searchable_texts_for_embedding.append(searchable_text)
                item_indices_for_embedding.append(len(items_to_process))
            
            items_to_process.append(item_dict)
        
        # Generate embeddings in batches of 500
        if searchable_texts_for_embedding:
            total_embeddings = len(searchable_texts_for_embedding)
            logger.info(f"Generating embeddings for {total_embeddings} items in batches of 500...")
            
            batch_size = 500
            for batch_start in range(0, total_embeddings, batch_size):
                batch_end = min(batch_start + batch_size, total_embeddings)
                batch_texts = searchable_texts_for_embedding[batch_start:batch_end]
                batch_indices = item_indices_for_embedding[batch_start:batch_end]
                
                logger.info(f"Processing embedding batch {batch_start // batch_size + 1}/{(total_embeddings + batch_size - 1) // batch_size} ({batch_end - batch_start} items)...")
                
                try:
                    batch_embeddings = embedding_service.embed_texts(batch_texts)
                    
                    # Assign embeddings to items
                    for idx, embedding in zip(batch_indices, batch_embeddings):
                        items_to_process[idx]["embedding"] = embedding
                        embeddings_generated += 1
                    
                    logger.info(f"✓ Generated {len(batch_embeddings)} embeddings in this batch")
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch starting at {batch_start}: {e}")
                    # Set None for failed batch
                    for idx in batch_indices:
                        items_to_process[idx]["embedding"] = None
        
        # Second pass: create/update items and add price history
        for item_dict in items_to_process:
            existing_item = item_dict.pop("existing_item")
            price_info = item_dict.pop("price_info")
            
            # Create or update item
            if existing_item:
                # Update existing item
                for key, value in item_dict.items():
                    if key != "item_id":  # Don't update the primary key
                        setattr(existing_item, key, value)
                items_updated += 1
            else:
                # Create new item
                db_item = Item(**item_dict)
                db.add(db_item)
                items_created += 1
            
            # Add price history entry
            price_entry = PriceHistory(
                item_id=item_dict["item_id"],
                high_price=price_info.get("high"),
                low_price=price_info.get("low"),
                timestamp=datetime.utcnow()
            )
            db.add(price_entry)
            prices_added += 1
        
        # Commit all changes
        db.commit()
        
        logger.info(
            f"Update complete: {items_created} created, {items_updated} updated, "
            f"{prices_added} prices added, {embeddings_generated} embeddings generated, "
            f"{items_skipped} items skipped (no prices)"
        )
        
    except Exception as e:
        logger.error(f"Error updating items and prices: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def run_polling_loop():
    """
    Run the polling service continuously, updating every minute.
    This function runs in a background thread.
    """
    import time
    import traceback
    
    logger.info("=" * 60)
    logger.info("Starting polling service (updates every minute)...")
    logger.info("=" * 60)
    
    # Run initial update immediately
    logger.info("Running initial update...")
    try:
        update_items_and_prices()
        logger.info("Initial update completed successfully")
    except Exception as e:
        logger.error(f"Error in initial update: {e}")
        logger.error(traceback.format_exc())
    
    # Then continue with regular polling every 60 seconds
    while True:
        try:
            logger.info("Waiting 60 seconds before next update...")
            time.sleep(60)
            logger.info("Starting scheduled update...")
            update_items_and_prices()
            logger.info("Scheduled update completed successfully")
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            logger.error(traceback.format_exc())
            # Wait before retrying even on error
            time.sleep(60)


if __name__ == "__main__":
    # Run once for testing
    update_items_and_prices()

