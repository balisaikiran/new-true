#!/usr/bin/env python3
"""
ML Pipeline Data Fetcher
Fetches NIFTY data from deployed GraphQL API for machine learning pipelines.
"""

import httpx
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json


class NiftyDataClient:
    """Client to fetch NIFTY data from GraphQL API"""
    
    def __init__(self, base_url: str = "https://be.balisaikiran.com"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of your deployed backend (default: https://be.balisaikiran.com)
        """
        self.base_url = base_url.rstrip('/')
        self.graphql_url = f"{self.base_url}/graphql"
        self.client = httpx.Client(timeout=30.0)
    
    def _query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Response data as dictionary
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = self.client.post(
                self.graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                raise Exception(f"GraphQL errors: {result['errors']}")
            
            return result.get("data", {})
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error: {e}")
        except Exception as e:
            raise Exception(f"Error executing query: {e}")
    
    def fetch_data(
        self,
        name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10000,
        offset: int = 0
    ) -> pd.DataFrame:
        """
        Fetch NIFTY data and return as pandas DataFrame
        
        Args:
            name: Filter by index name ("NIFTY 50" or "NIFTY BANK")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of records (default: 10000)
            offset: Number of records to skip (for pagination)
            
        Returns:
            pandas DataFrame with columns: name, date, open, high, low, close, price, volume, change_percent
        """
        query = """
        query GetNiftyData($name: String, $startDate: String, $endDate: String, $limit: Int, $offset: Int) {
            niftyData(
                name: $name
                startDate: $startDate
                endDate: $endDate
                limit: $limit
                offset: $offset
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
        """
        
        variables = {
            "limit": limit,
            "offset": offset
        }
        
        if name:
            variables["name"] = name
        if start_date:
            variables["startDate"] = start_date
        if end_date:
            variables["endDate"] = end_date
        
        data = self._query(query, variables)
        records = data.get("niftyData", [])
        
        if not records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Convert date to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date (ascending for time series)
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def fetch_latest(self, name: Optional[str] = None, days: int = 1) -> pd.DataFrame:
        """
        Fetch latest N days of data
        
        Args:
            name: Filter by index name ("NIFTY 50" or "NIFTY BANK")
            days: Number of recent days to fetch
            
        Returns:
            pandas DataFrame with latest data
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return self.fetch_data(name=name, start_date=start_date, end_date=end_date)
    
    def fetch_all_historical(self, name: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch all historical data (with pagination)
        
        Args:
            name: Filter by index name ("NIFTY 50" or "NIFTY BANK")
            
        Returns:
            pandas DataFrame with all historical data
        """
        all_data = []
        offset = 0
        limit = 10000
        
        while True:
            df = self.fetch_data(name=name, limit=limit, offset=offset)
            
            if df.empty:
                break
            
            all_data.append(df)
            
            if len(df) < limit:
                break
            
            offset += limit
        
        if not all_data:
            return pd.DataFrame()
        
        return pd.concat(all_data, ignore_index=True).drop_duplicates(subset=['name', 'date'])
    
    def get_data_count(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """
        Get count of records
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Number of records
        """
        query = """
        query GetCount($startDate: String, $endDate: String) {
            niftyDataCount(startDate: $startDate, endDate: $endDate)
        }
        """
        
        variables = {}
        if start_date:
            variables["startDate"] = start_date
        if end_date:
            variables["endDate"] = end_date
        
        data = self._query(query, variables)
        return data.get("niftyDataCount", 0)
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage for ML pipelines
if __name__ == "__main__":
    # Initialize client
    client = NiftyDataClient(base_url="https://be.balisaikiran.com")
    
    print("📊 Fetching data for ML pipeline...\n")
    
    # Example 1: Fetch last 30 days of NIFTY 50 data
    print("1. Fetching last 30 days of NIFTY 50 data...")
    df_nifty50 = client.fetch_latest(name="NIFTY 50", days=30)
    print(f"   ✅ Got {len(df_nifty50)} records")
    print(f"   Date range: {df_nifty50['date'].min()} to {df_nifty50['date'].max()}")
    print(f"   Columns: {list(df_nifty50.columns)}\n")
    
    # Example 2: Fetch specific date range
    print("2. Fetching NIFTY BANK data for date range...")
    df_bank = client.fetch_data(
        name="NIFTY BANK",
        start_date="2025-01-01",
        end_date="2025-12-31"
    )
    print(f"   ✅ Got {len(df_bank)} records\n")
    
    # Example 3: Get all historical data (for training)
    print("3. Fetching all historical NIFTY 50 data...")
    df_all = client.fetch_all_historical(name="NIFTY 50")
    print(f"   ✅ Got {len(df_all)} records")
    print(f"   Date range: {df_all['date'].min()} to {df_all['date'].max()}\n")
    
    # Example 4: Prepare data for ML (feature engineering)
    print("4. Preparing data for ML...")
    if not df_nifty50.empty:
        # Calculate technical indicators
        df_nifty50['returns'] = df_nifty50['close'].pct_change()
        df_nifty50['volatility'] = df_nifty50['returns'].rolling(window=5).std()
        df_nifty50['sma_5'] = df_nifty50['close'].rolling(window=5).mean()
        df_nifty50['sma_20'] = df_nifty50['close'].rolling(window=20).mean()
        
        print("   ✅ Added features: returns, volatility, SMA_5, SMA_20")
        print(f"\n   Sample data:\n{df_nifty50[['date', 'close', 'returns', 'volatility', 'sma_5']].tail()}\n")
    
    # Example 5: Export to CSV for ML training
    print("5. Exporting to CSV...")
    if not df_nifty50.empty:
        df_nifty50.to_csv('nifty50_ml_data.csv', index=False)
        print("   ✅ Saved to nifty50_ml_data.csv")
    
    client.close()
    print("\n✅ Done!")

