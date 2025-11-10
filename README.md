# TrueData Analytics Dashboard

A professional F&O (Futures & Options) market analytics dashboard built with React and FastAPI, integrated with TrueData API.

## Features

### 🔐 Authentication
- Secure login with TrueData credentials
- Session management with token expiry handling
- Automatic token storage and validation

### 📊 Dashboard
- **Top 20 F&O Stocks**: Real-time market data for major stocks and indices
- **Live Spot Prices**: Fetched directly from TrueData API
- **Market Metrics**:
  - Spot Price
  - Change % (with trend indicators)
  - Volume
  - Implied Volatility (IV)
  - IV Percentile
  - Market Signals (Bullish/Bearish/Neutral/High Volatility)
- **Option Chain View**: Click "View" to see detailed option chain data

### 🔄 Auto-Refresh
- **30-minute auto-refresh interval**: Keeps data current
- **Pause/Resume controls**: Toggle auto-refresh on/off
- **Manual refresh button**: Refresh data on demand
- **Last updated timestamp**: See when data was last fetched

### 🎨 Themes
- **Dark Mode**: Professional trading terminal aesthetic (default)
- **Light Mode**: Clean, modern light theme
- Seamless theme switching with persistent preferences

### 🎯 Top 20 F&O Stocks Covered
1. NIFTY
2. BANKNIFTY
3. RELIANCE
4. TCS
5. HDFCBANK
6. INFY
7. ICICIBANK
8. HINDUNILVR
9. ITC
10. SBIN
11. BHARTIARTL
12. KOTAKBANK
13. LT
14. ASIANPAINT
15. HCLTECH
16. AXISBANK
17. MARUTI
18. SUNPHARMA
19. TITAN
20. ULTRACEMCO

## Usage

1. **Login**: Enter your TrueData username and password
2. **Dashboard**: View live market data for top 20 F&O stocks
3. **Refresh**: 
   - Click "Refresh" for manual updates
   - Use "Pause/Resume" to control auto-refresh
4. **Theme**: Click sun/moon icon to switch themes
5. **Option Chain**: Click "View" next to any symbol to see option chain data
6. **Logout**: Click "Logout" to end session
# new-true
