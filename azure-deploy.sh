#!/bin/bash

# Scout Analytics - Complete Azure Deployment Script
# This script deploys both frontend and backend to Azure

set -e  # Exit on any error

# Configuration
PROJECT_NAME="scout-analytics"
RESOURCE_GROUP="${PROJECT_NAME}-rg"
LOCATION="eastus"
BACKEND_APP_NAME="${PROJECT_NAME}-api-${RANDOM}"
FRONTEND_APP_NAME="${PROJECT_NAME}-web-${RANDOM}"
SQL_SERVER_NAME="${PROJECT_NAME}-sql-${RANDOM}"
SQL_DATABASE_NAME="scout_analytics"
SQL_ADMIN="scoutadmin"
SQL_PASSWORD="Scout@Analytics2024!"
STORAGE_ACCOUNT_NAME="scout${RANDOM}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check if logged in to Azure
    if ! az account show > /dev/null 2>&1; then
        print_error "Not logged in to Azure. Please run 'az login' and try again."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Create resource group
create_resource_group() {
    print_status "Creating resource group..."
    
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    
    print_success "Resource group created: $RESOURCE_GROUP"
}

# Create Azure SQL Database
create_sql_database() {
    print_status "Creating Azure SQL Database..."
    
    # Create SQL Server
    az sql server create \
        --name $SQL_SERVER_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --admin-user $SQL_ADMIN \
        --admin-password $SQL_PASSWORD \
        --output none
    
    # Configure firewall rule to allow Azure services
    az sql server firewall-rule create \
        --resource-group $RESOURCE_GROUP \
        --server $SQL_SERVER_NAME \
        --name AllowAzureServices \
        --start-ip-address 0.0.0.0 \
        --end-ip-address 0.0.0.0 \
        --output none
    
    # Create database
    az sql db create \
        --resource-group $RESOURCE_GROUP \
        --server $SQL_SERVER_NAME \
        --name $SQL_DATABASE_NAME \
        --service-objective S0 \
        --output none
    
    print_success "Azure SQL Database created"
    
    # Get connection string
    SQL_CONNECTION_STRING="mssql+pyodbc://${SQL_ADMIN}:${SQL_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DATABASE_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
    echo "SQL_CONNECTION_STRING=$SQL_CONNECTION_STRING" > .azure-env
}

# Deploy Backend API
deploy_backend() {
    print_status "Deploying Backend API..."
    
    cd backend/scout-analytics-api-flask
    
    # Create App Service Plan
    az appservice plan create \
        --name ${BACKEND_APP_NAME}-plan \
        --resource-group $RESOURCE_GROUP \
        --sku B1 \
        --is-linux \
        --output none
    
    # Create Web App
    az webapp create \
        --resource-group $RESOURCE_GROUP \
        --plan ${BACKEND_APP_NAME}-plan \
        --name $BACKEND_APP_NAME \
        --runtime "PYTHON:3.11" \
        --output none
    
    # Configure app settings
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP \
        --name $BACKEND_APP_NAME \
        --settings \
            DATABASE_URL="$SQL_CONNECTION_STRING" \
            CORS_ORIGINS="https://${FRONTEND_APP_NAME}.azurewebsites.net" \
            FLASK_ENV="production" \
        --output none
    
    # Deploy code using zip deployment
    print_status "Preparing backend for deployment..."
    
    # Create deployment package
    zip -r deploy.zip . -x "*.pyc" "__pycache__/*" "venv/*" "env/*" ".env*"
    
    # Deploy to Azure
    az webapp deployment source config-zip \
        --resource-group $RESOURCE_GROUP \
        --name $BACKEND_APP_NAME \
        --src deploy.zip \
        --output none
    
    # Clean up
    rm deploy.zip
    
    print_success "Backend API deployed to: https://${BACKEND_APP_NAME}.azurewebsites.net"
    
    cd ../..
}

