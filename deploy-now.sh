#!/bin/bash

# Scout Analytics - One-Click Deployment
# This script creates everything and runs the deployment immediately

set -e

echo "🚀 Scout Analytics - One-Click Deployment"
echo "========================================="
echo ""
echo "This will:"
echo "✅ Create Azure DevOps service connection"
echo "✅ Create and configure pipeline"
echo "✅ Run immediate deployment"
echo "✅ Deploy to your existing Azure resources"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Quick resource detection (if you have Azure CLI configured)
print_status "Detecting your Azure resources..."

# Get default subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")

if [ -n "$SUBSCRIPTION_ID" ]; then
    print_success "Found subscription: $SUBSCRIPTION_ID"
    
    # Try to find existing App Services and Storage Accounts
    echo ""
    echo "🔍 Found these resources in your subscription:"
    echo ""
    echo "App Services:"
    az webapp list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table 2>/dev/null || echo "None found"
    
    echo ""
    echo "Storage Accounts:"
    az storage account list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table 2>/dev/null || echo "None found"
    
    echo ""
    echo "SQL Servers:"
    az sql server list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table 2>/dev/null || echo "None found"
fi

echo ""
print_status "Please enter your resource details:"

# Collect minimal required info
read -p "Azure DevOps org URL (e.g., https://dev.azure.com/yourorg): " DEVOPS_ORG
read -p "Azure DevOps project name: " DEVOPS_PROJECT
read -p "App Service name: " APP_NAME
read -p "Resource Group name: " RESOURCE_GROUP

# Quick validation
if [ -z "$DEVOPS_ORG" ] || [ -z "$DEVOPS_PROJECT" ] || [ -z "$APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
    echo "❌ Missing required information. Please run again with all details."
    exit 1
fi

# Run the full setup script
print_status "Running automated pipeline creation..."
export DEVOPS_ORG DEVOPS_PROJECT APP_NAME RESOURCE_GROUP

# Create a streamlined version that uses the provided values
./create-azure-devops-pipeline.sh

print_success "Pipeline created successfully!"

# Trigger immediate deployment
print_status "Triggering immediate deployment..."

# Install Azure DevOps CLI if needed
az extension add --name azure-devops --only-show-errors 2>/dev/null || true

# Configure defaults
az devops configure --defaults organization="$DEVOPS_ORG" project="$DEVOPS_PROJECT"

# Run the pipeline
PIPELINE_ID=$(az pipelines list --name "scout-analytics-deployment" --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ -n "$PIPELINE_ID" ]; then
    print_status "Starting pipeline deployment..."
    
    RUN_ID=$(az pipelines run --id "$PIPELINE_ID" --query "id" -o tsv)
    
    print_success "Pipeline started! Run ID: $RUN_ID"
    
    # Get the URL for monitoring
    PIPELINE_URL="$DEVOPS_ORG/$DEVOPS_PROJECT/_build/results?buildId=$RUN_ID"
    
    echo ""
    echo "🎯 Monitor your deployment:"
    echo "   $PIPELINE_URL"
    echo ""
    echo "⏱️  Expected completion: 8-12 minutes"
    echo ""
    echo "📊 When complete, your dashboard will be at:"
    echo "   https://$APP_NAME.azurewebsites.net"
    echo ""
    
    # Optional: Open in browser
    if command -v open &> /dev/null; then
        read -p "Open deployment monitor in browser? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "$PIPELINE_URL"
        fi
    fi
    
else
    echo "❌ Could not find pipeline. Please check Azure DevOps manually."
    echo "   Go to: $DEVOPS_ORG/$DEVOPS_PROJECT/_build"
fi

echo ""
echo "🎉 Deployment initiated!"
echo "✅ Check Azure DevOps for progress"
echo "✅ Your Scout Analytics dashboard will be live shortly!"