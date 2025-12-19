#!/usr/bin/env python3
"""
Simple script to view NIFTY data from MongoDB
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from server import db

async def view_data():
    """View NIFTY data from MongoDB"""
    if db is None:
        print("❌ MongoDB not connected")
        return
    
    collection = db.nifty_data
    
    # Get total count
    total = await collection.count_documents({})
    print(f"\n📊 Total Records: {total}\n")
    
    # Get count by name
    nifty50_count = await collection.count_documents({"name": "NIFTY 50"})
    niftybank_count = await collection.count_documents({"name": "NIFTY BANK"})
    other_count = await collection.count_documents({"name": {"$nin": ["NIFTY 50", "NIFTY BANK"]}})
    
    print(f"📈 NIFTY 50 records: {nifty50_count}")
    print(f"📈 NIFTY BANK records: {niftybank_count}")
    if other_count > 0:
        print(f"📈 Other records: {other_count}")
    
    # Get latest records for each index
    print("\n" + "="*80)
    print("LATEST NIFTY 50 DATA (Last 10 records)")
    print("="*80)
    
    cursor = collection.find({"name": "NIFTY 50"}).sort("date", -1).limit(10)
    print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Source':<20}")
    print("-" * 80)
    async for doc in cursor:
        print(f"{doc.get('date', 'N/A'):<12} "
              f"{doc.get('open', 0):>10.2f} "
              f"{doc.get('high', 0):>10.2f} "
              f"{doc.get('low', 0):>10.2f} "
              f"{doc.get('close', 0):>10.2f} "
              f"{doc.get('source', 'N/A'):<20}")
    
    print("\n" + "="*80)
    print("LATEST NIFTY BANK DATA (Last 10 records)")
    print("="*80)
    
    cursor = collection.find({"name": "NIFTY BANK"}).sort("date", -1).limit(10)
    print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Source':<20}")
    print("-" * 80)
    async for doc in cursor:
        print(f"{doc.get('date', 'N/A'):<12} "
              f"{doc.get('open', 0):>10.2f} "
              f"{doc.get('high', 0):>10.2f} "
              f"{doc.get('low', 0):>10.2f} "
              f"{doc.get('close', 0):>10.2f} "
              f"{doc.get('source', 'N/A'):<20}")
    
    print("\n" + "="*80)
    print("✅ Data viewing complete!")
    print("="*80)
    print("\n💡 To view data in GraphQL:")
    print("   1. Make sure server is running: python3 -m uvicorn server:app --host 0.0.0.0 --port 8000")
    print("   2. Open browser: http://localhost:8000/graphql")
    print("   3. Or use the viewer: http://localhost:8000/graphql-viewer")
    print("\n📝 Sample GraphQL Query:")
    print("""
    {
      niftyData(limit: 10) {
        name
        date
        open
        high
        low
        close
        importedAt
      }
    }
    """)

if __name__ == "__main__":
    asyncio.run(view_data())

