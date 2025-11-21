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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


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
client = None
db = None

try:
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if mongo_url and db_name:
        try:
            logger.info(f"Connecting to MongoDB database: {db_name}")
            # Strip quotes from environment variables if present
            mongo_url = mongo_url.strip('"').strip("'")
            db_name = db_name.strip('"').strip("'")
            
            # Add SSL certificate bypass to connection string for development
            # This fixes SSL certificate verification errors on macOS/development environments
            if '?' not in mongo_url:
                mongo_url += '?tlsAllowInvalidCertificates=true'
            elif 'tlsAllowInvalidCertificates' not in mongo_url:
                mongo_url += '&tlsAllowInvalidCertificates=true'
            
            logger.info(f"Connecting with URL: {mongo_url.split('@')[0]}@***")  # Log without password
            
            # Motor/AsyncIOMotorClient SSL configuration for MongoDB Atlas
            # mongodb+srv:// automatically uses TLS
            # SSL certificate validation is disabled via connection string parameter
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=20000
            )
            db = client[db_name]
            logger.info("MongoDB client initialized (connection will be tested on first use)")
        except Exception as e:
            logger.warning(f"MongoDB connection failed (app will work without it): {str(e)}")
            import traceback
            logger.warning(traceback.format_exc())
            client = None
            db = None
    else:
        logger.info("MongoDB not configured - app will run without database (tokens stored in localStorage on frontend)")
