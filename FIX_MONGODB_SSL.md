# 🔧 Fix MongoDB SSL Certificate Issue (Local Development)

The MongoDB SSL certificate error you're seeing is a **local development issue only**. It won't affect Vercel deployment.

## Why This Happens

MongoDB Atlas uses SSL certificates, and your local Python might not have the right certificates installed. This is common on macOS.

## ✅ Solution (Optional - MongoDB is Optional!)

The app works fine without MongoDB! But if you want to fix it locally:

### Option 1: Install Certificates (Recommended)

```bash
# Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Or if that doesn't exist:
pip install --upgrade certifi
```

### Option 2: Update MongoDB Connection String

Add `tlsAllowInvalidCertificates=true` to your MongoDB connection string (for local dev only):

```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname?tlsAllowInvalidCertificates=true
```

**⚠️ Warning**: Only use this for local development! Never use `tlsAllowInvalidCertificates=true` in production.

### Option 3: Just Ignore It

The app works perfectly without MongoDB! MongoDB is only used for storing login tokens, and the app handles the connection failure gracefully.

---

## ✅ Your Backend is Working!

All your endpoints are working:
- ✅ Root endpoint: `GET /api/` → 200 OK
- ✅ Health check: `GET /api/health` → 200 OK  
- ✅ Login endpoint: `POST /api/auth/login` → 401 (expected with test creds)
- ✅ Error handling: Proper error responses

**The MongoDB SSL error doesn't break anything!**

