#!/bin/bash

# Local Backend Testing Script
# Tests the locally running backend API

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default URL
API_URL=${1:-http://localhost:8000}

echo ""
echo -e "${BLUE}🧪 Testing Local Backend API${NC}"
echo -e "${BLUE}📍 URL: ${API_URL}${NC}"
echo ""

# Test 1: Root endpoint
echo -e "${YELLOW}Test 1: Root endpoint${NC}"
echo "GET ${API_URL}/api/"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/api/")
http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS/d')

if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Success (HTTP ${http_status})${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Failed (HTTP ${http_status})${NC}"
    echo "$body"
fi
echo ""

# Test 2: Database test
echo -e "${YELLOW}Test 2: Database connection test${NC}"
echo "GET ${API_URL}/api/test-db"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/api/test-db")
http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS/d')

if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Success (HTTP ${http_status})${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Failed (HTTP ${http_status})${NC}"
    echo "$body"
fi
echo ""

# Test 3: Health check
echo -e "${YELLOW}Test 3: Health check${NC}"
echo "GET ${API_URL}/api/health"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/api/health")
http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS/d')

if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Success (HTTP ${http_status})${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Failed (HTTP ${http_status})${NC}"
    echo "$body"
fi
echo ""

# Test 4: Login endpoint (without credentials - should fail gracefully)
echo -e "${YELLOW}Test 4: Login endpoint (testing endpoint availability)${NC}"
echo "POST ${API_URL}/api/auth/login"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    "${API_URL}/api/auth/login")
http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS/d')

if [ "$http_status" = "401" ] || [ "$http_status" = "422" ] || [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Endpoint exists (HTTP ${http_status})${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Unexpected response (HTTP ${http_status})${NC}"
    echo "$body"
fi
echo ""

echo -e "${GREEN}✅ Testing complete!${NC}"
echo ""
echo -e "${BLUE}💡 Tip: To test with real credentials, use:${NC}"
echo -e "   curl -X POST ${API_URL}/api/auth/login \\"
echo -e "     -H 'Content-Type: application/json' \\"
echo -e "     -d '{\"username\":\"YOUR_USERNAME\",\"password\":\"YOUR_PASSWORD\"}'"

