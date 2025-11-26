# Deploy Backend to Vercel

## Quick Deployment Guide

### Step 1: Ensure Code is Ready

Make sure your code is committed and pushed to Git:
```bash
git add .
git commit -m "Backend ready for Vercel deployment"
git push origin main
```

### Step 2: Deploy via Vercel Dashboard

1. **Go to Vercel Dashboard**
   - Visit https://vercel.com/new
   - Click "Import Git Repository"
   - Select your repository

2. **Configure Project Settings**
   - **Framework Preset**: `Other`
   - **Root Directory**: `./` (root directory)
   - **Build Command**: Leave **EMPTY** (no build needed for Python)
   - **Output Directory**: Leave **EMPTY**
   - **Install Command**: Leave **EMPTY**

3. **Add Environment Variables**
   Go to Settings → Environment Variables and add:
   ```
   MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
   DB_NAME=pothos
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   VERCEL=1
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete

### Step 3: Test Deployment

After deployment, test these URLs:
- `https://your-app.vercel.app/api/` → Should return `{"message": "TrueData Analytics API"}`
- `https://your-app.vercel.app/api/test-db` → Should show MongoDB connection status

### Step 4: Deploy via Vercel CLI (Alternative)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (preview)
vercel

# Deploy to production
vercel --prod
```

## Important Notes

1. **Scheduler Disabled**: APScheduler is disabled in Vercel (serverless doesn't support long-running processes)
   - Use Vercel Cron Jobs for scheduled tasks
   - Or use external scheduler service

2. **Environment Variables**: Make sure all required variables are set:
   - `MONGO_URL` - MongoDB connection string
   - `DB_NAME` - Database name
   - `CORS_ORIGINS` - Allowed origins
   - `VERCEL=1` - Detects serverless environment

3. **Dependencies**: All dependencies are in `api/requirements.txt`
   - Includes: FastAPI, Mangum, Motor, APScheduler, NumPy, etc.

4. **File Structure**: 
   - `api/index.py` - Vercel serverless function entry point
   - `backend/server.py` - FastAPI application
   - `vercel.json` - Vercel configuration

## Troubleshooting

### Build Fails
- Check Vercel build logs
- Ensure `api/requirements.txt` has all dependencies
- Verify Python version (Vercel uses Python 3.9+)

### API Returns 500 Error
- Check Vercel function logs
- Verify environment variables are set
- Check MongoDB connection string

### Import Errors
- Ensure `backend/` directory is included (via `includeFiles` in vercel.json)
- Check that all dependencies are in `api/requirements.txt`

## Vercel Cron Jobs (for Scheduled Tasks)

Since APScheduler doesn't work in serverless, use Vercel Cron Jobs:

1. Create `vercel.json` with cron configuration:
```json
{
  "crons": [{
    "path": "/api/cron/daily-save",
    "schedule": "0 10 * * *"
  }]
}
```

2. Create endpoint `/api/cron/daily-save` that calls `save_daily_stock_data()`

