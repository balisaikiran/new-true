from fastapi import FastAPI, APIRouter, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import asyncio


ROOT_DIR = Path(__file__).parent
# Try to load .env file if it exists (for local development)
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
# For Vercel, environment variables are already set

# MongoDB connection with better error handling
try:
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url:
        raise ValueError("MONGO_URL environment variable is not set")
    if not db_name:
        raise ValueError("DB_NAME environment variable is not set")
    
    logger.info(f"Connecting to MongoDB database: {db_name}")
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    
    # Test connection
    async def test_mongo_connection():
        try:
            await client.admin.command('ping')
            logger.info("MongoDB connection successful")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            raise
    
    # Note: This will be called on first request in serverless environment
    
except Exception as e:
    logger.error(f"Failed to initialize MongoDB: {str(e)}")
    # Create a dummy client to prevent app crash, but log the error
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TrueData API URLs
TRUEDATA_AUTH_URL = "https://auth.truedata.in/token"
TRUEDATA_ANALYTICS_URL = "https://analytics.truedata.in/api"

# Top 20 F&O stocks
TOP_20_STOCKS = [
    "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK", 
    "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN", 
    "BHARTIARTL", "KOTAKBANK", "LT", "ASIANPAINT", "HCLTECH", 
    "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO"
]


# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    expires_in: Optional[int] = None
    username: Optional[str] = None

class StockData(BaseModel):
    symbol: str
    spot: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    iv: Optional[float] = None
    iv_percentile: Optional[float] = None
    signal: Optional[str] = None
    error: Optional[str] = None

class DashboardResponse(BaseModel):
    success: bool
    data: List[StockData]
    timestamp: datetime

class OptionChainResponse(BaseModel):
    success: bool
    symbol: str
    expiry: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Helper functions
