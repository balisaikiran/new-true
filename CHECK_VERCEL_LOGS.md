# 🔍 How to Check Vercel Function Logs for Detailed Errors

The logs you're seeing only show "Python process exited with exit status: 1" but not the actual error. Here's how to see the detailed error messages:

## 📋 Step-by-Step Guide

### Method 1: Function Logs (Recommended)

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click on your project**: `pothos-v2`
3. **Go to "Functions" tab** (not "Deployments")
4. **Click on `api/index.py`** (or the function name)
5. **Click "Logs" tab**
6. **Look for messages starting with**:
   - `INFO: Starting API initialization...`
   - `ERROR: ...`
   - `INFO: Current file: ...`
   - `INFO: Backend dir exists: ...`

### Method 2: Runtime Logs

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click on your project**: `pothos-v2`
3. **Go to "Deployments" tab**
4. **Click on the latest deployment**
5. **Click "Runtime Logs"** (different from "Build Logs")
6. **Look for stderr output** - our error messages print to stderr

### Method 3: Real-time Logs

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click on your project**: `pothos-v2`
3. **Go to "Logs" tab** (in the top navigation)
4. **Make a request** to your API: `https://pothos-v2.vercel.app/api/`
5. **Watch the logs in real-time** - you should see the error messages appear

---

## 🔍 What to Look For

The logs should show messages like:

```
INFO: === Starting API initialization ===
INFO: Current file: /var/task/api/index.py
INFO: API dir: /var/task/api
INFO: Project root: /var/task
INFO: Backend dir: /var/task/backend
INFO: Backend dir exists: True/False
INFO: Attempting to import server module...
ERROR: Direct import failed: No module named 'server'
ERROR: Traceback (most recent call last):
  ...
```

**Share these error messages** - they will tell us exactly what's wrong!

---

## 🚨 Common Issues You Might See

### Issue 1: "Backend dir exists: False"
**Problem**: Backend directory not found in Vercel
**Solution**: Check `.vercelignore` doesn't exclude `backend/`

### Issue 2: "No module named 'server'"
**Problem**: Can't import server.py
**Solution**: Path issue or file not deployed

### Issue 3: "No module named 'X'"
**Problem**: Missing dependency
**Solution**: Add to `api/requirements.txt`

### Issue 4: "ImportError: cannot import name 'app'"
**Problem**: server.py doesn't export `app`
**Solution**: Check server.py has `app = FastAPI()`

---

## 📸 Screenshot Guide

If you can't find the logs, here's where to look:

1. **Functions Tab**:
   ```
   Dashboard → pothos-v2 → Functions → api/index.py → Logs
   ```

2. **Deployments Tab**:
   ```
   Dashboard → pothos-v2 → Deployments → [Latest] → Runtime Logs
   ```

3. **Real-time Logs**:
   ```
   Dashboard → pothos-v2 → Logs (top nav)
   ```

---

## 🧪 Test Simple Handler First

To verify Vercel Python functions work at all, you can temporarily test with a simple handler:

1. **Rename current file**:
   ```bash
   mv api/index.py api/index.py.backup
   ```

2. **Create simple test**:
   ```bash
   cp api/test-simple.py api/index.py
   ```

3. **Commit and push**:
   ```bash
   git add api/index.py
   git commit -m "Test simple handler"
   git push
   ```

4. **Test**: `https://pothos-v2.vercel.app/api/`
   - If this works → The issue is with importing server.py
   - If this fails → The issue is with Vercel Python setup

5. **Restore original**:
   ```bash
   mv api/index.py.backup api/index.py
   git add api/index.py
   git commit -m "Restore original handler"
   git push
   ```

---

## 📝 What to Share

After checking the logs, please share:

1. **Full error messages** (especially lines starting with `ERROR:`)
2. **INFO messages** showing paths
3. **Any traceback** information
4. **Screenshot** of the logs if possible

This will help identify the exact issue!

