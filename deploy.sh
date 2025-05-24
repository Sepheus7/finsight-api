#!/bin/bash

# 🚀 Quick Deploy Script for FinSight API

echo "🏦 FinSight API - Quick Deploy Script"
echo "====================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Financial AI Quality Enhancement API MVP"
fi

echo ""
echo "🌐 Choose your deployment platform:"
echo "1) Railway (Easiest - 2 minutes)"
echo "2) Render (Free tier available)"
echo "3) Google Cloud Run"
echo "4) Just setup GitHub (manual deploy later)"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚄 Deploying to Railway..."
        echo "1. Visit: https://railway.app"
        echo "2. Sign up with GitHub"
        echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
        echo "4. Select this repository"
        echo "5. Railway will auto-detect and deploy!"
        echo ""
        echo "Your API will be live at: https://[random-name].railway.app"
        ;;
    2)
        echo "🎨 Setting up for Render..."
        echo "1. Visit: https://render.com"
        echo "2. Sign up with GitHub"
        echo "3. Click 'New +' → 'Web Service'"
        echo "4. Connect this repository"
        echo "5. Build Command: pip install -r requirements.txt"
        echo "6. Start Command: uvicorn finai_quality_api:app --host 0.0.0.0 --port \$PORT"
        echo ""
        echo "Free tier includes: 750 hours/month + HTTPS"
        ;;
    3)
        echo "☁️ Google Cloud Run deployment..."
        if ! command -v gcloud &> /dev/null; then
            echo "Installing Google Cloud CLI..."
            echo "Run: brew install google-cloud-sdk"
            echo "Then: gcloud auth login"
            echo "Then: gcloud config set project YOUR_PROJECT_ID"
        fi
        echo ""
        echo "Deploy command:"
        echo "gcloud run deploy finai-quality-api --source . --platform managed --region us-central1 --allow-unauthenticated"
        ;;
    4)
        echo "📚 GitHub setup for manual deployment..."
        echo "Repository will be ready for any platform!"
        ;;
esac

echo ""
echo "📋 Next steps after deployment:"
echo "• Test your API at: [YOUR_URL]/docs"
echo "• Update README.md with your live URL"
echo "• Share with potential customers"
echo "• Monitor usage and performance"

echo ""
echo "🎯 Business next steps:"
echo "• Create demo videos/screenshots"
echo "• Reach out to financial institutions"
echo "• Set up analytics and monitoring"
echo "• Plan pricing and billing integration"

echo ""
echo "✅ Your FinSight API is ready to go live!"
echo "💰 Market opportunity: $5.6B+ in financial AI spending"
