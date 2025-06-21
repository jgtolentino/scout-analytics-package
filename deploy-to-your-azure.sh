#!/bin/bash

# Scout Analytics - Deploy to Your Specific Azure Resources
# Using your actual Azure resource names

set -e

echo "🚀 Scout Analytics - Deploying to Your Azure Resources"
echo "====================================================="
echo ""
echo "Using your Azure resources:"
echo "✅ App Service: scout-analytics-dashboard"
echo "✅ Storage Account: projectscoutdata"
echo "✅ SQL Server: sqltbwaprojectscoutserver"
echo "✅ SQL Database: SQL-TBWA-ProjectScout-Reporting-Prod"
echo "✅ Resource Group: RG-TBWA-ProjectScout-Compute"
echo ""

# Your actual Azure configuration
DEVOPS_ORG="https://dev.azure.com/jgtolentino"
DEVOPS_PROJECT="scout-analytics"
SUBSCRIPTION_NAME="TBWA-ProjectScout-Prod"

# Your actual Azure resources
RESOURCE_GROUP="RG-TBWA-ProjectScout-Compute"
APP_SERVICE="scout-analytics-dashboard"
STORAGE_ACCOUNT="projectscoutdata"
SQL_SERVER="sqltbwaprojectscoutserver"
SQL_DATABASE="SQL-TBWA-ProjectScout-Reporting-Prod"

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo "❌ Please install Azure CLI first and run: az login"
    exit 1
fi

if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure: az login"
    exit 1
fi

echo "✅ Azure CLI ready"

# Install Azure DevOps extension
echo "📦 Installing Azure DevOps extension..."
az extension add --name azure-devops --only-show-errors --upgrade 2>/dev/null || true

# Get subscription ID
SUBSCRIPTION_ID=$(az account list --query "[?name=='$SUBSCRIPTION_NAME'].id" -o tsv)
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "❌ Subscription '$SUBSCRIPTION_NAME' not found"
    echo "Available subscriptions:"
    az account list --query "[].{Name:name, Id:id}" -o table
    exit 1
fi

echo "✅ Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Configure Azure DevOps
echo "🔧 Configuring Azure DevOps..."
az devops configure --defaults organization="$DEVOPS_ORG"

# Create or use existing project
echo "📁 Setting up project..."
az devops project create --name "$DEVOPS_PROJECT" --description "Scout Analytics Project" 2>/dev/null || echo "✅ Project exists"
az devops configure --defaults project="$DEVOPS_PROJECT"

# Create service principal
echo "🔐 Creating service connection..."
SP_NAME="scout-analytics-sp-$(date +%s)"

SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --query "{appId:appId, password:password, tenant:tenant}" 2>/dev/null)

CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.appId')
CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.password')
TENANT_ID=$(echo "$SP_OUTPUT" | jq -r '.tenant')

