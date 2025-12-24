#!/usr/bin/env python3
"""
Simple example: How to use the ML Data Fetcher
Run this to see how to integrate with your ML pipeline
"""

from ml_data_fetcher import NiftyDataClient
import pandas as pd

# ============================================
# EXAMPLE 1: Basic Data Fetching
# ============================================
print("=" * 60)
print("EXAMPLE 1: Basic Data Fetching")
print("=" * 60)

client = NiftyDataClient(base_url="https://be.balisaikiran.com")

# Fetch last 30 days
df = client.fetch_latest(name="NIFTY 50", days=30)
print(f"\n✅ Fetched {len(df)} records")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
print(f"\n   Latest 5 records:")
print(df[['date', 'close', 'volume', 'changePercent']].tail())

# ============================================
# EXAMPLE 2: Date Range Query
# ============================================
print("\n" + "=" * 60)
print("EXAMPLE 2: Date Range Query")
print("=" * 60)

df_range = client.fetch_data(
    name="NIFTY BANK",
    start_date="2025-12-01",
    end_date="2025-12-31"
)
print(f"\n✅ Fetched {len(df_range)} records for December 2025")

# ============================================
# EXAMPLE 3: Feature Engineering for ML
# ============================================
print("\n" + "=" * 60)
print("EXAMPLE 3: Feature Engineering for ML")
print("=" * 60)

# Get more data for feature engineering
df_features = client.fetch_latest(name="NIFTY 50", days=100)

# Calculate features
df_features['returns'] = df_features['close'].pct_change()
df_features['volatility'] = df_features['returns'].rolling(window=5).std()
df_features['sma_5'] = df_features['close'].rolling(window=5).mean()
df_features['sma_20'] = df_features['close'].rolling(window=20).mean()
df_features['rsi'] = calculate_rsi_simple(df_features['close'])

# Remove NaN rows
df_features = df_features.dropna()

print(f"\n✅ Created features: returns, volatility, sma_5, sma_20, rsi")
print(f"   Records with features: {len(df_features)}")
print(f"\n   Sample with features:")
print(df_features[['date', 'close', 'returns', 'volatility', 'sma_5', 'rsi']].tail())

# ============================================
# EXAMPLE 4: Export for ML Training
# ============================================
print("\n" + "=" * 60)
print("EXAMPLE 4: Export for ML Training")
print("=" * 60)

# Export to CSV
df_features.to_csv('nifty50_ml_ready.csv', index=False)
print("✅ Exported to: nifty50_ml_ready.csv")

# ============================================
# EXAMPLE 5: Real-time Prediction Data
# ============================================
print("\n" + "=" * 60)
print("EXAMPLE 5: Get Latest Data for Predictions")
print("=" * 60)

latest = client.fetch_latest(name="NIFTY 50", days=1)
if not latest.empty:
    latest_row = latest.iloc[-1]
    print(f"\n✅ Latest data for predictions:")
    print(f"   Date: {latest_row['date']}")
    print(f"   Close: {latest_row['close']}")
    print(f"   Volume: {latest_row['volume']}")
    print(f"   Change %: {latest_row.get('changePercent', 'N/A')}%")
    
    # You can use this data for real-time predictions
    features = {
        'open': latest_row['open'],
        'high': latest_row['high'],
        'low': latest_row['low'],
        'close': latest_row['close'],
        'volume': latest_row['volume']
    }
    print(f"\n   Features ready for model: {features}")

client.close()

print("\n" + "=" * 60)
print("✅ All examples completed!")
print("=" * 60)


# Helper function for RSI calculation
def calculate_rsi_simple(prices, period=14):
    """Simple RSI calculation"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

