# Daily Data Storage & Change Percentage Feature

## Overview
This feature implements automatic end-of-day data storage to MongoDB and calculates change percentages based on previous day's closing prices.

## Features Implemented

### 1. Daily Data Storage
- **Collection**: `daily_stock_data` in MongoDB
- **Structure**: Each document contains:
  - `symbol`: Stock symbol (e.g., "NIFTY", "RELIANCE")
  - `date`: Date in YYYY-MM-DD format
  - `spot`: Closing spot price
  - `volume`: Trading volume
  - `iv`: Implied Volatility
  - `iv_percentile`: IV Percentile
  - `saved_at`: Timestamp when data was saved

### 2. Automatic End-of-Day Save
- **Scheduled Time**: 10:00 AM UTC (3:30 PM IST) - typical market close time
- **Scheduler**: APScheduler (AsyncIOScheduler)
- **Function**: `scheduled_end_of_day_save()` automatically saves data for all 20 F&O stocks

### 3. Change Percentage Calculation
- **Method**: Compares current spot price with previous day's closing price
- **Formula**: `((current_price - previous_close) / previous_close) * 100`
- **Fallback**: If no previous day data exists, uses mock data (for first day)

### 4. Previous Day Data Retrieval
- **Function**: `get_previous_day_data(symbol)`
- **Logic**:
  1. First tries to get yesterday's data
  2. If not found, gets the most recent data before today
  3. Returns None if no historical data exists

### 5. Manual Save Endpoint
- **Endpoint**: `POST /api/market/save-daily-data?token=<token>`
- **Purpose**: Manually trigger end-of-day data save (useful for testing)
- **Response**: Returns count of stocks saved and date

## How It Works

### Daily Flow:
1. **During Trading Hours**: 
   - Dashboard fetches live data from TrueData API
   - Change % is calculated using previous day's closing price from MongoDB
   - If no previous data exists, mock data is used

2. **End of Day (3:30 PM IST)**:
   - Scheduler automatically triggers `save_daily_stock_data()`
   - Fetches current spot prices for all stocks
   - Saves to MongoDB with today's date

3. **Next Day**:
   - Dashboard uses yesterday's saved data as reference
   - Calculates accurate change % based on previous close

## MongoDB Setup

### Required Environment Variables:
```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=truedata
```

### Collection Structure:
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

## API Endpoints

### Get Dashboard Data (with change %)
```
GET /api/market/dashboard?token=<token>
```
- Returns current market data with change % calculated from previous day

### Manual Save Daily Data
```
POST /api/market/save-daily-data?token=<token>
```
- Manually triggers end-of-day data save
- Useful for testing or if scheduled job fails

## Code Changes

### New Dependencies:
- `apscheduler==3.10.4` - For scheduled tasks

### Modified Functions:
- `fetch_stock_data()` - Now calculates change % from previous day's data
- Added `get_previous_day_data()` - Retrieves historical data
- Added `save_daily_stock_data()` - Saves end-of-day data
- Added `scheduled_end_of_day_save()` - Scheduled job function

### New Endpoints:
- `POST /api/market/save-daily-data` - Manual save trigger

## Testing

### Test Manual Save:
```bash
curl -X POST "http://localhost:8000/api/market/save-daily-data?token=YOUR_TOKEN"
```

### Verify Data Saved:
Check MongoDB collection `daily_stock_data` for saved records.

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

### Data not saving:
- Check MongoDB connection (`/api/test-db` endpoint)
- Verify token is valid
- Check backend logs for errors

