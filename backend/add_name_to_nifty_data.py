#!/usr/bin/env python3
"""
One-time script to add 'name' field to existing nifty_data documents.

- If a document has no 'name' field, it will be set to "NIFTY 50".
- Existing 'name' values (e.g. "NIFTY 50", "NIFTY BANK") are left unchanged.
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


async def main() -> None:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    if not mongo_url or not db_name:
        print("❌ MONGO_URL and DB_NAME environment variables must be set")
        return

    # Normalize values and allow invalid certs (same pattern as other scripts)
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
        # Quick connection test
        await client.admin.command("ping")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        client.close()
        return

    # Count docs without a name field
    missing_filter = {"name": {"$exists": False}}
    missing_count = await collection.count_documents(missing_filter)
    print(f"📊 Documents without 'name': {missing_count}")

    if missing_count == 0:
        print("✅ No updates needed.")
        client.close()
        return

    # Update in batches
    result = await collection.update_many(
        missing_filter,
        {"$set": {"name": "NIFTY 50"}},  # historical sheet data is NIFTY 50
    )

    print(f"✅ Updated {result.modified_count} documents to set name='NIFTY 50'")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())

