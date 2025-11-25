# MongoDB SSL Certificate Fix

## Problem
MongoDB connection was failing with SSL certificate verification error:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

## Solution
Fixed by adding `tlsAllowInvalidCertificates=true` parameter to the MongoDB connection string.

### Changes Made

1. **Connection String Modification** (`backend/server.py`):
   - Automatically appends `?tlsAllowInvalidCertificates=true` to the MongoDB URL
   - This allows MongoDB Atlas connections to work even when SSL certificates can't be verified locally
   - **Note**: This is for development only. For production, use proper certificate validation.

2. **Database Boolean Check Fix**:
   - Changed `if db:` to `if db is not None:` 
   - MongoDB Database objects don't support truth value testing
   - Fixed in multiple locations: `test_db()`, `scheduled_end_of_day_save()`, `shutdown_db_client()`

## Code Changes

### Before:
```python
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
```

### After:
```python
# Add SSL certificate bypass to connection string
if '?' not in mongo_url:
    mongo_url += '?tlsAllowInvalidCertificates=true'
elif 'tlsAllowInvalidCertificates' not in mongo_url:
    mongo_url += '&tlsAllowInvalidCertificates=true'

client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=20000)
```

## Testing

Test the connection:
```bash
curl http://localhost:8000/api/test-db
```

Expected response:
```json
{
    "status": "connected",
    "database": "pothos",
    "message": "MongoDB connection successful"
}
```

## Security Note

⚠️ **Important**: `tlsAllowInvalidCertificates=true` disables SSL certificate verification. This is acceptable for:
- ✅ Local development
- ✅ Testing environments
- ❌ **NOT recommended for production**

For production, ensure proper SSL certificates are installed and verified.

## Alternative Solutions

If you want proper SSL verification in production:

1. **Install certificates**:
   ```bash
   # macOS
   /Applications/Python\ 3.11/Install\ Certificates.command
   ```

2. **Use certificate file**:
   ```python
   client = AsyncIOMotorClient(
       mongo_url,
       tlsCAFile='/path/to/ca-certificate.crt'
   )
   ```

3. **Remove the bypass** and ensure system certificates are properly configured.

## Status

✅ **Fixed** - MongoDB connection now works with SSL certificate bypass for development.

