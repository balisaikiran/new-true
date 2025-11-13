#!/usr/bin/env python3
"""
Interactive Local API Testing Script
Tests your locally running backend API with real credentials
"""

import requests
import json
import sys

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

# Get API URL from command line or use default
if len(sys.argv) > 1:
    api_url = sys.argv[1].rstrip('/')
else:
    api_url = "http://localhost:8000"

print(f"\n{Colors.BLUE}🧪 Testing Local Backend API{Colors.NC}")
print(f"{Colors.BLUE}📍 URL: {api_url}{Colors.NC}\n")

# Test 1: Root endpoint
print_info("Test 1: Root endpoint")
try:
    response = requests.get(f"{api_url}/api/", timeout=5)
    if response.status_code == 200:
        print_success(f"Root endpoint works (HTTP {response.status_code})")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Root endpoint failed (HTTP {response.status_code})")
        print(response.text)
except requests.exceptions.ConnectionError:
    print_error("Cannot connect to server. Is it running?")
    print_info("Start the server with: ./run-backend-local.sh")
    sys.exit(1)
except Exception as e:
    print_error(f"Error: {e}")

print()

# Test 2: Database test
print_info("Test 2: Database connection test")
try:
    response = requests.get(f"{api_url}/api/test-db", timeout=5)
    if response.status_code == 200:
        print_success(f"Database test works (HTTP {response.status_code})")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Database test failed (HTTP {response.status_code})")
        print(response.text)
except Exception as e:
    print_error(f"Error: {e}")

print()

# Test 3: Health check
print_info("Test 3: Health check")
try:
    response = requests.get(f"{api_url}/api/health", timeout=5)
    if response.status_code == 200:
        print_success(f"Health check works (HTTP {response.status_code})")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Health check failed (HTTP {response.status_code})")
        print(response.text)
except Exception as e:
    print_error(f"Error: {e}")

print()

# Test 4: Login (interactive)
print_info("Test 4: Login endpoint")
print_warning("This requires valid TrueData credentials")
use_real_creds = input("Do you want to test login with real credentials? (y/n): ").lower().strip()

if use_real_creds == 'y':
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    
    try:
        response = requests.post(
            f"{api_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Login successful (HTTP {response.status_code})")
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # If login successful, test dashboard
            if "access_token" in data or "token" in data:
                token = data.get("access_token") or data.get("token")
                print_info("\nTest 5: Dashboard endpoint")
                try:
                    dashboard_response = requests.get(
                        f"{api_url}/api/market/dashboard",
                        params={"token": token},
                        timeout=10
                    )
                    if dashboard_response.status_code == 200:
                        print_success(f"Dashboard works (HTTP {dashboard_response.status_code})")
                        print(json.dumps(dashboard_response.json(), indent=2))
                    else:
                        print_error(f"Dashboard failed (HTTP {dashboard_response.status_code})")
                        print(dashboard_response.text)
                except Exception as e:
                    print_error(f"Dashboard error: {e}")
        else:
            print_error(f"Login failed (HTTP {response.status_code})")
            print(response.text)
    except Exception as e:
        print_error(f"Error: {e}")
else:
    print_info("Skipping login test")

print()
print_success("Testing complete!")

