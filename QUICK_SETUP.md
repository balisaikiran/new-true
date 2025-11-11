# Quick MongoDB Setup for Vercel

## ✅ Your MongoDB Connection String

```
mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
```

## 🚀 Quick Setup Steps

### 1. Set Environment Variables in Vercel

Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**

Add these **5 variables**:

| Variable Name | Value |
|--------------|-------|
| `MONGO_URL` | `mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/` |
| `DB_NAME` | `truedata` |
| `CORS_ORIGINS` | `https://YOUR-VERCEL-URL.vercel.app,http://localhost:3000` |
| `REACT_APP_BACKEND_URL` | `https://YOUR-VERCEL-URL.vercel.app` |
| `REACT_APP_ENABLE_VISUAL_EDITS` | `false` |

**Important:** Replace `YOUR-VERCEL-URL.vercel.app` with your actual Vercel deployment URL!

### 2. Allow MongoDB Access from Vercel

1. Go to **MongoDB Atlas**: https://cloud.mongodb.com
2. Click **"Network Access"** (left sidebar)
3. Click **"Add IP Address"**
4. Click **"Allow Access from Anywhere"** 
5. Click **"Confirm"**

This adds `0.0.0.0/0` which allows Vercel to connect.

### 3. Redeploy Your App

**After setting environment variables, you MUST redeploy:**

1. Go to **Deployments** tab in Vercel
2. Click **"Redeploy"** on latest deployment
3. Wait for deployment to complete

### 4. Test Connection

Visit: `https://YOUR-VERCEL-URL.vercel.app/api/test-db`

Should return:
```json
{
  "status": "connected",
  "database": "truedata",
  "message": "MongoDB connection successful"
}
```

## 📋 Complete Checklist

- [ ] Set `MONGO_URL` in Vercel
- [ ] Set `DB_NAME` in Vercel (e.g., `truedata`)
- [ ] Set `CORS_ORIGINS` with your Vercel URL
- [ ] Set `REACT_APP_BACKEND_URL` with your Vercel URL
- [ ] Allow MongoDB access from `0.0.0.0/0` in Atlas
- [ ] Redeploy app in Vercel
- [ ] Test `/api/test-db` endpoint
- [ ] Try logging in with TrueData credentials

## 🔍 Finding Your Vercel URL

1. Go to Vercel Dashboard
2. Click on your project
3. Copy the URL shown (e.g., `https://your-app-name.vercel.app`)

## ⚠️ Important Notes

1. **Trailing Slash:** Make sure `MONGO_URL` ends with `/`
2. **Redeploy Required:** Environment variables only take effect after redeploy
3. **Network Access:** MongoDB Atlas must allow `0.0.0.0/0` for Vercel to connect
4. **Database Name:** You can use any name (e.g., `truedata`, `mydb`, etc.)

## 🐛 Troubleshooting

**If `/api/test-db` shows error:**

1. Check MongoDB Atlas Network Access allows `0.0.0.0/0`
2. Verify `MONGO_URL` has trailing `/`
3. Check Vercel Function Logs for detailed error
4. Ensure you redeployed after setting env vars

**If login still shows "invalid creds":**

- This is a TrueData API issue, not MongoDB
- Check Vercel Function Logs for TrueData API response
- Verify TrueData credentials are correct

Your MongoDB is now configured! 🎉

