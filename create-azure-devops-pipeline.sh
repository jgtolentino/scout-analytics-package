#!/bin/bash

# Scout Analytics - Azure DevOps Pipeline Creator
# This script creates the Azure DevOps pipeline automatically

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

echo "🚀 Scout Analytics - Azure DevOps Pipeline Creator"
echo "=================================================="

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in
if ! az account show > /dev/null 2>&1; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_success "Prerequisites met"

# Collect Azure DevOps information
echo ""
print_status "Azure DevOps Configuration"
read -p "Enter your Azure DevOps organization URL (e.g., https://dev.azure.com/yourorg): " DEVOPS_ORG
read -p "Enter your Azure DevOps project name: " DEVOPS_PROJECT

# Collect Azure resource information
echo ""
print_status "Azure Resource Configuration"
read -p "Enter your Azure subscription ID: " SUBSCRIPTION_ID
read -p "Enter your resource group name: " RESOURCE_GROUP
read -p "Enter your App Service name: " APP_SERVICE_NAME
read -p "Enter your Storage Account name: " STORAGE_ACCOUNT
read -p "Enter your SQL Server name: " SQL_SERVER
read -p "Enter your SQL Database name: " SQL_DATABASE
read -p "Enter your SQL username: " SQL_USERNAME
read -s -p "Enter your SQL password: " SQL_PASSWORD
echo ""

# Create service principal for Azure DevOps
print_status "Creating service principal for Azure DevOps..."

SP_NAME="scout-analytics-sp-$(date +%s)"
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --sdk-auth)

# Extract values from service principal output
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.clientSecret')
TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenantId')

print_success "Service principal created: $SP_NAME"

# Install Azure DevOps CLI extension
print_status "Installing Azure DevOps CLI extension..."
az extension add --name azure-devops --only-show-errors

# Login to Azure DevOps
print_status "Configuring Azure DevOps..."
az devops configure --defaults organization="$DEVOPS_ORG" project="$DEVOPS_PROJECT"

# Create service connection
print_status "Creating Azure service connection..."
SERVICE_CONNECTION_NAME="scout-analytics-sc"

# Create the service connection JSON
cat > service-connection.json << EOF
{
  "data": {
    "subscriptionId": "$SUBSCRIPTION_ID",
    "subscriptionName": "$(az account show --query name -o tsv)",
    "environment": "AzureCloud",
    "scopeLevel": "Subscription",
    "creationMode": "Manual"
  },
  "name": "$SERVICE_CONNECTION_NAME",
  "type": "AzureRM",
  "url": "https://management.azure.com/",
  "authorization": {
    "parameters": {
      "tenantid": "$TENANT_ID",
      "serviceprincipalid": "$CLIENT_ID",
      "authenticationType": "spnKey",
      "serviceprincipalkey": "$CLIENT_SECRET"
    },
    "scheme": "ServicePrincipal"
  },
  "isShared": false,
  "isReady": true,
  "serviceEndpointProjectReferences": [
    {
      "projectReference": {
        "id": "$(az devops project show --project '$DEVOPS_PROJECT' --query id -o tsv)",
        "name": "$DEVOPS_PROJECT"
      },
      "name": "$SERVICE_CONNECTION_NAME"
    }
  ]
}
EOF

# Create service connection (this might require manual approval)
print_status "Service connection configuration created. You may need to approve it manually in Azure DevOps."

# Create variable group
print_status "Creating variable group..."
VARIABLE_GROUP_NAME="scout-analytics-vars"

az pipelines variable-group create \
    --name "$VARIABLE_GROUP_NAME" \
    --variables \
        sqlUsername="$SQL_USERNAME" \
        appName="$APP_SERVICE_NAME" \
        resourceGroup="$RESOURCE_GROUP" \
        storageAccount="$STORAGE_ACCOUNT" \
        sqlServerName="$SQL_SERVER" \
        sqlDatabaseName="$SQL_DATABASE" \
    --authorize true \
    --project "$DEVOPS_PROJECT" \
    --organization "$DEVOPS_ORG"

