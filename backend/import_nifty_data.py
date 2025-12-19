#!/usr/bin/env python3
"""
Script to import Nifty historical data from Google Sheets to MongoDB.
Usage: python import_nifty_data.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import pandas as pd
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Google Sheets URL
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/18Ybife1vGGxLfrlEeYUdpsGhjzIwLRmTYgMd3GYgHbk/export?format=csv&gid=1234653346"

# MongoDB connection
client = None
db = None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in format '1-Sep-10' to datetime"""
    try:
        # Try parsing formats like "1-Sep-10", "10-Sep-10", etc.
        return datetime.strptime(date_str, "%d-%b-%y")
    except ValueError:
        try:
            # Try alternative format
            return datetime.strptime(date_str, "%d-%B-%y")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None


async def fetch_google_sheets_data() -> pd.DataFrame:
    """Fetch data from Google Sheets as CSV"""
    try:
        logger.info(f"Fetching data from Google Sheets...")
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_client:
            response = await http_client.get(GOOGLE_SHEETS_URL)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            logger.info(f"Fetched {len(df)} rows from Google Sheets")
            return df
    except Exception as e:
        logger.error(f"Error fetching Google Sheets data: {str(e)}")
        raise


def safe_float(value) -> Optional[float]:
    """Safely convert value to float, handling strings, None, NaN, etc."""
    if value is None:
        return None
    
    # Convert to string first to handle various types
    str_val = str(value).strip()
    
    # Check for NaN or empty strings
    if not str_val or str_val.lower() in ['nan', 'none', 'null', '', '-', 'n/a', 'na']:
        return None
    
    try:
        # Remove any commas or other formatting
        str_val = str_val.replace(',', '').replace(' ', '')
        return float(str_val)
    except (ValueError, TypeError):
        return None


def process_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process DataFrame and convert to list of documents"""
    documents = []
    skipped_rows = []
    
    # Expected columns: Date, Open, High, Low, Close
    # Handle case-insensitive column names
    df.columns = df.columns.str.strip()
    
    # Map column names (case-insensitive)
    date_col = None
    open_col = None
    high_col = None
    low_col = None
    close_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'date' in col_lower:
            date_col = col
        elif 'open' in col_lower:
            open_col = col
        elif 'high' in col_lower:
            high_col = col
        elif 'low' in col_lower:
            low_col = col
        elif 'close' in col_lower:
            close_col = col
    
    if not date_col:
        raise ValueError("Date column not found in CSV")
    
    logger.info(f"Using columns: Date={date_col}, Open={open_col}, High={high_col}, Low={low_col}, Close={close_col}")
    logger.info(f"Total rows in CSV: {len(df)}")
    
    for idx, row in df.iterrows():
        try:
            # Get date value
            date_val = row[date_col]
            date_str = str(date_val).strip() if pd.notna(date_val) else ""
            
            # Skip header row or invalid date strings
            if not date_str or date_str.lower() in ['nan', 'none', 'null', '', 'date', 'date ']:
                skipped_rows.append((idx, "Invalid or empty date"))
                continue
            
            # Parse date - try multiple formats
            date_obj = parse_date(date_str)
            if not date_obj:
                # Try additional date formats
                try:
                    # Try DD-MM-YYYY format
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                except ValueError:
                    try:
                        # Try YYYY-MM-DD format
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        skipped_rows.append((idx, f"Could not parse date: {date_str}"))
                        continue
            
            # Extract OHLC values - always try to convert, even if string
            open_val = safe_float(row[open_col]) if open_col else None
            high_val = safe_float(row[high_col]) if high_col else None
            low_val = safe_float(row[low_col]) if low_col else None
            close_val = safe_float(row[close_col]) if close_col else None
            
            # Only skip if ALL values are None (including date)
            # If we have a valid date, we should store the record even if some OHLC are None
            if date_obj:
                document = {
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "date_obj": date_obj,
                    "open": open_val,
                    "high": high_val,
                    "low": low_val,
                    "close": close_val,
                    "imported_at": datetime.utcnow().isoformat()
                }
                
                documents.append(document)
            else:
                skipped_rows.append((idx, "No valid date"))
            
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {str(e)}")
            skipped_rows.append((idx, str(e)))
            continue
    
    logger.info(f"Processed {len(documents)} valid documents")
    if skipped_rows:
        logger.info(f"Skipped {len(skipped_rows)} rows (showing first 10 reasons):")
        for idx, reason in skipped_rows[:10]:
            logger.info(f"  Row {idx}: {reason}")
    
    return documents


async def import_to_mongodb(documents: List[Dict[str, Any]], clear_existing: bool = False):
    """Import documents to MongoDB collection 'nifty_data'"""
    if db is None:
        raise ValueError("MongoDB not initialized")
    
    try:
        collection = db.nifty_data
        
        # Clear existing data if requested
        if clear_existing:
            await collection.delete_many({})
            logger.info("Cleared existing nifty_data collection")
        
        # Insert documents with upsert based on date
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                date_str = doc["date"]
                # Remove date_obj before inserting (MongoDB will store date as string)
                doc_to_insert = {k: v for k, v in doc.items() if k != "date_obj"}
                
                # Use $set to update all fields, ensuring exact values are preserved
                result = await collection.update_one(
                    {"date": date_str},
                    {"$set": doc_to_insert},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                error_count += 1
                logger.warning(f"Error inserting document for date {doc.get('date')}: {str(e)}")
        
        logger.info(f"Import complete: {inserted_count} inserted, {updated_count} updated, {error_count} errors")
        
        # Get total count
        total_count = await collection.count_documents({})
        logger.info(f"Total documents in nifty_data collection: {total_count}")
        
        return {
            "success": True,
            "inserted": inserted_count,
            "updated": updated_count,
            "errors": error_count,
            "total": total_count
        }
        
    except Exception as e:
        logger.error(f"Error importing to MongoDB: {str(e)}")
        raise


async def main():
    """Main function"""
    global client, db
    
    # Get MongoDB connection details
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        logger.error("MONGO_URL and DB_NAME environment variables must be set")
        sys.exit(1)
    
    # Initialize MongoDB connection
    try:
        logger.info(f"Connecting to MongoDB database: {db_name}")
        mongo_url = mongo_url.strip('"').strip("'")
        db_name = db_name.strip('"').strip("'")
        
        # Add SSL certificate bypass if needed
        if '?' not in mongo_url:
            mongo_url += '?tlsAllowInvalidCertificates=true'
        elif 'tlsAllowInvalidCertificates' not in mongo_url:
            mongo_url += '&tlsAllowInvalidCertificates=true'
        
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        sys.exit(1)
    
    try:
        # Fetch data from Google Sheets
        df = await fetch_google_sheets_data()
        
        # Process DataFrame
        documents = process_dataframe(df)
        
        if not documents:
            logger.warning("No valid documents to import")
            return
        
        # Import to MongoDB WITHOUT clearing existing data
        # This will backfill / fix missing days while keeping any extra records
        logger.info("Importing to MongoDB (upserting, without clearing existing data)...")
        result = await import_to_mongodb(documents, clear_existing=False)
        
        logger.info("✅ Import completed successfully!")
        logger.info(f"   Inserted: {result['inserted']}")
        logger.info(f"   Updated: {result['updated']}")
        logger.info(f"   Total: {result['total']}")
        
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    asyncio.run(main())

