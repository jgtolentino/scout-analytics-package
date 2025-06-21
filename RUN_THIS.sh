#!/bin/bash

# Scout Analytics - Run This Script to Deploy Everything
# This is the simplest way to get Scout Analytics running

echo "🚀 Scout Analytics - Instant Deployment"
echo "======================================="
echo ""
echo "This will:"
echo "✅ Create Azure DevOps pipeline in your organization"
echo "✅ Deploy backend API to your App Service"
echo "✅ Deploy frontend to your Storage Account"
echo "✅ Load 30,000 sample transactions"
echo "✅ Create live analytics dashboard"
echo ""

# Quick prereq check
if ! command -v az &> /dev/null; then
    echo "❌ Please install Azure CLI first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    echo ""
    echo "Then run: az login"
    exit 1
fi

if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure first:"
    echo "   az login"
    exit 1
fi

echo "✅ Azure CLI ready"
echo ""

read -p "Ready to create your Scout Analytics pipeline? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "No problem! Run this script when you're ready."
    exit 0
fi

echo ""
echo "🔧 Running pipeline creation..."
echo ""

# Run the simple pipeline creator
./create-pipeline.sh

echo ""
echo "🎉 DONE! Your Scout Analytics platform is deploying!"
echo ""
echo "📱 In 5-8 minutes you'll have:"
echo "   ✅ Live retail analytics dashboard"
echo "   ✅ 30,000+ transaction records"
echo "   ✅ Real-time charts and insights"
echo "   ✅ Philippine market data visualization"
echo ""
echo "🌐 Check Azure DevOps for deployment progress"
echo "📊 Your dashboard will be live shortly!"