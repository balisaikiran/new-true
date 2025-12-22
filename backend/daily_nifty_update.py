#!/usr/bin/env python3
"""
Daily script to fetch and update today's NIFTY 50 and NIFTY BANK OHLC data.
This script is designed to be run via cron at 3:35 PM IST daily.
Uses yfinance to fetch all fields: Open, High, Low, Close, Volume, and calculates Change %.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add backend to path so we can import from server
sys.path.insert(0, str(ROOT_DIR))


def get_yfinance_symbol(index_name: str) -> str:
    """Map index name to yfinance symbol"""
    mapping = {
        "NIFTY 50": "^NSEI",
        "NIFTY BANK": "^NSEBANK"
    }
    return mapping.get(index_name, "^NSEI")


def fetch_today_yfinance(index_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch today's OHLC data using yfinance.
    Returns dict with name, date, open, high, low, close, price, volume, change_percent.
    """
    try:
        symbol = get_yfinance_symbol(index_name)
        today = datetime.now()
        
        print(f"  📥 Fetching {index_name} ({symbol}) using yfinance...")
        
        # Fetch last 5 days to ensure we get today's data (or most recent)
        end_date = today.strftime("%Y-%m-%d")
        start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        
        df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if df is None or len(df) == 0:
            # Try previous day if today's data not available yet
            yesterday = today - timedelta(days=1)
            end_date = yesterday.strftime("%Y-%m-%d")
            start_date = (yesterday - timedelta(days=5)).strftime("%Y-%m-%d")
            print(f"  ⚠️ Today's data not available, trying {end_date}...")
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df is not None and len(df) > 0:
                today = yesterday
        
        if df is None or len(df) == 0:
            print(f"  ❌ No data returned from yfinance")
            return None
        
        # Get the last row (most recent data)
        row = df.iloc[-1]
        date_index = df.index[-1]
        
        # Extract OHLC and Volume
        open_val = None
        high_val = None
        low_val = None
        close_val = None
        volume_val = None
        
        try:
            # Access values directly - row is a Series, so we can use .iloc or direct access
            # Convert to scalar if needed
            def safe_float(val):
                if val is None:
                    return None
                try:
                    # If it's a Series, get first value
                    if isinstance(val, pd.Series):
                        val = val.iloc[0] if len(val) > 0 else None
                    # Convert to float
                    if val is not None:
                        fval = float(val)
                        # Check if it's NaN
                        if pd.isna(fval):
                            return None
                        return fval
                    return None
                except (ValueError, TypeError):
                    return None
            
            open_val = safe_float(row.get('Open'))
            high_val = safe_float(row.get('High'))
            low_val = safe_float(row.get('Low'))
            close_val = safe_float(row.get('Close'))
            volume_val = safe_float(row.get('Volume'))
        except Exception as e:
            print(f"  ⚠️ Error extracting values: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        if open_val is not None and high_val is not None and low_val is not None and close_val is not None:
            date_key = date_index.strftime("%Y-%m-%d")
            return {
                "name": index_name,
                "date": date_key,
                "open": round(open_val, 2),
                "high": round(high_val, 2),
                "low": round(low_val, 2),
                "close": round(close_val, 2),
                "price": round(close_val, 2),  # Price = Close
                "volume": int(volume_val) if volume_val else None,
                "source": "yfinance",
                "imported_at": datetime.utcnow().isoformat()
            }
        else:
            print(f"  ⚠️ Incomplete OHLC data: O={open_val}, H={high_val}, L={low_val}, C={close_val}")
            return None
            
    except ImportError:
        print(f"  ❌ yfinance not installed")
        return None
    except Exception as e:
        print(f"  ❌ Error with yfinance: {e}")
        return None


async def get_previous_close(collection, index_name: str, current_date: str) -> Optional[float]:
    """Get previous trading day's close price from MongoDB"""
    try:
        # Find the most recent document before current_date
        prev_doc = await collection.find_one(
            {"name": index_name, "date": {"$lt": current_date}},
            sort=[("date", -1)]
        )
        if prev_doc and prev_doc.get("close"):
            return float(prev_doc["close"])
        return None
    except Exception as e:
        print(f"  ⚠️ Error getting previous close: {e}")
        return None


async def upsert_to_mongodb(collection, doc: Dict[str, Any]) -> bool:
    """Upsert single document to MongoDB with all fields"""
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
        
        # Fetch data using yfinance
        data = None
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_today_yfinance, index_name)
        
        if data:
            # Get previous day's close to calculate change %
            prev_close = await get_previous_close(collection, index_name, data['date'])
            
            if prev_close and data.get('close'):
                # Calculate change percentage: ((current_close - prev_close) / prev_close) * 100
                change_pct = ((data['close'] - prev_close) / prev_close) * 100
                data['change_percent'] = round(change_pct, 2)
                print(f"  📈 Change %: {data['change_percent']:.2f}% (from prev close: {prev_close:.2f})")
            else:
                data['change_percent'] = None
                print(f"  ⚠️ Could not calculate change % (no previous close found)")
            
            # Ensure all required fields are present
            if 'price' not in data:
                data['price'] = data.get('close')
            
            # Upsert to MongoDB
            success = await upsert_to_mongodb(collection, data)
            if success:
                success_count += 1
                vol_str = f", Vol={data['volume']:,}" if data.get('volume') else ""
                change_str = f", Change%={data['change_percent']:.2f}%" if data.get('change_percent') is not None else ""
                print(f"  ✅ Updated {index_name} for {data['date']}: O={data['open']:.2f}, H={data['high']:.2f}, L={data['low']:.2f}, C={data['close']:.2f}{vol_str}{change_str}")
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
    asyncio.run(main())
