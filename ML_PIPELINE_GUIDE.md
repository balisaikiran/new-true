# ML Pipeline Integration Guide

This guide explains how to query NIFTY data from your deployed backend (`be.balisaikiran.com`) for machine learning pipelines.

## Quick Start

### 1. Install Dependencies

```bash
pip install httpx pandas
```

### 2. Basic Usage

```python
from ml_data_fetcher import NiftyDataClient

# Initialize client
client = NiftyDataClient(base_url="https://be.balisaikiran.com")

# Fetch last 30 days of NIFTY 50 data
df = client.fetch_latest(name="NIFTY 50", days=30)

# Fetch specific date range
df = client.fetch_data(
    name="NIFTY BANK",
    start_date="2025-01-01",
    end_date="2025-12-31"
)

# Fetch all historical data (for training)
df = client.fetch_all_historical(name="NIFTY 50")

client.close()
```

## API Endpoints

### GraphQL Endpoint
```
https://be.balisaikiran.com/graphql
```

### GraphQL Playground
```
https://be.balisaikiran.com/graphql
```
(Open in browser to test queries interactively)

## Available Queries

### 1. Fetch NIFTY Data

**Query:**
```graphql
query {
  niftyData(
    name: "NIFTY 50"
    startDate: "2025-01-01"
    endDate: "2025-12-31"
    limit: 1000
  ) {
    name
    date
    open
    high
    low
    close
    price
    volume
    changePercent
  }
}
```

**Python Example:**
```python
client = NiftyDataClient()
df = client.fetch_data(
    name="NIFTY 50",
    start_date="2025-01-01",
    end_date="2025-12-31",
    limit=1000
)
```

### 2. Get Data Count

**Query:**
```graphql
query {
  niftyDataCount(
    startDate: "2025-01-01"
    endDate: "2025-12-31"
  )
}
```

**Python Example:**
```python
count = client.get_data_count(
    start_date="2025-01-01",
    end_date="2025-12-31"
)
```

## ML Pipeline Examples

### Example 1: Time Series Forecasting

```python
from ml_data_fetcher import NiftyDataClient
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# Fetch data
client = NiftyDataClient()
df = client.fetch_all_historical(name="NIFTY 50")
client.close()

# Prepare features
df['returns'] = df['close'].pct_change()
df['volatility'] = df['returns'].rolling(window=5).std()
df['sma_5'] = df['close'].rolling(window=5).mean()
df['sma_20'] = df['close'].rolling(window=20).mean()
df['rsi'] = calculate_rsi(df['close'])  # Your RSI function

# Create sequences for LSTM/RNN
def create_sequences(data, seq_length=60):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

# Prepare data
features = ['close', 'volume', 'returns', 'volatility', 'sma_5', 'sma_20']
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df[features].dropna())

X, y = create_sequences(scaled_data, seq_length=60)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Train your model...
```

### Example 2: Daily Data Updates for Real-time Predictions

```python
from ml_data_fetcher import NiftyDataClient
import schedule
import time

def fetch_daily_data():
    """Fetch today's data for real-time predictions"""
    client = NiftyDataClient()
    
    # Get latest data
    df = client.fetch_latest(name="NIFTY 50", days=1)
    
    if not df.empty:
        # Process and make predictions
        latest = df.iloc[-1]
        print(f"Latest close: {latest['close']}")
        # Your prediction logic here
        
    client.close()

# Schedule to run daily at 4:30 PM IST (after market close)
schedule.every().day.at("16:30").do(fetch_daily_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Example 3: Feature Engineering for ML Models

```python
from ml_data_fetcher import NiftyDataClient
import pandas as pd
import talib  # Technical Analysis Library

client = NiftyDataClient()
df = client.fetch_all_historical(name="NIFTY 50")
client.close()

# Technical indicators
df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'].values)
df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'].values)
df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values)

# Price patterns
df['doji'] = talib.CDLDOJI(df['open'].values, df['high'].values, 
                           df['low'].values, df['close'].values)

# Volume indicators
df['volume_sma'] = df['volume'].rolling(window=20).mean()
df['volume_ratio'] = df['volume'] / df['volume_sma']

# Save for ML training
df.to_csv('nifty50_features.csv', index=False)
```

### Example 4: Batch Processing for Training

```python
from ml_data_fetcher import NiftyDataClient
import pandas as pd
from datetime import datetime, timedelta

def fetch_training_data(start_date: str, end_date: str):
    """Fetch data in batches for large datasets"""
    client = NiftyDataClient()
    
    all_data = []
    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Fetch in 3-month batches
    while current_start < end:
        batch_end = min(current_start + timedelta(days=90), end)
        
        df = client.fetch_data(
            name="NIFTY 50",
            start_date=current_start.strftime("%Y-%m-%d"),
            end_date=batch_end.strftime("%Y-%m-%d")
        )
        
        if not df.empty:
            all_data.append(df)
            print(f"Fetched {len(df)} records from {current_start.date()} to {batch_end.date()}")
        
        current_start = batch_end + timedelta(days=1)
    
    client.close()
    
    if all_data:
        return pd.concat(all_data, ignore_index=True).drop_duplicates(subset=['date'])
    return pd.DataFrame()

