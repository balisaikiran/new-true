# Vercel Deployment - Troubleshooting 404 Errors

## Common 404 Issues and Solutions

### Issue: API routes return 404

**Solution 1: Check Function Location**
- Ensure `api/index.py` exists in the root directory
- Ensure `backend/server.py` exists
- Both files should be committed to Git

**Solution 2: Verify Vercel Configuration**
- Check `vercel.json` has correct routing:
  ```json
  {
    "rewrites": [
      {
        "source": "/api/(.*)",
        "destination": "/api/index.py"
      }
    ]
  }
  ```

**Solution 3: Check Environment Variables**
- `MONGO_URL` must be set
- `DB_NAME` must be set
- These are required for the app to start

**Solution 4: Verify Python Dependencies**
- `api/requirements.txt` must include `mangum>=0.17.0`
- All FastAPI dependencies must be listed

### Testing Steps

1. **Test API endpoint directly:**
   ```
   https://your-app.vercel.app/api/
   ```
   Should return: `{"message": "TrueData Analytics API"}`

2. **Check Vercel Function Logs:**
   - Go to Vercel Dashboard → Your Project → Functions
   - Check logs for errors

3. **Verify Build:**
   - Check build logs in Vercel dashboard
   - Ensure Python function builds successfully

### Quick Fixes

**If still getting 404:**

1. **Redeploy:**
   ```bash
   vercel --prod
   ```

2. **Check file structure:**
   ```
   .
   ├── api/
   │   ├── index.py
   │   └── requirements.txt
   ├── backend/
   │   └── server.py
   └── vercel.json
   ```

3. **Verify Git commit:**
   ```bash
   git add api/ backend/ vercel.json
   git commit -m "Fix API routing"
   git push
   ```

4. **Check Vercel deployment:**
   - Go to Vercel Dashboard
   - Check latest deployment logs
   - Look for Python function build errors

### Debug Mode

The current `api/index.py` includes debug output. Check Vercel function logs to see:
- Backend path resolution
- Import success/failure
- Any Python errors

### Alternative: Separate Backend Deployment

If issues persist, consider deploying backend separately:
- Use Railway, Render, or Fly.io for backend
- Update `REACT_APP_BACKEND_URL` to point to backend URL
- Keep frontend on Vercel

