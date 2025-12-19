#!/usr/bin/env python3
"""
Daily script to fetch and update today's NIFTY 50 and NIFTY BANK OHLC data.
This script is designed to be run via cron at 3:35 PM IST daily.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add backend to path so we can import from server
sys.path.insert(0, str(ROOT_DIR))


def fetch_today_nsedownload(index_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch today's OHLC data using NSEDownload.
    Returns dict with name, date, open, high, low, close or None if failed.
    """
    try:
        from NSEDownload import indices
        
        today = datetime.now()
        date_str = today.strftime("%d-%m-%Y")
        
        print(f"  📥 Fetching {index_name} for {date_str} using NSEDownload...")
        
        # Fetch today's data
        df = indices.get_data(
            index_name=index_name,
            start_date=date_str,
            end_date=date_str
        )
        
        if df is None or len(df) == 0:
            # Try previous day if today's data not available yet
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime("%d-%m-%Y")
            print(f"  ⚠️ Today's data not available, trying {date_str}...")
            df = indices.get_data(
                index_name=index_name,
                start_date=date_str,
                end_date=date_str
            )
            if df is not None and len(df) > 0:
                today = yesterday
        
        if df is None or len(df) == 0:
            print(f"  ❌ No data returned from NSEDownload")
            return None
        
        # Get the last row (most recent data)
        row = df.iloc[-1]
        
        # Extract OHLC
        open_val = None
        high_val = None
        low_val = None
        close_val = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'open' in col_lower and open_val is None:
                open_val = row[col]
            elif 'high' in col_lower and high_val is None:
                high_val = row[col]
            elif 'low' in col_lower and low_val is None:
                low_val = row[col]
            elif 'close' in col_lower and close_val is None:
                close_val = row[col]
        
        # Try positional if column names don't match
        if open_val is None and len(df.columns) >= 5:
            try:
                open_val = row.iloc[1] if pd.notna(row.iloc[1]) else None
                high_val = row.iloc[2] if pd.notna(row.iloc[2]) else None
                low_val = row.iloc[3] if pd.notna(row.iloc[3]) else None
                close_val = row.iloc[4] if pd.notna(row.iloc[4]) else None
            except:
                pass
        
        def safe_float(val):
            if val is None:
                return None
            try:
                if isinstance(val, str):
                    val = val.replace(',', '').strip()
                return float(val)
            except:
                return None
        
        open_val = safe_float(open_val)
        high_val = safe_float(high_val)
        low_val = safe_float(low_val)
        close_val = safe_float(close_val)
        
        if all([open_val, high_val, low_val, close_val]):
            date_key = today.strftime("%Y-%m-%d")
            return {
                "name": index_name,
                "date": date_key,
                "open": round(open_val, 2),
                "high": round(high_val, 2),
                "low": round(low_val, 2),
                "close": round(close_val, 2),
                "source": "NSEDownload",
                "imported_at": datetime.utcnow().isoformat()
            }
        else:
            print(f"  ⚠️ Incomplete OHLC data: O={open_val}, H={high_val}, L={low_val}, C={close_val}")
            return None
            
    except ImportError:
        print(f"  ❌ NSEDownload not installed")
        return None
    except Exception as e:
        print(f"  ❌ Error with NSEDownload: {e}")
        return None


async def fetch_today_via_api(index_name: str) -> Optional[Dict[str, Any]]:
    """
    Fallback: Fetch today's data using the server's fetch_nifty_ohlc_from_truedata function.
    """
    try:
        from server import fetch_nifty_ohlc_from_truedata
        
        # Get token from database if available
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        
        token = None
        if mongo_url and db_name:
            try:
                mongo_url = mongo_url.strip('"').strip("'")
                db_name = db_name.strip('"').strip("'")
                if "?" not in mongo_url:
                    mongo_url += "?tlsAllowInvalidCertificates=true"
                elif "tlsAllowInvalidCertificates" not in mongo_url:
                    mongo_url += "&tlsAllowInvalidCertificates=true"
                
                client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
                db = client[db_name]
                token_doc = await db.tokens.find_one(sort=[("created_at", -1)])
                if token_doc and token_doc.get("access_token"):
                    token = token_doc.get("access_token")
                client.close()
            except:
                pass
        
        print(f"  📥 Fetching {index_name} via API fallback...")
        data = await fetch_nifty_ohlc_from_truedata(index_name, token)
        
        if data:
            return {
                "name": index_name,
                "date": data.get("date"),
                "open": data.get("open"),
                "high": data.get("high"),
                "low": data.get("low"),
                "close": data.get("close"),
                "source": data.get("source", "API"),
                "imported_at": datetime.utcnow().isoformat()
            }
        
        return None
    except Exception as e:
        print(f"  ❌ Error with API fallback: {e}")
        return None


async def upsert_to_mongodb(collection, doc: Dict[str, Any]) -> bool:
    """Upsert single document to MongoDB"""
    try:
        result = await collection.update_one(
            {"name": doc["name"], "date": doc["date"]},
            {"$set": doc},
            upsert=True
        )
        return result.upserted_id is not None or result.modified_count > 0
    except Exception as e:
        print(f"  ❌ MongoDB error: {e}")
        return False


async def main():
    """Main function to fetch and update today's NIFTY data"""
    print(f"🕐 Daily NIFTY Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # MongoDB connection
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    
    if not mongo_url or not db_name:
        print("❌ MONGO_URL and DB_NAME must be set in .env file")
        sys.exit(1)
    
    mongo_url = mongo_url.strip('"').strip("'")
    db_name = db_name.strip('"').strip("'")
    
    if "?" not in mongo_url:
        mongo_url += "?tlsAllowInvalidCertificates=true"
    elif "tlsAllowInvalidCertificates" not in mongo_url:
        mongo_url += "&tlsAllowInvalidCertificates=true"
    
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
    db = client[db_name]
    collection = db.nifty_data
    
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        sys.exit(1)
    
    indices = ["NIFTY 50", "NIFTY BANK"]
    success_count = 0
    
    for index_name in indices:
        print(f"\n📊 Processing {index_name}...")
        
        # Try NSEDownload first
        data = None
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_today_nsedownload, index_name)
        
        # Fallback to API if NSEDownload failed
        if not data:
            print(f"  ⚠️ NSEDownload failed, trying API fallback...")
            data = await fetch_today_via_api(index_name)
        
        if data:
            success = await upsert_to_mongodb(collection, data)
            if success:
                success_count += 1
                print(f"  ✅ Updated {index_name} for {data['date']}: O={data['open']:.2f}, H={data['high']:.2f}, L={data['low']:.2f}, C={data['close']:.2f}")
            else:
                print(f"  ❌ Failed to save {index_name} to MongoDB")
        else:
            print(f"  ❌ Could not fetch data for {index_name}")
    
    print(f"\n🏁 Done! Successfully updated {success_count}/{len(indices)} indices")
    client.close()
    
    # Exit with error code if no data was updated
    if success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    import pandas as pd  # NSEDownload uses pandas
    asyncio.run(main())
