# Vercel Build Fix Guide

## Common Build Errors and Solutions

### Error: Build fails during "vercel build"

**Solution 1: Check Build Command**
The build command must run from the correct directory:
```json
"buildCommand": "cd frontend && npm install --legacy-peer-deps && npm run build"
```

**Solution 2: Verify Node.js Version**
Vercel uses Node.js 18.x by default. If you need a specific version, add to `package.json`:
```json
{
  "engines": {
    "node": ">=18.0.0"
  }
}
```

**Solution 3: Check Python Runtime**
Ensure `api/requirements.txt` exists and includes all dependencies:
- `mangum>=0.17.0` (required for FastAPI on Vercel)
- All FastAPI dependencies

**Solution 4: Verify File Structure**
Ensure these files exist and are committed:
```
├── api/
│   ├── index.py          ✅ Must exist
│   └── requirements.txt ✅ Must exist
├── backend/
│   └── server.py         ✅ Must exist
├── frontend/
│   └── package.json     ✅ Must exist
└── vercel.json          ✅ Must exist
```

### Error: Python function build fails

**Check:**
1. `api/requirements.txt` includes `mangum`
2. All backend dependencies are listed
3. Python version is compatible (3.9)

### Error: Frontend build fails

**Check:**
1. `frontend/package.json` exists
2. Build command uses `--legacy-peer-deps`
3. No syntax errors in React code

### Quick Fix Steps

1. **Remove conflicting configs:**
   - Delete `frontend/vercel.json` if it exists
   - Keep only root `vercel.json`

2. **Verify environment variables are set:**
   - Go to Vercel Dashboard → Settings → Environment Variables
   - Ensure `MONGO_URL` and `DB_NAME` are set

3. **Check build logs:**
   - Look for specific error messages
   - Common errors:
     - `Module not found` → Missing dependency
     - `Command failed` → Build command issue
     - `File not found` → Missing file

4. **Try simplified build:**
   If build still fails, try this minimal `vercel.json`:
   ```json
   {
     "buildCommand": "cd frontend && npm install --legacy-peer-deps && npm run build",
     "outputDirectory": "frontend/build"
   }
   ```

5. **Redeploy:**
   ```bash
   git add .
   git commit -m "Fix build configuration"
   git push
   ```

### Debugging Build Issues

1. **Check Vercel Build Logs:**
   - Go to Deployment → Build Logs
   - Look for error messages
   - Check which step fails

2. **Test Locally:**
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   npm run build
   ```
   If this fails locally, fix the issue before deploying.

3. **Check Function Logs:**
   - After deployment, check Function Logs
   - Look for Python import errors
   - Check if backend files are accessible

### Still Failing?

If build continues to fail:

1. **Check Vercel Status:** https://vercel-status.com
2. **Review Documentation:** https://vercel.com/docs
3. **Try Manual Deployment:**
   ```bash
   npm i -g vercel
   vercel --prod
   ```

