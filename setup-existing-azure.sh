#!/bin/bash

# Scout Analytics - Setup Script for Existing Azure Resources
# This script configures deployment to use your existing Azure infrastructure

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

# Configuration
echo "🚀 Scout Analytics - Existing Azure Resources Setup"
echo "=================================================="
echo ""

# Prompt for Azure resource details
read -p "Enter your Azure Resource Group name: " RESOURCE_GROUP
read -p "Enter your Azure SQL Server name: " SQL_SERVER_NAME
read -p "Enter your Azure SQL Database name: " SQL_DATABASE_NAME
read -p "Enter your SQL username: " SQL_USERNAME
read -s -p "Enter your SQL password: " SQL_PASSWORD
echo ""
read -p "Enter your App Service name (for backend): " APP_SERVICE_NAME
read -p "Enter your Storage Account name (for frontend): " STORAGE_ACCOUNT_NAME

# Save configuration
print_status "Saving configuration..."
cat > .azure-config <<EOF
# Azure Resource Configuration
export RESOURCE_GROUP="$RESOURCE_GROUP"
export SQL_SERVER_NAME="$SQL_SERVER_NAME"
export SQL_DATABASE_NAME="$SQL_DATABASE_NAME"
export SQL_USERNAME="$SQL_USERNAME"
export SQL_PASSWORD="$SQL_PASSWORD"
export APP_SERVICE_NAME="$APP_SERVICE_NAME"
export STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME"
export SQL_SCHEMA_NAME="mvp"
EOF

print_success "Configuration saved to .azure-config"

# Create database schema script
print_status "Creating database schema script..."
cat > create-mvp-schema.sql <<'EOF'
-- Create MVP schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mvp')
BEGIN
    EXEC('CREATE SCHEMA mvp')
END
GO

-- Grant permissions to the user
GRANT CREATE TABLE TO [$(SQL_USERNAME)]
GRANT ALTER ON SCHEMA::mvp TO [$(SQL_USERNAME)]
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::mvp TO [$(SQL_USERNAME)]
GO

-- Create tables in MVP schema
IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'stores')
CREATE TABLE mvp.stores (
    store_id INT PRIMARY KEY,
    store_name NVARCHAR(255),
    barangay NVARCHAR(255),
    city NVARCHAR(255),
    province NVARCHAR(255),
    region NVARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    store_type NVARCHAR(50)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'customers')
CREATE TABLE mvp.customers (
    customer_id INT PRIMARY KEY,
    age INT,
    gender NVARCHAR(10),
    income_level NVARCHAR(50)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'brands')
CREATE TABLE mvp.brands (
    brand_id INT PRIMARY KEY,
    brand_name NVARCHAR(255),
    category NVARCHAR(255)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'products')
CREATE TABLE mvp.products (
    product_id INT PRIMARY KEY,
    product_name NVARCHAR(255),
    brand_id INT,
    category NVARCHAR(255),
    unit_price DECIMAL(10,2),
    FOREIGN KEY (brand_id) REFERENCES mvp.brands(brand_id)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'transactions')
CREATE TABLE mvp.transactions (
    transaction_id INT PRIMARY KEY,
    store_id INT,
    customer_id INT,
    transaction_datetime DATETIME,
    total_amount DECIMAL(10,2),
    FOREIGN KEY (store_id) REFERENCES mvp.stores(store_id),
    FOREIGN KEY (customer_id) REFERENCES mvp.customers(customer_id)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'transaction_items')
CREATE TABLE mvp.transaction_items (
    item_id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(10,2),
    FOREIGN KEY (transaction_id) REFERENCES mvp.transactions(transaction_id),
    FOREIGN KEY (product_id) REFERENCES mvp.products(product_id)
)
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'substitutions')
CREATE TABLE mvp.substitutions (
    substitution_id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id INT,
    original_product_id INT,
    substituted_product_id INT,
    reason NVARCHAR(255),
    FOREIGN KEY (transaction_id) REFERENCES mvp.transactions(transaction_id),
    FOREIGN KEY (original_product_id) REFERENCES mvp.products(product_id),
    FOREIGN KEY (substituted_product_id) REFERENCES mvp.products(product_id)
)
GO

