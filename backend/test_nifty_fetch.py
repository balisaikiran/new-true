#!/usr/bin/env python3
"""Test script for NIFTY data fetch function"""
import asyncio
import sys
from datetime import datetime
from server import fetch_nifty_ohlc_from_truedata, save_nifty_data_to_db

async def test_nifty_fetch():
    """Test fetching NIFTY data"""
    print("🧪 Testing NIFTY data fetch...")
    print("=" * 60)
    
    # Get token from command line or use test token
    token = sys.argv[1] if len(sys.argv) > 1 else "test_token"
    
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Token: {token[:20]}..." if len(token) > 20 else f"🔑 Token: {token}")
    print()
    
    try:
        # Fetch NIFTY OHLC data
        print("1️⃣ Fetching NIFTY OHLC data...")
        nifty_data = await fetch_nifty_ohlc_from_truedata(token)
        
        if nifty_data:
            print("✅ Successfully fetched NIFTY data!")
            print()
            print("📊 Data:")
            print(f"   Date: {nifty_data['date']}")
            print(f"   Open:  {nifty_data['open']}")
            print(f"   High:  {nifty_data['high']}")
            print(f"   Low:   {nifty_data['low']}")
            print(f"   Close: {nifty_data['close']}")
            print(f"   Source: {nifty_data.get('source', 'Unknown')}")
            print()
            
            # Save to database
            print("2️⃣ Saving to MongoDB...")
            success = await save_nifty_data_to_db(nifty_data)
            
            if success:
                print("✅ Successfully saved to MongoDB!")
                print()
                print("🎉 Test completed successfully!")
                return True
            else:
                print("❌ Failed to save to MongoDB")
                return False
        else:
            print("❌ Failed to fetch NIFTY data")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_nifty_fetch())
    sys.exit(0 if result else 1)