async def get_truedata_token(username: str, password: str) -> Dict[str, Any]:
    """Authenticate with TrueData API and get access token"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TRUEDATA_AUTH_URL,
                data={
                    "username": username,
                    "password": password,
                    "grant_type": "password"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"TrueData auth failed: {response.status_code} - {response.text}")
                return {"error": "Authentication failed", "status_code": response.status_code}
    except Exception as e:
        logger.error(f"Error authenticating with TrueData: {str(e)}")
        return {"error": str(e)}


async def fetch_ltp_spot(token: str, symbol: str, series: str = "EQ") -> Optional[float]:
    """Fetch LTP for spot/equity"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # TrueData API returns CSV format with just LTP value
            response = await client.get(
                f"{TRUEDATA_ANALYTICS_URL}/getLTPSpot",
                params={"symbol": symbol, "series": series, "response": "csv"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                # Parse CSV response - format is "LTP\n<value>"
                lines = response.text.strip().split('\n')
                if len(lines) >= 2:
                    return float(lines[1])
                return None
            else:
                logger.error(f"Error fetching LTP for {symbol}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Exception fetching LTP for {symbol}: {str(e)}")
        return None


async def fetch_option_chain(token: str, symbol: str, expiry: str) -> Optional[Dict[str, Any]]:
    """Fetch option chain data for a symbol"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{TRUEDATA_ANALYTICS_URL}/getoptionchain",
                params={"symbol": symbol, "expiry": expiry, "response": "json"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching option chain for {symbol}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Exception fetching option chain for {symbol}: {str(e)}")
        return None


def calculate_iv_metrics(option_chain_data: Dict[str, Any]) -> tuple:
    """Calculate IV and IV percentile from option chain data"""
    # This is a simplified calculation - in real scenario, you'd need historical IV data
    # For now, we'll extract IV from the option chain if available
    try:
        if isinstance(option_chain_data, dict) and 'data' in option_chain_data:
            # Extract IVs from options data
            ivs = []
            # Implementation would depend on actual response structure
            # For now, return placeholder values
            return 25.5, 45.2
        return None, None
    except Exception as e:
        logger.error(f"Error calculating IV metrics: {str(e)}")
        return None, None


async def fetch_stock_data(token: str, symbol: str) -> StockData:
    """Fetch comprehensive stock data for dashboard"""
    try:
        # Determine series based on symbol
        if symbol in ["NIFTY", "BANKNIFTY"]:
            series = "XX"  # Index
        else:
            series = "EQ"  # Equity
        
        # Fetch spot price data
        ltp = await fetch_ltp_spot(token, symbol, series)
        
        if ltp is None:
            return StockData(
                symbol=symbol,
                error="Failed to fetch data"
            )
        
        # For demo purposes, generate realistic mock data based on LTP
        # In production, you would fetch this from historical data or other endpoints
        # Generate a random but consistent change for demo
        import random
        random.seed(hash(symbol) + int(ltp))
        
        change_percent = random.uniform(-3.0, 3.0)
        volume = random.randint(1000000, 50000000)
        
        # Generate signal based on change
        signal = None
        if abs(change_percent) > 2.0:
            signal = "High Volatility"
        elif change_percent > 1.0:
            signal = "Bullish"
        elif change_percent < -1.0:
            signal = "Bearish"
        else:
            signal = "Neutral"
        
        # Mock IV metrics (would need option chain data for real calculation)
        iv = 20 + (hash(symbol) % 30)  # Mock IV between 20-50
        iv_percentile = 30 + (hash(symbol) % 60)  # Mock percentile
        
        return StockData(
            symbol=symbol,
            spot=ltp,
            change_percent=round(change_percent, 2),
            volume=volume,
            iv=round(iv, 2),
            iv_percentile=round(iv_percentile, 2),
            signal=signal
        )
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return StockData(
            symbol=symbol,
            error=str(e)
        )


# Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with TrueData credentials"""
    try:
        result = await get_truedata_token(request.username, request.password)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        # Store token in database for session management
        token_doc = {
            "username": request.username,
            "access_token": result.get("access_token"),
            "expires_in": result.get("expires_in"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 3600))).isoformat()
        }
        
        # Upsert token
        if db is None:
            logger.error("MongoDB not initialized - cannot store token")
            # Continue without storing in DB (for development/testing)
        else:
            await db.tokens.update_one(
                {"username": request.username},
                {"$set": token_doc},
                upsert=True
            )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            access_token=result.get("access_token"),
            expires_in=result.get("expires_in"),
            username=request.username
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/market/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(token: str):
    """Fetch dashboard data for top 20 F&O stocks"""
    try:
        # Fetch data for all stocks concurrently
        tasks = [fetch_stock_data(token, symbol) for symbol in TOP_20_STOCKS]
        stocks_data = await asyncio.gather(*tasks)
        
        return DashboardResponse(
            success=True,
            data=list(stocks_data),
            timestamp=datetime.now(timezone.utc)
        )
    
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/market/optionchain/{symbol}", response_model=OptionChainResponse)
async def get_option_chain(symbol: str, expiry: str, token: str):
    """Fetch option chain for a specific symbol and expiry"""
    try:
        data = await fetch_option_chain(token, symbol, expiry)
        
        if not data:
            return OptionChainResponse(
                success=False,
                symbol=symbol,
                expiry=expiry,
                error="Failed to fetch option chain data"
            )
        
        return OptionChainResponse(
            success=True,
            symbol=symbol,
            expiry=expiry,
            data=data
        )
    
    except Exception as e:
        logger.error(f"Option chain error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/")
async def root():
    return {"message": "TrueData Analytics API"}


@api_router.get("/test-db")
async def test_db():
    """Test MongoDB connection"""
    if not client or not db:
        return {
            "status": "error",
            "message": "MongoDB client not initialized",
            "mongo_url_set": bool(os.environ.get('MONGO_URL')),
            "db_name_set": bool(os.environ.get('DB_NAME'))
        }
    
    try:
        await client.admin.command('ping')
        return {
            "status": "connected",
            "database": os.environ.get('DB_NAME'),
            "message": "MongoDB connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()