PRINT 'MVP schema and tables created successfully'
EOF

print_success "Schema script created"

# Create deployment script for existing resources
print_status "Creating deployment script..."
cat > deploy-to-existing-azure.sh <<'EOF'
#!/bin/bash

# Load configuration
source .azure-config

set -e

echo "🚀 Deploying Scout Analytics to existing Azure resources"
echo "======================================================="

# Deploy Backend
echo ""
echo "📦 Deploying Backend API..."
cd backend/scout-analytics-api-flask

# Create app settings
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --settings \
        DATABASE_URL="mssql+pyodbc://${SQL_USERNAME}:${SQL_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DATABASE_NAME}?driver=ODBC+Driver+17+for+SQL+Server" \
        DATABASE_SCHEMA="mvp" \
        FLASK_ENV="production" \
        CORS_ORIGINS="https://${STORAGE_ACCOUNT_NAME}.z13.web.core.windows.net"

# Create deployment package
zip -r deploy.zip . -x "*.pyc" "__pycache__/*" "venv/*" "env/*" ".env*"

# Deploy to App Service
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --src deploy.zip

rm deploy.zip
cd ../..

echo "✅ Backend deployed"

# Deploy Frontend
echo ""
echo "📦 Deploying Frontend..."
cd frontend/scout-analytics-dashboard

# Build with production API URL
echo "VITE_API_BASE_URL=https://${APP_SERVICE_NAME}.azurewebsites.net/api" > .env.production
npm install
npm run build

# Enable static website hosting
az storage blob service-properties update \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --static-website \
    --index-document index.html \
    --404-document index.html

# Upload to blob storage
az storage blob upload-batch \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --source dist \
    --destination '$web' \
    --overwrite

cd ../..

echo "✅ Frontend deployed"

# Get URLs
BACKEND_URL="https://${APP_SERVICE_NAME}.azurewebsites.net"
FRONTEND_URL=$(az storage account show \
    --name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "primaryEndpoints.web" \
    --output tsv)

echo ""
echo "🎉 Deployment completed!"
echo "========================"
echo "Backend API: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""
echo "Run health check: curl $BACKEND_URL/api/health"
EOF

chmod +x deploy-to-existing-azure.sh
print_success "Deployment script created"

# Create Azure DevOps setup guide
print_status "Creating Azure DevOps setup guide..."
cat > AZURE_DEVOPS_SETUP.md <<EOF
# Azure DevOps Setup Guide for Scout Analytics

## Prerequisites
- Azure DevOps organization and project
- Azure subscription with existing resources
- Service connection to Azure

## Setup Steps

### 1. Create Service Connection
1. Go to Project Settings > Service connections
2. Click "New service connection" > "Azure Resource Manager"
3. Choose "Service principal (automatic)"
4. Select your subscription and resource group
5. Name it: "Scout-Analytics-Service-Connection"

### 2. Create Variable Group
1. Go to Pipelines > Library
2. Create new variable group: "scout-analytics-vars"
3. Add variables:
   - sqlUsername: $SQL_USERNAME
   - sqlPassword: $SQL_PASSWORD (mark as secret)
   - Any other sensitive values

### 3. Import Pipeline
1. Go to Pipelines > New pipeline
2. Choose your repository
3. Select "Existing Azure Pipelines YAML file"
4. Choose: /azure-pipelines.yml

### 4. Update Pipeline Variables
Edit azure-pipelines.yml and update:
- azureSubscription: 'Scout-Analytics-Service-Connection'
- resourceGroup: '$RESOURCE_GROUP'
- backendWebAppName: '$APP_SERVICE_NAME'
- frontendStorageAccount: '$STORAGE_ACCOUNT_NAME'
- sqlServerName: '$SQL_SERVER_NAME'
- sqlDatabaseName: '$SQL_DATABASE_NAME'

