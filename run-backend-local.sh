#!/bin/bash

# Local Backend Testing Script
# Runs the FastAPI backend server locally for testing

echo "🚀 Starting Backend Server Locally..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Check for .env file
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found in backend/ directory${NC}"
    echo -e "${YELLOW}   The app will use environment variables or defaults${NC}"
    echo ""
fi

# Set default port
PORT=${1:-8000}

echo -e "${GREEN}🌐 Starting server on http://localhost:${PORT}${NC}"
echo -e "${YELLOW}📝 API will be available at: http://localhost:${PORT}/api/${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the server
cd backend
uvicorn server:app --host 0.0.0.0 --port $PORT --reload

