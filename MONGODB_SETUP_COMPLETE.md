# MongoDB Atlas Setup for Vercel

## Your MongoDB Connection Details

**Connection String:**
```
mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net
```

**Database Name:** (You'll need to choose one, e.g., `truedata`)

## Step-by-Step Setup

### Step 1: Set Environment Variables in Vercel

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**

2. Add these variables:

   **Variable 1:**
   ```
   Name: MONGO_URL
   Value: mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
   ```
   (Note: Added trailing `/` at the end)

   **Variable 2:**
   ```
   Name: DB_NAME
   Value: truedata
   ```
   (Or any database name you prefer)

   **Variable 3:**
   ```
   Name: CORS_ORIGINS
   Value: https://your-app.vercel.app,http://localhost:3000
   ```
   (Replace `your-app.vercel.app` with your actual Vercel URL)

   **Variable 4:**
   ```
   Name: REACT_APP_BACKEND_URL
   Value: https://your-app.vercel.app
   ```
   (Replace with your actual Vercel URL)

3. Make sure to select **"Production"**, **"Preview"**, and **"Development"** environments (or at least Production)

4. Click **"Save"** for each variable

### Step 2: Verify MongoDB Atlas Network Access

1. Go to **MongoDB Atlas Dashboard**: https://cloud.mongodb.com
2. Click on your cluster (`cluster0`)
3. Go to **"Network Access"** (left sidebar)
4. Click **"Add IP Address"**
5. Click **"Allow Access from Anywhere"** (adds `0.0.0.0/0`)
6. Click **"Confirm"**

This allows Vercel to connect to your MongoDB.

### Step 3: Verify Database User Permissions

1. In MongoDB Atlas, go to **"Database Access"** (left sidebar)
2. Find user: `saiashok49_db_user`
3. Click **"Edit"**
4. Under **"Database User Privileges"**, ensure:
   - **"Read and write to any database"** OR
   - **"Atlas admin"**
5. Click **"Update User"**

### Step 4: Redeploy Your App

After setting environment variables, you MUST redeploy:

**Option A: Via Dashboard**
1. Go to **Deployments** tab
2. Click **"Redeploy"** on latest deployment
3. Select **"Use existing Build Cache"** = No (to rebuild with new env vars)
4. Click **"Redeploy"**

**Option B: Via Git**
```bash
git add .
git commit -m "Add MongoDB configuration"
git push
```

### Step 5: Test MongoDB Connection

After redeploying, test the connection:

1. Visit: `https://your-app.vercel.app/api/test-db`

Should return:
```json
{
  "status": "connected",
  "database": "truedata",
  "message": "MongoDB connection successful"
}
```

## Complete Environment Variables List

Here's the complete list you need in Vercel:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=truedata
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
REACT_APP_BACKEND_URL=https://your-app.vercel.app
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

**Important:** Replace `your-app.vercel.app` with your actual Vercel deployment URL!

## Troubleshooting

### If MongoDB connection fails:

1. **Check Network Access:**
   - Ensure `0.0.0.0/0` is allowed in MongoDB Atlas

2. **Check User Permissions:**
   - User must have read/write access

3. **Check Connection String:**
   - Must include trailing `/` after `.net`
   - No spaces or extra characters

4. **Check Vercel Logs:**
   - Go to Functions → `api/index.py` → Logs
   - Look for MongoDB connection errors

5. **Test Connection:**
   - Use `/api/test-db` endpoint
   - Check what error it returns

## Security Note

⚠️ **Important:** Your MongoDB password is now visible in environment variables. Make sure:
- Only you have access to Vercel dashboard
- Don't share your Vercel project publicly
- Consider rotating password periodically

## Next Steps

1. ✅ Set environment variables in Vercel
2. ✅ Allow MongoDB access from anywhere (`0.0.0.0/0`)
3. ✅ Redeploy app
4. ✅ Test connection at `/api/test-db`
5. ✅ Try logging in with TrueData credentials

Your app should now work with MongoDB!

