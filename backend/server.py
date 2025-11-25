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
from calendar import monthrange
import httpx
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import math


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


def normal_cdf(x: float) -> float:
    """Cumulative Distribution Function for standard normal distribution"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_pdf(x: float) -> float:
    """Probability Density Function for standard normal distribution"""
    return (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * x * x)


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str = "call"
) -> float:
    """
    Calculate Black-Scholes option price.
    
    Parameters:
    - spot: Current spot price
    - strike: Strike price
    - time_to_expiry: Time to expiry in years
    - risk_free_rate: Risk-free interest rate (as decimal, e.g., 0.06 for 6%)
    - volatility: Volatility (as decimal, e.g., 0.20 for 20%)
    - option_type: "call" or "put"
    
    Returns:
    - Option price
    """
    if time_to_expiry <= 0:
        # If expired, return intrinsic value
        if option_type.lower() == "call":
            return max(spot - strike, 0)
        else:
            return max(strike - spot, 0)
    
    if volatility <= 0:
        # If no volatility, return intrinsic value
        if option_type.lower() == "call":
            return max(spot - strike, 0)
        else:
            return max(strike - spot, 0)
    
    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility * volatility) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)
    
    if option_type.lower() == "call":
        price = spot * normal_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * normal_cdf(d2)
    else:  # put
        price = strike * math.exp(-risk_free_rate * time_to_expiry) * normal_cdf(-d2) - spot * normal_cdf(-d1)
    
    return max(price, 0)  # Option price cannot be negative


def black_scholes_vega(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float
) -> float:
    """
    Calculate Vega (sensitivity to volatility) for Black-Scholes model.
    Used in Newton-Raphson method for IV calculation.
    """
    if time_to_expiry <= 0 or volatility <= 0:
        return 0
    
    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility * volatility) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
    vega = spot * normal_pdf(d1) * math.sqrt(time_to_expiry)
    return vega


def calculate_implied_volatility(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_price: float,
    option_type: str = "call",
    max_iterations: int = 100,
    tolerance: float = 0.0001
) -> Optional[float]:
    """
    Calculate Implied Volatility using Newton-Raphson method.
    
    Parameters:
    - spot: Current spot price
    - strike: Strike price
    - time_to_expiry: Time to expiry in years
    - risk_free_rate: Risk-free interest rate (as decimal)
    - option_price: Market price of the option
    - option_type: "call" or "put"
    - max_iterations: Maximum iterations for Newton-Raphson
    - tolerance: Convergence tolerance
    
    Returns:
    - Implied volatility as decimal (e.g., 0.20 for 20%)
    """
    # Initial guess: Use Manaster-Koehler seed
    if time_to_expiry <= 0:
        return None
    
    # Initial volatility guess (20% is a reasonable starting point)
    volatility = 0.20
    
    for i in range(max_iterations):
        # Calculate option price with current volatility
        calculated_price = black_scholes_price(spot, strike, time_to_expiry, risk_free_rate, volatility, option_type)
        
        # Calculate vega (derivative with respect to volatility)
        vega = black_scholes_vega(spot, strike, time_to_expiry, risk_free_rate, volatility)
        
        if vega == 0:
            # If vega is zero, try different approach
            break
        
        # Newton-Raphson update
        price_diff = calculated_price - option_price
        volatility_new = volatility - (price_diff / vega)
        
        # Ensure volatility stays in reasonable bounds (0.001% to 500%)
        volatility_new = max(0.001, min(5.0, volatility_new))
        
        # Check convergence
        if abs(volatility_new - volatility) < tolerance:
            return volatility_new
        
        volatility = volatility_new
    
    # If Newton-Raphson didn't converge, try bisection method
    return calculate_iv_bisection(spot, strike, time_to_expiry, risk_free_rate, option_price, option_type)


def calculate_iv_bisection(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_price: float,
    option_type: str = "call",
    max_iterations: int = 100,
    tolerance: float = 0.0001
) -> Optional[float]:
    """
    Calculate Implied Volatility using bisection method (fallback).
    """
    vol_low = 0.001  # 0.1%
    vol_high = 5.0   # 500%
    
    # Check bounds
    price_low = black_scholes_price(spot, strike, time_to_expiry, risk_free_rate, vol_low, option_type)
    price_high = black_scholes_price(spot, strike, time_to_expiry, risk_free_rate, vol_high, option_type)
    
    if option_price < price_low or option_price > price_high:
        return None
    
    for i in range(max_iterations):
        vol_mid = (vol_low + vol_high) / 2
        price_mid = black_scholes_price(spot, strike, time_to_expiry, risk_free_rate, vol_mid, option_type)
        
        if abs(price_mid - option_price) < tolerance:
            return vol_mid
        
        if price_mid < option_price:
            vol_low = vol_mid
        else:
            vol_high = vol_mid
    
    return (vol_low + vol_high) / 2


def parse_expiry_date(expiry_str: str) -> Optional[datetime]:
    """
    Parse expiry date from DD-MM-YYYY format.
    """
    try:
        return datetime.strptime(expiry_str, "%d-%m-%Y")
    except:
        return None


def calculate_time_to_expiry(expiry_date: datetime) -> float:
    """
    Calculate time to expiry in years.
    """
    now = datetime.now(timezone.utc)
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    
    time_diff = expiry_date - now
    days = time_diff.total_seconds() / 86400
    
    if days <= 0:
        return 0.0001  # Very small value for same-day expiry
    
    return days / 365.25  # Convert to years


def get_lot_size(symbol: str) -> int:
    """
    Get lot size for a symbol.
    Common lot sizes:
    - NIFTY: 50
    - BANKNIFTY: 15
    - Stocks: Usually 500 (like RELIANCE)
    """
    lot_sizes = {
        "NIFTY": 50,
        "BANKNIFTY": 15,
    }
    # Default lot size for stocks is 500
    return lot_sizes.get(symbol, 500)


def parse_option_chain_record(record: List[Any], symbol: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single option chain record based on TrueData API structure.
    
    TrueData API structure (based on actual data):
    Index 0: Symbol
    Index 1: Expiry date (DD-MM-YYYY)
    Index 2: Call timestamp
    Index 3: Call OI (already multiplied by lot size)
    Index 4: Call LTP
    Index 5: Call Bid
    Index 6: Call Bid Qty
    Index 7: Call Ask
    Index 8: Call Ask Qty
    Index 9: Call Volume (already multiplied by lot size) or Call pOI
    Index 10: Call pOI or Call Volume
    Index 11: Strike Price
    Index 12: Put Bid
    Index 13: Put Bid Qty
    Index 14: Put Ask
    Index 15: Put Ask Qty
    Index 16: Put OI (already multiplied by lot size)
    Index 17: Put pOI
    Index 18: Put LTP
    Index 19: Put Volume (already multiplied by lot size)
    Index 20: Put timestamp
    
    Note: OI and Volume values are already multiplied by lot size in TrueData API.
    To get NSE-equivalent values, divide by lot size.
    """
    if not isinstance(record, list) or len(record) < 21:
        return None
    
    try:
        lot_size = get_lot_size(symbol)
        
        # Extract strike price
        strike = record[11] if len(record) > 11 else None
        if strike is None or not isinstance(strike, (int, float)):
            return None
        
        # Call option data
        call_oi_raw = record[3] if len(record) > 3 else None
        call_ltp = record[4] if len(record) > 4 else None
        call_bid = record[5] if len(record) > 5 else None
        call_bid_qty = record[6] if len(record) > 6 else None
        call_ask = record[7] if len(record) > 7 else None
        call_ask_qty = record[8] if len(record) > 8 else None
        call_vol_raw = record[9] if len(record) > 9 else (record[10] if len(record) > 10 else None)
        
        # Put option data
        put_bid = record[12] if len(record) > 12 else None
        put_bid_qty = record[13] if len(record) > 13 else None
        put_ask = record[14] if len(record) > 14 else None
        put_ask_qty = record[15] if len(record) > 15 else None
        put_oi_raw = record[16] if len(record) > 16 else None
        put_ltp = record[18] if len(record) > 18 else None
        put_vol_raw = record[19] if len(record) > 19 else None
        
        # Convert OI and Volume from lot-size-multiplied to NSE-equivalent
        # TrueData provides: OI * lot_size, so divide by lot_size to get NSE value
        call_oi = call_oi_raw / lot_size if call_oi_raw and lot_size > 0 else None
        call_vol = call_vol_raw / lot_size if call_vol_raw and lot_size > 0 else None
        put_oi = put_oi_raw / lot_size if put_oi_raw and lot_size > 0 else None
        put_vol = put_vol_raw / lot_size if put_vol_raw and lot_size > 0 else None
        
        return {
            "strike": strike,
            "call": {
                "oi": call_oi,
                "ltp": call_ltp,
                "bid": call_bid,
                "bid_qty": call_bid_qty,
                "ask": call_ask,
                "ask_qty": call_ask_qty,
                "volume": call_vol,
            },
            "put": {
                "oi": put_oi,
                "ltp": put_ltp,
                "bid": put_bid,
                "bid_qty": put_bid_qty,
                "ask": put_ask,
                "ask_qty": put_ask_qty,
                "volume": put_vol,
            }
        }
    except (IndexError, TypeError, ValueError, ZeroDivisionError) as e:
        logger.debug(f"Error parsing option chain record: {str(e)}")
        return None