# Add secret variable for SQL password
az pipelines variable-group variable create \
    --group-id $(az pipelines variable-group list --group-name "$VARIABLE_GROUP_NAME" --query "[0].id" -o tsv) \
    --name sqlPassword \
    --value "$SQL_PASSWORD" \
    --secret true \
    --project "$DEVOPS_PROJECT" \
    --organization "$DEVOPS_ORG"

print_success "Variable group created: $VARIABLE_GROUP_NAME"

# Update azure-pipelines.yml with actual values
print_status "Updating pipeline configuration..."
sed -i.bak "s/scout-analytics-sc/$SERVICE_CONNECTION_NAME/g" azure-pipelines.yml
sed -i.bak "s/scout-analytics-api/$APP_SERVICE_NAME/g" azure-pipelines.yml
sed -i.bak "s/scout-analytics-rg/$RESOURCE_GROUP/g" azure-pipelines.yml
sed -i.bak "s/scoutanalyticsweb/$STORAGE_ACCOUNT/g" azure-pipelines.yml
sed -i.bak "s/scout-sql-server/$SQL_SERVER/g" azure-pipelines.yml
sed -i.bak "s/scout_analytics/$SQL_DATABASE/g" azure-pipelines.yml

# Create the pipeline
print_status "Creating Azure DevOps pipeline..."
PIPELINE_NAME="scout-analytics-deployment"

az pipelines create \
    --name "$PIPELINE_NAME" \
    --description "Scout Analytics automated deployment pipeline" \
    --repository https://github.com/jgtolentino/scout-analytics-package \
    --branch main \
    --yml-path azure-pipelines.yml \
    --project "$DEVOPS_PROJECT" \
    --organization "$DEVOPS_ORG"

print_success "Pipeline created: $PIPELINE_NAME"

# Clean up
rm -f service-connection.json azure-pipelines.yml.bak

# Summary
echo ""
echo "=========================================="
echo "🎉 Azure DevOps Pipeline Created Successfully!"
echo "=========================================="
echo ""
echo "📊 Configuration Summary:"
echo "   Organization: $DEVOPS_ORG"
echo "   Project: $DEVOPS_PROJECT"
echo "   Pipeline: $PIPELINE_NAME"
echo "   Service Connection: $SERVICE_CONNECTION_NAME"
echo "   Variable Group: $VARIABLE_GROUP_NAME"
echo ""
echo "🔗 Next Steps:"
echo "   1. Go to $DEVOPS_ORG/$DEVOPS_PROJECT/_build"
echo "   2. Find the '$PIPELINE_NAME' pipeline"
echo "   3. Click 'Run pipeline' to start deployment"
echo "   4. Monitor the 5 stages: Build → Database → Backend → Frontend → Verify"
echo ""
echo "🎯 Expected Results:"
echo "   - Backend API: https://$APP_SERVICE_NAME.azurewebsites.net"
echo "   - Frontend: https://$STORAGE_ACCOUNT.z13.web.core.windows.net"
echo ""
echo "✅ Pipeline is ready to deploy Scout Analytics!"

# Save configuration for future reference
cat > .devops-config << EOF
# Azure DevOps Configuration
DEVOPS_ORG="$DEVOPS_ORG"
DEVOPS_PROJECT="$DEVOPS_PROJECT"
PIPELINE_NAME="$PIPELINE_NAME"
SERVICE_CONNECTION_NAME="$SERVICE_CONNECTION_NAME"
VARIABLE_GROUP_NAME="$VARIABLE_GROUP_NAME"

# Azure Resources
SUBSCRIPTION_ID="$SUBSCRIPTION_ID"
RESOURCE_GROUP="$RESOURCE_GROUP"
APP_SERVICE_NAME="$APP_SERVICE_NAME"
STORAGE_ACCOUNT="$STORAGE_ACCOUNT"
SQL_SERVER="$SQL_SERVER"
SQL_DATABASE="$SQL_DATABASE"
EOF

print_success "Configuration saved to .devops-config"