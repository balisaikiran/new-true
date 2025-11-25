# Daily Data Storage & Change Percentage Feature

## Overview
This feature implements automatic end-of-day data storage to MongoDB and calculates change percentages based on previous day's closing prices.

## Features Implemented

### 1. Daily Stock Data Storage
- **Collection**: `daily_stock_data` in MongoDB
- **Structure**: Each document contains:
  - `symbol`: Stock symbol (e.g., "NIFTY", "RELIANCE")
  - `date`: Date in YYYY-MM-DD format
  - `spot`: Closing spot price
  - `volume`: Trading volume
  - `iv`: Implied Volatility
  - `iv_percentile`: IV Percentile
  - `saved_at`: Timestamp when data was saved

### 2. Daily Option Chain Data Storage
- **Collection**: `option_chain_data` in MongoDB
- **Structure**: Each document contains:
  - `symbol`: Stock symbol (e.g., "NIFTY", "RELIANCE")
  - `date`: Date in YYYY-MM-DD format
  - `expiry`: Expiry date in DD-MM-YYYY format (next month's last Thursday)
  - `data`: Complete option chain data from TrueData API
  - `saved_at`: Timestamp when data was saved

### 3. Automatic End-of-Day Save
- **Scheduled Time**: 10:00 AM UTC (3:30 PM IST) - typical market close time
- **Scheduler**: APScheduler (AsyncIOScheduler)
- **Function**: `scheduled_end_of_day_save()` automatically saves:
  - Stock data for all 20 F&O stocks
  - Complete option chain data for all 20 F&O stocks (with next month's expiry)

### 4. Change Percentage Calculation
- **Method**: Compares current spot price with previous day's closing price
- **Formula**: `((current_price - previous_close) / previous_close) * 100`
- **Fallback**: If no previous day data exists, uses mock data (for first day)

### 5. Previous Day Data Retrieval
- **Function**: `get_previous_day_data(symbol)`
- **Logic**:
  1. First tries to get yesterday's data
  2. If not found, gets the most recent data before today
  3. Returns None if no historical data exists

### 6. Manual Save Endpoints
- **Save Stock Data**: `POST /api/market/save-daily-data?token=<token>`
  - Manually trigger stock data save
  - Returns count of stocks saved and date
  
- **Save Option Chains**: `POST /api/market/save-option-chains?token=<token>`
  - Manually trigger option chain data save
  - Returns count of option chains saved, expiry date, and details
  
- **Save All Data**: `POST /api/market/save-all-daily-data?token=<token>`
  - Manually trigger complete end-of-day save (stocks + option chains)
  - Returns counts for both stocks and option chains

## How It Works

### Daily Flow:
1. **During Trading Hours**: 
   - Dashboard fetches live data from TrueData API
   - Change % is calculated using previous day's closing price from MongoDB
   - If no previous data exists, mock data is used

2. **End of Day (3:30 PM IST)**:
   - Scheduler automatically triggers `scheduled_end_of_day_save()`
   - Saves stock data: Fetches current spot prices for all stocks
   - Saves option chain data: Fetches complete option chains for all stocks with next month's expiry
   - All data saved to MongoDB with today's date

3. **Next Day**:
   - Dashboard uses yesterday's saved data as reference
   - Calculates accurate change % based on previous close

## MongoDB Setup

### Required Environment Variables:
```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=truedata
```

### Collection Structures:

**daily_stock_data:**
```javascript
{
  "_id": ObjectId("..."),
  "symbol": "NIFTY",
  "date": "2025-01-15",
  "spot": 24500.50,
  "volume": 5000000,
  "iv": 25.5,
  "iv_percentile": 45.2,
  "saved_at": "2025-01-15T10:00:00.000Z"
}
```

**option_chain_data:**
```javascript
{
  "_id": ObjectId("..."),
  "symbol": "NIFTY",
  "date": "2025-01-15",
  "expiry": "27-02-2025",
  "data": {
    "Records": [...],  // Complete option chain records
    // ... other fields from TrueData API
  },
  "saved_at": "2025-01-15T10:00:00.000Z"
}
```

## API Endpoints

### Get Dashboard Data (with change %)
```
GET /api/market/dashboard?token=<token>
```
- Returns current market data with change % calculated from previous day

### Manual Save Endpoints

**Save Stock Data:**
```
POST /api/market/save-daily-data?token=<token>
```
- Manually triggers stock data save
- Useful for testing or if scheduled job fails

**Save Option Chains:**
```
POST /api/market/save-option-chains?token=<token>
```
- Manually triggers option chain data save
- Saves option chains for all stocks with next month's expiry

**Save All Data:**
```
POST /api/market/save-all-daily-data?token=<token>
```
- Manually triggers complete end-of-day save (stocks + option chains)
- Most comprehensive save endpoint

## Code Changes

### New Dependencies:
- `apscheduler==3.10.4` - For scheduled tasks

### Modified Functions:
- `fetch_stock_data()` - Now calculates change % from previous day's data
- Added `get_previous_day_data()` - Retrieves historical data
- Added `save_daily_stock_data()` - Saves end-of-day stock data
- Added `save_option_chain_data()` - Saves end-of-day option chain data
- Added `get_next_expiry()` - Calculates next month's last Thursday expiry
- Added `scheduled_end_of_day_save()` - Scheduled job function (saves both stocks + option chains)

### New Endpoints:
- `POST /api/market/save-daily-data` - Manual stock data save trigger
- `POST /api/market/save-option-chains` - Manual option chain save trigger
- `POST /api/market/save-all-daily-data` - Manual complete save trigger (stocks + option chains)

## Testing

### Test Manual Saves:

**Save Stock Data:**
```bash
curl -X POST "http://localhost:8000/api/market/save-daily-data?token=YOUR_TOKEN"
```

**Save Option Chains:**
```bash
curl -X POST "http://localhost:8000/api/market/save-option-chains?token=YOUR_TOKEN"
```

**Save All Data:**
```bash
curl -X POST "http://localhost:8000/api/market/save-all-daily-data?token=YOUR_TOKEN"
```

### Verify Data Saved:
- Check MongoDB collection `daily_stock_data` for saved stock records
- Check MongoDB collection `option_chain_data` for saved option chain records

### Test Change %:
1. Save data for today (manual save)
2. Wait for next day or manually update date
3. Fetch dashboard data - change % should be calculated from saved data

## Notes

- **First Day**: On the first day, there's no previous data, so mock change % is used
- **MongoDB Optional**: If MongoDB is not configured, the app still works but:
  - No daily data is saved
  - Change % uses mock data
  - Scheduled job logs warnings but doesn't fail
- **Timezone**: Scheduler uses UTC. Adjust `CronTrigger` in `startup_event()` if needed
- **Token Requirement**: Scheduled save requires a valid token in database. If no token exists, it logs a warning.

## Troubleshooting

### Scheduled job not running:
- Check backend logs for scheduler messages
- Verify MongoDB connection
- Check if valid token exists in database

### Change % showing mock data:
- Verify MongoDB is connected
- Check if previous day's data exists in `daily_stock_data` collection
- Manually trigger save to create initial data

### Option chain data not saving:
- Verify token has access to option chain API
- Check if expiry date is correct (next month's last Thursday)
- Verify MongoDB connection
- Check backend logs for specific errors

### Data not saving:
- Check MongoDB connection (`/api/test-db` endpoint)
- Verify token is valid
- Check backend logs for errors
- For option chains, ensure token hasn't expired (option chain API may require fresh token)