# Deploy Frontend
deploy_frontend() {
    print_status "Deploying Frontend..."
    
    cd frontend/scout-analytics-dashboard
    
    # Create static web app storage account
    az storage account create \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --output none
    
    # Enable static website hosting
    az storage blob service-properties update \
        --account-name $STORAGE_ACCOUNT_NAME \
        --static-website \
        --index-document index.html \
        --404-document index.html \
        --output none
    
    # Build frontend with production API URL
    print_status "Building frontend..."
    echo "VITE_API_BASE_URL=https://${BACKEND_APP_NAME}.azurewebsites.net/api" > .env.production
    npm install
    npm run build
    
    # Upload to blob storage
    print_status "Uploading frontend files..."
    az storage blob upload-batch \
        --account-name $STORAGE_ACCOUNT_NAME \
        --source dist \
        --destination '$web' \
        --output none
    
    # Get static website URL
    FRONTEND_URL=$(az storage account show \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "primaryEndpoints.web" \
        --output tsv)
    
    print_success "Frontend deployed to: $FRONTEND_URL"
    
    # Update backend CORS settings
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP \
        --name $BACKEND_APP_NAME \
        --settings CORS_ORIGINS="$FRONTEND_URL" \
        --output none
    
    cd ../..
}

# Load sample data
load_sample_data() {
    print_status "Loading sample data to database..."
    
    cd deployment
    
    # Update database connection in migration script
    python3 migrate_to_azure_sql.py \
        --server "${SQL_SERVER_NAME}.database.windows.net" \
        --database "$SQL_DATABASE_NAME" \
        --username "$SQL_ADMIN" \
        --password "$SQL_PASSWORD"
    
    cd ..
    
    print_success "Sample data loaded successfully"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check backend health
    BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"
    print_status "Checking backend health..."
    
    for i in {1..5}; do
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BACKEND_URL}/api/health)
        
        if [ "$HTTP_STATUS" = "200" ]; then
            print_success "Backend API is healthy"
            break
        else
            print_warning "Backend not ready yet (attempt $i/5). Waiting 30 seconds..."
            sleep 30
        fi
    done
    
    # Print deployment summary
    echo ""
    echo "=========================================="
    echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉"
    echo "=========================================="
    echo ""
    echo "📊 Scout Analytics URLs:"
    echo "   Frontend:  $FRONTEND_URL"
    echo "   Backend:   https://${BACKEND_APP_NAME}.azurewebsites.net"
    echo ""
    echo "🗄️ Database:"
    echo "   Server:    ${SQL_SERVER_NAME}.database.windows.net"
    echo "   Database:  $SQL_DATABASE_NAME"
    echo ""
    echo "🔧 Resource Group: $RESOURCE_GROUP"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Visit the frontend URL to access Scout Analytics"
    echo "   2. Test all dashboard features"
    echo "   3. Configure custom domain (optional)"
    echo "   4. Set up monitoring and alerts"
    echo ""
    
    # Save deployment info
    cat > deployment-info.json <<EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "frontendUrl": "$FRONTEND_URL",
    "backendUrl": "https://${BACKEND_APP_NAME}.azurewebsites.net",
    "sqlServer": "${SQL_SERVER_NAME}.database.windows.net",
    "sqlDatabase": "$SQL_DATABASE_NAME",
    "deploymentDate": "$(date -u +"%Y-%m-%d %H:%M:%S UTC")"
}
EOF
    
    print_success "Deployment information saved to deployment-info.json"
}

# Cleanup function (optional)
cleanup() {
    print_warning "Cleaning up resources..."
    az group delete --name $RESOURCE_GROUP --yes --no-wait
    print_success "Resource group deletion initiated"
}

# Main deployment function
main() {
    echo ""
    echo "🚀 Scout Analytics Azure Deployment"
    echo "==================================="
    echo ""
    
    check_prerequisites
    create_resource_group
    create_sql_database
    deploy_backend
    deploy_frontend
    load_sample_data
    verify_deployment
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 [deploy|cleanup]"
        echo "  deploy  - Deploy Scout Analytics to Azure (default)"
        echo "  cleanup - Delete all Azure resources"
        exit 1
        ;;
esac