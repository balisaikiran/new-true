from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv
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
import traceback


ROOT_DIR = Path(__file__).parent
# Try to load .env file if it exists (for local development)
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
# For Vercel, environment variables are already set

# Configure logging first (needed for MongoDB connection logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection with better error handling (optional)
# MongoDB is only used for storing login tokens - app works without it
# IMPORTANT: Don't block initialization - MongoDB connection is lazy
client = None
db = None

def init_mongodb():
    """Initialize MongoDB connection (non-blocking, called lazily)"""
    global client, db
    if client is not None or db is not None:
        return  # Already initialized
    
    try:
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        
        if mongo_url and db_name:
            try:
                logger.info(f"Connecting to MongoDB database: {db_name}")
                # Use very short timeout to avoid blocking
                client = AsyncIOMotorClient(
                    mongo_url, 
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000
                )
                db = client[db_name]
                logger.info("MongoDB initialized successfully")
            except Exception as e:
                logger.warning(f"MongoDB connection failed (app will work without it): {str(e)}")
                print(f"MongoDB warning: {str(e)}")  # Also print for Vercel logs
                client = None
                db = None
        else:
            logger.info("MongoDB not configured - app will run without database")
            print("MongoDB not configured")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {str(e)}")
        print(f"MongoDB error: {str(e)}")  # Also print for Vercel logs
        client = None
        db = None

# Don't initialize MongoDB during import - do it lazily when needed
# This prevents blocking during function initialization

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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
        logger.info(f"Attempting TrueData authentication for user: {username}")
        
        # Prepare form data - httpx will automatically URL-encode special characters
        form_data = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        
        logger.info(f"TrueData auth URL: {TRUEDATA_AUTH_URL}")
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Send form data - httpx automatically URL-encodes special characters
            response = await client.post(
                TRUEDATA_AUTH_URL,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            logger.info(f"TrueData auth response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("TrueData authentication successful")
                return result
            else:
                error_text = response.text
                logger.error(f"TrueData auth failed: {response.status_code}")
                logger.error(f"Response text: {error_text[:500]}")
                
                # Try to parse error message
                try:
                    error_json = response.json()
                    error_msg = error_json.get('error_description') or error_json.get('error') or error_json.get('message') or "Authentication failed"
                    logger.error(f"Parsed error: {error_msg}")
                except:
                    error_msg = error_text[:200] if error_text else "Authentication failed"
                    logger.error(f"Could not parse error JSON, using raw text: {error_msg}")
                
                return {"error": error_msg, "status_code": response.status_code}
    except httpx.TimeoutException:
        logger.error("TrueData auth timeout")
        return {"error": "Request timeout. Please try again."}
    except httpx.RequestError as e:
        logger.error(f"TrueData request error: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error authenticating with TrueData: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


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
        logger.info(f"Login attempt for username: {request.username}")
        result = await get_truedata_token(request.username, request.password)
        
        if "error" in result:
            error_msg = result.get("error", "Authentication failed")
            logger.warning(f"Login failed for {request.username}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            )
        
        # Store token in database for session management
        token_doc = {
            "username": request.username,
            "access_token": result.get("access_token"),
            "expires_in": result.get("expires_in"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 3600))).isoformat()
        }
        
        # Upsert token (MongoDB is optional - app works without it)
        # Try to initialize MongoDB if not already done
        if client is None and db is None:
            init_mongodb()
        
        if db is None:
            logger.warning("MongoDB not initialized - cannot store token (tokens will be stored in frontend localStorage)")
            # Continue without storing in DB (for development/testing)
        else:
            try:
                # Use 'tokens' collection (will be created automatically if it doesn't exist)
                await db.tokens.update_one(
                    {"username": request.username},
                    {"$set": token_doc},
                    upsert=True
                )
                logger.info(f"Token stored in MongoDB for {request.username}")
            except Exception as e:
                # Don't fail login if MongoDB storage fails
                logger.warning(f"Failed to store token in MongoDB (non-critical): {str(e)}")
                # Continue - token will be stored in frontend localStorage
        
        logger.info(f"Login successful for {request.username}")
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
        logger.error(f"Login error: {str(e)}", exc_info=True)
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
    try:
        # Try to initialize MongoDB if not already done
        if client is None and db is None:
            init_mongodb()
        
        if db is None:
            return {
                "status": "not_configured",
                "message": "MongoDB not configured or connection failed",
                "mongo_url_set": bool(os.environ.get('MONGO_URL')),
                "db_name_set": bool(os.environ.get('DB_NAME'))
            }
        
        # Try to ping the database
        await client.admin.command('ping')
        return {
            "status": "success",
            "database": os.environ.get('DB_NAME'),
            "message": "MongoDB connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }

@api_router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "ok",
        "message": "API is running"
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

# Add global exception handler to catch all errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": str(exc.status_code),
                "message": str(exc.detail)
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to catch all unhandled exceptions"""
    error_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    logger.error(f"Traceback: {error_trace}")
    print(f"ERROR: {str(exc)}")  # Also print for Vercel logs
    print(error_trace)  # Print traceback for Vercel logs
    
    # Return proper error response
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "500",
                "message": str(exc),
                "type": type(exc).__name__
            }
        }
    )


@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()
