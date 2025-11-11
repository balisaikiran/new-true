# MongoDB Setup Guide

## Your MongoDB Configuration

Based on what you shared:
- **Cluster**: `cluster0.kykrymz.mongodb.net`
- **Database Name**: `pothos`
- **Collection Name**: `pothos` (but code uses `tokens` - that's fine, MongoDB will create it)

## Vercel Environment Variables

Make sure these are set in Vercel:

```
MONGO_URL=mongodb+srv://saiashok49_db_user:udHwPFcdabvxG3JS@cluster0.kykrymz.mongodb.net/
DB_NAME=pothos
```

**Note**: The collection name doesn't need to match - MongoDB will automatically create the `tokens` collection when needed.

## Important Notes

1. **MongoDB is Optional**: The app works WITHOUT MongoDB. Tokens will be stored in browser localStorage instead.

2. **Collection Name**: The code uses `tokens` collection, but your MongoDB shows `pothos`. This is fine - MongoDB will create the `tokens` collection automatically when the first token is saved.

3. **If MongoDB Fails**: The login will still work! The app is designed to continue even if MongoDB connection fails.

## Check Vercel Logs

After redeploying, check the Vercel Function Logs to see:
- If MongoDB connects successfully
- If TrueData authentication works
- Any error messages

The logs will show:
```
Connecting to MongoDB database: pothos
MongoDB initialized successfully
```

OR if MongoDB fails (non-critical):
```
MongoDB connection failed (app will work without it): ...
```

## Still Seeing "Invalid Creds"?

If you're still seeing "invalid creds" after fixing the 500 error:

1. **Check Vercel Function Logs** - Look for TrueData API responses
2. **Verify Credentials** - Make sure username/password are correct
3. **Check Network Tab** - See what error the API actually returns

The improved error logging will show exactly what TrueData API is returning!