def extract_iv_from_option_chain(option_chain_data: Dict[str, Any], spot_price: float) -> Optional[float]:
    """
    Calculate Implied Volatility (IV) from option chain data using Black-Scholes model.
    Uses ATM (At-The-Money) options to get representative IV.
    
    According to Investopedia: IV is derived from option prices using pricing models
    like Black-Scholes. We calculate it from option prices.
    
    TrueData API option chain structure (corrected):
    Records array contains lists with 21 elements mapping to option chain fields.
    See parse_option_chain_record() for detailed mapping.
    """
    try:
        if not isinstance(option_chain_data, dict):
            return None
        
        # Check if IV is directly provided (some APIs provide it)
        if 'IV' in option_chain_data:
            return float(option_chain_data['IV'])
        if 'impliedVolatility' in option_chain_data:
            return float(option_chain_data['impliedVolatility'])
        if 'iv' in option_chain_data:
            return float(option_chain_data['iv'])
        
        # Extract IV from Records array by calculating from option prices
        records = option_chain_data.get('Records', [])
        if not records or not isinstance(records, list):
            return None
        
        # Risk-free rate for India (typically 6-7%, using 6.5%)
        risk_free_rate = 0.065
        
        # Find ATM options and calculate IV
        ivs = []
        atm_options = []
        
        # Parse expiry date from first record
        expiry_str = None
        if records and len(records[0]) > 1:
            expiry_str = records[0][1] if isinstance(records[0][1], str) else None
        
        expiry_date = parse_expiry_date(expiry_str) if expiry_str else None
        if not expiry_date:
            logger.warning("Could not parse expiry date from option chain")
            return None
        
        time_to_expiry = calculate_time_to_expiry(expiry_date)
        
        # Get symbol from first record to determine lot size
        symbol = records[0][0] if records and len(records[0]) > 0 else "NIFTY"
        
        # Find ATM options (closest to spot price)
        for record in records:
            parsed = parse_option_chain_record(record, symbol)
            if not parsed:
                continue
            
            strike = parsed["strike"]
            call_ltp = parsed["call"]["ltp"]
            put_ltp = parsed["put"]["ltp"]
            
            strike_diff = abs(strike - spot_price)
            
            # Calculate IV from call option if available
            if call_ltp and isinstance(call_ltp, (int, float)) and call_ltp > 0:
                iv_call = calculate_implied_volatility(
                    spot_price, strike, time_to_expiry, risk_free_rate, call_ltp, "call"
                )
                if iv_call and 0.05 <= iv_call <= 2.0:  # IV between 5% and 200%
                    atm_options.append((strike_diff, iv_call, "call"))
            
            # Calculate IV from put option if available
            if put_ltp and isinstance(put_ltp, (int, float)) and put_ltp > 0:
                iv_put = calculate_implied_volatility(
                    spot_price, strike, time_to_expiry, risk_free_rate, put_ltp, "put"
                )
                if iv_put and 0.05 <= iv_put <= 2.0:  # IV between 5% and 200%
                    atm_options.append((strike_diff, iv_put, "put"))
        
        if not atm_options:
            logger.warning("Could not calculate IV from option chain - no valid option prices found")
            return None
        
        # Sort by distance from spot (ATM options first)
        atm_options.sort(key=lambda x: x[0])
        
        # Use ATM options (within 2% of spot price) or closest options
        atm_ivs = []
        for strike_diff, iv, opt_type in atm_options[:10]:  # Top 10 closest
            if strike_diff / spot_price < 0.05:  # Within 5% of spot
                atm_ivs.append(iv)
        
        if atm_ivs:
            # Return average IV from ATM options
            avg_iv = sum(atm_ivs) / len(atm_ivs)
            # Convert to percentage
            return round(avg_iv * 100, 2)
        else:
            # If no ATM options, use closest options
            closest_iv = atm_options[0][1] if atm_options else None
            if closest_iv:
                return round(closest_iv * 100, 2)
        
        return None
    
    except Exception as e:
        logger.error(f"Error calculating IV from option chain: {str(e)}", exc_info=True)
        return None