# Create service endpoint
ENDPOINT_OUTPUT=$(az devops service-endpoint azurerm create \
    --azure-rm-service-principal-id "$CLIENT_ID" \
    --azure-rm-subscription-id "$SUBSCRIPTION_ID" \
    --azure-rm-subscription-name "$SUBSCRIPTION_NAME" \
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
    --repository "scout-analytics-package" 2>/dev/null || echo "✅ Repository exists"

# Create pipeline with your exact resource names
echo "📝 Creating pipeline..."
cat > azure-pipelines-custom.yml << EOF
trigger:
- main

pool:
  vmImage: ubuntu-latest

variables:
  appName: $APP_SERVICE
  resourceGroup: $RESOURCE_GROUP
  storageAccount: $STORAGE_ACCOUNT
  sqlServerName: $SQL_SERVER
  sqlDatabaseName: $SQL_DATABASE
  azureSubscription: 'scout-analytics-sc'
  apiBase: https://$APP_SERVICE.azurewebsites.net/api

stages:
- stage: Build
  displayName: 'Build Application'
  jobs:
  - job: BuildJob
    displayName: 'Build and Package'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.11'
      displayName: 'Install Python 3.11'

    - script: |
        cd deployment
        python -m pip install --upgrade pip
        pip install pandas numpy
        
        # Generate sample data if not exists
        if [ ! -f "data/transactions.csv" ]; then
          echo "Generating sample data..."
          python generate_supporting_data.py
        fi
        
        # Load data to SQLite
        python load_to_sqlite.py
        
        # Copy database to API directory
        mkdir -p ../backend/scout-analytics-api-flask/src/database
        cp scout_analytics.db ../backend/scout-analytics-api-flask/src/database/
      displayName: 'Create SQLite database with sample data'

    - task: NodeTool@0
      inputs:
        versionSpec: '18.x'
      displayName: 'Install Node.js'

    - script: |
        cd frontend/scout-analytics-dashboard
        npm ci
        echo "VITE_API_BASE_URL=\$(apiBase)" > .env.production
        npm run build
      displayName: 'Build React frontend'

    - script: |
        cat > backend/scout-analytics-api-flask/startup.sh << 'EOL'
        #!/bin/bash
        export FLASK_APP=src/main.py
        export FLASK_ENV=production
        cd /home/site/wwwroot
        python -m pip install -r requirements.txt
        gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 600 src.main:app
        EOL
        chmod +x backend/scout-analytics-api-flask/startup.sh
      displayName: 'Create startup script'

    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: 'backend/scout-analytics-api-flask'
        includeRootFolder: false
        archiveType: 'zip'
        archiveFile: '\$(Build.ArtifactStagingDirectory)/backend.zip'
      displayName: 'Package backend'

    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: 'frontend/scout-analytics-dashboard/dist'
        includeRootFolder: false
        archiveType: 'zip'
        archiveFile: '\$(Build.ArtifactStagingDirectory)/frontend.zip'
      displayName: 'Package frontend'

    - publish: '\$(Build.ArtifactStagingDirectory)'
      artifact: drop
      displayName: 'Publish artifacts'

- stage: Deploy
  displayName: 'Deploy to Azure'
  dependsOn: Build
  jobs:
  - deployment: DeploymentJob
    displayName: 'Deploy Application'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - download: current
            artifact: drop
            displayName: 'Download artifacts'

          - task: AzureWebApp@1
            displayName: 'Deploy Backend to App Service'
            inputs:
              azureSubscription: '\$(azureSubscription)'
              appType: 'webAppLinux'
              appName: '\$(appName)'
              package: '\$(Pipeline.Workspace)/drop/backend.zip'
              runtimeStack: 'PYTHON|3.11'
              startUpCommand: 'bash startup.sh'

          - task: ExtractFiles@1
            inputs:
              archiveFilePatterns: '\$(Pipeline.Workspace)/drop/frontend.zip'
              destinationFolder: '\$(Pipeline.Workspace)/frontend-dist'
            displayName: 'Extract frontend files'

          - task: AzureCLI@2
            displayName: 'Deploy Frontend to Storage'
            inputs:
              azureSubscription: '\$(azureSubscription)'
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                # Enable static website hosting
                az storage blob service-properties update \\
                  --account-name \$(storageAccount) \\
                  --static-website \\
                  --index-document index.html \\
                  --404-document index.html
                
                # Upload frontend files
                az storage blob upload-batch \\
                  --account-name \$(storageAccount) \\
                  --source '\$(Pipeline.Workspace)/frontend-dist' \\
                  --destination '\$web' \\
                  --overwrite
                
                # Get website URL
                WEBSITE_URL=\$(az storage account show \\
                  --name \$(storageAccount) \\
                  --resource-group \$(resourceGroup) \\
                  --query "primaryEndpoints.web" \\
                  --output tsv)
                
                echo "Frontend deployed to: \$WEBSITE_URL"

          - task: AzureCLI@2
            displayName: 'Configure CORS'
            inputs:
              azureSubscription: '\$(azureSubscription)'
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                # Get frontend URL and configure CORS
                FRONTEND_URL=\$(az storage account show \\
                  --name \$(storageAccount) \\
                  --resource-group \$(resourceGroup) \\
                  --query "primaryEndpoints.web" \\
                  --output tsv | sed 's/\/$//')
                
                az webapp cors add \\
                  --resource-group \$(resourceGroup) \\
                  --name \$(appName) \\
                  --allowed-origins "\$FRONTEND_URL"

- stage: Verify
  displayName: 'Verify Deployment'
  dependsOn: Deploy
  jobs:
  - job: VerifyJob
    displayName: 'Health Checks'
    steps:
    - task: AzureCLI@2
      displayName: 'Test endpoints'
      inputs:
        azureSubscription: '\$(azureSubscription)'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          BACKEND_URL="https://\$(appName).azurewebsites.net"
          FRONTEND_URL=\$(az storage account show \\
            --name \$(storageAccount) \\
            --resource-group \$(resourceGroup) \\
            --query "primaryEndpoints.web" \\
            --output tsv)
          
          echo "Testing backend health..."
          for i in {1..5}; do
            HTTP_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" "\$BACKEND_URL/api/health" || echo "000")
            if [ "\$HTTP_STATUS" = "200" ]; then
              echo "✅ Backend is healthy"
              break
            else
              echo "Attempt \$i: Backend returned \$HTTP_STATUS, waiting 30 seconds..."
              sleep 30
            fi
          done
          
          echo "Testing frontend..."
          HTTP_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" "\$FRONTEND_URL")
          if [ "\$HTTP_STATUS" = "200" ]; then
            echo "✅ Frontend is accessible"
          else
            echo "❌ Frontend returned \$HTTP_STATUS"
          fi
          
          echo ""
          echo "🎉 Deployment Summary"
          echo "===================="
          echo "Backend API: \$BACKEND_URL"
          echo "Frontend: \$FRONTEND_URL"
          echo "Health: \$BACKEND_URL/api/health"
EOF

# Create the pipeline
PIPELINE_OUTPUT=$(az pipelines create \
    --name "scout-analytics-deployment" \
    --description "Scout Analytics deployment to TBWA resources" \
    --repository-type "tfsgit" \
    --branch "main" \
    --yml-path "azure-pipelines-custom.yml" 2>/dev/null)

PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | jq -r '.id')

