# Test TrueData Login Endpoint

This endpoint helps debug TrueData authentication issues.

## Usage

Test the login directly via API:

```bash
curl -X POST https://your-app.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tdwsp784", "password": "sid@784"}'
```

## Check Vercel Function Logs

1. Go to Vercel Dashboard → Your Project → Functions
2. Click on `api/index.py`
3. Go to "Logs" tab
4. Try to log in
5. Check the logs for:
   - "Attempting TrueData authentication for user: tdwsp784"
   - "TrueData auth response status: XXX"
   - Any error messages

## Common Issues

### Issue 1: TrueData API Returns 401
**Meaning:** Credentials are wrong or account is disabled

**Check:**
- Verify credentials on TrueData website
- Check if account is active
- Try logging into TrueData website directly

### Issue 2: TrueData API Returns 400
**Meaning:** Request format is wrong

**Check logs for:**
- Form data being sent
- Headers being used
- API endpoint URL

### Issue 3: Connection Timeout
**Meaning:** Cannot reach TrueData API

**Check:**
- Vercel function can access external APIs
- TrueData API is not blocking Vercel IPs
- Network connectivity

### Issue 4: CORS Error
**Meaning:** Frontend cannot call backend

**Fix:** Set `CORS_ORIGINS` environment variable:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

## Debug Steps

1. **Check Vercel Function Logs:**
   - Look for detailed error messages
   - Check what TrueData API returns

2. **Test API Directly:**
   ```bash
   curl -X POST https://your-app.vercel.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "tdwsp784", "password": "sid@784"}'
   ```

3. **Check Browser Console:**
   - Open DevTools (F12)
   - Go to Console tab
   - Try to log in
   - Check for error messages

4. **Check Network Tab:**
   - Open DevTools → Network tab
   - Try to log in
   - Click on `/api/auth/login` request
   - Check Request and Response tabs

## Expected Response

**Success:**
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "...",
  "expires_in": 3600,
  "username": "tdwsp784"
}
```

**Failure:**
```json
{
  "detail": "error message from TrueData API"
}
```