async def calculate_iv_percentile(symbol: str, current_iv: float) -> Optional[float]:
    """
    Calculate IV Percentile based on historical IV data.
    
    IV Percentile = (Number of days IV was below current IV) / (Total number of days) × 100
    
    Reference: https://www.investopedia.com/terms/i/iv.asp
    IV Percentile shows where current IV ranks compared to historical IV values.
    """
    if db is None or current_iv is None:
        return None
    
    try:
        # Get historical IV data for this symbol (typically last 252 trading days = 1 year)
        # We'll use all available historical data
        cursor = db.daily_stock_data.find(
            {"symbol": symbol, "iv": {"$exists": True, "$ne": None}},
            {"iv": 1, "date": 1}
        ).sort("date", -1).limit(252)  # Last 252 trading days
        
        historical_ivs = []
        async for doc in cursor:
            if doc.get("iv") is not None:
                historical_ivs.append(float(doc["iv"]))
        
        if not historical_ivs:
            logger.info(f"No historical IV data found for {symbol}, cannot calculate percentile")
            return None
        
        # Count how many days had IV below current IV
        days_below = sum(1 for iv in historical_ivs if iv < current_iv)
        total_days = len(historical_ivs)
        
        # Calculate percentile: (days below / total days) * 100
        percentile = (days_below / total_days) * 100
        
        logger.info(f"IV Percentile for {symbol}: {percentile:.2f}% (current IV: {current_iv}, historical days: {total_days})")
        return round(percentile, 2)
    
    except Exception as e:
        logger.error(f"Error calculating IV percentile for {symbol}: {str(e)}")
        return None


