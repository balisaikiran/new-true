#!/bin/bash

# API Testing Script
# Tests your deployed Vercel API endpoints

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get API URL from user or use default
if [ -z "$1" ]; then
    echo -e "${YELLOW}⚠️  No API URL provided${NC}"
    echo "Usage: ./test-api.sh <your-vercel-url>"
    echo "Example: ./test-api.sh https://my-app.vercel.app"
    echo ""
    read -p "Enter your Vercel deployment URL (without trailing slash): " API_URL
else
    API_URL=$1
fi

# Remove trailing slash if present
API_URL=${API_URL%/}

echo ""
echo -e "${GREEN}🧪 Testing API Endpoints at: ${API_URL}${NC}"
echo ""

# Test 1: Root endpoint
echo -e "${YELLOW}Test 1: Root endpoint${NC}"
echo "GET ${API_URL}/api/"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/api/")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')
if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Success (HTTP $http_status)${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Failed (HTTP $http_status)${NC}"
    echo "$body"
fi
echo ""

# Test 2: Test DB endpoint
echo -e "${YELLOW}Test 2: Database connection test${NC}"
echo "GET ${API_URL}/api/test-db"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/api/test-db")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')
if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Success (HTTP $http_status)${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Failed (HTTP $http_status)${NC}"
    echo "$body"
fi
echo ""

# Test 3: Login endpoint (without credentials - should fail gracefully)
echo -e "${YELLOW}Test 3: Login endpoint (testing endpoint availability)${NC}"
echo "POST ${API_URL}/api/auth/login"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    "${API_URL}/api/auth/login")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')
if [ "$http_status" = "401" ] || [ "$http_status" = "422" ] || [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Endpoint is accessible (HTTP $http_status)${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Unexpected response (HTTP $http_status)${NC}"
    echo "$body"
fi
echo ""

# Test 4: Dashboard endpoint (requires auth token)
echo -e "${YELLOW}Test 4: Dashboard endpoint (requires authentication)${NC}"
echo "GET ${API_URL}/api/market/dashboard?token=test"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    "${API_URL}/api/market/dashboard?token=test")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')
if [ "$http_status" = "401" ] || [ "$http_status" = "422" ] || [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Endpoint is accessible (HTTP $http_status)${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Unexpected response (HTTP $http_status)${NC}"
    echo "$body"
fi
echo ""

echo -e "${GREEN}✅ Testing complete!${NC}"
echo ""
echo "📝 Note: Some endpoints require valid credentials to return data."
echo "   To test with real credentials, use the test-api-with-auth.sh script"
echo ""

