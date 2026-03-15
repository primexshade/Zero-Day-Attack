#!/bin/bash

# X-IDS Vercel Deployment Script
# One-command deployment to Vercel

set -e

echo "🚀 X-IDS Vercel Deployment"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found"
    echo ""
    echo "Install with:"
    echo "  npm i -g vercel"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ vercel.json not found"
    echo "   Make sure you're in the vercel-deploy directory"
    echo ""
    exit 1
fi

echo "✅ Configuration ready"
echo ""

# Check models
if [ ! -d "models" ] || [ ! -f "models/trained_rf_model.pkl" ]; then
    echo "❌ Models not found in ./models/"
    echo "   Copy trained models before deploying"
    echo ""
    exit 1
fi

echo "✅ All models present"
echo ""

# Ask for deployment type
echo "Deployment Options:"
echo "  1) Preview (staging URL, auto-assigned)"
echo "  2) Production (permanent URL)"
echo ""
read -p "Choose [1 or 2]: " choice

case $choice in
    1)
        echo ""
        echo "Deploying to staging..."
        vercel
        ;;
    2)
        echo ""
        echo "Deploying to production..."
        vercel --prod
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Note your deployment URL"
echo "2. Update API_URL in public/index.html"
echo "3. Open URL in browser"
echo "4. Click 'Test Critical' to verify"
echo ""