def calculate_iv_metrics(option_chain_data: Dict[str, Any], spot_price: float) -> tuple:
    """
    Calculate IV from option chain data.
    Returns: (iv, None) - percentile is calculated separately using historical data.
    """
    iv = extract_iv_from_option_chain(option_chain_data, spot_price)
    return iv, None  # Percentile calculated separately using historical data


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


def get_next_expiry() -> str:
    """Get next month's last Thursday expiry date in DD-MM-YYYY format"""
    today = datetime.now(timezone.utc)
    # Get next month
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(today.year, today.month + 1, 1, tzinfo=timezone.utc)
    
    # Get last day of next month
    last_day = datetime(
        next_month.year, 
        next_month.month, 
        monthrange(next_month.year, next_month.month)[1],
        tzinfo=timezone.utc
    )
    
    # Find last Thursday
    last_thursday = last_day
    while last_thursday.weekday() != 3:  # Thursday is weekday 3
        last_thursday = last_thursday - timedelta(days=1)
    
    # Format as DD-MM-YYYY
    day = str(last_thursday.day).zfill(2)
    month = str(last_thursday.month).zfill(2)
    year = last_thursday.year
    
    return f"{day}-{month}-{year}"


async def get_available_expiry(token: str, symbol: str) -> Optional[str]:
    """
    Try multiple expiry dates to find one with option chain data.
    Returns the first expiry date that has option chain records.
    """
    today = datetime.now(timezone.utc)
    expiry_dates = []
    
    # Strategy 1: Try next few weeks (including all days, not just Thursdays)
    # Some indices/stocks have different expiry schedules
    for days_ahead in [7, 14, 21, 28, 35, 42]:  # Try next 6 weeks
        test_date = today + timedelta(days=days_ahead)
        expiry_str = test_date.strftime("%d-%m-%Y")
        if expiry_str not in expiry_dates:
            expiry_dates.append(expiry_str)
    
    # Strategy 2: Try next few Thursdays (weekly expiry)
    for weeks in range(0, 5):
        test_date = today + timedelta(weeks=weeks)
        days_until_thursday = (3 - test_date.weekday()) % 7
        if days_until_thursday == 0 and test_date.weekday() != 3:
            days_until_thursday = 7
        thursday = test_date + timedelta(days=days_until_thursday)
        expiry_str = thursday.strftime("%d-%m-%Y")
        if expiry_str not in expiry_dates:
            expiry_dates.append(expiry_str)
    
    # Strategy 3: Try month-end dates
    for months_offset in [0, 1]:
        test_date = today.replace(day=1) + timedelta(days=32 * (months_offset + 1))
        test_date = test_date.replace(day=1) - timedelta(days=1)
        # Try last few days of month
        for days_back in range(7):
            test_expiry = test_date - timedelta(days=days_back)
            expiry_str = test_expiry.strftime("%d-%m-%Y")
            if expiry_str not in expiry_dates:
                expiry_dates.append(expiry_str)
    
    # Try each expiry date (limit to first 15 to avoid too many API calls)
    for expiry in expiry_dates[:15]:
        try:
            option_chain = await fetch_option_chain(token, symbol, expiry)
            if option_chain:
                records = option_chain.get('Records', [])
                if records and len(records) > 0:
                    logger.info(f"Found option chain data for {symbol} with expiry {expiry} ({len(records)} records)")
                    return expiry
        except Exception as e:
            logger.debug(f"Error checking expiry {expiry} for {symbol}: {str(e)}")
            continue
    
    # Fallback: Try the default expiry one more time
    default_expiry = get_next_expiry()
    try:
        option_chain = await fetch_option_chain(token, symbol, default_expiry)
        if option_chain:
            records = option_chain.get('Records', [])
            if records and len(records) > 0:
                logger.info(f"Found option chain data for {symbol} with default expiry {default_expiry}")
                return default_expiry
    except:
        pass
    
    logger.warning(f"Could not find option chain data for {symbol} with any expiry, using default {default_expiry}")
    return default_expiry


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
                    # Fetch option chain to extract real IV
                    expiry = get_next_expiry()
                    option_chain_data = await fetch_option_chain(token, symbol, expiry)
                    
                    # Extract real IV from option chain
                    iv = None
                    if option_chain_data:
                        iv = extract_iv_from_option_chain(option_chain_data, ltp)
                        if iv:
                            logger.info(f"Extracted IV for {symbol}: {iv}%")
                    
                    # Fallback to mock IV if extraction failed (for first-time setup or API issues)
                    if iv is None:
                        logger.warning(f"Could not extract IV for {symbol}, using fallback calculation")
                        import random
                        random.seed(hash(symbol) + int(ltp))
                        iv = 20 + (hash(symbol) % 30)
                    
                    # Calculate IV percentile using historical data
                    iv_percentile = await calculate_iv_percentile(symbol, iv)
                    
                    # Generate volume (use mock for now as TrueData API may not provide it directly)
                    import random
                    random.seed(hash(symbol) + int(ltp))
                    volume = random.randint(1000000, 50000000)
                    
                    stock_doc = {
                        "symbol": symbol,
                        "date": date_key,
                        "spot": ltp,
                        "volume": volume,
                        "iv": round(iv, 2) if iv else None,
                        "iv_percentile": round(iv_percentile, 2) if iv_percentile else None,
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


async def save_option_chain_data(token: str):
    """Save end-of-day option chain data to MongoDB for all stocks"""
    if db is None:
        logger.warning("MongoDB not initialized - cannot save option chain data")
        return
    
    try:
        logger.info("Starting end-of-day option chain data save...")
        date_key = get_date_key()
        expiry = get_next_expiry()
        
        # Fetch option chain data for all stocks
        chains_saved = []
        for symbol in TOP_20_STOCKS:
            try:
                logger.info(f"Fetching option chain for {symbol} with expiry {expiry}")
                option_chain_data = await fetch_option_chain(token, symbol, expiry)
                
                if option_chain_data:
                    chain_doc = {
                        "symbol": symbol,
                        "date": date_key,
                        "expiry": expiry,
                        "data": option_chain_data,
                        "saved_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Upsert the document
                    await db.option_chain_data.update_one(
                        {"symbol": symbol, "date": date_key, "expiry": expiry},
                        {"$set": chain_doc},
                        upsert=True
                    )
                    chains_saved.append({
                        "symbol": symbol,
                        "expiry": expiry,
                        "records_count": len(option_chain_data.get("Records", [])) if isinstance(option_chain_data, dict) else 0
                    })
                    logger.info(f"Saved option chain for {symbol} with expiry {expiry}")
                else:
                    logger.warning(f"Failed to fetch option chain for {symbol}")
            except Exception as e:
                logger.error(f"Error saving option chain for {symbol}: {str(e)}")
        
        logger.info(f"End-of-day option chain save completed. Saved {len(chains_saved)} option chains.")
        return chains_saved
    except Exception as e:
        logger.error(f"Error in save_option_chain_data: {str(e)}", exc_info=True)


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
        
        # Get IV metrics - fetch real IV from option chain
        iv = None
        iv_percentile = None
        
        # Try to fetch current IV from option chain - try multiple expiry dates
        expiry = await get_available_expiry(token, symbol)
        option_chain_data = await fetch_option_chain(token, symbol, expiry)
        
        if option_chain_data:
            records = option_chain_data.get('Records', [])
            if records and len(records) > 0:
                # Extract real IV from option chain
                iv = extract_iv_from_option_chain(option_chain_data, ltp)
                if iv:
                    logger.info(f"Extracted current IV for {symbol}: {iv}% (from expiry {expiry})")
                    # Calculate IV percentile using historical data
                    iv_percentile = await calculate_iv_percentile(symbol, iv)
                else:
                    logger.warning(f"Could not extract IV from option chain for {symbol} (expiry {expiry})")
            else:
                logger.warning(f"Option chain for {symbol} has no records (expiry {expiry})")
        
        # Fallback: Use previous day's IV if current extraction failed
        if iv is None and previous_day_data:
            iv = previous_day_data.get("iv")
            iv_percentile = previous_day_data.get("iv_percentile")
            if iv:
                logger.info(f"Using previous day IV for {symbol}: {iv}%")
        
        # Final fallback: Use mock IV only if no data available (for first-time setup)
        if iv is None:
            logger.warning(f"Could not extract IV for {symbol}, using fallback calculation")
            import random
            random.seed(hash(symbol) + int(ltp))
            iv = 20 + (hash(symbol) % 30)  # Fallback IV between 20-50
            # Cannot calculate percentile without historical data
        
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


@api_router.post("/market/save-option-chains")
async def manual_save_option_chains(token: str):
    """Manually trigger end-of-day option chain data save (for testing)"""
    try:
        chains_data = await save_option_chain_data(token)
        return {
            "success": True,
            "message": f"Saved option chains for {len(chains_data) if chains_data else 0} stocks",
            "date": get_date_key(),
            "expiry": get_next_expiry(),
            "chains_count": len(chains_data) if chains_data else 0,
            "chains": chains_data if chains_data else []
        }
    except Exception as e:
        logger.error(f"Error in manual option chain save: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.post("/market/save-all-daily-data")
async def manual_save_all_daily_data(token: str):
    """Manually trigger complete end-of-day data save (stocks + option chains)"""
    try:
        # Save stock data
        stocks_data = await save_daily_stock_data(token)
        
        # Save option chain data
        chains_data = await save_option_chain_data(token)
        
        return {
            "success": True,
            "message": "Saved all daily data successfully",
            "date": get_date_key(),
            "expiry": get_next_expiry(),
            "stocks_count": len(stocks_data) if stocks_data else 0,
            "chains_count": len(chains_data) if chains_data else 0
        }
    except Exception as e:
        logger.error(f"Error in manual save all: {str(e)}")
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
    """Scheduled function to save end-of-day data (stocks + option chains)"""
    try:
        # Get a valid token from database (use the most recent one)
        if db is not None:
            token_doc = await db.tokens.find_one(
                sort=[("created_at", -1)]
            )
            if token_doc and token_doc.get("access_token"):
                token = token_doc.get("access_token")
                
                # Save stock data
                logger.info("Starting scheduled end-of-day stock data save...")
                await save_daily_stock_data(token)
                
                # Save option chain data
                logger.info("Starting scheduled end-of-day option chain data save...")
                await save_option_chain_data(token)
                
                logger.info("Scheduled end-of-day data save completed (stocks + option chains)")
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
