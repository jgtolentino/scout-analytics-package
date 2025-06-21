# Scout Analytics - Azure Deployment Guide

## 🚀 Quick Deploy to Azure

This guide provides step-by-step instructions for deploying Scout Analytics to Microsoft Azure.

## Prerequisites

Before starting, ensure you have:
- ✅ Azure account with active subscription
- ✅ Azure CLI installed (`az --version`)
- ✅ Node.js 18+ installed
- ✅ Python 3.11+ installed
- ✅ Git installed

## 📋 Deployment Options

### Option 1: Automated Deployment (Recommended)

Use our automated deployment script that handles everything:

```bash
# Make the script executable
chmod +x azure-deploy.sh

# Run the deployment
./azure-deploy.sh

# To clean up all resources later
./azure-deploy.sh cleanup
```

This script will:
- Create a resource group
- Deploy Azure SQL Database
- Deploy Backend API (App Service)
- Deploy Frontend (Static Web App)
- Load sample data
- Configure all connections

### Option 2: GitHub Actions CI/CD

1. **Set up GitHub Secrets**:
   ```
   AZURE_CREDENTIALS - Service principal credentials
   API_BASE_URL - Your backend API URL
   STORAGE_ACCOUNT_NAME - For frontend hosting
   FRONTEND_URL - Your frontend URL
   ```

2. **Get Azure Credentials**:
   ```bash
   az ad sp create-for-rbac --name "scout-analytics-sp" \
     --role contributor \
     --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
     --sdk-auth
   ```

3. **Push to main branch** to trigger deployment

### Option 3: Manual Deployment

#### 1. Create Resource Group
```bash
az group create --name scout-analytics-rg --location eastus
```

#### 2. Create Azure SQL Database
```bash
# Create SQL Server
az sql server create \
  --name scout-sql-server \
  --resource-group scout-analytics-rg \
  --location eastus \
  --admin-user scoutadmin \
  --admin-password 'YourSecurePassword123!'

# Create Database
az sql db create \
  --resource-group scout-analytics-rg \
  --server scout-sql-server \
  --name scout_analytics \
  --service-objective S0

# Configure Firewall
az sql server firewall-rule create \
  --resource-group scout-analytics-rg \
  --server scout-sql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 3. Deploy Backend API
```bash
cd backend/scout-analytics-api-flask

# Create App Service Plan
az appservice plan create \
  --name scout-api-plan \
  --resource-group scout-analytics-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group scout-analytics-rg \
  --plan scout-api-plan \
  --name scout-analytics-api \
  --runtime "PYTHON:3.11"

# Configure App Settings
az webapp config appsettings set \
  --resource-group scout-analytics-rg \
  --name scout-analytics-api \
  --settings \
    DATABASE_URL="mssql+pyodbc://..." \
    FLASK_ENV="production"

# Deploy Code
zip -r deploy.zip . -x "*.pyc" "__pycache__/*" "venv/*"
az webapp deployment source config-zip \
  --resource-group scout-analytics-rg \
  --name scout-analytics-api \
  --src deploy.zip
```

#### 4. Deploy Frontend
```bash
cd frontend/scout-analytics-dashboard

# Create Storage Account
az storage account create \
  --name scoutanalyticsweb \
  --resource-group scout-analytics-rg \
  --location eastus \
  --sku Standard_LRS

# Enable Static Website
az storage blob service-properties update \
  --account-name scoutanalyticsweb \
  --static-website \
  --index-document index.html

# Build Frontend
echo "VITE_API_BASE_URL=https://scout-analytics-api.azurewebsites.net/api" > .env.production
npm install
npm run build

# Upload Files
az storage blob upload-batch \
  --account-name scoutanalyticsweb \
  --source dist \
  --destination '$web'
```

#### 5. Load Sample Data
```bash
cd deployment

# First, create local SQLite database
python load_to_sqlite.py

# Then migrate to Azure SQL
python migrate_to_azure_sql.py \
  --server scout-sql-server.database.windows.net \
  --database scout_analytics \
  --username scoutadmin \
  --password 'YourSecurePassword123!'
```

## 🔧 Configuration

### Environment Variables

#### Backend (App Service Settings)
```bash
DATABASE_URL=mssql+pyodbc://user:pass@server/database?driver=ODBC+Driver+17+for+SQL+Server
CORS_ORIGINS=https://your-frontend.azurestaticapps.net
FLASK_ENV=production
```

#### Frontend (.env.production)
```bash
VITE_API_BASE_URL=https://your-backend.azurewebsites.net/api
NODE_ENV=production
```

## 📊 Monitoring & Maintenance

### Enable Application Insights
```bash
az monitor app-insights component create \
  --app scout-analytics-insights \
  --location eastus \
  --resource-group scout-analytics-rg \
  --application-type web
```

### Set Up Alerts
```bash
# CPU Alert
az monitor metrics alert create \
  --name high-cpu-alert \
  --resource-group scout-analytics-rg \
  --scopes /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Web/sites/{app-name} \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m
```

## 🔐 Security Best Practices

1. **Use Managed Identity** for database connections
2. **Enable HTTPS Only**:
   ```bash
   az webapp update --name scout-analytics-api \
     --resource-group scout-analytics-rg \
     --https-only true
   ```

3. **Configure CORS** properly:
   ```bash
   az webapp cors add --name scout-analytics-api \
     --resource-group scout-analytics-rg \
     --allowed-origins https://your-frontend-domain.com
   ```

4. **Use Key Vault** for secrets:
   ```bash
   az keyvault create --name scout-kv \
     --resource-group scout-analytics-rg \
     --location eastus
   ```

## 💰 Cost Optimization

### Estimated Monthly Costs (USD)
- App Service (B1): ~$55
- Azure SQL (S0): ~$15
- Storage Account: ~$1
- **Total**: ~$71/month

### Cost Saving Tips
1. Use **Free Tier** for development
2. **Scale down** during off-hours
3. Enable **Auto-scaling** for production
4. Use **Reserved Instances** for long-term savings

## 🐛 Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check logs
az webapp log tail --name scout-analytics-api \
  --resource-group scout-analytics-rg

# Restart app
az webapp restart --name scout-analytics-api \
  --resource-group scout-analytics-rg
```

#### Database Connection Failed
```bash
# Test connection
az sql db show-connection-string \
  --server scout-sql-server \
  --name scout_analytics \
  --client ado.net
```

#### CORS Issues
```bash
# List current CORS settings
az webapp cors show --name scout-analytics-api \
  --resource-group scout-analytics-rg

# Add frontend URL
az webapp cors add --name scout-analytics-api \
  --resource-group scout-analytics-rg \
  --allowed-origins https://your-frontend-url
```

## 📞 Support

- **Documentation**: Check `/documentation` folder
- **Issues**: Create an issue on GitHub
- **Azure Support**: https://azure.microsoft.com/support/

## 🎯 Success Verification

After deployment, verify:
- [ ] Backend health check: `https://your-api.azurewebsites.net/api/health`
- [ ] Frontend loads: `https://your-frontend.azurestaticapps.net`
- [ ] Data displays correctly in dashboard
- [ ] All navigation works
- [ ] No console errors

---

**Need help?** Check the complete documentation or run `./azure-deploy.sh --help`