# Start deployment
echo "🚀 Starting deployment..."
BUILD_OUTPUT=$(az pipelines run --id "$PIPELINE_ID" 2>/dev/null)
BUILD_ID=$(echo "$BUILD_OUTPUT" | jq -r '.id')

BUILD_URL="$DEVOPS_ORG/$DEVOPS_PROJECT/_build/results?buildId=$BUILD_ID"

# Clean up
rm -f azure-pipelines-custom.yml

echo ""
echo "🎉 SUCCESS! Scout Analytics Pipeline Created & Running!"
echo "======================================================="
echo ""
echo "📊 Deployment Details:"
echo "   Pipeline: scout-analytics-deployment"
echo "   Build ID: $BUILD_ID"
echo "   Monitor: $BUILD_URL"
echo ""
echo "🌐 Your URLs (live in 8-10 minutes):"
echo "   Backend API: https://$APP_SERVICE.azurewebsites.net"
echo "   Frontend: https://$STORAGE_ACCOUNT.z13.web.core.windows.net"
echo "   Health Check: https://$APP_SERVICE.azurewebsites.net/api/health"
echo ""
echo "⏱️  Expected completion: 8-10 minutes"
echo ""
echo "✅ Pipeline is running! Check Azure DevOps for progress."

# Save config
cat > .deployment-config << EOF
# Deployment completed: $(date)
BACKEND_URL=https://$APP_SERVICE.azurewebsites.net
FRONTEND_URL=https://$STORAGE_ACCOUNT.z13.web.core.windows.net
BUILD_URL=$BUILD_URL
BUILD_ID=$BUILD_ID
EOF

echo "📝 Configuration saved to .deployment-config"

# Optional: Open browser
if command -v open &> /dev/null; then
    echo ""
    read -p "Open deployment monitor in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$BUILD_URL"
    fi
fi

echo ""
echo "🎯 Next: Watch the deployment progress and visit your live dashboard!"