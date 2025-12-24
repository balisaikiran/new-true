# Refresh Today's NIFTY Data

Guide for manually refreshing today's NIFTY data, independent of cron schedules.

## Overview

This feature allows you to manually refresh today's NIFTY 50 and/or NIFTY BANK data at any time, without waiting for scheduled cron jobs. The refresh function:

- Fetches the latest data from multiple sources (NSE API, yfinance, NSEDownload, TrueData)
- Updates or creates the record for today's date in the database
- Works independently of cron schedules
- Can be called via API endpoint or standalone script

---

## API Endpoint

### Refresh Today's Data

**Endpoint:** `POST https://be.balisaikiran.com/api/nifty/refresh-today`

**Query Parameters:**
- `index_name` (String, optional): `"NIFTY 50"` or `"NIFTY BANK"`. If not provided, refreshes both.
- `token` (String, optional): TrueData API token. If not provided, uses token from database.

**Example Request (cURL):**
```bash
# Refresh both indices
curl -X POST "https://be.balisaikiran.com/api/nifty/refresh-today"

# Refresh only NIFTY 50
curl -X POST "https://be.balisaikiran.com/api/nifty/refresh-today?index_name=NIFTY%2050"

# Refresh only NIFTY BANK
curl -X POST "https://be.balisaikiran.com/api/nifty/refresh-today?index_name=NIFTY%20BANK"
```

**Example Request (Python):**
```python
import httpx

# Refresh both indices
response = httpx.post("https://be.balisaikiran.com/api/nifty/refresh-today")
result = response.json()
print(result)

# Refresh only NIFTY 50
response = httpx.post(
    "https://be.balisaikiran.com/api/nifty/refresh-today",
    params={"index_name": "NIFTY 50"}
)
result = response.json()
print(result)
```

**Example Response:**
```json
{
  "success": true,
  "message": "Refresh completed for 2 index(es)",
  "date": "2025-01-20",
  "results": {
    "NIFTY 50": {
      "status": "success",
      "message": "Successfully refreshed NIFTY 50 data for 2025-01-20",
      "data": {
        "date": "2025-01-20",
        "open": 24500.50,
        "high": 24600.75,
        "low": 24450.25,
        "close": 24550.00,
        "price": 24550.00,
        "volume": 125000000,
        "source": "NSE Official API"
      }
    },
    "NIFTY BANK": {
      "status": "success",
      "message": "Successfully refreshed NIFTY BANK data for 2025-01-20",
      "data": {
        "date": "2025-01-20",
        "open": 52000.00,
        "high": 52100.00,
        "low": 51900.00,
        "close": 52050.00,
        "price": 52050.00,
        "volume": 50000000,
        "source": "Yahoo Finance"
      }
    }
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Refresh completed for 2 index(es)",
  "date": "2025-01-20",
  "results": {
    "NIFTY 50": {
      "status": "error",
      "message": "Failed to fetch NIFTY 50 data from any source"
    },
    "NIFTY BANK": {
      "status": "success",
      "message": "Successfully refreshed NIFTY BANK data for 2025-01-20",
      "data": {...}
    }
  }
}
```

---

## Standalone Python Script

### Usage

The standalone script can be run directly from the command line:

```bash
# Navigate to backend directory
cd backend

# Refresh both indices
python3 refresh_today_nifty.py

# Refresh only NIFTY 50
python3 refresh_today_nifty.py --index "NIFTY 50"

# Refresh only NIFTY BANK
python3 refresh_today_nifty.py --index "NIFTY BANK"

# Use custom MongoDB connection
python3 refresh_today_nifty.py \
  --mongo-url "mongodb+srv://..." \
  --db-name "mydb"

# Use custom TrueData token
python3 refresh_today_nifty.py --token "your-token-here"
```

### Command Line Options

```
--index INDEX_NAME    Index to refresh: "NIFTY 50" or "NIFTY BANK" (default: both)
--mongo-url URL       MongoDB connection URL (default: from MONGO_URL env var)
--db-name NAME        Database name (default: from DB_NAME env var)
--token TOKEN         TrueData API token (default: from database)
```

### Example Output

