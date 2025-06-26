#!/bin/bash

echo "🚀 TrafficDetector - Railway Deployment Helper"
echo "=============================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if remote is set
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "🔗 Please set up your GitHub repository:"
    echo "1. Create a new repository on GitHub"
    echo "2. Run: git remote add origin https://github.com/YOUR_USERNAME/trafficDetector.git"
    echo "3. Run: git push -u origin main"
    echo ""
else
    echo "✅ GitHub remote is configured"
    echo "📤 Pushing to GitHub..."
    git add .
    git commit -m "Update for Railway deployment"
    git push
    echo "✅ Code pushed to GitHub"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://railway.app/"
echo "2. Sign up with GitHub"
echo "3. Click 'New Project'"
echo "4. Select 'Deploy from GitHub repo'"
echo "5. Choose your trafficDetector repository"
echo "6. Click 'Deploy'"
echo ""
echo "🔧 After deployment, add these environment variables in Railway:"
echo "   TOMTOM_API_KEY=your_tomtom_api_key_here"
echo "   HERE_API_KEY=your_here_api_key_here"
echo "   COLLECTION_INTERVAL_HOURS=1"
echo "   BATCH_SIZE=5"
echo "   CONTINUOUS_COLLECTION=true"
echo ""
echo "📖 See CLOUD_DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo "🎉 Your TrafficDetector will be running 24/7 in the cloud!" 