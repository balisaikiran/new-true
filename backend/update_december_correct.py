#!/usr/bin/env python3
"""
Update MongoDB with correct December 2025 OHLC data for NIFTY 50 and NIFTY BANK.
Data sourced from NSE official records.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


# Correct December 2025 data from NSE
NIFTY_50_DATA = [
    {"date": "2025-12-16", "open": 25951.50, "high": 25966.75, "low": 25837.05, "close": 25860.10},
    {"date": "2025-12-15", "open": 25930.05, "high": 26047.15, "low": 25904.75, "close": 26027.30},
    {"date": "2025-12-12", "open": 25971.20, "high": 26057.60, "low": 25938.45, "close": 26046.95},
    {"date": "2025-12-11", "open": 25771.40, "high": 25922.80, "low": 25693.25, "close": 25898.55},
    {"date": "2025-12-10", "open": 25864.05, "high": 25947.65, "low": 25734.55, "close": 25758.00},
    {"date": "2025-12-09", "open": 25867.10, "high": 25923.65, "low": 25728.00, "close": 25839.65},
    {"date": "2025-12-08", "open": 26159.80, "high": 26178.70, "low": 25892.25, "close": 25960.55},
    {"date": "2025-12-05", "open": 25999.80, "high": 26202.60, "low": 25985.35, "close": 26186.45},
    {"date": "2025-12-04", "open": 25981.85, "high": 26098.25, "low": 25938.95, "close": 26033.75},
    {"date": "2025-12-03", "open": 26004.90, "high": 26066.45, "low": 25891.00, "close": 25986.00},
    {"date": "2025-12-02", "open": 26087.95, "high": 26154.60, "low": 25997.85, "close": 26032.20},
    {"date": "2025-12-01", "open": 26325.80, "high": 26325.80, "low": 26124.20, "close": 26175.75},
]

NIFTY_BANK_DATA = [
    {"date": "2025-12-16", "open": 59288.75, "high": 59327.35, "low": 58971.60, "close": 59034.60},
    {"date": "2025-12-15", "open": 59053.70, "high": 59533.00, "low": 59052.30, "close": 59461.80},
    {"date": "2025-12-12", "open": 59401.50, "high": 59545.70, "low": 59224.85, "close": 59389.95},
    {"date": "2025-12-11", "open": 58966.20, "high": 59423.35, "low": 58799.90, "close": 59209.85},
    {"date": "2025-12-10", "open": 59281.55, "high": 59440.90, "low": 58853.90, "close": 58960.40},
    {"date": "2025-12-09", "open": 58918.85, "high": 59358.25, "low": 58878.45, "close": 59222.35},
    {"date": "2025-12-08", "open": 59672.05, "high": 59713.15, "low": 59030.60, "close": 59238.55},
    {"date": "2025-12-05", "open": 59133.20, "high": 59806.60, "low": 59106.55, "close": 59777.20},
    {"date": "2025-12-04", "open": 59287.10, "high": 59548.70, "low": 59062.15, "close": 59288.70},
    {"date": "2025-12-03", "open": 59158.70, "high": 59414.90, "low": 58925.70, "close": 59348.25},
    {"date": "2025-12-02", "open": 59354.20, "high": 59656.55, "low": 59251.95, "close": 59273.80},
    {"date": "2025-12-01", "open": 60102.05, "high": 60114.30, "low": 59527.60, "close": 59681.35},
]


async def main():
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
        print("✅ MongoDB connected\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    total_inserted = 0
    total_updated = 0

    # Update NIFTY 50 data
    print("📊 Updating NIFTY 50 data...")
    for record in NIFTY_50_DATA:
        doc = {
            "name": "NIFTY 50",
            "date": record["date"],
            "open": record["open"],
            "high": record["high"],
            "low": record["low"],
            "close": record["close"],
            "source": "NSE Official",
            "imported_at": datetime.utcnow().isoformat()
        }
        
        result = await collection.update_one(
            {"name": "NIFTY 50", "date": record["date"]},
            {"$set": doc},
            upsert=True
        )
        
        if result.upserted_id:
            total_inserted += 1
            print(f"  ➕ Inserted: {record['date']}")
        elif result.modified_count:
            total_updated += 1
            print(f"  ✏️  Updated: {record['date']}")
        else:
            print(f"  ⏭️  Unchanged: {record['date']}")

    print()

    # Update NIFTY BANK data
    print("📊 Updating NIFTY BANK data...")
    for record in NIFTY_BANK_DATA:
        doc = {
            "name": "NIFTY BANK",
            "date": record["date"],
            "open": record["open"],
            "high": record["high"],
            "low": record["low"],
            "close": record["close"],
            "source": "NSE Official",
            "imported_at": datetime.utcnow().isoformat()
        }
        
        result = await collection.update_one(
            {"name": "NIFTY BANK", "date": record["date"]},
            {"$set": doc},
            upsert=True
        )
        
        if result.upserted_id:
            total_inserted += 1
            print(f"  ➕ Inserted: {record['date']}")
        elif result.modified_count:
            total_updated += 1
            print(f"  ✏️  Updated: {record['date']}")
        else:
            print(f"  ⏭️  Unchanged: {record['date']}")

    print(f"\n🏁 Done! Inserted: {total_inserted}, Updated: {total_updated}")
    
    # Show final data
    print("\n📋 December 2025 data in MongoDB:")
    print("\nNIFTY 50:")
    cursor = collection.find({"name": "NIFTY 50", "date": {"$gte": "2025-12-01", "$lte": "2025-12-31"}}).sort("date", -1)
    async for doc in cursor:
        print(f"  {doc['date']}: O={doc['open']:.2f}, H={doc['high']:.2f}, L={doc['low']:.2f}, C={doc['close']:.2f}")
    
    print("\nNIFTY BANK:")
    cursor = collection.find({"name": "NIFTY BANK", "date": {"$gte": "2025-12-01", "$lte": "2025-12-31"}}).sort("date", -1)
    async for doc in cursor:
        print(f"  {doc['date']}: O={doc['open']:.2f}, H={doc['high']:.2f}, L={doc['low']:.2f}, C={doc['close']:.2f}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())


