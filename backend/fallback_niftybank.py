#!/usr/bin/env python3
"""
Delete all existing NIFTY BANK data and import fresh data from CSV.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


def parse_date(date_str: str) -> Optional[str]:
    """Parse date - already in YYYY-MM-DD format."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if not s or s.lower() in {"nan", "none", "null", "date", ""}:
        return None
    # Try YYYY-MM-DD format
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # Try pandas
        try:
            dt = pd.to_datetime(s)
            return dt.strftime("%Y-%m-%d")
        except:
            return None


def safe_float(val) -> Optional[float]:
    """Convert strings with commas / units to float."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "null", "-", ""}:
        return None
    # Remove % sign if present
    s = s.replace("%", "")
    # Replace commas
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_volume(vol_str) -> Optional[float]:
    """Parse volume - may be in millions or plain number."""
    if vol_str is None:
        return None
    s = str(vol_str).strip()
    if not s or s.lower() in {"nan", "none", "null", "-", ""}:
        return None

    multiplier = 1.0
    if s.endswith("M"):
        multiplier = 1_000_000.0
        s = s[:-1]
    elif s.endswith("K"):
        multiplier = 1_000.0
        s = s[:-1]

    try:
        s_clean = s.replace(",", "").strip()
        base = float(s_clean)
        return base * multiplier
    except ValueError:
        return None


def process_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Read CSV and return list of documents to insert."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📥 Reading CSV: {csv_path}")
    
    # Read CSV, skipping first 3 rows (header rows: Price/Open/High, Ticker, Date)
    # Row 4 onwards has actual data
    df = pd.read_csv(csv_path, skiprows=3, header=None)
    
    print(f"   CSV has {len(df.columns)} columns")
    print(f"   First row sample: {df.iloc[0].tolist() if len(df) > 0 else 'empty'}")
    
    # The CSV structure after skiprows=3 (real semantics):
    # Header row (row 1) says: Price,Open,High,Low,Close,Change %,Volume
    # But ACTUAL data rows look like:
    #   2010-01-04,9031.8,9129.34,9031.8,9112.24,,0
    # So the columns are actually:
    #   0: Date
    #   1: Open
    #   2: High
    #   3: Low
    #   4: Close (this is the true "Price")
    #   5: Change %
    #   6: Volume
    
    # Map columns by position (fixed for this CSV)
    col_map = {
        "date": 0,
        "open": 1,
        "high": 2,
        "low": 3,
        "close": 4,
        # price will be derived from close
    }
    
    # Change % and Volume positions
    col_map["change"] = 5 if len(df.columns) >= 6 else None
    col_map["volume"] = 6 if len(df.columns) >= 7 else None
    
    print(f"   Total rows: {len(df)}")
    
    docs: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        try:
            date_raw = row.iloc[col_map["date"]]
            date_norm = parse_date(date_raw)
            if not date_norm:
                continue  # Skip invalid dates

            open_val = safe_float(row.iloc[col_map["open"]])
            high_val = safe_float(row.iloc[col_map["high"]])
            low_val = safe_float(row.iloc[col_map["low"]])
            close_val = safe_float(row.iloc[col_map["close"]])
            
            volume = None
            if col_map["volume"] is not None and col_map["volume"] < len(row):
                volume = parse_volume(row.iloc[col_map["volume"]])
            
            change_pct = None
            if col_map["change"] is not None and col_map["change"] < len(row):
                change_pct = safe_float(row.iloc[col_map["change"]])

            doc: Dict[str, Any] = {
                "name": "NIFTY BANK",
                "date": date_norm,
                # Price = official close
                "price": close_val,
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val,
                "volume": volume,
                "change_percent": change_pct,
                "source": "CSV Import (Fresh)",
                "imported_at": datetime.utcnow().isoformat(),
            }

            docs.append(doc)
        except Exception as e:
            print(f"⚠️  Error processing row {idx}: {e}")
            continue

    print(f"✅ Processed {len(docs)} valid rows from CSV.")
    return docs


async def delete_and_import(csv_path: Path):
    """Delete all NIFTY BANK data and import fresh from CSV."""
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    if not mongo_url or not db_name:
        raise RuntimeError("MONGO_URL and DB_NAME must be set in environment or .env")

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
        raise RuntimeError(f"MongoDB connection failed: {e}")

    # Step 1: Delete all NIFTY BANK data
    print("\n🗑️  Deleting all existing NIFTY BANK data...")
    delete_result = await collection.delete_many({"name": "NIFTY BANK"})
    print(f"   Deleted {delete_result.deleted_count} NIFTY BANK documents")

    # Step 2: Process CSV
    print("\n📥 Processing CSV...")
    docs = process_csv(csv_path)
    
    if not docs:
        print("❌ No valid rows to import.")
        client.close()
        return

    # Step 3: Insert all documents
    print(f"\n💾 Inserting {len(docs)} documents...")
    inserted = 0
    
    # Insert in batches for better performance
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        try:
            await collection.insert_many(batch)
            inserted += len(batch)
            print(f"   Inserted batch {i//batch_size + 1}: {len(batch)} documents (total: {inserted}/{len(docs)})")
        except Exception as e:
            print(f"   ⚠️  Error inserting batch {i//batch_size + 1}: {e}")
            # Try inserting one by one
            for doc in batch:
                try:
                    await collection.insert_one(doc)
                    inserted += 1
                except Exception as e2:
                    print(f"     ⚠️  Error inserting {doc.get('date')}: {e2}")

    total = await collection.count_documents({"name": "NIFTY BANK"})
    print(f"\n🏁 Import complete!")
    print(f"   Inserted: {inserted}")
    print(f"   Total NIFTY BANK documents in MongoDB: {total}")
    
    # Show date range
    if total > 0:
        first = await collection.find_one({"name": "NIFTY BANK"}, sort=[("date", 1)])
        last = await collection.find_one({"name": "NIFTY BANK"}, sort=[("date", -1)])
        if first and last:
            print(f"   Date range: {first.get('date')} to {last.get('date')}")

    client.close()


async def main():
    csv_path = Path("/Users/saikiran/Desktop/aa/nifty_bank_historical_data_2010_to_today.csv")
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        print("   Please check the path and try again.")
        return

    await delete_and_import(csv_path)


if __name__ == "__main__":
    asyncio.run(main())
