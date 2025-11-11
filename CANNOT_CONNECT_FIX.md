# Fix "Cannot Connect to Server" Error

## The Problem
Frontend shows: "Cannot connect to server. Please check if backend is running at https://new-true-two.vercel.app"

API test shows: `FUNCTION_INVOCATION_FAILED`

## Root Cause
The Python serverless function is crashing during initialization.

## Immediate Fix Steps

### Step 1: Check Vercel Function Logs

1. Go to **Vercel Dashboard** → Your Project (`new-true-two`)
2. Click **"Functions"** tab
3. Click on **`api/index.py`**
4. Go to **"Logs"** tab
5. Look for error messages

**Common errors you might see:**
- `ModuleNotFoundError` → Missing dependency
- `ImportError` → Cannot import server.py
- `NameError` → Variable not defined
- `ConnectionError` → MongoDB connection issue

### Step 2: Set Environment Variables

Go to **Settings → Environment Variables** and add:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=truedata
CORS_ORIGINS=https://new-true-two.vercel.app,http://localhost:3000
REACT_APP_BACKEND_URL=https://new-true-two.vercel.app
REACT_APP_ENABLE_VISUAL_EDITS=false
```

**Important:** 
- Add trailing `/` to MONGO_URL
- Replace URLs with your actual Vercel URL if different

### Step 3: Allow MongoDB Access

1. Go to **MongoDB Atlas**: https://cloud.mongodb.com
2. Click **"Network Access"**
3. Click **"Add IP Address"**
4. Click **"Allow Access from Anywhere"** (`0.0.0.0/0`)
5. Click **"Confirm"**

### Step 4: Commit and Redeploy

```bash
git add .
git commit -m "Fix API function error handling"
git push
```

Or redeploy from Vercel Dashboard:
- Go to **Deployments** → Click **"Redeploy"**

### Step 5: Test Again

1. Test API: `https://new-true-two.vercel.app/api/`
2. Should return: `{"message": "TrueData Analytics API"}`

## Debugging the Function Failure

### Check Function Logs

The logs will show exactly why the function is failing:

1. **Import errors:**
   - `ModuleNotFoundError: No module named 'server'`
   - Fix: Check if `backend/server.py` exists

2. **MongoDB errors:**
   - `ServerSelectionTimeoutError`
   - Fix: Allow `0.0.0.0/0` in MongoDB Atlas

3. **Missing dependencies:**
   - `ModuleNotFoundError: No module named 'mangum'`
   - Fix: Check `api/requirements.txt` includes all dependencies

### Test Locally First

Before deploying, test the function locally:

```bash
cd api
python3 -c "from index import handler; print('✅ Function loads successfully')"
```

## Quick Checklist

- [ ] Check Vercel Function Logs for specific error
- [ ] Set all environment variables in Vercel
- [ ] Allow MongoDB access from `0.0.0.0/0`
- [ ] Verify `api/index.py` exists
- [ ] Verify `backend/server.py` exists
- [ ] Verify `api/requirements.txt` includes `mangum`
- [ ] Redeploy after setting env vars
- [ ] Test `/api/` endpoint

## Still Not Working?

Share the error from Vercel Function Logs and I'll help fix it!

The improved error handling should prevent crashes and show better error messages.

