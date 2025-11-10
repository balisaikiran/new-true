# Vercel Deployment Guide

## Prerequisites
1. Vercel account (sign up at https://vercel.com)
2. MongoDB Atlas account (for cloud MongoDB) or your MongoDB connection string
3. Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### 1. Prepare Your Repository
Make sure your code is pushed to a Git repository (GitHub, GitLab, or Bitbucket).

### 2. Set Up Environment Variables in Vercel

Go to your Vercel project settings and add these environment variables:

- `MONGO_URL` - Your MongoDB connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`)
- `DB_NAME` - Your database name (e.g., `truedata`)
- `CORS_ORIGINS` - Comma-separated list of allowed origins (e.g., `https://your-app.vercel.app,http://localhost:3000`)

### 3. Deploy via Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your Git repository
3. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty (or set to root)
   - **Build Command**: `cd frontend && npm install --legacy-peer-deps && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `cd frontend && npm install --legacy-peer-deps`
4. Add environment variables (from step 2)
5. Click "Deploy"

### 4. Deploy via Vercel CLI (Alternative)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# For production deployment
vercel --prod
```

### 5. Update Frontend Environment Variables

After deployment, update your frontend `.env` file or Vercel environment variables:

- `REACT_APP_BACKEND_URL` - Your Vercel deployment URL (e.g., `https://your-app.vercel.app`)

## Project Structure

```
.
├── api/
│   ├── index.py          # Vercel serverless function entry point
│   └── requirements.txt  # Python dependencies for API
├── backend/
│   ├── server.py         # FastAPI application
│   └── requirements.txt  # Backend dependencies
├── frontend/
│   ├── src/              # React source code
│   ├── public/           # Static files
│   └── package.json      # Frontend dependencies
└── vercel.json           # Vercel configuration
```

## Important Notes

1. **MongoDB**: Make sure your MongoDB connection string is accessible from Vercel's servers. Use MongoDB Atlas for cloud hosting.

2. **CORS**: Update `CORS_ORIGINS` environment variable to include your Vercel deployment URL.

3. **API Routes**: All API routes are accessible at `/api/*` and will be handled by the Python serverless function.

4. **Frontend Routes**: All other routes will serve the React app (SPA routing).

## Troubleshooting

- If build fails, check the build logs in Vercel dashboard
- Ensure all environment variables are set correctly
- Check MongoDB connection string format
- Verify Python runtime version (3.9) in vercel.json

## Post-Deployment

After successful deployment:
1. Test the API endpoints at `https://your-app.vercel.app/api/`
2. Test the frontend at `https://your-app.vercel.app/`
3. Update `REACT_APP_BACKEND_URL` in Vercel environment variables to match your deployment URL

