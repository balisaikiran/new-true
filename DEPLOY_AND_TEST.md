# 🚀 Deploy and Test API on Vercel

This guide will help you deploy your backend API to Vercel and test it online.

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier available)
2. **Node.js**: Installed on your machine (for Vercel CLI)
3. **Git**: Your code should be in a Git repository (GitHub/GitLab/Bitbucket)

## 🚀 Quick Deployment (Method 1: Using Script)

### Step 1: Run the deployment script

```bash
./deploy-to-vercel.sh
```

This script will:
- Check/install Vercel CLI
- Authenticate you with Vercel
- Deploy your API to Vercel

### Step 2: Follow the prompts

- The script will ask you to login if not already logged in
- Answer questions about your project (or press Enter for defaults)
- Vercel will provide you with a deployment URL

### Step 3: Set Environment Variables

After deployment, go to your Vercel Dashboard:
1. Go to your project → Settings → Environment Variables
2. Add these variables:

```
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=truedata
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

3. Redeploy after adding environment variables:
   ```bash
   vercel --prod
   ```

## 🚀 Manual Deployment (Method 2: Using Vercel CLI)

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

## 🌐 Deployment via Vercel Dashboard (Method 3)

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push origin main
   ```

2. **Go to Vercel Dashboard**
   - Visit https://vercel.com/new
   - Click "Import Git Repository"
   - Select your repository

3. **Configure Project Settings**
   - **Framework Preset**: Other
   - **Root Directory**: `./` (root)
   - **Build Command**: `cd frontend && npm install --legacy-peer-deps && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `cd frontend && npm install --legacy-peer-deps`

4. **Add Environment Variables**
   - Go to Settings → Environment Variables
   - Add all required variables (see above)

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete

## 🧪 Testing Your Deployed API

### Quick Test (No Authentication)

```bash
# Test basic endpoints
./test-api.sh https://your-app.vercel.app
```

This will test:
- ✅ Root endpoint (`/api/`)
- ✅ Database connection (`/api/test-db`)
- ✅ Login endpoint availability (`/api/auth/login`)
- ✅ Dashboard endpoint availability (`/api/market/dashboard`)

### Full Test (With Authentication)

```bash
# Interactive test with real credentials
python3 test-api-with-auth.py https://your-app.vercel.app
```

This will:
- Test all endpoints
- Prompt for TrueData credentials
- Test login and retrieve access token
- Test dashboard data retrieval
- Test option chain data retrieval

### Manual Testing with curl

```bash
# 1. Test root endpoint
curl https://your-app.vercel.app/api/

# 2. Test database connection
curl https://your-app.vercel.app/api/test-db

# 3. Test login (replace with your credentials)
curl -X POST https://your-app.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# 4. Test dashboard (replace TOKEN with actual token from login)
curl "https://your-app.vercel.app/api/market/dashboard?token=YOUR_TOKEN"

# 5. Test option chain
curl "https://your-app.vercel.app/api/market/optionchain/NIFTY?expiry=2024-12-26&token=YOUR_TOKEN"
```

### Testing in Browser

1. **Root endpoint**: Visit `https://your-app.vercel.app/api/`
2. **Database test**: Visit `https://your-app.vercel.app/api/test-db`
3. **API Documentation**: Vercel doesn't automatically serve FastAPI docs, but you can test endpoints directly

## 📝 API Endpoints Reference

Once deployed, your API will be available at:
- **Base URL**: `https://your-app.vercel.app/api`

### Available Endpoints:

1. **GET `/api/`** - Root endpoint
   - Returns: `{"message": "TrueData Analytics API"}`

2. **GET `/api/test-db`** - Database connection test
   - Returns: Database connection status

3. **POST `/api/auth/login`** - User authentication
   - Body: `{"username": "string", "password": "string"}`
   - Returns: `{"success": true, "access_token": "...", "expires_in": 3600}`

4. **GET `/api/market/dashboard`** - Get dashboard data
   - Query params: `token` (required)
   - Returns: List of stock data for top 20 F&O stocks

5. **GET `/api/market/optionchain/{symbol}`** - Get option chain
   - Query params: `expiry` (required), `token` (required)
   - Returns: Option chain data for the symbol

## 🔧 Troubleshooting

### Issue: API returns 404

**Solution**: 
- Check that `api/index.py` exists
- Verify `vercel.json` has correct rewrites
- Ensure `api/requirements.txt` includes `mangum`

### Issue: Import errors in logs

**Solution**:
- Check that `backend/server.py` exists
- Verify Python path in `api/index.py`
- Check Vercel function logs in dashboard

### Issue: MongoDB connection fails

**Solution**:
- Verify `MONGO_URL` environment variable is set correctly
- Check MongoDB Atlas allows connections from Vercel IPs (0.0.0.0/0)
- Verify `DB_NAME` is set correctly

### Issue: CORS errors

**Solution**:
- Add your Vercel URL to `CORS_ORIGINS` environment variable
- Format: `https://your-app.vercel.app,https://www.your-app.vercel.app`

### Issue: Build fails

**Solution**:
- Check build logs in Vercel dashboard
- Ensure all dependencies are in `api/requirements.txt`
- Verify Python version (Vercel uses Python 3.9 by default)

## 📊 Monitoring Your Deployment

1. **Vercel Dashboard**: https://vercel.com/dashboard
   - View deployment logs
   - Check function logs
   - Monitor performance

2. **Function Logs**:
   - Go to your project → Functions tab
   - Click on a function to see logs
   - Check for errors or warnings

## 🔄 Updating Your Deployment

After making changes:

```bash
# Commit changes
git add .
git commit -m "Update API"

# Push to trigger auto-deployment (if connected to Git)
git push origin main

# Or deploy manually
vercel --prod
```

## ✅ Success Checklist

- [ ] API deployed to Vercel
- [ ] Environment variables set
- [ ] Root endpoint returns success (`/api/`)
- [ ] Database test endpoint works (`/api/test-db`)
- [ ] Login endpoint accepts requests (`/api/auth/login`)
- [ ] Can authenticate with TrueData credentials
- [ ] Dashboard endpoint returns data (`/api/market/dashboard`)
- [ ] Option chain endpoint works (`/api/market/optionchain/{symbol}`)

## 🎯 Next Steps

1. **Test all endpoints** using the provided scripts
2. **Update frontend** to use your Vercel API URL
3. **Set up monitoring** in Vercel dashboard
4. **Configure custom domain** (optional) in Vercel settings

## 📞 Support

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Support**: https://vercel.com/support
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Mangum Docs**: https://mangum.io

---

Happy deploying! 🚀

