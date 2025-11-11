# Fixing "Invalid Creds" Error on Vercel

## The Problem
MongoDB connection fails on Vercel with "invalid creds" error, but works locally.

## Common Causes

### 1. Environment Variables Not Set
**Check:** Go to Vercel Dashboard → Your Project → Settings → Environment Variables

**Required Variables:**
- `MONGO_URL` - Your MongoDB connection string
- `DB_NAME` - Your database name

### 2. MongoDB Atlas IP Whitelist
**Problem:** MongoDB Atlas blocks connections from Vercel's IP addresses.

**Solution:**
1. Go to MongoDB Atlas Dashboard
2. Click "Network Access" (or "IP Access List")
3. Click "Add IP Address"
4. Click "Allow Access from Anywhere" (adds `0.0.0.0/0`)
   - Or add Vercel's IP ranges (less secure but more restrictive)

### 3. Connection String Format
**Problem:** Connection string might have special characters that need encoding.

**Check your MONGO_URL format:**
```
mongodb+srv://username:password@cluster.mongodb.net/
```

**Important:**
- Username/password should be URL-encoded if they contain special characters
- No database name at the end (that's set via DB_NAME)
- Must include `mongodb+srv://` for Atlas

### 4. Database User Permissions
**Problem:** Database user doesn't have proper permissions.

**Solution:**
1. Go to MongoDB Atlas → Database Access
2. Edit your database user
3. Ensure user has "Read and write to any database" or specific database access
4. Save changes

## Step-by-Step Fix

### Step 1: Verify Environment Variables in Vercel

1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Verify these are set:
   ```
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DB_NAME=your_database_name
   ```

**Note:** Replace `username`, `password`, `cluster`, and `your_database_name` with your actual values.

### Step 2: Check MongoDB Atlas Network Access

1. Log into MongoDB Atlas
2. Go to "Network Access" (left sidebar)
3. Click "Add IP Address"
4. Click "Allow Access from Anywhere" 
5. This adds `0.0.0.0/0` (allows all IPs)
6. Click "Confirm"

**Security Note:** For production, consider restricting to Vercel's IP ranges, but allowing all IPs is fine for development.

### Step 3: Verify Database User

1. In MongoDB Atlas, go to "Database Access"
2. Find your database user
3. Click "Edit"
4. Under "Database User Privileges", ensure:
   - "Atlas admin" OR
   - "Read and write to any database" OR
   - Specific database access with read/write permissions
5. Save changes

### Step 4: Test Connection String Locally

Test your connection string format:
```bash
# Replace with your actual connection string
mongosh "mongodb+srv://username:password@cluster.mongodb.net/your_database"
```

If this fails locally, the connection string is wrong.

### Step 5: Check Vercel Function Logs

1. Go to Vercel Dashboard → Your Project
2. Click "Functions" tab
3. Click on `api/index.py`
4. Check "Logs" tab
5. Look for MongoDB connection errors

Common error messages:
- `ServerSelectionTimeoutError` → IP not whitelisted
- `Authentication failed` → Wrong username/password
- `bad auth` → Invalid credentials

### Step 6: URL Encode Special Characters

If your MongoDB password has special characters, URL encode them:

**Special characters that need encoding:**
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`
- `#` → `%23`
- `?` → `%3F`
- `&` → `%26`
- `=` → `%3D`
- `+` → `%2B`
- `%` → `%25`
- ` ` (space) → `%20`

**Example:**
```
Password: my@pass#123
Encoded: my%40pass%23123
```

### Step 7: Redeploy After Changes

After updating environment variables or MongoDB settings:
1. Go to Vercel Dashboard → Deployments
2. Click "Redeploy" on latest deployment
3. Or push a new commit to trigger redeploy

## Quick Test

Create a test endpoint to check MongoDB connection:

```python
@app.get("/api/test-db")
async def test_db():
    try:
        await client.admin.command('ping')
        return {"status": "connected", "db": os.environ.get('DB_NAME')}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

Access: `https://your-app.vercel.app/api/test-db`

## Still Not Working?

1. **Double-check connection string:**
   - Copy from MongoDB Atlas → Connect → Connect your application
   - Remove `<password>` and replace with actual password
   - Remove `<dbname>` if present (we use DB_NAME env var)

2. **Create new database user:**
   - Sometimes creating a fresh user fixes permission issues
   - Use a simple password without special characters

3. **Check MongoDB Atlas Status:**
   - Ensure your cluster is running
   - Check for any Atlas service issues

4. **Try localhost connection string:**
   - If using local MongoDB, ensure it's accessible from internet
   - Consider using MongoDB Atlas instead for Vercel deployment

## Example Environment Variables

**For MongoDB Atlas:**
```
MONGO_URL=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/
DB_NAME=truedata
```

**For MongoDB Atlas with special characters:**
```
MONGO_URL=mongodb+srv://myuser:my%40pass%23123@cluster0.xxxxx.mongodb.net/
DB_NAME=truedata
```

**Note:** Never commit `.env` files with real credentials to Git!

