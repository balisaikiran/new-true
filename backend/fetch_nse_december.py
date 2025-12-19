#!/usr/bin/env python3
"""
Fetch December 2025 OHLC data directly from NSE India and update MongoDB.
Uses multiple methods to get the data.
"""

import os
import asyncio
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


async def fetch_nse_with_session(index_name: str) -> List[Dict[str, Any]]:
    """
    Fetch historical index data from NSE India using proper session handling.
    """
    results = []
    
    # Map index names to NSE symbols
    index_map = {
        "NIFTY 50": "NIFTY 50",
        "NIFTY BANK": "NIFTY BANK"
    }
    
    nse_index = index_map.get(index_name, index_name)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    
    # Create SSL context that doesn't verify
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with httpx.AsyncClient(
        timeout=60.0, 
        follow_redirects=True, 
        verify=False,
        http2=False
    ) as client:
        try:
            # Step 1: Get the main page to establish session
            print(f"  Step 1: Getting NSE session...")
            main_resp = await client.get(
                'https://www.nseindia.com/reports-indices-historical-index-data',
                headers=headers
            )
            
            if main_resp.status_code != 200:
                print(f"  Warning: Main page returned {main_resp.status_code}")
            
            # Step 2: Try the index quote API first (for recent data)
            print(f"  Step 2: Fetching quote data for {nse_index}...")
            
            quote_url = f"https://www.nseindia.com/api/equity-stockIndices?index={nse_index.replace(' ', '%20')}"
            
            headers['Referer'] = 'https://www.nseindia.com/reports-indices-historical-index-data'
            
            quote_resp = await client.get(quote_url, headers=headers)
            
            if quote_resp.status_code == 200:
                data = quote_resp.json()
                print(f"  Got quote data, checking structure...")
                
                # This gives current/latest data
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        if item.get("index") == nse_index or item.get("symbol") == nse_index:
                            # This is today's data
                            today = datetime.now().strftime("%Y-%m-%d")
                            results.append({
                                "name": index_name,
                                "date": today,
                                "open": float(str(item.get("open", 0)).replace(",", "")),
                                "high": float(str(item.get("dayHigh", 0)).replace(",", "")),
                                "low": float(str(item.get("dayLow", 0)).replace(",", "")),
                                "close": float(str(item.get("previousClose", item.get("lastPrice", 0))).replace(",", "")),
                                "source": "NSE Quote API",
                                "imported_at": datetime.utcnow().isoformat()
                            })
            
            # Step 3: Try historical data API
            print(f"  Step 3: Trying historical data API...")
            
            from_date = "01-Dec-2025"
            to_date = "31-Dec-2025"
            
            hist_url = f"https://www.nseindia.com/api/historical/indicesHistory?indexType={nse_index.replace(' ', '%20')}&from={from_date}&to={to_date}"
            
            hist_resp = await client.get(hist_url, headers=headers)
            
            if hist_resp.status_code == 200:
                data = hist_resp.json()
                print(f"  Got historical data response")
                
                records = []
                if isinstance(data, dict) and "data" in data:
                    records = data["data"]
                
                for record in records:
                    try:
                        date_str = record.get("HistoricalDate") or record.get("EOD_TIMESTAMP")
                        if not date_str:
                            continue
                        
                        # Parse date
                        date_obj = None
                        for fmt in ["%d %b %Y", "%d-%b-%Y", "%d-%m-%Y"]:
                            try:
                                date_obj = datetime.strptime(date_str.strip(), fmt)
                                break
                            except:
                                continue
                        
                        if not date_obj:
                            continue
                        
                        open_val = record.get("OPEN") or record.get("open")
                        high_val = record.get("HIGH") or record.get("high")
                        low_val = record.get("LOW") or record.get("low")
                        close_val = record.get("CLOSE") or record.get("close")
                        
                        if all([open_val, high_val, low_val, close_val]):
                            results.append({
                                "name": index_name,
                                "date": date_obj.strftime("%Y-%m-%d"),
                                "open": float(str(open_val).replace(",", "")),
                                "high": float(str(high_val).replace(",", "")),
                                "low": float(str(low_val).replace(",", "")),
                                "close": float(str(close_val).replace(",", "")),
                                "source": "NSE Historical API",
                                "imported_at": datetime.utcnow().isoformat()
                            })
                    except Exception as e:
                        continue
            else:
                print(f"  Historical API returned {hist_resp.status_code}")
            
            # Step 4: Try CSV download
            print(f"  Step 4: Trying CSV download...")
            
            csv_url = f"https://www.nseindia.com/api/historical/indicesHistory?indexType={nse_index.replace(' ', '%20')}&from=01-12-2025&to=31-12-2025"
            
            csv_resp = await client.get(csv_url, headers=headers)
            print(f"  CSV response status: {csv_resp.status_code}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    return results


async def fetch_via_alternative(index_name: str) -> List[Dict[str, Any]]:
    """
    Try alternative data source - using a proxy or different endpoint.
    """
    results = []
    
    # Try Google Finance or other alternatives
    print(f"  Trying alternative sources...")
    
    # Map to Google Finance symbols
    gf_map = {
        "NIFTY 50": "INDEXNSE:NIFTY_50",
        "NIFTY BANK": "INDEXNSE:NIFTY_BANK"
    }
    
    return results


async def upsert_records(collection, records: List[Dict[str, Any]]) -> tuple:
    """Upsert records to MongoDB"""
    inserted = 0
    updated = 0
    
    for doc in records:
        result = await collection.update_one(
            {"name": doc["name"], "date": doc["date"]},
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            inserted += 1
        elif result.modified_count:
            updated += 1
    
    return inserted, updated


async def main():
    # MongoDB connection
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    
    if not mongo_url or not db_name:
        print("❌ MONGO_URL and DB_NAME must be set")
        return
    
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
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    indices = ["NIFTY 50", "NIFTY BANK"]
    total_inserted = 0
    total_updated = 0
    
    for index_name in indices:
        print(f"\n📥 Fetching {index_name}...")
        
        records = await fetch_nse_with_session(index_name)
        
        if not records:
            records = await fetch_via_alternative(index_name)
        
        if records:
            inserted, updated = await upsert_records(collection, records)
            total_inserted += inserted
            total_updated += updated
            print(f"  💾 Inserted: {inserted}, Updated: {updated}")
            
            for r in sorted(records, key=lambda x: x["date"], reverse=True):
                print(f"    {r['date']}: O={r['open']:.2f}, H={r['high']:.2f}, L={r['low']:.2f}, C={r['close']:.2f}")
        else:
            print(f"  ⚠️ No data returned for {index_name}")
    
    print(f"\n🏁 Done! Total inserted: {total_inserted}, updated: {total_updated}")
    client.close()


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    asyncio.run(main())

