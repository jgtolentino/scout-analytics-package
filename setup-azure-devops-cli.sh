#!/bin/bash

# Scout Analytics - Azure DevOps Setup via CLI
# Run this script to create everything in your Azure DevOps organization

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Scout Analytics - Azure DevOps CLI Setup"
echo "============================================"
echo "This will create the pipeline in your Azure DevOps organization"
echo ""

# Configuration - UPDATE THESE VALUES
DEVOPS_ORG="https://dev.azure.com/jgtolentino"
DEVOPS_PROJECT="scout-analytics"
GITHUB_REPO="https://github.com/jgtolentino/scout-analytics-package"

echo "📋 Configuration:"
echo "   Organization: $DEVOPS_ORG"
echo "   Project: $DEVOPS_PROJECT"
echo "   Repository: $GITHUB_REPO"
echo ""

read -p "Continue with this configuration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please update the configuration in this script and run again."
    exit 0
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show > /dev/null 2>&1; then
    print_error "Not logged in to Azure. Please run: az login"
    exit 1
fi

print_success "Azure CLI ready"

# Install Azure DevOps extension
print_status "Installing Azure DevOps CLI extension..."
az extension add --name azure-devops --only-show-errors --upgrade

# Get Azure subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

print_success "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Collect Azure resource information
echo ""
print_status "Please provide your Azure resource details:"
read -p "Resource Group name: " RESOURCE_GROUP
read -p "App Service name: " APP_SERVICE
read -p "Storage Account name: " STORAGE_ACCOUNT
read -p "SQL Server name: " SQL_SERVER
read -p "SQL Database name: " SQL_DATABASE
read -p "SQL Username: " SQL_USERNAME
read -s -p "SQL Password: " SQL_PASSWORD
echo ""

# Validate inputs
if [ -z "$RESOURCE_GROUP" ] || [ -z "$APP_SERVICE" ] || [ -z "$STORAGE_ACCOUNT" ]; then
    print_error "Missing required resource information. Please run again."
    exit 1
fi

# Verify resources exist
print_status "Verifying Azure resources..."

if ! az group show --name "$RESOURCE_GROUP" > /dev/null 2>&1; then
    print_error "Resource group '$RESOURCE_GROUP' not found"
    exit 1
fi

if ! az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1; then
    print_error "App Service '$APP_SERVICE' not found in resource group '$RESOURCE_GROUP'"
    exit 1
fi

print_success "Azure resources verified"

# Configure Azure DevOps CLI
print_status "Configuring Azure DevOps CLI..."
az devops configure --defaults organization="$DEVOPS_ORG"

# Check if project exists, create if not
print_status "Checking Azure DevOps project..."
if ! az devops project show --project "$DEVOPS_PROJECT" > /dev/null 2>&1; then
    print_status "Creating project '$DEVOPS_PROJECT'..."
    az devops project create --name "$DEVOPS_PROJECT" --description "Scout Analytics deployment project"
    print_success "Project created"
else
    print_success "Project '$DEVOPS_PROJECT' exists"
fi

# Set project as default
az devops configure --defaults project="$DEVOPS_PROJECT"

# Create service principal for service connection
print_status "Creating service principal..."
SP_NAME="scout-analytics-sp-$(date +%s)"

# Create service principal with contributor role
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP")

CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.appId')
CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.password')
TENANT_ID=$(echo "$SP_OUTPUT" | jq -r '.tenant')

print_success "Service principal created: $SP_NAME"

# Create service endpoint (service connection)
print_status "Creating Azure service connection..."

# Create service endpoint
ENDPOINT_OUTPUT=$(az devops service-endpoint azurerm create \
    --azure-rm-service-principal-id "$CLIENT_ID" \
    --azure-rm-subscription-id "$SUBSCRIPTION_ID" \
    --azure-rm-subscription-name "$SUBSCRIPTION_NAME" \
    --azure-rm-tenant-id "$TENANT_ID" \
    --name "scout-analytics-sc")

ENDPOINT_ID=$(echo "$ENDPOINT_OUTPUT" | jq -r '.id')

# Update the service endpoint with the secret
az devops service-endpoint azurerm update \
    --id "$ENDPOINT_ID" \
    --azure-rm-service-principal-key "$CLIENT_SECRET"

print_success "Service connection created: scout-analytics-sc"

