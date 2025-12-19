# 🕐 NIFTY Data Collection Cron Job

Automated daily collection of NIFTY OHLC data from TrueData API at 3:30 PM IST.

## ✅ What Was Added

1. **Scheduled Job**: Runs daily at 3:30 PM IST (10:00 AM UTC)
2. **TrueData Integration**: Fetches NIFTY data from TrueData API
3. **MongoDB Storage**: Automatically saves to `nifty_data` collection
4. **Manual Trigger**: API endpoint for manual testing

## 🕐 Schedule

- **Time**: 3:30 PM IST (10:00 AM UTC) daily
- **Timezone**: UTC (converted from IST)
- **Trigger**: Market close time (typical end of trading day)

## 📋 How It Works

### Automatic Collection Flow:

1. **3:30 PM IST Daily**:
   - Scheduler triggers `scheduled_nifty_data_collection()`
   - Gets latest TrueData token from MongoDB
   - Fetches current NIFTY price from TrueData API
   - Gets previous day's close from MongoDB (for open price)
   - Calculates OHLC:
     - **Close**: Current NIFTY price from TrueData
     - **Open**: Previous day's close (from MongoDB)
     - **High**: Max of open and close
     - **Low**: Min of open and close
   - Saves to MongoDB `nifty_data` collection

### Data Structure:

```json
{
  "date": "2025-12-05",
  "open": 26033.75,
  "high": 26100.50,
  "low": 25950.25,
  "close": 26050.00,
  "source": "TrueData API",
  "imported_at": "2025-12-05T10:00:00.000Z"
}
```

## 🧪 Manual Testing

### Test the Function Manually:

```bash
# Get a token first (login)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'

# Then fetch NIFTY data
curl -X POST "http://localhost:8000/api/nifty/fetch-from-truedata?token=YOUR_TOKEN"
```

### Expected Response:

```json
{
  "success": true,
  "message": "NIFTY data fetched and saved for 2025-12-05",
  "data": {
    "date": "2025-12-05",
    "open": 26033.75,
    "high": 26100.50,
    "low": 25950.25,
    "close": 26050.00,
    "source": "TrueData API",
    "imported_at": "2025-12-05T10:00:00.000Z"
  }
}
```

## 📊 Verify Data

### Check via GraphQL:

```graphql
query {
  niftyDataByDate(date: "2025-12-05") {
    date
    open
    high
    low
    close
    importedAt
  }
}
```

### Check via REST API:

```bash
curl "http://localhost:8000/api/nifty/data?limit=5"
```

## 🔧 Configuration

### Scheduler Settings:

The cron job is configured in `backend/server.py`:

```python
scheduler.add_job(
    scheduled_nifty_data_collection,
    trigger=CronTrigger(hour=10, minute=0),  # 10:00 AM UTC = 3:30 PM IST
    id="nifty_data_collection",
    name="Daily NIFTY Data Collection from TrueData",
    replace_existing=True
)
```

### To Change Time:

Edit the `CronTrigger` in `backend/server.py`:
- `hour=10, minute=0` = 10:00 AM UTC = 3:30 PM IST
- Adjust `hour` and `minute` as needed

## 📝 Requirements

1. **TrueData Credentials**: Must have valid login token in MongoDB
2. **MongoDB Connection**: Must be configured and connected
3. **Server Running**: Backend server must be running for scheduler to work

## 🚨 Troubleshooting

### Issue: No data collected

**Check:**
1. Server logs for scheduler messages
2. MongoDB connection status
3. TrueData token validity

**Solution:**
- Ensure server is running
- Check MongoDB connection: `GET /api/test-db`
- Verify token exists: Check `tokens` collection in MongoDB

### Issue: Wrong time

**Solution:**
- Check server timezone
- Adjust `CronTrigger` hour/minute
- IST is UTC+5:30, so 3:30 PM IST = 10:00 AM UTC

### Issue: Missing previous day data

**Solution:**
- First run will use current price as open
- Subsequent runs will use previous day's close
- Import historical data first: `python3 backend/import_nifty_data.py`

## 📈 Logs

Check server logs for:
```
🕐 Scheduled NIFTY data collection started (3:30 PM IST)
Fetching NIFTY OHLC data from TrueData API...
✅ Successfully saved NIFTY data for 2025-12-05
```

## ✅ Status

The cron job is **active** and will run automatically every day at 3:30 PM IST.

To verify it's scheduled, check server startup logs:
```
Scheduler started:
  - Daily stock data save: 10:00 AM UTC (3:30 PM IST)
  - NIFTY data collection: 10:00 AM UTC (3:30 PM IST)
```

