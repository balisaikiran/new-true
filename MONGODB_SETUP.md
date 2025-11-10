# MongoDB Atlas Setup Guide (Free Tier)

## Option 1: Set Up MongoDB Atlas (Recommended for Production)

MongoDB Atlas has a **free tier** that's perfect for this app!

### Step 1: Create MongoDB Atlas Account

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with your email (free account)
3. Verify your email

### Step 2: Create a Free Cluster

1. After login, click "Build a Database"
2. Choose **FREE** (M0) tier
3. Select a cloud provider (AWS recommended)
4. Choose a region close to you
5. Name your cluster (e.g., "Cluster0")
6. Click "Create"

**Wait 3-5 minutes** for cluster to be created.

### Step 3: Create Database User

1. Go to "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Enter username (e.g., "truedata_user")
5. Enter password (save this securely!)
6. Under "Database User Privileges", select "Read and write to any database"
7. Click "Add User"

### Step 4: Configure Network Access

1. Go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (adds `0.0.0.0/0`)
   - This allows Vercel to connect
   - For production, you can restrict to Vercel IPs later
4. Click "Confirm"

### Step 5: Get Connection String

1. Go to "Database" (left sidebar)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string
   - It looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/`
5. Replace `<username>` with your database username
6. Replace `<password>` with your database password
7. **Remove** `<dbname>` if present (we use DB_NAME env var)

**Example:**
```
mongodb+srv://truedata_user:MyPassword123@cluster0.abc123.mongodb.net/
```

**Important:** If your password has special characters, URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `:` → `%3A`
- `/` → `%2F`

### Step 6: Set Environment Variables in Vercel

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add these variables:

```
MONGO_URL=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/
DB_NAME=truedata
```

3. Click "Save"
4. Redeploy your app

### Step 7: Test Connection

After redeploying, test:
```
https://your-app.vercel.app/api/test-db
```

Should return: `{"status": "connected", ...}`

---

## Option 2: Run Without MongoDB (Current Setup)

**Good news!** The app already works without MongoDB! 

MongoDB is only used to store login tokens in the database. The frontend stores tokens in `localStorage`, so the app works fine without MongoDB.

### To Run Without MongoDB:

1. **Don't set** `MONGO_URL` and `DB_NAME` in Vercel environment variables
2. The app will log a warning but continue working
3. Login tokens will be stored only in browser localStorage (not in database)

### What Works Without MongoDB:
✅ User login  
✅ Dashboard data  
✅ Option chain data  
✅ All features work!

### What Doesn't Work Without MongoDB:
❌ Token storage in database (but tokens still work via localStorage)  
❌ Session management across devices (each device has its own session)

---

## Quick Setup Summary

**For MongoDB Atlas (5 minutes):**
1. Sign up at mongodb.com/cloud/atlas
2. Create free cluster
3. Create database user
4. Allow access from anywhere (0.0.0.0/0)
5. Copy connection string
6. Add to Vercel environment variables
7. Redeploy

**To Skip MongoDB:**
- Just don't set `MONGO_URL` and `DB_NAME`
- App works perfectly without it!

---

## Free Tier Limits

MongoDB Atlas Free Tier includes:
- ✅ 512 MB storage (plenty for this app)
- ✅ Shared RAM and vCPU
- ✅ No credit card required
- ✅ Perfect for development and small apps

This is more than enough for storing login tokens!

---

## Troubleshooting

**Connection fails:**
- Check IP whitelist allows `0.0.0.0/0`
- Verify username/password are correct
- Check connection string format
- Ensure cluster is running (not paused)

**"Invalid credentials" error:**
- Verify username/password in connection string
- URL-encode special characters in password
- Check database user has read/write permissions

**Still having issues?**
- Test connection string locally with `mongosh`
- Check Vercel function logs for detailed errors
- Use `/api/test-db` endpoint to debug