# Fetch 5 years of data
df = fetch_training_data("2020-01-01", "2025-12-31")
df.to_csv('nifty50_5years.csv', index=False)
```

## Alternative: REST API

You can also use the REST API endpoint:

```python
import httpx
import pandas as pd

def fetch_nifty_data_rest(start_date: str = None, end_date: str = None, limit: int = 10000):
    """
    Fetch data using REST API endpoint
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        limit: Maximum number of records
    """
    params = {"limit": limit}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    response = httpx.get(
        "https://be.balisaikiran.com/api/nifty/data",
        params=params,
        timeout=30.0
    )
    
    result = response.json()
    records = result.get("data", [])
    
    df = pd.DataFrame(records)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
    
    return df

# Usage
df = fetch_nifty_data_rest(start_date="2025-01-01", end_date="2025-12-31", limit=10000)
```

**REST API Endpoint:**
```
GET https://be.balisaikiran.com/api/nifty/data?start_date=2025-01-01&end_date=2025-12-31&limit=1000
```

## Direct GraphQL HTTP Requests

If you prefer direct HTTP requests without the client:

```python
import httpx
import pandas as pd

def fetch_nifty_data_graphql(name: str = None, start_date: str = None, end_date: str = None):
    query = """
    query GetNiftyData($name: String, $startDate: String, $endDate: String) {
        niftyData(name: $name, startDate: $startDate, endDate: $endDate, limit: 10000) {
            name
            date
            open
            high
            low
            close
            price
            volume
            changePercent
        }
    }
    """
    
    variables = {}
    if name:
        variables["name"] = name
    if start_date:
        variables["startDate"] = start_date
    if end_date:
        variables["endDate"] = end_date
    
    response = httpx.post(
        "https://be.balisaikiran.com/graphql",
        json={"query": query, "variables": variables},
        timeout=30.0
    )
    
    data = response.json()
    records = data.get("data", {}).get("niftyData", [])
    
    return pd.DataFrame(records)

# Usage
df = fetch_nifty_data_graphql(name="NIFTY 50", start_date="2025-01-01", end_date="2025-12-31")
```

## Data Schema

The returned data has the following structure:

```python
{
    "name": "NIFTY 50" | "NIFTY BANK",
    "date": "YYYY-MM-DD",
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "price": float,  # Same as close
    "volume": int,
    "changePercent": float  # Daily change percentage
}
```

## Error Handling

```python
from ml_data_fetcher import NiftyDataClient

try:
    client = NiftyDataClient()
    df = client.fetch_data(name="NIFTY 50")
except Exception as e:
    print(f"Error fetching data: {e}")
finally:
    client.close()
```

## Performance Tips

1. **Use date filters**: Always specify `start_date` and `end_date` to reduce data transfer
2. **Pagination**: For large datasets, use `offset` and `limit` parameters
3. **Caching**: Cache frequently accessed data locally
4. **Batch requests**: Fetch data in batches for very large date ranges

## Example: Complete ML Training Pipeline

```python
from ml_data_fetcher import NiftyDataClient
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

# 1. Fetch data
print("Fetching data...")
client = NiftyDataClient()
df = client.fetch_all_historical(name="NIFTY 50")
client.close()

# 2. Feature engineering
print("Engineering features...")
df['returns'] = df['close'].pct_change()
df['volatility'] = df['returns'].rolling(window=5).std()
df['sma_5'] = df['close'].rolling(window=5).mean()
df['sma_20'] = df['close'].rolling(window=20).mean()
df['target'] = df['close'].shift(-1)  # Predict next day's close

# 3. Prepare features
features = ['open', 'high', 'low', 'close', 'volume', 'returns', 'volatility', 'sma_5', 'sma_20']
df = df.dropna()

X = df[features]
y = df['target']

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 5. Train model
print("Training model...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. Evaluate
score = model.score(X_test, y_test)
print(f"Model R² score: {score:.4f}")

# 7. Save model
joblib.dump(model, 'nifty50_predictor.pkl')
print("Model saved!")

# 8. Make predictions on latest data
client = NiftyDataClient()
latest = client.fetch_latest(name="NIFTY 50", days=1)
client.close()

if not latest.empty:
    latest_features = latest[features].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(latest_features)
    print(f"Predicted next close: {prediction[0]:.2f}")
```

## Support

For issues or questions:
- Check GraphQL playground: `https://be.balisaikiran.com/graphql`
- Review API documentation in `graphql_schema.py`
- Test queries using the interactive GraphQL interface

