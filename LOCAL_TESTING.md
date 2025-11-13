# 🧪 Local Backend Testing Guide

Test your backend API locally before deploying to Vercel!

## 🚀 Quick Start

### Step 1: Start the Backend Server

```bash
./run-backend-local.sh
```

This will:
- Create a virtual environment (if needed)
- Install all dependencies
- Start the server on `http://localhost:8000`

**The server will run until you press `Ctrl+C`**

---

### Step 2: Test the API (in a new terminal)

**Option A: Quick Test Script**
```bash
./test-backend-local.sh
```

**Option B: Interactive Python Script**
```bash
python3 test-api-local.py
```

**Option C: Manual Testing with curl**
```bash
# Test root endpoint
curl http://localhost:8000/api/

# Test database connection
curl http://localhost:8000/api/test-db

# Test health check
curl http://localhost:8000/api/health

# Test login (replace with your credentials)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'
```

---

## 📋 Manual Setup (if scripts don't work)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Set Environment Variables (Optional)

Create `backend/.env` file:
```env
MONGO_URL=your_mongodb_connection_string
DB_NAME=your_database_name
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Note**: MongoDB is optional - the app works without it!

### 4. Run the Server

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload on code changes.

---

## 🧪 Testing Endpoints

### Available Endpoints:

1. **Root**: `GET http://localhost:8000/api/`
   - Should return: `{"message": "TrueData Analytics API"}`

2. **Health Check**: `GET http://localhost:8000/api/health`
   - Should return: `{"status": "ok", "message": "API is running"}`

3. **Database Test**: `GET http://localhost:8000/api/test-db`
   - Tests MongoDB connection (optional)

4. **Login**: `POST http://localhost:8000/api/auth/login`
   ```json
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

5. **Dashboard**: `GET http://localhost:8000/api/market/dashboard?token=YOUR_TOKEN`
   - Requires authentication token from login

---

## 🔍 Troubleshooting

### Issue: "Port 8000 already in use"

**Solution**: Use a different port
```bash
./run-backend-local.sh 8001
# Then test with: http://localhost:8001
```

### Issue: "Module not found"

**Solution**: Make sure virtual environment is activated
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Issue: "Cannot connect to MongoDB"

**Solution**: MongoDB is optional! The app works without it. If you want MongoDB:
1. Set `MONGO_URL` and `DB_NAME` in `backend/.env`
2. Or export them:
   ```bash
   export MONGO_URL="your_mongodb_url"
   export DB_NAME="your_database_name"
   ```

### Issue: "Import errors"

**Solution**: Make sure you're running from the project root:
```bash
cd /Users/saikiran/Downloads/app-main\ 2
./run-backend-local.sh
```

---

## 📝 Expected Responses

### ✅ Success Response (Root):
```json
{
  "message": "TrueData Analytics API"
}
```

### ✅ Success Response (Health):
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### ✅ Success Response (Login):
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "...",
  "expires_in": 3600
}
```

### ❌ Error Response:
```json
{
  "error": {
    "code": "401",
    "message": "Invalid credentials"
  }
}
```

---

## 🎯 Next Steps

Once local testing works:

1. **Fix any issues** you find locally
2. **Test all endpoints** with real credentials
3. **Then deploy to Vercel** - it should work the same way!

---

## 💡 Tips

- Keep the server running in one terminal
- Use another terminal for testing
- The server auto-reloads when you change code (with `--reload` flag)
- Check server logs in the terminal running `run-backend-local.sh`