# Create variable group
print_status "Creating variable group..."
VARIABLE_GROUP_OUTPUT=$(az pipelines variable-group create \
    --name "scout-analytics-vars" \
    --variables \
        appName="$APP_SERVICE" \
        resourceGroup="$RESOURCE_GROUP" \
        storageAccount="$STORAGE_ACCOUNT" \
        sqlServerName="$SQL_SERVER" \
        sqlDatabaseName="$SQL_DATABASE" \
        sqlUsername="$SQL_USERNAME" \
    --authorize true)

VARIABLE_GROUP_ID=$(echo "$VARIABLE_GROUP_OUTPUT" | jq -r '.id')

# Add secret variable for SQL password
az pipelines variable-group variable create \
    --group-id "$VARIABLE_GROUP_ID" \
    --name "sqlPassword" \
    --value "$SQL_PASSWORD" \
    --secret true

print_success "Variable group created with ID: $VARIABLE_GROUP_ID"

# Import repository from GitHub
print_status "Importing repository from GitHub..."
REPO_OUTPUT=$(az repos import create \
    --git-source-url "$GITHUB_REPO" \
    --repository "scout-analytics-package")

REPO_ID=$(echo "$REPO_OUTPUT" | jq -r '.repository.id')
print_success "Repository imported with ID: $REPO_ID"

# Create the pipeline
print_status "Creating Azure DevOps pipeline..."
PIPELINE_OUTPUT=$(az pipelines create \
    --name "scout-analytics-deployment" \
    --description "Scout Analytics automated deployment pipeline" \
    --repository "$REPO_ID" \
    --repository-type "tfsgit" \
    --branch "main" \
    --yml-path "azure-pipelines.yml")

PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | jq -r '.id')
print_success "Pipeline created with ID: $PIPELINE_ID"

# Update pipeline to use variable group
print_status "Linking variable group to pipeline..."
az pipelines variable-group list --group-name "scout-analytics-vars" --query "[0].id" -o tsv

# Queue a build
print_status "Starting initial deployment..."
BUILD_OUTPUT=$(az pipelines run --id "$PIPELINE_ID")
BUILD_ID=$(echo "$BUILD_OUTPUT" | jq -r '.id')

BUILD_URL="$DEVOPS_ORG/$DEVOPS_PROJECT/_build/results?buildId=$BUILD_ID"

print_success "Pipeline run started! Build ID: $BUILD_ID"

# Save configuration
cat > .azure-devops-config << EOF
# Azure DevOps Configuration Created: $(date)
DEVOPS_ORG="$DEVOPS_ORG"
DEVOPS_PROJECT="$DEVOPS_PROJECT"
PIPELINE_ID="$PIPELINE_ID"
BUILD_ID="$BUILD_ID"
RESOURCE_GROUP="$RESOURCE_GROUP"
APP_SERVICE="$APP_SERVICE"
STORAGE_ACCOUNT="$STORAGE_ACCOUNT"
SERVICE_CONNECTION_ID="$ENDPOINT_ID"
VARIABLE_GROUP_ID="$VARIABLE_GROUP_ID"
EOF

echo ""
echo "=========================================="
echo "🎉 Azure DevOps Pipeline Created Successfully!"
echo "=========================================="
echo ""
echo "📊 Deployment Details:"
echo "   Pipeline: scout-analytics-deployment"
echo "   Build ID: $BUILD_ID"
echo "   Monitor: $BUILD_URL"
echo ""
echo "🔗 Resources:"
echo "   Backend API: https://$APP_SERVICE.azurewebsites.net"
echo "   Frontend: https://$STORAGE_ACCOUNT.z13.web.core.windows.net"
echo ""
echo "⏱️  Expected completion: 8-12 minutes"
echo ""
echo "🎯 Next Steps:"
echo "   1. Monitor deployment: $BUILD_URL"
echo "   2. Check logs for any issues"
echo "   3. Visit your dashboard when complete"
echo ""

# Optional: Open browser
if command -v open &> /dev/null; then
    read -p "Open deployment monitor in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$BUILD_URL"
    fi
fi

print_success "Configuration saved to .azure-devops-config"
print_success "Pipeline is running! Check Azure DevOps for progress."

echo ""
echo "✅ Your Scout Analytics platform is deploying!"
echo "📱 You'll have a live dashboard with 30k transactions shortly."