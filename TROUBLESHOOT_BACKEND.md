# 🔧 Backend Deployment Troubleshooting

Your backend is deployed but showing errors. Let's fix it!

## 🚨 Current Error

The API is returning: `FUNCTION_INVOCATION_FAILED`

This usually means:
- Import errors in the Python code
- Missing dependencies
- Path issues
- Environment variable problems

---

## 🔍 Step 1: Check Vercel Function Logs

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Click on your **`pothos-v2`** project
3. Go to **"Deployments"** tab
4. Click on the **latest deployment**
5. Click on **"Function Logs"** or **"Runtime Logs"**
6. Look for Python errors (ImportError, ModuleNotFoundError, etc.)

**Common errors you might see:**
- `ModuleNotFoundError: No module named 'server'`
- `ImportError: cannot import name 'app'`
- `FileNotFoundError: [Errno 2] No such file or directory`

---

## 🔧 Step 2: Fix Common Issues

### Issue 1: Import Path Problems

The `api/index.py` tries to import from `backend/server.py`. Make sure:

1. **Check file structure** in Vercel:
   - `api/index.py` exists
   - `backend/server.py` exists
   - Both are in the repository

2. **Verify `api/index.py` path resolution**:
   ```python
   # Should find backend/server.py relative to project root
   backend_dir = project_root / "backend"
   ```

### Issue 2: Missing Dependencies

Check `api/requirements.txt` includes:
- `mangum>=0.17.0` ✅ (already there)
- `fastapi` ✅ (already there)
- All other dependencies from `backend/requirements.txt`

**Solution**: Make sure `api/requirements.txt` has all needed packages.

### Issue 3: Python Version

Vercel uses Python 3.9 by default. Check if your code needs a specific version.

**Solution**: Add `runtime.txt` in `api/` folder:
```
python-3.9
```

---

## 🛠️ Step 3: Quick Fixes to Try

### Fix 1: Update `api/index.py` Import Path

The current import might fail. Try this alternative:

```python
# In api/index.py, replace the import section with:
import sys
import os
from pathlib import Path

# Get absolute paths
current_file = Path(__file__).resolve()
api_dir = current_file.parent
project_root = api_dir.parent
backend_dir = project_root / "backend"

# Add backend to path
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

# Try importing
try:
    from backend.server import app
except ImportError:
    try:
        from server import app
    except ImportError:
        # Fallback: create minimal app
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/")
        async def root():
            return {"error": "Import failed", "backend_path": str(backend_dir)}
```

### Fix 2: Check `api/requirements.txt`

Make sure it has ALL dependencies. Compare with `backend/requirements.txt`:

```txt
# api/requirements.txt should include:
fastapi==0.110.1
mangum>=0.17.0
motor==3.3.1
pydantic==2.12.4
python-dotenv==1.2.1
httpx==0.28.1
starlette==0.37.2
# ... all other dependencies
```

### Fix 3: Add Error Handling

Update `api/index.py` to log errors:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from backend.server import app
    logger.info("Successfully imported app from backend.server")
except Exception as e:
    logger.error(f"Import error: {e}", exc_info=True)
    # Fallback app
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/")
    async def root():
        return {"error": str(e), "type": type(e).__name__}
```

---

## 📋 Step 4: Verify Deployment Structure

In Vercel, your project structure should be:

```
/
├── api/
│   ├── index.py          ← Serverless function entry point
│   └── requirements.txt   ← Python dependencies
├── backend/
│   ├── server.py         ← FastAPI app
│   └── requirements.txt
└── vercel.json           ← Backend-only config
```

---

## 🧪 Step 5: Test After Fixes

1. **Make changes** to `api/index.py` or `api/requirements.txt`
2. **Commit and push**:
   ```bash
   git add .
   git commit -m "Fix backend deployment"
   git push origin main
   ```
3. **Wait for auto-deployment** (or manually redeploy)
4. **Test again**:
   ```bash
   curl https://pothos-v2.vercel.app/api/
   ```

---

## 🔍 Step 6: Check Specific Error Details

Run this to see the full error:

```bash
curl -v https://pothos-v2.vercel.app/api/
```

Or check in browser:
1. Open: `https://pothos-v2.vercel.app/api/`
2. Open Developer Tools (F12)
3. Check Network tab
4. Click on the request
5. Check Response tab for full error message

---

## 📞 Need More Help?

1. **Check Vercel Function Logs** (most important!)
2. **Share the error message** from logs
3. **Verify file structure** matches expected layout
4. **Check environment variables** are set correctly

---

## ✅ Success Checklist

- [ ] Function logs checked
- [ ] Import paths verified
- [ ] Dependencies in `api/requirements.txt` complete
- [ ] Code pushed and redeployed
- [ ] Test endpoint works: `https://pothos-v2.vercel.app/api/`

---

Let's get your backend working! 🚀

