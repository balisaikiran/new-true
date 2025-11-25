# 🚀 Separate Backend & Frontend Deployment Guide

This guide explains how to deploy backend and frontend as separate Vercel projects.

## 📋 Project Structure

- **Backend**: Deployed at `pothos-v2.vercel.app`
- **Frontend**: Deployed as separate Vercel project
- **Configuration**: 
  - Root `vercel.json` → Backend-only config
  - `frontend/vercel.json` → Frontend-only config

---

## 🔧 Backend Deployment (pothos-v2.vercel.app)

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Backend deployment setup"
git push origin main
```

### Step 2: Create Backend Project in Vercel

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your repository

### Step 3: Configure Backend Project

**Project Settings:**
- **Project Name**: `pothos-v2` (this gives you `pothos-v2.vercel.app`)
- **Framework Preset**: `Other`
- **Root Directory**: `./` (root directory)
- **Build Command**: Leave **EMPTY**
- **Output Directory**: Leave **EMPTY**
- **Install Command**: Leave **EMPTY**

**Environment Variables:**
Add these in Settings → Environment Variables:

| Key | Value | Environments |
|-----|-------|--------------|
| `MONGO_URL` | `mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/` | Production, Preview, Development |
| `DB_NAME` | `pothos` | Production, Preview, Development |
| `CORS_ORIGINS` | `*` (or specific frontend URLs) | Production, Preview, Development |

### Step 4: Deploy Backend

1. Click "Deploy"
2. Wait for deployment to complete
3. Your backend will be live at: `https://pothos-v2.vercel.app/api/`

### Step 5: Test Backend

Test these URLs in your browser:
- ✅ `https://pothos-v2.vercel.app/api/` → Should return `{"message": "TrueData Analytics API"}`
- ✅ `https://pothos-v2.vercel.app/api/test-db` → Should show MongoDB connection status

---

## 🎨 Frontend Deployment

### Step 1: Push Code (Same Repository)

The frontend code is already in the same repository, so no need to push again if you just pushed backend changes.

### Step 2: Create Frontend Project in Vercel

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select the **SAME** repository (yes, you'll have 2 projects from 1 repo)

### Step 3: Configure Frontend Project

**Project Settings:**
- **Project Name**: `pothos-frontend` (or any name you prefer)
- **Framework Preset**: `Create React App` (or `Other`)
- **Root Directory**: `frontend` ⚠️ **IMPORTANT: Set this to `frontend`**
- **Build Command**: `npm install --legacy-peer-deps && npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install --legacy-peer-deps`

**Environment Variables:**
Add this in Settings → Environment Variables:

| Key | Value | Environments |
|-----|-------|--------------|
| `REACT_APP_BACKEND_URL` | `https://pothos-v2.vercel.app` | Production, Preview, Development |

### Step 4: Deploy Frontend

1. Click "Deploy"
2. Wait for build to complete (may take 2-5 minutes)
3. Your frontend will be live at: `https://pothos-frontend.vercel.app` (or your chosen name)

---

## 🔗 Connect Frontend to Backend

### Step 1: Update Backend CORS

After frontend is deployed, update backend CORS settings:

1. Go to **Backend Project** (`pothos-v2`) → Settings → Environment Variables
2. Edit `CORS_ORIGINS`:
   ```
   https://pothos-frontend.vercel.app,https://pothos-frontend-*.vercel.app,http://localhost:3000
   ```
   (Replace `pothos-frontend` with your actual frontend project name)
3. Go to Deployments tab
4. Click "Redeploy" on the latest deployment

### Step 2: Test Connection

1. Visit your frontend URL: `https://pothos-frontend.vercel.app`
2. Try logging in with TrueData credentials
3. Check browser console (F12) to verify API calls are going to `https://pothos-v2.vercel.app/api/`

---

## ✅ Deployment Checklist

### Backend Checklist:
- [ ] Root `vercel.json` updated (backend-only config)
- [ ] Created Vercel project: `pothos-v2`
- [ ] Root Directory: `./` (root)
- [ ] Build/Output/Install commands: **EMPTY**
- [ ] `MONGO_URL` environment variable added
- [ ] `DB_NAME` environment variable added
- [ ] `CORS_ORIGINS` environment variable added
- [ ] Deployed successfully
- [ ] Tested `https://pothos-v2.vercel.app/api/`
- [ ] Tested `https://pothos-v2.vercel.app/api/test-db`

### Frontend Checklist:
- [ ] `frontend/vercel.json` created
- [ ] Created separate Vercel project for frontend
- [ ] Root Directory: `frontend` ⚠️
- [ ] Build Command: `npm install --legacy-peer-deps && npm run build`
- [ ] Output Directory: `build`
- [ ] `REACT_APP_BACKEND_URL` set to `https://pothos-v2.vercel.app`
- [ ] Deployed successfully
- [ ] Updated backend `CORS_ORIGINS` with frontend URL
- [ ] Tested frontend → backend connection

---

## 🧪 Testing

### Backend API Endpoints:

```bash
# Root endpoint
curl https://pothos-v2.vercel.app/api/

# Database test
curl https://pothos-v2.vercel.app/api/test-db

# Login (replace credentials)
curl -X POST https://pothos-v2.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

### Frontend:

1. Visit: `https://pothos-frontend.vercel.app`
2. Open browser console (F12)
3. Check Network tab to see API calls going to `pothos-v2.vercel.app`
4. Try logging in

---

## 🔄 Updating Deployments

### Update Backend:
```bash
git add .
git commit -m "Backend update"
git push origin main
# Backend project will auto-deploy
```

### Update Frontend:
```bash
git add .
git commit -m "Frontend update"
git push origin main
# Frontend project will auto-deploy
```

---

## 🐛 Troubleshooting

### Backend Issues:

**Problem**: API returns 404
- ✅ Check `vercel.json` has correct rewrites
- ✅ Verify `api/index.py` exists
- ✅ Check function logs in Vercel dashboard

**Problem**: MongoDB connection fails
- ✅ Verify `MONGO_URL` is correct
- ✅ Check MongoDB Atlas allows connections from Vercel (0.0.0.0/0)
- ✅ Verify `DB_NAME` matches your database

### Frontend Issues:

**Problem**: Frontend can't connect to backend
- ✅ Check `REACT_APP_BACKEND_URL` is set correctly
- ✅ Verify backend CORS includes frontend URL
- ✅ Check browser console for CORS errors

**Problem**: Build fails
- ✅ Check Node.js version (should be 18+)
- ✅ Verify `frontend/vercel.json` exists
- ✅ Check build logs in Vercel dashboard

---

## 📊 URLs Summary

After deployment, you'll have:

- **Backend API**: `https://pothos-v2.vercel.app/api/`
- **Frontend App**: `https://pothos-frontend.vercel.app` (or your chosen name)

Frontend automatically connects to backend via `REACT_APP_BACKEND_URL` environment variable.

---

## 🎯 Next Steps

1. Deploy backend first → Get `pothos-v2.vercel.app`
2. Deploy frontend → Set `REACT_APP_BACKEND_URL` to backend URL
3. Update backend CORS with frontend URL
4. Test both deployments
5. Share your frontend URL with users!

---

Happy deploying! 🚀

