# Netlify Deployment - Quick Setup

## ✅ Files Created

1. **`netlify.toml`** - Netlify configuration
2. **`netlify/functions/api/index.py`** - Netlify Functions handler
3. **`netlify/functions/api/requirements.txt`** - Python dependencies
4. **`netlify/functions/api/runtime.txt`** - Python runtime version

## 🚀 Quick Deploy Steps

### 1. Push to Git
```bash
git add netlify.toml netlify/ NETLIFY_DEPLOY.md
git commit -m "Add Netlify deployment configuration"
git push
```

### 2. Connect to Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect your Git repository
4. Netlify will auto-detect settings from `netlify.toml`

### 3. Set Environment Variables

In Netlify Dashboard → **Site settings** → **Environment variables**, add:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=pothos
CORS_ORIGINS=https://visionary-clafoutis-cf4558.netlify.app,http://localhost:3000
REACT_APP_BACKEND_URL=https://visionary-clafoutis-cf4558.netlify.app
```

**⚠️ Important**: Replace `visionary-clafoutis-cf4558.netlify.app` with your actual Netlify domain after deployment!

### 4. Deploy

Netlify will automatically deploy when you push. Or deploy manually:

```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

## 🔗 URLs Configuration

### After Deployment:

1. **Get your Netlify URL** (e.g., `https://visionary-clafoutis-cf4558.netlify.app`)

2. **Update Environment Variables** in Netlify Dashboard:
   - `REACT_APP_BACKEND_URL` = `https://your-site.netlify.app`
   - `CORS_ORIGINS` = `https://your-site.netlify.app,http://localhost:3000`

3. **Redeploy** to apply changes

## 📋 What Changed from Vercel

### File Structure:
- **Vercel**: `api/index.py` → **Netlify**: `netlify/functions/api/index.py`
- **Vercel**: `vercel.json` → **Netlify**: `netlify.toml`

### Routing:
- **Vercel**: `/api/*` → `/api/index.py`
- **Netlify**: `/api/*` → `/.netlify/functions/api/*`

### Frontend:
- **No changes needed!** Frontend uses `window.location.origin` as fallback
- Will automatically work with Netlify domain

## ✅ Testing

After deployment:

1. **Test API**: `https://your-site.netlify.app/api/`
   - Should return: `{"message": "TrueData Analytics API"}`

2. **Test Login**: `https://your-site.netlify.app`
   - Try logging in with: `tdwsp784` / `sid@784`

3. **Check Logs**: Netlify Dashboard → Functions → Logs
   - Look for initialization messages
   - Check for any errors

## 🐛 Troubleshooting

### 404 on API routes
- Check `netlify.toml` redirects
- Verify function is deployed in `netlify/functions/api/`

### Function timeout
- Increase timeout in Netlify settings (up to 26 seconds)

### CORS errors
- Update `CORS_ORIGINS` with your Netlify domain
- Redeploy after updating environment variables

## 📝 Checklist

- [x] `netlify.toml` created
- [x] `netlify/functions/api/index.py` created
- [x] `netlify/functions/api/requirements.txt` created
- [x] `netlify/functions/api/runtime.txt` created
- [ ] Code pushed to Git
- [ ] Site connected to Netlify
- [ ] Environment variables set
- [ ] Site deployed
- [ ] API tested
- [ ] Login tested

Your app is now ready for Netlify deployment! 🎉

