#!/bin/bash

# Vercel Deployment Script
# This script helps deploy your backend API to Vercel

echo "🚀 Starting Vercel Deployment Process..."
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed."
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
    echo "✅ Vercel CLI installed!"
else
    echo "✅ Vercel CLI is already installed"
fi

echo ""
echo "📋 Current Configuration:"
echo "   - API Handler: api/index.py"
echo "   - Backend: backend/server.py"
echo "   - Config: vercel.json"
echo ""

# Check if user is logged in
echo "🔐 Checking Vercel authentication..."
if vercel whoami &> /dev/null; then
    echo "✅ Already logged in to Vercel"
    vercel whoami
else
    echo "⚠️  Not logged in. Please login:"
    vercel login
fi

echo ""
echo "📦 Deploying to Vercel..."
echo "   This will create a preview deployment"
echo ""

# Deploy to preview
vercel

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📝 Next Steps:"
echo "   1. Check the deployment URL provided above"
echo "   2. Test your API endpoints (see test-api.sh)"
echo "   3. For production deployment, run: vercel --prod"
echo ""
echo "🔗 To test your API:"
echo "   - Root endpoint: https://your-app.vercel.app/api/"
echo "   - Health check: https://your-app.vercel.app/api/test-db"
echo "   - Login: POST https://your-app.vercel.app/api/auth/login"
echo ""

