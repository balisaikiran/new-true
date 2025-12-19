#!/usr/bin/env python3
"""
Quick script to verify Nifty data in MongoDB
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

async def verify_data():
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("MONGO_URL and DB_NAME environment variables must be set")
        return
    
    mongo_url = mongo_url.strip('"').strip("'")
    db_name = db_name.strip('"').strip("'")
    
    if '?' not in mongo_url:
        mongo_url += '?tlsAllowInvalidCertificates=true'
    elif 'tlsAllowInvalidCertificates' not in mongo_url:
        mongo_url += '&tlsAllowInvalidCertificates=true'
    
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
    db = client[db_name]
    
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        collection = db.nifty_data
        total = await collection.count_documents({})
        print(f"\n📊 Total documents in nifty_data collection: {total}")
        
        # Get first and last documents
        first_doc = await collection.find_one(sort=[("date", 1)])
        last_doc = await collection.find_one(sort=[("date", -1)])
        
        print("\n📅 First record:")
        if first_doc:
            print(f"   Date: {first_doc.get('date')}")
            print(f"   Open: {first_doc.get('open')}")
            print(f"   High: {first_doc.get('high')}")
            print(f"   Low: {first_doc.get('low')}")
            print(f"   Close: {first_doc.get('close')}")
        
        print("\n📅 Last record:")
        if last_doc:
            print(f"   Date: {last_doc.get('date')}")
            print(f"   Open: {last_doc.get('open')}")
            print(f"   High: {last_doc.get('high')}")
            print(f"   Low: {last_doc.get('low')}")
            print(f"   Close: {last_doc.get('close')}")
        
        # Get a few sample records
        print("\n📋 Sample records (last 5):")
        cursor = collection.find().sort("date", -1).limit(5)
        async for doc in cursor:
            print(f"   {doc.get('date')}: Open={doc.get('open')}, High={doc.get('high')}, Low={doc.get('low')}, Close={doc.get('close')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_data())








