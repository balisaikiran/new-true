#!/usr/bin/env python3
"""
Standalone script to refresh today's NIFTY data.
Can be called manually or integrated into other scripts/cron jobs.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging

# Add parent directory to path to import server functions
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Load environment variables
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import server functions
try:
    from server import (
        fetch_nifty_ohlc_from_truedata,
        save_nifty_data_to_db,
        db
    )
except ImportError as e:
    logger.error(f"Failed to import server functions: {e}")
    logger.error("Make sure you're running this from the backend directory")
    sys.exit(1)


async def refresh_today_nifty_data(
    index_name: Optional[str] = None,
    mongo_url: Optional[str] = None,
    db_name: Optional[str] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Refresh today's NIFTY data for the specified index (or both if not specified).
    
    Args:
        index_name: "NIFTY 50" or "NIFTY BANK". If None, refreshes both.
        mongo_url: MongoDB connection URL (optional, uses env var if not provided)
        db_name: Database name (optional, uses env var if not provided)
        token: TrueData API token (optional, uses DB if not provided)
    
    Returns:
        Dictionary with success status and results
    """
    # Initialize MongoDB connection if not already connected
    client = None
    local_db = None
    
    try:
        # Use provided MongoDB connection or create new one
        if db is None:
            if not mongo_url:
                mongo_url = os.environ.get('MONGO_URL')
            if not db_name:
                db_name = os.environ.get('DB_NAME')
            
            if not mongo_url or not db_name:
                raise ValueError("MongoDB connection details not provided. Set MONGO_URL and DB_NAME environment variables.")
            
            # Strip quotes from environment variables if present
            mongo_url = mongo_url.strip('"').strip("'")
            db_name = db_name.strip('"').strip("'")
            
            # Add SSL certificate bypass for development
            if '?' not in mongo_url:
                mongo_url += '?tlsAllowInvalidCertificates=true'
            elif 'tlsAllowInvalidCertificates' not in mongo_url:
                mongo_url += '&tlsAllowInvalidCertificates=true'
            
            logger.info(f"Connecting to MongoDB: {db_name}")
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
            local_db = client[db_name]
        else:
            local_db = db
        
        # Get token from database if not provided
        if not token and local_db:
            token_doc = await local_db.tokens.find_one(sort=[("created_at", -1)])
            token = token_doc.get("access_token") if token_doc else None
        
        # Determine which indices to refresh
        if index_name:
            if index_name not in ["NIFTY 50", "NIFTY BANK"]:
                raise ValueError(f"Invalid index name: {index_name}. Must be 'NIFTY 50' or 'NIFTY BANK'")
            indices_to_refresh = [index_name]
        else:
            indices_to_refresh = ["NIFTY 50", "NIFTY BANK"]
        
        # Get today's date
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        
        logger.info(f"🔄 Refreshing today's NIFTY data (date: {today_str})...")
        logger.info(f"   Indices to refresh: {', '.join(indices_to_refresh)}")
        
        results = {}
        
        for idx_name in indices_to_refresh:
            logger.info(f"\n📊 Processing {idx_name}...")
            
            try:
                # Temporarily set db in server module if using local connection
                if local_db and db is None:
                    import server
                    server.db = local_db
                
                # Fetch today's data
                index_data = await fetch_nifty_ohlc_from_truedata(idx_name, token)
                
                if index_data:
                    # Ensure the date is set to today
                    index_data["date"] = today_str
                    index_data["name"] = idx_name
                    
                    # Save/update in database
                    success = await save_nifty_data_to_db(index_data)
                    
                    if success:
                        results[idx_name] = {
                            "status": "success",
                            "message": f"Successfully refreshed {idx_name} data for {today_str}",
                            "data": {
                                "date": index_data["date"],
                                "open": index_data.get("open"),
                                "high": index_data.get("high"),
                                "low": index_data.get("low"),
                                "close": index_data.get("close"),
                                "price": index_data.get("price"),
                                "volume": index_data.get("volume"),
                                "source": index_data.get("source", "unknown")
                            }
                        }
                        logger.info(f"✅ Successfully refreshed {idx_name}")
                        logger.info(f"   O={index_data.get('open')}, H={index_data.get('high')}, "
                                  f"L={index_data.get('low')}, C={index_data.get('close')}")
                    else:
                        results[idx_name] = {
                            "status": "error",
                            "message": f"Failed to save {idx_name} data to database"
                        }
                        logger.error(f"❌ Failed to save {idx_name} data to database")
                else:
                    results[idx_name] = {
                        "status": "error",
                        "message": f"Failed to fetch {idx_name} data from any source"
                    }
                    logger.error(f"❌ Failed to fetch {idx_name} data from any source")
                    
            except Exception as e:
                logger.error(f"Error refreshing {idx_name} data: {str(e)}", exc_info=True)
                results[idx_name] = {
                    "status": "error",
                    "message": f"Error refreshing {idx_name} data: {str(e)}"
                }
        
        # Determine overall success
        all_success = all(r.get("status") == "success" for r in results.values())
        
        return {
            "success": all_success,
            "message": f"Refresh completed for {len(indices_to_refresh)} index(es)",
            "date": today_str,
            "results": results
        }
        
    finally:
        # Close MongoDB connection if we created it
        if client:
            client.close()
            logger.info("Closed MongoDB connection")


async def main():
    """Main entry point for the script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Refresh today's NIFTY data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Refresh both indices
  python refresh_today_nifty.py
  
  # Refresh only NIFTY 50
  python refresh_today_nifty.py --index "NIFTY 50"
  
  # Refresh only NIFTY BANK
  python refresh_today_nifty.py --index "NIFTY BANK"
  
  # Use custom MongoDB connection
  python refresh_today_nifty.py --mongo-url "mongodb://..." --db-name "mydb"
        """
    )
    
    parser.add_argument(
        "--index",
        type=str,
        choices=["NIFTY 50", "NIFTY BANK"],
        help="Index name to refresh (default: both)"
    )
    
    parser.add_argument(
        "--mongo-url",
        type=str,
        help="MongoDB connection URL (default: from MONGO_URL env var)"
    )
    
    parser.add_argument(
        "--db-name",
        type=str,
        help="Database name (default: from DB_NAME env var)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="TrueData API token (default: from database)"
    )
    
    args = parser.parse_args()
    
    try:
        result = await refresh_today_nifty_data(
            index_name=args.index,
            mongo_url=args.mongo_url,
            db_name=args.db_name,
            token=args.token
        )
        
        print("\n" + "=" * 60)
        print("📊 REFRESH SUMMARY")
        print("=" * 60)
        print(f"Date: {result['date']}")
        print(f"Overall Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        print(f"Message: {result['message']}")
        print("\nResults:")
        
        for index_name, index_result in result['results'].items():
            status_icon = "✅" if index_result['status'] == 'success' else "❌"
            print(f"\n{status_icon} {index_name}:")
            print(f"   Status: {index_result['status']}")
            print(f"   Message: {index_result['message']}")
            
            if index_result['status'] == 'success' and 'data' in index_result:
                data = index_result['data']
                print(f"   Data: O={data.get('open')}, H={data.get('high')}, "
                      f"L={data.get('low')}, C={data.get('close')}")
                print(f"   Source: {data.get('source', 'unknown')}")
        
        print("\n" + "=" * 60)
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

