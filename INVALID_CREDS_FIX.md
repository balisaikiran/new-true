# Fixing "Invalid Creds" Error

## The Problem
Seeing "invalid creds" error when trying to log in on Vercel, but it works locally.

## Most Common Causes

### 1. REACT_APP_BACKEND_URL Not Set in Vercel

**Problem:** Frontend doesn't know where the backend is.

**Fix:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add:
   ```
   REACT_APP_BACKEND_URL=https://your-app.vercel.app
   ```
   Replace `your-app.vercel.app` with your actual Vercel URL.

3. **Important:** After adding, redeploy the app!

### 2. Wrong Backend URL

**Check:** The URL should be your Vercel deployment URL, not localhost.

**Correct format:**
```
REACT_APP_BACKEND_URL=https://your-app-name.vercel.app
```

**Wrong formats:**
```
REACT_APP_BACKEND_URL=http://localhost:8000  ❌
REACT_APP_BACKEND_URL=https://localhost:8000  ❌
REACT_APP_BACKEND_URL=your-app.vercel.app  ❌ (missing https://)
```

### 3. CORS Issues

**Problem:** Backend might be blocking requests from frontend.

**Fix:** Ensure `CORS_ORIGINS` includes your Vercel URL:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### 4. TrueData API Credentials

**Problem:** The actual TrueData username/password might be wrong.

**Check:**
- Verify your TrueData credentials are correct
- Test them on TrueData website first
- Ensure account is active

## Step-by-Step Fix

### Step 1: Get Your Vercel URL

1. Go to Vercel Dashboard
2. Click on your project
3. Copy the deployment URL (e.g., `https://your-app.vercel.app`)

### Step 2: Set Environment Variables

Go to Settings → Environment Variables and set:

**For Frontend:**
```
REACT_APP_BACKEND_URL=https://your-app.vercel.app
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

**For Backend (optional - only if using MongoDB):**
```
MONGO_URL=mongodb+srv://...
DB_NAME=truedata
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### Step 3: Redeploy

After setting environment variables:
1. Go to Deployments tab
2. Click "Redeploy" on latest deployment
3. Or push a new commit

**Important:** Environment variables require a redeploy to take effect!

### Step 4: Test

1. Open your Vercel app: `https://your-app.vercel.app`
2. Open browser console (F12)
3. Try to log in
4. Check console for errors:
   - If you see "Cannot connect to server" → Backend URL is wrong
   - If you see CORS error → CORS_ORIGINS not set correctly
   - If you see "Invalid credentials" → TrueData credentials are wrong

## Debugging

### Check Browser Console

Open browser DevTools (F12) → Console tab, and look for:
- Network errors
- CORS errors
- API call failures

### Check Network Tab

1. Open DevTools → Network tab
2. Try to log in
3. Look for the `/api/auth/login` request
4. Check:
   - **Request URL:** Should be `https://your-app.vercel.app/api/auth/login`
   - **Status:** Should be 200 (success) or 401 (invalid creds)
   - **Response:** Check the error message

### Test Backend Directly

Try accessing:
```
https://your-app.vercel.app/api/
```

Should return: `{"message": "TrueData Analytics API"}`

If this fails, the backend isn't deployed correctly.

### Check Vercel Function Logs

1. Go to Vercel Dashboard → Your Project → Functions
2. Click on `api/index.py`
3. Check "Logs" tab
4. Look for errors when you try to log in

## Common Error Messages

**"Cannot connect to server"**
→ `REACT_APP_BACKEND_URL` not set or wrong

**"CORS policy" error**
→ `CORS_ORIGINS` doesn't include your Vercel URL

**"Invalid credentials"**
→ TrueData username/password are wrong

**"Network Error"**
→ Backend not deployed or URL incorrect

## Quick Checklist

- [ ] `REACT_APP_BACKEND_URL` is set to your Vercel URL
- [ ] URL includes `https://` (not `http://`)
- [ ] No trailing slash in URL
- [ ] Redeployed after setting environment variables
- [ ] `CORS_ORIGINS` includes your Vercel URL
- [ ] TrueData credentials are correct
- [ ] Backend API is accessible at `/api/`

## Still Not Working?

1. **Check Vercel deployment status:**
   - Is deployment successful?
   - Are there any build errors?

2. **Test API endpoint:**
   ```
   curl https://your-app.vercel.app/api/
   ```

3. **Check browser console:**
   - What exact error do you see?
   - What's the request URL?

4. **Verify environment variables:**
   - Are they set for "Production" environment?
   - Did you redeploy after setting them?

