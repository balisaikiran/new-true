# 🧪 Quick Backend Testing Guide

## 🚀 Test Your Backend Now

### Method 1: Browser (Easiest)

Open these URLs in your browser:

1. **Root Endpoint**:
   ```
   https://pothos-v2.vercel.app/api/
   ```

2. **Database Test**:
   ```
   https://pothos-v2.vercel.app/api/test-db
   ```

---

### Method 2: Terminal (curl)

```bash
# Test root endpoint
curl https://pothos-v2.vercel.app/api/

# Test database
curl https://pothos-v2.vercel.app/api/test-db

# Pretty print JSON response
curl -s https://pothos-v2.vercel.app/api/ | python3 -m json.tool
```

---

### Method 3: Using Test Script

```bash
./test-api.sh https://pothos-v2.vercel.app
```

---

## 🔍 If You See Errors

### Step 1: Check Vercel Function Logs

1. Go to: https://vercel.com/dashboard
2. Click on **`pothos-v2`** project
3. Click **"Deployments"** tab
4. Click on **latest deployment**
5. Click **"Function Logs"** or **"Runtime Logs"**
6. Look for error messages (they'll be in red)

**What to look for:**
- `ModuleNotFoundError` → Missing dependency
- `ImportError` → Path/import issue
- `FileNotFoundError` → File structure issue

### Step 2: Check the Error Response

The improved `api/index.py` now returns detailed error messages. Check the response:

```bash
curl https://pothos-v2.vercel.app/api/
```

The response will tell you:
- What file it's looking for
- Where it's looking
- What files exist
- What the error is

---

## ✅ Expected Success Response

**Root endpoint** (`/api/`):
```json
{
  "message": "TrueData Analytics API"
}
```

**Database test** (`/api/test-db`):
```json
{
  "status": "connected",
  "database": "pothos",
  "message": "MongoDB connection successful"
}
```

---

## 🔧 After Fixing Issues

1. **Commit and push**:
   ```bash
   git add .
   git commit -m "Fix backend deployment"
   git push origin main
   ```

2. **Wait for auto-deployment** (or manually redeploy in Vercel)

3. **Test again**:
   ```bash
   curl https://pothos-v2.vercel.app/api/
   ```

---

## 📋 Quick Checklist

- [ ] Tested root endpoint: `https://pothos-v2.vercel.app/api/`
- [ ] Tested database endpoint: `https://pothos-v2.vercel.app/api/test-db`
- [ ] Checked Vercel function logs for errors
- [ ] Fixed any issues found
- [ ] Redeployed and tested again

---

## 🎯 Next Steps After Backend Works

Once backend is working:

1. **Test login endpoint** (requires TrueData credentials)
2. **Deploy frontend** separately
3. **Connect frontend to backend** via `REACT_APP_BACKEND_URL`

---

Happy Testing! 🚀