```
🔄 Refreshing today's NIFTY data (date: 2025-01-20)...
   Indices to refresh: NIFTY 50, NIFTY BANK

📊 Processing NIFTY 50...
✅ Successfully refreshed NIFTY 50
   O=24500.5, H=24600.75, L=24450.25, C=24550.0

📊 Processing NIFTY BANK...
✅ Successfully refreshed NIFTY BANK
   O=52000.0, H=52100.0, L=51900.0, C=52050.0

============================================================
📊 REFRESH SUMMARY
============================================================
Date: 2025-01-20
Overall Status: ✅ SUCCESS
Message: Refresh completed for 2 index(es)

Results:

✅ NIFTY 50:
   Status: success
   Message: Successfully refreshed NIFTY 50 data for 2025-01-20
   Data: O=24500.5, H=24600.75, L=24450.25, C=24550.0
   Source: NSE Official API

✅ NIFTY BANK:
   Status: success
   Message: Successfully refreshed NIFTY BANK data for 2025-01-20
   Data: O=52000.0, H=52100.0, L=51900.0, C=52050.0
   Source: Yahoo Finance

============================================================
✅ Refresh completed successfully!
```

---

## Shell Script Wrapper

A convenient shell script wrapper is also available:

```bash
# Refresh both indices
./refresh-today-nifty.sh

# Refresh only NIFTY 50
./refresh-today-nifty.sh "NIFTY 50"

# Refresh only NIFTY BANK
./refresh-today-nifty.sh "NIFTY BANK"
```

---

## Integration Examples

### Python Integration

```python
import httpx
import asyncio
from ml_data_fetcher import NiftyDataClient

async def refresh_and_verify():
    """Refresh today's data and verify it was updated"""
    
    # Refresh data via API
    response = httpx.post("https://be.balisaikiran.com/api/nifty/refresh-today")
    result = response.json()
    
    if result['success']:
        print("✅ Data refreshed successfully")
        
        # Verify by fetching latest data
        client = NiftyDataClient()
        latest = client.fetch_latest(name="NIFTY 50", days=1)
        client.close()
        
        if not latest.empty:
            print(f"Latest data: {latest.iloc[-1]['close']}")
    else:
        print("❌ Refresh failed")
        print(result)

# Run
asyncio.run(refresh_and_verify())
```

### Cron Alternative

Instead of relying on cron, you can call the refresh endpoint from external schedulers:

```bash
# Add to crontab or external scheduler
# Refresh every day at 4:00 PM IST
0 16 * * * curl -X POST "https://be.balisaikiran.com/api/nifty/refresh-today"
```

### Webhook Integration

You can set up webhooks to trigger refresh:

```python
from flask import Flask, request
import httpx

app = Flask(__name__)

@app.route('/webhook/refresh-nifty', methods=['POST'])
def webhook_refresh():
    """Webhook endpoint to trigger NIFTY data refresh"""
    try:
        response = httpx.post("https://be.balisaikiran.com/api/nifty/refresh-today")
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500
```

---

## Data Sources Priority

The refresh function tries multiple data sources in order of reliability:

1. **NSE Official API** (most reliable)
2. **Yahoo Finance (yfinance)** (backup)
3. **NSEDownload** (free alternative)
4. **TrueData API** (if token available)

The function returns data from the first successful source.

---

## Error Handling

### Common Errors

1. **MongoDB not initialized**
   - Ensure `MONGO_URL` and `DB_NAME` environment variables are set
   - Check MongoDB connection

2. **Failed to fetch data**
   - All data sources failed
   - Check internet connection
   - Verify data sources are accessible

3. **Invalid index name**
   - Must be exactly `"NIFTY 50"` or `"NIFTY BANK"`

### Error Response Format

```json
{
  "success": false,
  "message": "Refresh completed for 1 index(es)",
  "date": "2025-01-20",
  "results": {
    "NIFTY 50": {
      "status": "error",
      "message": "Failed to fetch NIFTY 50 data from any source"
    }
  }
}
```

---

## Use Cases

1. **Manual Data Update**: Refresh data manually when needed
2. **Data Correction**: Update today's data if it was incorrect
3. **Real-time Updates**: Refresh data multiple times during the day
4. **Backup to Cron**: Use as backup if cron job fails
5. **Testing**: Test data fetching without waiting for scheduled jobs
6. **Integration**: Integrate into other systems/workflows

---

## Best Practices

1. **Don't Overuse**: Avoid calling too frequently (once per hour is reasonable)
2. **Check Success**: Always verify the response `success` field
3. **Handle Errors**: Implement proper error handling in your integration
4. **Log Results**: Log refresh attempts for debugging
5. **Monitor**: Set up monitoring/alerts for failed refreshes

---

## API Documentation

For complete API documentation, see:
- **Full API Docs**: `API_DOCUMENTATION.md`
- **FastAPI Swagger UI**: https://be.balisaikiran.com/docs
- **GraphQL Playground**: https://be.balisaikiran.com/graphql

---

## Files

- **API Endpoint**: `backend/server.py` - `refresh_today_nifty_data()` function
- **Standalone Script**: `backend/refresh_today_nifty.py`
- **Shell Wrapper**: `refresh-today-nifty.sh`

---

**Last Updated**: January 2025

