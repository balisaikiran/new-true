# 🧪 Backend API Testing Guide

Quick guide to test your deployed backend at `https://pothos-v2.vercel.app`

## 🚀 Quick Test Methods

### Method 1: Browser Testing (Easiest)

Just open these URLs in your browser:

1. **Root Endpoint** (Should work immediately):
   ```
   https://pothos-v2.vercel.app/api/
   ```
   Expected: `{"message": "TrueData Analytics API"}`

2. **Database Test**:
   ```
   https://pothos-v2.vercel.app/api/test-db
   ```
   Expected: MongoDB connection status

---

### Method 2: Using Test Script (Automated)

Run the test script:

```bash
./test-api.sh https://pothos-v2.vercel.app
```

This will test all endpoints automatically.

---

### Method 3: Using curl (Terminal)

```bash
# Test root endpoint
curl https://pothos-v2.vercel.app/api/

# Test database connection
curl https://pothos-v2.vercel.app/api/test-db

# Test login endpoint (will fail with invalid credentials, but confirms endpoint works)
curl -X POST https://pothos-v2.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

---

### Method 4: Browser Console (JavaScript)

Open browser console (F12) and run:

```javascript
// Test root endpoint
fetch('https://pothos-v2.vercel.app/api/')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Test database
fetch('https://pothos-v2.vercel.app/api/test-db')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Test login (replace with your credentials)
fetch('https://pothos-v2.vercel.app/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

---

### Method 5: Using Python Script (Full Test with Auth)

```bash
python3 test-api-with-auth.py https://pothos-v2.vercel.app
```

This will:
- Test all endpoints
- Prompt for TrueData credentials
- Test login and get access token
- Test dashboard data
- Test option chain data

---

## 📋 Available Endpoints

### 1. GET `/api/` - Root Endpoint
- **URL**: `https://pothos-v2.vercel.app/api/`
- **Method**: GET
- **Auth**: Not required
- **Response**: `{"message": "TrueData Analytics API"}`

### 2. GET `/api/test-db` - Database Test
- **URL**: `https://pothos-v2.vercel.app/api/test-db`
- **Method**: GET
- **Auth**: Not required
- **Response**: MongoDB connection status

### 3. POST `/api/auth/login` - Login
- **URL**: `https://pothos-v2.vercel.app/api/auth/login`
- **Method**: POST
- **Auth**: Not required (but needs valid credentials)
- **Body**: 
  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```
- **Response**: 
  ```json
  {
    "success": true,
    "access_token": "...",
    "expires_in": 3600,
    "username": "your_username"
  }
  ```

### 4. GET `/api/market/dashboard` - Dashboard Data
- **URL**: `https://pothos-v2.vercel.app/api/market/dashboard?token=YOUR_TOKEN`
- **Method**: GET
- **Auth**: Required (token from login)
- **Response**: List of stock data for top 20 F&O stocks

### 5. GET `/api/market/optionchain/{symbol}` - Option Chain
- **URL**: `https://pothos-v2.vercel.app/api/market/optionchain/NIFTY?expiry=2024-12-26&token=YOUR_TOKEN`
- **Method**: GET
- **Auth**: Required (token from login)
- **Response**: Option chain data

---

## ✅ Success Indicators

### ✅ Backend is Working If:
- Root endpoint (`/api/`) returns `{"message": "TrueData Analytics API"}`
- Database test (`/api/test-db`) returns connection status
- Login endpoint responds (even if credentials are wrong)

### ❌ Common Issues:

**404 Not Found**:
- Check that deployment completed successfully
- Verify URL is correct: `https://pothos-v2.vercel.app/api/`
- Check Vercel function logs

**500 Internal Server Error**:
- Check Vercel function logs
- Verify environment variables are set
- Check MongoDB connection

**CORS Errors**:
- Update `CORS_ORIGINS` environment variable
- Include your frontend URL

---

## 🔍 Check Deployment Status

1. Go to Vercel Dashboard: https://vercel.com/dashboard
2. Click on your `pothos-v2` project
3. Check "Deployments" tab
4. Click on latest deployment
5. Check "Function Logs" for any errors

---

## 🎯 Quick Test Checklist

- [ ] Root endpoint works: `https://pothos-v2.vercel.app/api/`
- [ ] Database test works: `https://pothos-v2.vercel.app/api/test-db`
- [ ] Login endpoint accessible: `https://pothos-v2.vercel.app/api/auth/login`
- [ ] Can login with TrueData credentials
- [ ] Can fetch dashboard data with token
- [ ] Can fetch option chain data

---

Happy Testing! 🚀

