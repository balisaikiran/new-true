#!/usr/bin/env python3
"""
Interactive API Testing Script with Authentication
Tests your deployed Vercel API endpoints with real credentials
"""

import requests
import json
import sys
from typing import Optional

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")

def get_api_url() -> str:
    """Get API URL from command line or prompt user"""
    if len(sys.argv) > 1:
        api_url = sys.argv[1].rstrip('/')
    else:
        api_url = input("Enter your Vercel deployment URL (without trailing slash): ").strip().rstrip('/')
    
    if not api_url:
        print_error("API URL is required")
        sys.exit(1)
    
    return api_url

def test_endpoint(method: str, url: str, headers: Optional[dict] = None, data: Optional[dict] = None) -> tuple:
    """Test an API endpoint and return (success, status_code, response_data)"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            return False, 0, {"error": "Unsupported method"}
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        success = 200 <= response.status_code < 300
        return success, response.status_code, response_data
    
    except requests.exceptions.RequestException as e:
        return False, 0, {"error": str(e)}

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}🧪 API Testing Script with Authentication{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")
    
    api_url = get_api_url()
    base_url = f"{api_url}/api"
    
    print_info(f"Testing API at: {base_url}\n")
    
    # Test 1: Root endpoint
    print("Test 1: Root endpoint")
    print(f"GET {base_url}/")
    success, status, data = test_endpoint('GET', f"{base_url}/")
    if success:
        print_success(f"Success (HTTP {status})")
    else:
        print_error(f"Failed (HTTP {status})")
    print(json.dumps(data, indent=2))
    print()
    
    # Test 2: Database connection
    print("Test 2: Database connection test")
    print(f"GET {base_url}/test-db")
    success, status, data = test_endpoint('GET', f"{base_url}/test-db")
    if success:
        print_success(f"Success (HTTP {status})")
    else:
        print_error(f"Failed (HTTP {status})")
    print(json.dumps(data, indent=2))
    print()
    
    # Test 3: Login (interactive)
    print("Test 3: Login with TrueData credentials")
    username = input("Enter TrueData username: ").strip()
    password = input("Enter TrueData password: ").strip()
    
    if not username or not password:
        print_warning("Skipping login test (no credentials provided)")
    else:
        print(f"POST {base_url}/auth/login")
        login_data = {"username": username, "password": password}
        success, status, data = test_endpoint('POST', f"{base_url}/auth/login", data=login_data)
        
        if success and data.get('success'):
            print_success(f"Login successful (HTTP {status})")
            access_token = data.get('access_token')
            expires_in = data.get('expires_in')
            print_info(f"Token expires in: {expires_in} seconds")
            
            # Test 4: Dashboard with token
            print("\nTest 4: Dashboard data")
            print(f"GET {base_url}/market/dashboard?token={access_token[:20]}...")
            success, status, dashboard_data = test_endpoint('GET', f"{base_url}/market/dashboard?token={access_token}")
            
            if success:
                print_success(f"Dashboard data retrieved (HTTP {status})")
                if isinstance(dashboard_data, dict) and 'data' in dashboard_data:
                    stocks_count = len(dashboard_data.get('data', []))
                    print_info(f"Retrieved data for {stocks_count} stocks")
                    # Show first 3 stocks as sample
                    for stock in dashboard_data.get('data', [])[:3]:
                        print(f"  - {stock.get('symbol')}: {stock.get('spot')}")
            else:
                print_error(f"Failed to get dashboard data (HTTP {status})")
                print(json.dumps(dashboard_data, indent=2))
            
            # Test 5: Option Chain (interactive)
            print("\nTest 5: Option Chain")
            symbol = input("Enter symbol for option chain (e.g., NIFTY, RELIANCE): ").strip().upper()
            expiry = input("Enter expiry date (YYYY-MM-DD) or press Enter for default: ").strip()
            
            if symbol:
                if not expiry:
                    expiry = "2024-12-26"  # Default expiry
                    print_info(f"Using default expiry: {expiry}")
                
                print(f"GET {base_url}/market/optionchain/{symbol}?expiry={expiry}&token={access_token[:20]}...")
                success, status, option_data = test_endpoint('GET', 
                    f"{base_url}/market/optionchain/{symbol}?expiry={expiry}&token={access_token}")
                
                if success:
                    print_success(f"Option chain retrieved (HTTP {status})")
                    print(json.dumps(option_data, indent=2)[:500] + "..." if len(str(option_data)) > 500 else json.dumps(option_data, indent=2))
                else:
                    print_error(f"Failed to get option chain (HTTP {status})")
                    print(json.dumps(option_data, indent=2))
        else:
            print_error(f"Login failed (HTTP {status})")
            print(json.dumps(data, indent=2))
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print_success("Testing complete!")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)

