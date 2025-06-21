#!/bin/bash

# Scout Analytics - Simple Pipeline Creator
# One command to create everything in Azure DevOps

set -e

echo "🚀 Scout Analytics - Pipeline Creator"
echo "====================================="
echo ""
echo "This will create the complete Azure DevOps pipeline for Scout Analytics"
echo ""

# Quick check for Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check login
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure first:"
    echo "   az login"
    exit 1
fi

echo "✅ Azure CLI ready"
echo ""

# Install Azure DevOps extension
echo "📦 Installing Azure DevOps extension..."
az extension add --name azure-devops --only-show-errors --upgrade 2>/dev/null || true

# Simple configuration
DEVOPS_ORG="https://dev.azure.com/jgtolentino"
DEVOPS_PROJECT="scout-analytics"

echo "📋 Using configuration:"
echo "   Organization: $DEVOPS_ORG"
echo "   Project: $DEVOPS_PROJECT"
echo ""

# Get resource details
echo "🔧 Please enter your Azure resource names:"
read -p "Resource Group: " RESOURCE_GROUP
read -p "App Service name: " APP_SERVICE
read -p "Storage Account: " STORAGE_ACCOUNT

# Optional SQL details
echo ""
echo "📊 SQL Database (optional - leave blank to use SQLite):"
read -p "SQL Server name (optional): " SQL_SERVER
read -p "SQL Database name (optional): " SQL_DATABASE

echo ""
echo "🚀 Creating pipeline..."

# Configure Azure DevOps
az devops configure --defaults organization="$DEVOPS_ORG"

# Create project if it doesn't exist
echo "📁 Setting up project..."
az devops project create --name "$DEVOPS_PROJECT" --description "Scout Analytics" 2>/dev/null || echo "Project exists"
az devops configure --defaults project="$DEVOPS_PROJECT"

# Create service principal
echo "🔐 Creating service connection..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "scout-analytics-sp-$(date +%s)" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    2>/dev/null)

CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.appId')
CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.password')
TENANT_ID=$(echo "$SP_OUTPUT" | jq -r '.tenant')

# Create service endpoint
ENDPOINT_OUTPUT=$(az devops service-endpoint azurerm create \
    --azure-rm-service-principal-id "$CLIENT_ID" \
    --azure-rm-subscription-id "$SUBSCRIPTION_ID" \
    --azure-rm-subscription-name "$(az account show --query name -o tsv)" \
    --azure-rm-tenant-id "$TENANT_ID" \
    --name "scout-analytics-sc" 2>/dev/null)

ENDPOINT_ID=$(echo "$ENDPOINT_OUTPUT" | jq -r '.id')

# Update with secret
az devops service-endpoint azurerm update \
    --id "$ENDPOINT_ID" \
    --azure-rm-service-principal-key "$CLIENT_SECRET" 2>/dev/null

echo "✅ Service connection created"

# Import repository
echo "📦 Importing repository..."
az repos import create \
    --git-source-url "https://github.com/jgtolentino/scout-analytics-package" \
    --repository "scout-analytics-package" 2>/dev/null || echo "Repository exists"

# Create simple pipeline YAML with actual values
echo "📝 Creating pipeline configuration..."
cat > temp-pipeline.yml << EOF
trigger:
- main

pool:
  vmImage: ubuntu-latest

variables:
  appName: $APP_SERVICE
  resourceGroup: $RESOURCE_GROUP
  storageAccount: $STORAGE_ACCOUNT
  azureSubscription: 'scout-analytics-sc'

stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - script: |
        cd deployment
        python -m pip install pandas numpy
        python load_to_sqlite.py
        mkdir -p ../backend/scout-analytics-api-flask/src/database
        cp scout_analytics.db ../backend/scout-analytics-api-flask/src/database/
      displayName: 'Create database'
    
    - script: |
        cd frontend/scout-analytics-dashboard
        npm ci
        echo "VITE_API_BASE_URL=https://\$(appName).azurewebsites.net/api" > .env.production
        npm run build
      displayName: 'Build frontend'
    
    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: 'backend/scout-analytics-api-flask'
        archiveFile: '\$(Build.ArtifactStagingDirectory)/backend.zip'
    
    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: 'frontend/scout-analytics-dashboard/dist'
        archiveFile: '\$(Build.ArtifactStagingDirectory)/frontend.zip'
    
    - publish: '\$(Build.ArtifactStagingDirectory)'
      artifact: drop

- stage: Deploy
  jobs:
  - job: DeployJob
    steps:
    - download: current
      artifact: drop
    
    - task: AzureWebApp@1
      inputs:
        azureSubscription: '\$(azureSubscription)'
        appName: '\$(appName)'
        package: '\$(Pipeline.Workspace)/drop/backend.zip'
    
    - task: AzureCLI@2
      inputs:
        azureSubscription: '\$(azureSubscription)'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          az storage blob service-properties update --account-name \$(storageAccount) --static-website --index-document index.html
          az storage blob upload-batch --account-name \$(storageAccount) --source \$(Pipeline.Workspace)/drop --destination '\$web' --pattern "*.html,*.js,*.css,*.json,*.ico"
EOF

# Create pipeline
echo "🔧 Creating pipeline..."
az pipelines create \
    --name "scout-analytics-deployment" \
    --description "Scout Analytics deployment" \
    --repository-type "tfsgit" \
    --branch "main" \
    --yml-path "temp-pipeline.yml" 2>/dev/null

# Start deployment
echo "🚀 Starting deployment..."
PIPELINE_ID=$(az pipelines list --name "scout-analytics-deployment" --query "[0].id" -o tsv)
BUILD_OUTPUT=$(az pipelines run --id "$PIPELINE_ID" 2>/dev/null)
BUILD_ID=$(echo "$BUILD_OUTPUT" | jq -r '.id')

# Clean up temp file
rm -f temp-pipeline.yml

echo ""
echo "🎉 SUCCESS! Pipeline created and running"
echo "========================================"
echo ""
echo "📊 Deployment started:"
echo "   Build ID: $BUILD_ID"
echo "   Monitor: $DEVOPS_ORG/$DEVOPS_PROJECT/_build/results?buildId=$BUILD_ID"
echo ""
echo "⏱️  Expected completion: 5-8 minutes"
echo ""
echo "🌐 Your URLs (when complete):"
echo "   Backend: https://$APP_SERVICE.azurewebsites.net"
echo "   Frontend: https://$STORAGE_ACCOUNT.z13.web.core.windows.net"
echo ""
echo "✅ Pipeline is running! Check Azure DevOps for progress."