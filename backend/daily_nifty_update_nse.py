#!/usr/bin/env python3
"""
Daily script to fetch and update today's NIFTY 50 and NIFTY BANK OHLC data.
Run at 4:00 PM IST.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import pytz 

import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add backend to path so we can import from server
sys.path.insert(0, str(ROOT_DIR))

# --- CONSTANTS ---
IST = pytz.timezone('Asia/Kolkata')

def get_ist_today_str():
    """Get today's date in IST as YYYY-MM-DD"""
    return datetime.now(IST).strftime("%Y-%m-%d")

def is_today(date_str: str) -> bool:
    """Check if a date string match today's IST date"""
    try:
        if not date_str: return False
        # Normalize date string to YYYY-MM-DD
        d = pd.to_datetime(date_str).strftime("%Y-%m-%d")
        return d == get_ist_today_str()
    except:
        return False

def safe_float(val) -> Optional[float]:
    if val is None: return None
    try:
        if isinstance(val, str): val = val.replace(',', '').strip()
        if pd.isna(val): return None
        return float(val)
    except: return None

# ---------------------------------------------------------
# DATA FETCHING FUNCTIONS
# ---------------------------------------------------------

def fetch_today_nsepython(index_name: str) -> Optional[Dict[str, Any]]:
    """Fetch using nsepython"""
    try:
        from nsepython import index_history
        today_str = datetime.now(IST).strftime("%d-%m-%Y")
        today_iso = get_ist_today_str()
        
        print(f"  📥 [nsepython] Fetching {index_name}...")
        df = index_history(index=index_name, start_date=today_str, end_date=today_str)
        
        if df is None or len(df) == 0:
            start_date = (datetime.now(IST) - timedelta(days=5)).strftime("%d-%m-%Y")
            df = index_history(index=index_name, start_date=start_date, end_date=today_str)

        if df is None or len(df) == 0: return None
        
        row = df.iloc[-1]
        
        def get_val(keywords):
            for col in df.columns:
                if any(k in str(col).lower() for k in keywords):
                    return safe_float(row[col])
            return None

        open_val = get_val(['open'])
        high_val = get_val(['high'])
        low_val = get_val(['low'])
        close_val = get_val(['close'])
        volume_val = get_val(['volume', 'shares', 'traded'])
        
        date_key = today_iso 
        try:
            if hasattr(row, 'name'):
                dt = pd.to_datetime(str(row.name))
                date_key = dt.strftime("%Y-%m-%d")
        except: pass

        if close_val is not None:
            return {
                "name": index_name, "date": date_key,
                "open": open_val, "high": high_val, "low": low_val, "close": close_val,
                "price": close_val, "volume": int(volume_val) if volume_val else 0,
                "source": "nsepython",
                "imported_at": datetime.now(timezone.utc).isoformat()
            }
    except Exception: pass
    return None


