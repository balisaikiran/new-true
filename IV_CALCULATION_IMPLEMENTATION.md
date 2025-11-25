# Real IV% Calculation Implementation

## Overview
This document explains the implementation of real Implied Volatility (IV) and IV Percentile calculation, replacing the previous mock data approach.

## Reference
Based on Investopedia's explanation: https://www.investopedia.com/terms/i/iv.asp

## Implementation Details

### 1. IV Extraction (`extract_iv_from_option_chain`)

**Location**: `backend/server.py` (lines 235-305)

**Function**: Extracts Implied Volatility from option chain data returned by TrueData API.

**Logic**:
1. **Direct IV Check**: First checks if IV is directly provided in the option chain response (fields: `IV`, `impliedVolatility`, `iv`)
2. **Records Array Parsing**: If not found directly, parses the `Records` array from TrueData API
3. **ATM Option Selection**: Finds At-The-Money (ATM) options - options with strike price closest to current spot price
4. **IV Extraction**: Extracts IV values from ATM options (IV typically ranges from 5% to 150%)
5. **Fallback**: Returns average IV if multiple IVs found, or None if extraction fails

**Why ATM Options?**
- ATM options are most liquid and provide the most representative IV
- They reflect current market expectations of volatility

### 2. IV Percentile Calculation (`calculate_iv_percentile`)

**Location**: `backend/server.py` (lines 308-349)

**Function**: Calculates IV Percentile using historical IV data stored in MongoDB.

**Formula**:
```
IV Percentile = (Number of days IV was below current IV) / (Total number of days) × 100
```

**Logic**:
1. **Historical Data Retrieval**: Fetches last 252 trading days (1 year) of IV data from MongoDB
2. **Comparison**: Counts how many historical days had IV below current IV
3. **Percentile Calculation**: Calculates percentage rank of current IV
4. **Result**: Returns percentile value (0-100%)

**Example**:
- Historical IVs: [15, 18, 20, 22, 25, 28, 30, 32, 35, 40]
- Current IV: 28
- Days below: 5 (15, 18, 20, 22, 25)
- IV Percentile: (5/10) × 100 = 50%

**What IV Percentile Means**:
- **High IV% (70-100%)**: Current IV is higher than most historical values → Options are expensive
- **Low IV% (0-30%)**: Current IV is lower than most historical values → Options are cheap
- **Medium IV% (30-70%)**: Current IV is around average historical levels

### 3. Daily Data Storage (`save_daily_stock_data`)

**Location**: `backend/server.py` (lines 430-503)

**Changes**:
- Now fetches option chain data for each symbol
- Extracts real IV using `extract_iv_from_option_chain`
- Calculates IV percentile using `calculate_iv_percentile`
- Stores both IV and IV percentile in MongoDB

**Fallback Strategy**:
1. Try to extract IV from option chain
2. If extraction fails, use previous day's IV (if available)
3. Only use mock IV as last resort (for first-time setup)

### 4. Dashboard Data Fetching (`fetch_stock_data`)

**Location**: `backend/server.py` (lines 556-640)

**Changes**:
- Fetches option chain data in real-time
- Extracts current IV from option chain
- Calculates IV percentile using historical data
- Falls back to previous day's data if current extraction fails

**Priority Order**:
1. **Current IV from option chain** (most accurate)
2. **Previous day's IV** (if current extraction fails)
3. **Mock IV** (only if no historical data exists)

## Data Flow

```
1. User requests dashboard data
   ↓
2. fetch_stock_data() called
   ↓
3. Fetch spot price from TrueData API
   ↓
4. Fetch option chain data from TrueData API
   ↓
5. extract_iv_from_option_chain() extracts IV
   ↓
6. calculate_iv_percentile() calculates percentile from historical data
   ↓
7. Return StockData with real IV and IV percentile
```

## Daily Data Collection

```
1. Scheduled job runs at 3:30 PM IST (end of trading day)
   ↓
2. save_daily_stock_data() called for each symbol
   ↓
3. Fetch spot price and option chain
   ↓
4. Extract and store IV
   ↓
5. Calculate and store IV percentile
   ↓
6. Save to MongoDB for future percentile calculations
```

## MongoDB Collections Used

### `daily_stock_data`
Stores daily stock data including:
- `symbol`: Stock symbol
- `date`: Date (YYYY-MM-DD)
- `spot`: Spot price
- `iv`: Implied Volatility (extracted from option chain)
- `iv_percentile`: IV Percentile (calculated from historical data)
- `volume`: Trading volume
- `saved_at`: Timestamp

## Important Notes

1. **Historical Data Requirement**: IV Percentile requires historical IV data. On first run, percentile will be `None` until enough historical data is collected.

2. **Option Chain Dependency**: Real IV extraction depends on option chain data availability. If TrueData API doesn't provide IV directly, the extraction logic attempts to find it in the Records array.

3. **Fallback Behavior**: The system gracefully falls back to previous day's data or mock data if real extraction fails, ensuring the dashboard always shows values.

4. **Performance**: Option chain fetching adds API calls. Consider caching or using background jobs for better performance.

5. **IV Range**: The extraction logic assumes IV values are between 5% and 150%. Values outside this range are filtered out.

## Testing

To test the implementation:

1. **Manual Save**: Trigger daily data save to collect IV data
   ```bash
   curl -X POST "http://localhost:8000/api/market/save-daily-data?token=YOUR_TOKEN"
   ```

2. **Check Dashboard**: View dashboard to see real IV values
   ```bash
   curl "http://localhost:8000/api/market/dashboard?token=YOUR_TOKEN"
   ```

3. **Verify MongoDB**: Check stored IV data
   ```javascript
   db.daily_stock_data.find({symbol: "NIFTY"}).sort({date: -1}).limit(5)
   ```

## Future Improvements

1. **Black-Scholes Calculation**: If TrueData API doesn't provide IV directly, implement Black-Scholes model to calculate IV from option prices.

2. **IV Rank**: Add IV Rank calculation (current IV vs 52-week high/low range).

3. **Caching**: Cache option chain data to reduce API calls.

4. **Error Handling**: Improve error handling for edge cases in IV extraction.

5. **Validation**: Add validation to ensure extracted IV values are reasonable.

## References

- [Investopedia: Implied Volatility](https://www.investopedia.com/terms/i/iv.asp)
- [IV Percentile Explanation](https://www.investopedia.com/terms/i/iv.asp)

