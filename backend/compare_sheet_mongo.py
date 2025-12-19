#!/usr/bin/env python3
"""
Compare Google Sheets data with MongoDB to ensure exact match
"""

import os
import asyncio
import httpx
import pandas as pd
from io import StringIO
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
ROOT_DIR = Path(__file__).parent
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/18Ybife1vGGxLfrlEeYUdpsGhjzIwLRmTYgMd3GYgHbk/export?format=csv&gid=1234653346"

def parse_date(date_str: str):
    """Parse date string"""
    try:
        return pd.to_datetime(date_str, format="%d-%b-%y")
    except:
        try:
            return pd.to_datetime(date_str, format="%d-%B-%y")
        except:
            return None

async def compare():
    # Fetch Google Sheets data
    print("📥 Fetching Google Sheets data...")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(GOOGLE_SHEETS_URL)
        response.raise_for_status()
        df_sheet = pd.read_csv(StringIO(response.text))
    
    print(f"   Fetched {len(df_sheet)} rows from Google Sheets")
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("❌ MONGO_URL and DB_NAME must be set")
        return
    
    mongo_url = mongo_url.strip('"').strip("'")
    db_name = db_name.strip('"').strip("'")
    
    if '?' not in mongo_url:
        mongo_url += '?tlsAllowInvalidCertificates=true'
    elif 'tlsAllowInvalidCertificates' not in mongo_url:
        mongo_url += '&tlsAllowInvalidCertificates=true'
    
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
    db = client[db_name]
    collection = db.nifty_data
    
    print("📥 Fetching MongoDB data...")
    cursor = collection.find().sort("date", 1)
    mongo_docs = []
    async for doc in cursor:
        mongo_docs.append(doc)
    
    print(f"   Fetched {len(mongo_docs)} documents from MongoDB")
    
    # Compare
    print("\n🔍 Comparing data...")
    
    # Convert MongoDB docs to DataFrame for easier comparison
    mongo_data = []
    for doc in mongo_docs:
        mongo_data.append({
            'date': doc.get('date'),
            'open': doc.get('open'),
            'high': doc.get('high'),
            'low': doc.get('low'),
            'close': doc.get('close')
        })
    
    df_mongo = pd.DataFrame(mongo_data)
    
    # Parse dates in sheet
    df_sheet['date_parsed'] = df_sheet['Date'].apply(parse_date)
    df_sheet['date_str'] = df_sheet['date_parsed'].dt.strftime('%Y-%m-%d')
    
    # Convert sheet values to float
    for col in ['Open', 'High', 'Low', 'Close']:
        df_sheet[col.lower()] = pd.to_numeric(df_sheet[col], errors='coerce')
    
    # Merge on date
    merged = pd.merge(
        df_sheet[['date_str', 'open', 'high', 'low', 'close']],
        df_mongo[['date', 'open', 'high', 'low', 'close']],
        left_on='date_str',
        right_on='date',
        suffixes=('_sheet', '_mongo'),
        how='outer'
    )
    
    # Check for mismatches
    mismatches = []
    null_issues = []
    
    for idx, row in merged.iterrows():
        date_val = row.get('date_str') or row.get('date')
        
        # Check for null values
        if pd.isna(row.get('open_mongo')) or pd.isna(row.get('high_mongo')) or \
           pd.isna(row.get('low_mongo')) or pd.isna(row.get('close_mongo')):
            null_issues.append({
                'date': date_val,
                'open': row.get('open_mongo'),
                'high': row.get('high_mongo'),
                'low': row.get('low_mongo'),
                'close': row.get('close_mongo')
            })
        
        # Check for value mismatches
        for field in ['open', 'high', 'low', 'close']:
            sheet_val = row.get(f'{field}_sheet')
            mongo_val = row.get(f'{field}_mongo')
            
            if pd.notna(sheet_val) and pd.notna(mongo_val):
                if abs(float(sheet_val) - float(mongo_val)) > 0.01:  # Allow small floating point differences
                    mismatches.append({
                        'date': date_val,
                        'field': field,
                        'sheet': sheet_val,
                        'mongo': mongo_val,
                        'diff': abs(float(sheet_val) - float(mongo_val))
                    })
    
    # Report results
    print(f"\n📊 Comparison Results:")
    print(f"   Total rows in sheet: {len(df_sheet)}")
    print(f"   Total rows in MongoDB: {len(df_mongo)}")
    print(f"   Rows with null values in MongoDB: {len(null_issues)}")
    print(f"   Value mismatches: {len(mismatches)}")
    
    if null_issues:
        print(f"\n⚠️  Records with null values (first 10):")
        for issue in null_issues[:10]:
            print(f"   {issue}")
    
    if mismatches:
        print(f"\n⚠️  Value mismatches (first 10):")
        for mismatch in mismatches[:10]:
            print(f"   Date: {mismatch['date']}, Field: {mismatch['field']}, "
                  f"Sheet: {mismatch['sheet']}, MongoDB: {mismatch['mongo']}, "
                  f"Diff: {mismatch['diff']:.4f}")
    else:
        print("\n✅ No value mismatches found!")
    
    if not null_issues:
        print("✅ No null values found!")
    
    # Show sample comparison
    print(f"\n📋 Sample comparison (first 5 rows):")
    for i in range(min(5, len(df_sheet))):
        sheet_row = df_sheet.iloc[i]
        date_str = sheet_row.get('date_str', 'N/A')
        
        # Find matching MongoDB row
        mongo_row = df_mongo[df_mongo['date'] == date_str]
        if len(mongo_row) > 0:
            mongo_row = mongo_row.iloc[0]
            print(f"   {date_str}:")
            print(f"      Sheet:  O={sheet_row.get('open')}, H={sheet_row.get('high')}, "
                  f"L={sheet_row.get('low')}, C={sheet_row.get('close')}")
            print(f"      Mongo:  O={mongo_row.get('open')}, H={mongo_row.get('high')}, "
                  f"L={mongo_row.get('low')}, C={mongo_row.get('close')}")
            print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(compare())