def fetch_today_nsedownload(index_name: str) -> Optional[Dict[str, Any]]:
    """Fetch using NSEDownload"""
    try:
        from NSEDownload import indices
        today_str = datetime.now(IST).strftime("%d-%m-%Y")
        print(f"  📥 [NSEDownload] Fetching {index_name}...")
        try:
            df = indices.get_data(index_name=index_name, start_date=today_str, end_date=today_str)
        except TypeError:
            df = indices.get_data(index=index_name, start_date=today_str, end_date=today_str)

        if df is None or df.empty: return None

        row = df.iloc[-1]
        df.columns = [c.strip().lower() for c in df.columns]
        
        try:
            open_val = safe_float(row['open'])
            high_val = safe_float(row['high'])
            low_val = safe_float(row['low'])
            close_val = safe_float(row['close'])
            volume_val = safe_float(row.get('volume', 0))
            
            date_key = get_ist_today_str()
            if hasattr(row, 'name'): date_key = pd.to_datetime(row.name).strftime("%Y-%m-%d")
            elif 'date' in df.columns: date_key = pd.to_datetime(row['date']).strftime("%Y-%m-%d")

            return {
                "name": index_name, "date": date_key,
                "open": open_val, "high": high_val, "low": low_val, "close": close_val,
                "price": close_val, "volume": int(volume_val) if volume_val else 0,
                "source": "NSEDownload",
                "imported_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception: return None
    except Exception: pass
    return None


def fetch_today_yfinance(index_name: str) -> Optional[Dict[str, Any]]:
    """Fetch using yfinance Ticker (Optimized for Current Day)"""
    try:
        import yfinance as yf
        mapping = {"NIFTY 50": "^NSEI", "NIFTY BANK": "^NSEBANK"}
        symbol = mapping.get(index_name, "^NSEI")
        
        print(f"  📥 [yfinance] Fetching {symbol} (Live/Intraday)...")
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d")
        
        if df is None or df.empty: return None
            
        row = df.iloc[-1]
        date_idx = df.index[-1]
        date_key = date_idx.strftime("%Y-%m-%d")

        return {
            "name": index_name, "date": date_key,
            "open": round(row['Open'], 2), "high": round(row['High'], 2),
            "low": round(row['Low'], 2), "close": round(row['Close'], 2),
            "price": round(row['Close'], 2), "volume": int(row['Volume']),
            "source": "yfinance",
            "imported_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"  ❌ yfinance error: {e}")
        return None

# ---------------------------------------------------------
# DB OPERATIONS
# ---------------------------------------------------------

async def get_previous_close(collection, index_name: str, current_date: str) -> Optional[float]:
    prev_doc = await collection.find_one(
        {"name": index_name, "date": {"$lt": current_date}},
        sort=[("date", -1)]
    )
    return float(prev_doc["close"]) if prev_doc and prev_doc.get("close") else None

async def upsert_to_mongodb(collection, doc: Dict[str, Any]) -> bool:
    res = await collection.update_one(
        {"name": doc["name"], "date": doc["date"]},
        {"$set": doc},
        upsert=True
    )
    return res.upserted_id is not None or res.modified_count > 0

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

async def main():
    print(f"🕐 Daily NIFTY Update - {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 60)
    
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url:
        print("❌ MONGO_URL missing")
        sys.exit(1)
        
    # FIX: Added tlsAllowInvalidCertificates=True to bypass macOS SSL issues
    client = AsyncIOMotorClient(mongo_url, tlsAllowInvalidCertificates=True)
    
    db = client[db_name]
    collection = db.nifty_data
    
    indices = ["NIFTY 50", "NIFTY BANK"]
    
    for index_name in indices:
        print(f"\n📊 Processing {index_name}...")
        data = None
        loop = asyncio.get_event_loop()
        
        data = await loop.run_in_executor(None, fetch_today_nsepython, index_name)
        
        if not data or not is_today(data.get('date')):
            data = await loop.run_in_executor(None, fetch_today_nsedownload, index_name)

        if not data or not is_today(data.get('date')):
            print("  ⚠️ Primary sources failed/stale. Using yfinance history...")
            data = await loop.run_in_executor(None, fetch_today_yfinance, index_name)

        if data:
            target_date = get_ist_today_str()
            data_date = data.get('date')
            
            if data_date != target_date:
                print(f"  ❌ Data is OLD ({data_date}). Expected {target_date}. Skipping save.")
                continue

            prev_close = await get_previous_close(collection, index_name, data_date)
            if prev_close:
                pct = ((data['close'] - prev_close) / prev_close) * 100
                data['change_percent'] = round(pct, 2)
            
            if await upsert_to_mongodb(collection, data):
                print(f"  ✅ SAVED {index_name} [{data_date}]: Close={data['close']} (Change: {data.get('change_percent')}%)")
            else:
                print(f"  ⚠️ MongoDB update skipped (No changes)")
        else:
            print(f"  ❌ Failed to fetch current data for {index_name}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())