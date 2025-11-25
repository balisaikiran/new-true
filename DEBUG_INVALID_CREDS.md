# Debug "Invalid Creds" Error on Vercel

## 🔍 The Real Issue

The "invalid creds" error you're seeing is likely a **500 Internal Server Error** that's being displayed as "invalid creds" by the frontend.

## ✅ What I Fixed

1. **Improved MongoDB Error Handling** - MongoDB failures won't break login anymore
2. **Better Error Logging** - Detailed logs will show what's happening
3. **Collection Name** - Code uses `tokens` collection (MongoDB will create it automatically)

## 📋 Step-by-Step Debugging

### Step 1: Check Vercel Function Logs

**This is the most important step!**

1. Go to **Vercel Dashboard** → `new-true-two` project
2. Click **"Functions"** tab
3. Click on **`api/index.py`**
4. Go to **"Logs"** tab
5. Try to log in
6. Look for these messages:

#### ✅ Success Path:
```
Current file: /var/task/api/index.py
Backend dir exists: True
✅ Successfully imported server module
✅ Mangum handler created successfully
Login attempt for username: tdwsp784
Attempting TrueData authentication for user: tdwsp784
TrueData auth response status: 200
✅ TrueData authentication successful
Login successful for tdwsp784
```

#### ❌ Failure Path (will show exact error):
```
ERROR: Failed to import server: ...
OR
TrueData auth failed: 401
Response text: {"error": "invalid_grant", ...}
```

### Step 2: Verify Environment Variables

Make sure these are set correctly in Vercel:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=pothos
CORS_ORIGINS=https://new-true-two.vercel.app,http://localhost:3000
REACT_APP_BACKEND_URL=https://new-true-two.vercel.app
```

**Note**: The collection name in MongoDB (`pothos`) doesn't need to match - the code uses `tokens` collection which MongoDB will create automatically.

### Step 3: Test API Directly

Test the API endpoint directly to see the real error:

```bash
curl -X POST https://new-true-two.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tdwsp784", "password": "sid@784"}'
```

This will show you the actual error response (not masked by frontend).

### Step 4: Check Browser Console

1. Open your app: `https://new-true-two.vercel.app`
2. Open DevTools (F12)
3. Go to **Network** tab
4. Try to log in
5. Click on `/api/auth/login` request
6. Check:
   - **Status Code** (should be 200, not 500)
   - **Response** tab (see actual error message)

## 🐛 Common Issues

### Issue 1: Python Function Still Crashing (500)
**Symptom**: Logs show "Python process exited with exit status: 1"

**Solution**: Check the Function Logs for import errors. The improved `api/index.py` will show exactly what's failing.

### Issue 2: TrueData Authentication Failing
**Symptom**: Logs show "TrueData auth failed: 401"

**Solution**: 
- Verify credentials are correct: `tdwsp784` / `sid@784`
- Check if TrueData API is accessible from Vercel
- Look at the error message from TrueData API in logs

### Issue 3: MongoDB Connection Failing
**Symptom**: Logs show "MongoDB connection failed"

**Solution**: This is **NON-CRITICAL** - the app works without MongoDB! Tokens will be stored in browser localStorage instead.

## ✅ What Should Happen

After the fixes:

1. **Function loads successfully** (no crash)
2. **Login request reaches backend**
3. **TrueData API called** with credentials
4. **TrueData returns token** (if credentials are correct)
5. **Login succeeds** (even if MongoDB fails)

## 📝 Next Steps

1. **Commit and push** the latest changes:
```bash
git add backend/server.py api/index.py vercel.json
git commit -m "Improve MongoDB error handling and add detailed logging"
git push
```

2. **Wait for deployment** to complete

3. **Check Vercel Function Logs** - This will show you exactly what's happening!

4. **Try logging in** and check the logs for:
   - Function loading messages
   - TrueData API responses
   - Any error messages

The detailed logging will tell us exactly where it's failing!

## 💡 Key Point

**MongoDB is optional!** Even if MongoDB fails, login should still work. The tokens will just be stored in browser localStorage instead of MongoDB.

The real issue is likely:
1. Python function crashing (check logs)
2. TrueData authentication failing (check logs for TrueData response)

**Check the Vercel Function Logs - they will show you exactly what's wrong!**