### 5. Run Pipeline
1. Save and run the pipeline
2. Monitor each stage for successful completion
3. Verify deployment using the URLs provided

## Manual Database Setup
If the pipeline can't create the schema, run this locally:
\`\`\`bash
sqlcmd -S ${SQL_SERVER_NAME}.database.windows.net -U $SQL_USERNAME -P '$SQL_PASSWORD' -d $SQL_DATABASE_NAME -i create-mvp-schema.sql
\`\`\`

## Troubleshooting
- Check service connection permissions
- Verify SQL firewall rules allow Azure services
- Ensure storage account has static website enabled
- Check App Service configuration for Python 3.11
EOF

print_success "Azure DevOps setup guide created"

# Create data migration script
print_status "Creating data migration script..."
cat > migrate-to-mvp-schema.py <<'EOF'
#!/usr/bin/env python3
"""
Migrate data to MVP schema in existing Azure SQL Database
"""

import os
import sys
import pyodbc
from pathlib import Path
from deployment.load_to_sqlite import create_sample_data
from deployment.migrate_to_azure_sql import migrate_table_data

# Load configuration
def load_config():
    config = {}
    with open('.azure-config', 'r') as f:
        for line in f:
            if line.startswith('export '):
                key, value = line.replace('export ', '').strip().split('=')
                config[key] = value.strip('"')
    return config

def main():
    config = load_config()
    
    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['SQL_SERVER_NAME']}.database.windows.net;"
        f"DATABASE={config['SQL_DATABASE_NAME']};"
        f"UID={config['SQL_USERNAME']};"
        f"PWD={config['SQL_PASSWORD']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print("🚀 Migrating data to MVP schema...")
    
    # First create sample data in SQLite
    print("📊 Creating sample data...")
    os.system("cd deployment && python load_to_sqlite.py")
    
    # Then migrate to Azure SQL MVP schema
    print("☁️ Migrating to Azure SQL MVP schema...")
    os.system(f"""cd deployment && python migrate_to_azure_sql.py \\
        --server {config['SQL_SERVER_NAME']}.database.windows.net \\
        --database {config['SQL_DATABASE_NAME']} \\
        --username {config['SQL_USERNAME']} \\
        --password '{config['SQL_PASSWORD']}' \\
        --schema mvp""")
    
    print("✅ Migration completed!")

if __name__ == "__main__":
    main()
EOF

chmod +x migrate-to-mvp-schema.py
print_success "Migration script created"

# Summary
echo ""
echo "=========================================="
echo "✅ Setup completed successfully!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "1. Create MVP schema in database:"
echo "   sqlcmd -S ${SQL_SERVER_NAME}.database.windows.net -U $SQL_USERNAME -d $SQL_DATABASE_NAME -i create-mvp-schema.sql"
echo ""
echo "2. Deploy to Azure:"
echo "   ./deploy-to-existing-azure.sh"
echo ""
echo "3. Load sample data:"
echo "   python migrate-to-mvp-schema.py"
echo ""
echo "4. For Azure DevOps:"
echo "   - Follow instructions in AZURE_DEVOPS_SETUP.md"
echo "   - Update azure-pipelines.yml with your resource names"
echo ""
echo "📄 Created files:"
echo "   - .azure-config (your Azure resource configuration)"
echo "   - create-mvp-schema.sql (database schema)"
echo "   - deploy-to-existing-azure.sh (deployment script)"
echo "   - azure-pipelines.yml (Azure DevOps pipeline)"
echo "   - AZURE_DEVOPS_SETUP.md (setup guide)"
echo "   - migrate-to-mvp-schema.py (data migration)"
echo ""
echo "⚠️  Add .azure-config to .gitignore to keep credentials safe!"