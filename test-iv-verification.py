#!/usr/bin/env python3
"""
Script to verify IV calculation for a stock.
Usage: python test-iv-verification.py <SYMBOL> <TOKEN>
Example: python test-iv-verification.py NIFTY YOUR_TOKEN_HERE
"""

import sys
import requests
import json

def verify_iv(symbol: str, token: str, base_url: str = "http://localhost:8000"):
    """Verify IV calculation for a symbol"""
    url = f"{base_url}/api/market/verify-iv/{symbol}"
    params = {"token": token}
    
    print(f"\n🔍 Verifying IV for {symbol}...")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            return
        
        print(f"\n📊 IV Verification Results for {symbol}")
        print("=" * 60)
        
        # Spot Price
        print(f"\n📍 Spot Price: {data.get('spot_price', 'N/A')}")
        print(f"📅 Expiry Used: {data.get('expiry_used', 'N/A')}")
        
        # Cached IV
        cached = data.get('cached_iv', {})
        print(f"\n💾 Cached IV (from MongoDB):")
        print(f"   IV: {cached.get('iv', 'N/A')}%")
        print(f"   IV Percentile: {cached.get('iv_percentile', 'N/A')}%")
        print(f"   Source: {cached.get('source', 'N/A')}")
        
        # Calculated IV
        calculated = data.get('calculated_iv', {})
        print(f"\n🧮 Calculated IV (real-time):")
        print(f"   IV: {calculated.get('iv', 'N/A')}%")
        print(f"   IV Percentile: {calculated.get('iv_percentile', 'N/A')}%")
        print(f"   Source: {calculated.get('source', 'N/A')}")
        
        # Comparison
        comparison = data.get('comparison')
        if comparison:
            print(f"\n⚖️  Comparison:")
            print(f"   Difference: {comparison.get('difference', 'N/A')}%")
            print(f"   Difference %: {comparison.get('difference_percent', 'N/A')}%")
            match_status = "✅ MATCH" if comparison.get('match') else "❌ MISMATCH"
            print(f"   Status: {match_status}")
        
        # Calculation Details
        details = data.get('calculation_details', {})
        if details:
            print(f"\n🔧 Calculation Details:")
            print(f"   Method: {details.get('calculation_method', 'N/A')}")
            print(f"   Records Count: {details.get('records_count', 'N/A')}")
            if 'sample_option' in details:
                sample = details['sample_option']
                print(f"   Sample Option:")
                print(f"     Strike: {sample.get('strike', 'N/A')}")
                print(f"     Call Price: {sample.get('call_price', 'N/A')}")
                print(f"     Put Price: {sample.get('put_price', 'N/A')}")
        
        print(f"\n⏰ Timestamp: {data.get('timestamp', 'N/A')}")
        print("=" * 60)
        
        # Summary
        cached_iv = cached.get('iv')
        calc_iv = calculated.get('iv')
        
        if cached_iv and calc_iv:
            if comparison and comparison.get('match'):
                print(f"\n✅ VERIFICATION PASSED: IV values match!")
            else:
                print(f"\n⚠️  VERIFICATION WARNING: IV values differ")
                print(f"   Cached: {cached_iv}% vs Calculated: {calc_iv}%")
        elif calc_iv:
            print(f"\n✅ IV Calculated Successfully: {calc_iv}%")
        else:
            print(f"\n❌ Could not calculate IV")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test-iv-verification.py <SYMBOL> <TOKEN>")
        print("Example: python test-iv-verification.py NIFTY YOUR_TOKEN")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    token = sys.argv[2]
    
    # Optional: specify base URL
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"
    
    verify_iv(symbol, token, base_url)