except Exception as e:
    logger.error(f"Error initializing MongoDB: {str(e)}")
    client = None
    db = None

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
        
        # Prepare form data
        form_data = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        
        logger.info(f"TrueData auth URL: {TRUEDATA_AUTH_URL}")
        logger.info(f"Form data keys: {list(form_data.keys())}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TRUEDATA_AUTH_URL,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            logger.info(f"TrueData auth response status: {response.status_code}")
            logger.info(f"TrueData auth response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("TrueData authentication successful")
                return result
            else:
                error_text = response.text
                logger.error(f"TrueData auth failed: {response.status_code}")
                logger.error(f"Response text: {error_text[:500]}")  # First 500 chars
                
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


# Daily data storage functions
def get_date_key(date: Optional[datetime] = None) -> str:
    """Get date key in YYYY-MM-DD format"""
    if date is None:
        date = datetime.now(timezone.utc)
    return date.strftime("%Y-%m-%d")


async def get_previous_day_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get previous trading day's closing data for a symbol"""
    if db is None:
        return None
    
    try:
        # Get yesterday's date
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        date_key = get_date_key(yesterday)
        
        # Try to find data for yesterday
        doc = await db.daily_stock_data.find_one({
            "date": date_key,
            "symbol": symbol
        })
        
        if doc:
            return doc
        
        # If not found, try to find the most recent data before today
        doc = await db.daily_stock_data.find_one(
            {"symbol": symbol},
            sort=[("date", -1)]
        )
        
        return doc
    except Exception as e:
        logger.error(f"Error fetching previous day data for {symbol}: {str(e)}")
        return None


async def save_daily_stock_data(token: str):
    """Save end-of-day stock data to MongoDB"""
    if db is None:
        logger.warning("MongoDB not initialized - cannot save daily data")
        return
    
    try:
        logger.info("Starting end-of-day data save...")
        date_key = get_date_key()
        
        # Fetch current data for all stocks
        stocks_data = []
        for symbol in TOP_20_STOCKS:
            try:
                # Determine series based on symbol
                if symbol in ["NIFTY", "BANKNIFTY"]:
                    series = "XX"
                else:
                    series = "EQ"
                
                ltp = await fetch_ltp_spot(token, symbol, series)
                
                if ltp is not None:
                    # Fetch volume and IV if available (using mock for now)
                    import random
                    random.seed(hash(symbol) + int(ltp))
                    volume = random.randint(1000000, 50000000)
                    iv = 20 + (hash(symbol) % 30)
                    iv_percentile = 30 + (hash(symbol) % 60)
                    
                    stock_doc = {
                        "symbol": symbol,
                        "date": date_key,
                        "spot": ltp,
                        "volume": volume,
                        "iv": round(iv, 2),
                        "iv_percentile": round(iv_percentile, 2),
                        "saved_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Upsert the document
                    await db.daily_stock_data.update_one(
                        {"symbol": symbol, "date": date_key},
                        {"$set": stock_doc},
                        upsert=True
                    )
                    stocks_data.append(stock_doc)
                    logger.info(f"Saved data for {symbol}: {ltp}")
            except Exception as e:
                logger.error(f"Error saving data for {symbol}: {str(e)}")
        
        logger.info(f"End-of-day data save completed. Saved {len(stocks_data)} stocks.")
        return stocks_data
    except Exception as e:
        logger.error(f"Error in save_daily_stock_data: {str(e)}", exc_info=True)


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
        
        # Get previous day's closing price from MongoDB
        previous_day_data = await get_previous_day_data(symbol)
        previous_close = None
        change_percent = None
        
        if previous_day_data and previous_day_data.get("spot"):
            previous_close = previous_day_data.get("spot")
            # Calculate change percentage
            if previous_close > 0:
                change_percent = ((ltp - previous_close) / previous_close) * 100
                change_percent = round(change_percent, 2)
        
        # If no previous data, use mock data (for first day or when DB is not available)
        if change_percent is None:
            import random
            random.seed(hash(symbol) + int(ltp))
            change_percent = random.uniform(-3.0, 3.0)
            logger.info(f"No previous day data for {symbol}, using mock change %")
        
        # Generate volume (use previous day's volume if available, otherwise mock)
        if previous_day_data and previous_day_data.get("volume"):
            volume = previous_day_data.get("volume")
        else:
            import random
            random.seed(hash(symbol) + int(ltp))
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
        
        # Get IV metrics (use previous day's if available, otherwise mock)
        if previous_day_data:
            iv = previous_day_data.get("iv")
            iv_percentile = previous_day_data.get("iv_percentile")
        else:
            # Mock IV metrics
            iv = 20 + (hash(symbol) % 30)  # Mock IV between 20-50
            iv_percentile = 30 + (hash(symbol) % 60)  # Mock percentile
        
        if iv:
            iv = round(iv, 2)
        if iv_percentile:
            iv_percentile = round(iv_percentile, 2)
        
        return StockData(
            symbol=symbol,
            spot=ltp,
            change_percent=round(change_percent, 2),
            volume=volume,
            iv=iv,
            iv_percentile=iv_percentile,
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
        
        # Upsert token
        if db is None:
            logger.warning("MongoDB not initialized - cannot store token")
            # Continue without storing in DB (for development/testing)
        else:
            await db.tokens.update_one(
                {"username": request.username},
                {"$set": token_doc},
                upsert=True
            )
        
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
    if client is None or db is None:
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


@api_router.post("/market/save-daily-data")
async def manual_save_daily_data(token: str):
    """Manually trigger end-of-day data save (for testing)"""
    try:
        stocks_data = await save_daily_stock_data(token)
        return {
            "success": True,
            "message": f"Saved data for {len(stocks_data) if stocks_data else 0} stocks",
            "date": get_date_key(),
            "stocks_count": len(stocks_data) if stocks_data else 0
        }
    except Exception as e:
        logger.error(f"Error in manual save: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize scheduler for daily end-of-day data save
scheduler = AsyncIOScheduler()

async def scheduled_end_of_day_save():
    """Scheduled function to save end-of-day data"""
    try:
        # Get a valid token from database (use the most recent one)
        if db is not None:
            token_doc = await db.tokens.find_one(
                sort=[("created_at", -1)]
            )
            if token_doc and token_doc.get("access_token"):
                token = token_doc.get("access_token")
                await save_daily_stock_data(token)
                logger.info("Scheduled end-of-day data save completed")
            else:
                logger.warning("No valid token found for scheduled save")
        else:
            logger.warning("MongoDB not available for scheduled save")
    except Exception as e:
        logger.error(f"Error in scheduled end-of-day save: {str(e)}", exc_info=True)

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    # Schedule daily save at 3:30 PM IST (10:00 AM UTC) - typical market close time
    # Adjust timezone as needed
    scheduler.add_job(
        scheduled_end_of_day_save,
        trigger=CronTrigger(hour=10, minute=0),  # 10:00 AM UTC = 3:30 PM IST
        id="daily_stock_save",
        name="Daily End-of-Day Stock Data Save",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started - Daily data save scheduled at 10:00 AM UTC (3:30 PM IST)")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    if client is not None:
        client.close()
