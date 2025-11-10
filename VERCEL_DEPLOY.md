# Quick Vercel Deployment Guide

## 🚀 Quick Start

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Go to Vercel Dashboard**
   - Visit https://vercel.com/new
   - Click "Import Git Repository"
   - Select your repository

3. **Configure Project Settings**
   - **Framework Preset**: Other
   - **Root Directory**: `./` (leave as root)
   - **Build Command**: `cd frontend && npm install --legacy-peer-deps && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `cd frontend && npm install --legacy-peer-deps`

4. **Add Environment Variables**
   Go to Settings → Environment Variables and add:
   ```
   MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
   DB_NAME=truedata
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   REACT_APP_BACKEND_URL=https://your-app.vercel.app
   REACT_APP_ENABLE_VISUAL_EDITS=false
   ENABLE_HEALTH_CHECK=false
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-app.vercel.app`

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel

# For production
vercel --prod
```

## 📋 Environment Variables Checklist

Make sure these are set in Vercel Dashboard → Settings → Environment Variables:

- ✅ `MONGO_URL` - MongoDB connection string
- ✅ `DB_NAME` - Database name
- ✅ `CORS_ORIGINS` - Allowed origins (include your Vercel URL)
- ✅ `REACT_APP_BACKEND_URL` - Your Vercel deployment URL
- ✅ `REACT_APP_ENABLE_VISUAL_EDITS` - Set to `false`
- ✅ `ENABLE_HEALTH_CHECK` - Set to `false`

## 🔧 Project Structure

```
.
├── api/
│   ├── index.py              # Vercel serverless function
│   └── requirements.txt       # Python dependencies
├── backend/
│   ├── server.py              # FastAPI app
│   └── requirements.txt      # Backend dependencies
├── frontend/
│   ├── src/                   # React source
│   ├── public/                # Static files
│   └── package.json           # Frontend dependencies
└── vercel.json                # Vercel configuration
```

## 🐛 Troubleshooting

### Build Fails
- Check build logs in Vercel dashboard
- Ensure `npm install --legacy-peer-deps` is used
- Verify Node.js version (should be 18+)

### API Routes Not Working
- Check that `api/index.py` exists
- Verify `api/requirements.txt` includes `mangum`
- Check function logs in Vercel dashboard

### MongoDB Connection Issues
- Verify `MONGO_URL` is correct
- Ensure MongoDB Atlas allows connections from Vercel IPs (0.0.0.0/0)
- Check database name matches `DB_NAME`

### CORS Errors
- Add your Vercel URL to `CORS_ORIGINS`
- Format: `https://your-app.vercel.app,https://www.your-app.vercel.app`

## 📝 Post-Deployment

1. Test API: `https://your-app.vercel.app/api/`
2. Test Frontend: `https://your-app.vercel.app/`
3. Update `REACT_APP_BACKEND_URL` to match your deployment URL

## 🔄 Updating Deployment

After making changes:
```bash
git add .
git commit -m "Update app"
git push origin main
```
Vercel will automatically redeploy!

