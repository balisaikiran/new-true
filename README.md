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

---

## 🚀 Running Locally

### Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **npm** or **yarn** (package manager)
- **TrueData API credentials** (username and password)

---

## 📦 Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Set Environment Variables (Optional)

Create a `.env` file in the `backend/` directory:

```env
REACT_APP_BACKEND_URL=https://pothos-backend.onrender.com
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=pothos
CORS_ORIGINS="*"
**Note**: MongoDB is optional - the app works without it!

### Step 6: Run Backend Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at: **http://localhost:8000**

API endpoints:
- Root: `http://localhost:8000/api/`
- Health: `http://localhost:8000/api/health`
- Login: `http://localhost:8000/api/auth/login`

---

## 🎨 Frontend Setup

### Step 1: Navigate to Frontend Directory

Open a **new terminal** (keep backend running) and:

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install --legacy-peer-deps
```

### Step 3: Set Backend URL (Optional)

Create a `.env.local` file in the `frontend/` directory:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

**Note**: If not set, frontend will use `window.location.origin` (current domain)

### Step 4: Start Frontend Development Server

```bash
npm start
```

The frontend will open automatically at: **http://localhost:3000**

---

## 🧪 Testing

### Test Backend API

```bash
# Test root endpoint
curl http://localhost:8000/api/

# Test health check
curl http://localhost:8000/api/health

# Test database connection
curl http://localhost:8000/api/test-db
```

### Test Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── server.py              # FastAPI backend server
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (optional)
├── frontend/
│   ├── src/                   # React source code
│   ├── public/                # Static files
│   ├── package.json           # Node dependencies
│   └── .env.local            # Frontend env vars (optional)
└── README.md                 # This file
```

---

## 🔧 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Use a different port
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Module not found:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**MongoDB connection fails:**
- MongoDB is optional - the app works without it!
- If you want MongoDB, check your connection string in `.env`

### Frontend Issues

**Port 3000 already in use:**
- The terminal will prompt you to use a different port
- Or set: `PORT=3001 npm start`

**Cannot connect to backend:**
- Make sure backend is running on `http://localhost:8000`
- Check `.env.local` has: `REACT_APP_BACKEND_URL=http://localhost:8000`
- Check browser console for CORS errors

**npm install fails:**
```bash
# Try with legacy peer deps
npm install --legacy-peer-deps

# Or clear cache
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

---

## 🌐 Production Deployment

### Backend (Render.com)

- **URL**: `https://pothos-backend.onrender.com`
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel/Netlify)

Set environment variable:
```
REACT_APP_BACKEND_URL=https://pothos-backend.onrender.com
```

---

## 📝 Usage

1. **Login**: Enter your TrueData username and password
2. **Dashboard**: View live market data for top 20 F&O stocks
3. **Refresh**: 
   - Click "Refresh" for manual updates
   - Use "Pause/Resume" to control auto-refresh
4. **Theme**: Click sun/moon icon to switch themes
5. **Option Chain**: Click "View" next to any symbol to see option chain data
6. **Logout**: Click "Logout" to end session

---

## 🛠️ Development

### Backend Development

- Backend uses **FastAPI** with auto-reload enabled
- Changes to `backend/server.py` will automatically reload
- Check logs in the terminal running uvicorn

### Frontend Development

- Frontend uses **React** with hot-reload
- Changes to `frontend/src/` will automatically reload
- Check browser console for errors

---

## 📄 License

This project is for personal/educational use.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Check browser console (F12) for frontend errors
3. Check backend terminal for server errors

---

Happy coding! 🚀

Quick start summary
Backend:
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

Frontend (in new terminal):
cd frontend
npm install --legacy-peer-deps
npm start