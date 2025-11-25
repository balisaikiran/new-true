# Netlify Deployment Guide

## 🚀 Deploying to Netlify

### Prerequisites

1. **Netlify Account**: Sign up at [netlify.com](https://www.netlify.com)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

### Step 1: Configure Netlify

1. **Connect Repository**:
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect your Git repository

2. **Build Settings** (should auto-detect from `netlify.toml`):
   - **Build command**: `cd frontend && npm install --legacy-peer-deps && npm run build`
   - **Publish directory**: `frontend/build`
   - **Functions directory**: `netlify/functions`

### Step 2: Set Environment Variables

Go to **Site settings** → **Environment variables** and add:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=pothos
CORS_ORIGINS=https://visionary-clafoutis-cf4558.netlify.app,http://localhost:3000
REACT_APP_BACKEND_URL=https://visionary-clafoutis-cf4558.netlify.app
```

**Important**: Replace `visionary-clafoutis-cf4558.netlify.app` with your actual Netlify domain!

### Step 3: Deploy

1. **Automatic Deploy**:
   - Push to your main branch
   - Netlify will automatically deploy

2. **Manual Deploy**:
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Login
   netlify login
   
   # Deploy
   netlify deploy --prod
   ```

### Step 4: Verify Deployment

1. **Check Build Logs**:
   - Go to Netlify Dashboard → Your site → Deploys
   - Check build logs for errors

2. **Test API**:
   - Visit: `https://your-site.netlify.app/api/`
   - Should return: `{"message": "TrueData Analytics API"}`

3. **Test Login**:
   - Visit: `https://your-site.netlify.app`
   - Try logging in with your credentials

## 📋 File Structure

```
.
├── netlify.toml              # Netlify configuration
├── netlify/
│   └── functions/
│       └── api/
│           ├── index.py      # Netlify function handler
│           └── requirements.txt
├── backend/
│   └── server.py             # FastAPI backend
└── frontend/
    └── build/                # Built frontend (generated)
```

## 🔧 Configuration Files

### `netlify.toml`
- Build settings
- Redirect rules for API routes
- SPA routing (all routes → index.html)

### `netlify/functions/api/index.py`
- Netlify Functions handler
- Wraps FastAPI app with Mangum
- Handles all `/api/*` routes

## ⚠️ Important Notes

1. **Python Runtime**: Netlify Functions supports Python 3.11
2. **Function Timeout**: Default is 10 seconds (can be increased in Netlify settings)
3. **Cold Starts**: First request may be slower (cold start)
4. **Environment Variables**: Must be set in Netlify Dashboard

## 🐛 Troubleshooting

### Issue: 404 on API routes
**Solution**: Check `netlify.toml` redirects are correct

### Issue: Function timeout
**Solution**: Increase timeout in Netlify settings (up to 26 seconds)

### Issue: Import errors
**Solution**: Check `netlify/functions/api/requirements.txt` has all dependencies

### Issue: CORS errors
**Solution**: Update `CORS_ORIGINS` environment variable with your Netlify domain

## 🔗 URLs to Update

After deployment, update these URLs:

1. **Netlify Site URL**: `https://visionary-clafoutis-cf4558.netlify.app`
2. **Environment Variables**:
   - `REACT_APP_BACKEND_URL` = Your Netlify URL
   - `CORS_ORIGINS` = Your Netlify URL + localhost

## ✅ After Deployment

1. **Update Environment Variables** with your actual Netlify domain
2. **Redeploy** to apply changes
3. **Test** the login functionality
4. **Check Function Logs** in Netlify Dashboard if issues occur

## 📝 Quick Checklist

- [ ] `netlify.toml` created
- [ ] `netlify/functions/api/index.py` created
- [ ] `netlify/functions/api/requirements.txt` created
- [ ] Environment variables set in Netlify
- [ ] Site deployed successfully
- [ ] API endpoint works (`/api/`)
- [ ] Login works

Your app should now be live on Netlify! 🎉

