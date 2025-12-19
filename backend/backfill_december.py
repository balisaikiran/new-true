#!/usr/bin/env python3
"""
Backfill December 2025 OHLC for NIFTY 50 and NIFTY BANK using NSEDownload.

This upserts data (does NOT clear existing), setting name accordingly.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


def normalize_float(val) -> Optional[float]:
    try:
        if val is None:
            return None
        return float(val)
    except Exception:
        return None


def make_docs_from_df(df, index_name: str, source: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if df is None or len(df) == 0:
        return results

    for _, row in df.iterrows():
        open_v = normalize_float(row.get("Open", row.get("open")))
        high_v = normalize_float(row.get("High", row.get("high")))
        low_v = normalize_float(row.get("Low", row.get("low")))
        close_v = normalize_float(row.get("Close", row.get("close")))

        date_val = row.get("Date", None)
        if date_val is None and hasattr(row, "name"):
            date_val = row.name

        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)

        if not date_str or date_str.lower() in {"nan", "none", "null"}:
            continue

        results.append(
            {
                "name": index_name,
                "date": date_str,
                "open": open_v,
                "high": high_v,
                "low": low_v,
                "close": close_v,
                "source": source,
                "imported_at": datetime.utcnow().isoformat(),
            }
        )
    return results


async def fetch_range_nsedl(index_name: str, start: str, end: str):
    """Fetch via NSEDownload."""
    try:
        from NSEDownload import indices

        df = indices.get_data(index_name=index_name, start_date=start, end_date=end)
        return make_docs_from_df(df, index_name, "NSEDownload")
    except Exception as e:
        print(f"⚠️ NSEDownload failed for {index_name}: {e}")
        return []


async def fetch_range_yf(index_name: str, start: str, end: str):
    """Fetch via yfinance as fallback."""
    import yfinance as yf

    symbol_map = {
        "NIFTY 50": ["^NSEI", "NIFTY.NS", "NSEI"],
        "NIFTY BANK": ["^NSEBANK", "BANKNIFTY.NS", "NSEBANK"],
    }
    symbols = symbol_map.get(index_name, [])
    results: List[Dict[str, Any]] = []
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(start=start, end=end, interval="1d")
            if df is None or len(df) == 0:
                continue
            # yfinance returns columns Open High Low Close
            df = df.reset_index()
            df = df.rename(columns={"Date": "Date"})
            docs = make_docs_from_df(df, index_name, f"Yahoo Finance ({sym})")
            if docs:
                results.extend(docs)
                break  # take first successful symbol
        except Exception as e:
            print(f"⚠️ yfinance failed for {index_name} symbol {sym}: {e}")
            continue
    return results


async def upsert_many(collection, docs):
    inserted = 0
    updated = 0
    for doc in docs:
        res = await collection.update_one(
            {"name": doc["name"], "date": doc["date"]},
            {"$set": doc},
            upsert=True,
        )
        if res.upserted_id:
            inserted += 1
        elif res.modified_count:
            updated += 1
    return inserted, updated


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
    coll = db.nifty_data

    await client.admin.command("ping")

    start = "2025-12-01"
    end = "2026-01-01"
    indices = ["NIFTY 50", "NIFTY BANK"]

    total_ins = total_upd = 0
    for idx in indices:
        print(f"📥 Fetching {idx} from {start} to {end} via NSEDownload...")
        docs = await fetch_range_nsedl(idx, start, end)
        if not docs:
            print(f"⚠️ NSEDownload returned no data for {idx}, trying yfinance...")
            docs = await fetch_range_yf(idx, start, end)
        if not docs:
            print(f"❌ No data returned for {idx} from any source")
            continue
        ins, upd = await upsert_many(coll, docs)
        total_ins += ins
        total_upd += upd
        print(f"✅ {idx}: inserted {ins}, updated {upd}")

    print(f"🏁 Done. Inserted: {total_ins}, updated: {total_upd}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())



