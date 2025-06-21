# Azure DevOps Setup Guide for Scout Analytics

This guide will help you set up Azure DevOps to deploy Scout Analytics using your existing Azure resources.

## 📋 Prerequisites

- ✅ Azure DevOps organization and project
- ✅ Azure subscription with existing resources:
  - App Service (for backend API)
  - Storage Account (for frontend)
  - Azure SQL Database
- ✅ Permissions to create service connections and pipelines

## 🚀 Quick Setup Steps

### 1. Create Service Connection

1. Go to **Project Settings** → **Service connections**
2. Click **New service connection** → **Azure Resource Manager**
3. Choose **Service principal (automatic)**
4. Select:
   - Subscription: Your Azure subscription
   - Resource group: Your existing resource group
   - Service connection name: `scout-analytics-sc`
5. Check **Grant access permission to all pipelines**
6. Click **Save**

### 2. Create Variable Group (for sensitive data)

1. Go to **Pipelines** → **Library**
2. Click **+ Variable group**
3. Name: `scout-analytics-vars`
4. Add these variables:
   ```
   sqlUsername     = your-sql-username
   sqlPassword     = your-sql-password     [🔒 Make secret]
   ```
5. Click **Save**

### 3. Update Pipeline Variables

Edit the `azure-pipelines.yml` file and update these values with your actual resource names:

```yaml
variables:
  # UPDATE THESE WITH YOUR ACTUAL VALUES
  appName: your-app-service-name        # e.g., scout-analytics-api
  resourceGroup: your-resource-group    # e.g., scout-analytics-rg
  storageAccount: your-storage-account  # e.g., scoutanalyticsweb
  sqlServerName: your-sql-server        # e.g., scout-sql-server
  sqlDatabaseName: your-database        # e.g., scout_analytics
```

### 4. Import the Pipeline

1. Go to **Pipelines** → **New pipeline**
2. Choose **Azure Repos Git** (or your repo location)
3. Select your repository
4. Choose **Existing Azure Pipelines YAML file**
5. Branch: `main`
6. Path: `/azure-pipelines.yml`
7. Click **Continue** → **Run**

### 5. Link Variable Group to Pipeline

1. Edit the pipeline
2. Click **Variables** → **Variable groups**
3. Link the `scout-analytics-vars` group
4. Save

## 🔧 Manual Prerequisites

Before running the pipeline, ensure:

### A. App Service Configuration
```bash
# Ensure Python 3.11 runtime
az webapp config set \
  --resource-group your-resource-group \
  --name your-app-service \
  --linux-fx-version "PYTHON|3.11"

# Enable build automation
az webapp config appsettings set \
  --resource-group your-resource-group \
  --name your-app-service \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### B. Storage Account Setup
```bash
# Enable static website hosting
az storage blob service-properties update \
  --account-name your-storage-account \
  --static-website \
  --index-document index.html \
  --404-document index.html
```

### C. SQL Database Firewall
```bash
# Allow Azure services
az sql server firewall-rule create \
  --resource-group your-resource-group \
  --server your-sql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## 📊 Pipeline Overview

The pipeline has 5 stages:

1. **Build** - Creates SQLite database, builds frontend and backend
2. **Deploy Database** - Creates MVP schema in SQL Database
3. **Deploy Backend** - Deploys Flask API to App Service
4. **Deploy Frontend** - Deploys React app to Storage Account
5. **Verify** - Runs smoke tests

## 🐛 Troubleshooting

### Service Connection Issues
```bash
# Test service connection
az account show --subscription your-subscription-id

# If fails, recreate with manual service principal:
az ad sp create-for-rbac \
  --name scout-analytics-sp \
  --role Contributor \
  --scopes /subscriptions/{id}/resourceGroups/{rg}
```

### Database Connection Issues
```bash
# Test SQL connection
sqlcmd -S your-server.database.windows.net \
       -d your-database \
       -U your-username \
       -P 'your-password' \
       -Q "SELECT 1"
```

### Pipeline Failed at Database Stage
If the schema creation fails, run manually:
```sql
-- Connect to your database and run:
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mvp')
BEGIN
    EXEC('CREATE SCHEMA mvp')
END
GO
```

### Frontend Not Loading Data
1. Check CORS settings:
   ```bash
   az webapp cors show \
     --resource-group your-rg \
     --name your-app-service
   ```

2. Verify API URL in frontend:
   ```bash
   # Should show your API URL
   curl https://your-storage.z13.web.core.windows.net/config.json
   ```

## 🎯 Success Verification

After successful deployment:

1. **Backend API Health**:
   ```
   https://your-app-service.azurewebsites.net/api/health
   ```
   Should return: `{"status": "healthy"}`

2. **Frontend Dashboard**:
   ```
   https://your-storage.z13.web.core.windows.net
   ```
   Should show the Scout Analytics dashboard

3. **Data Loading**:
   - Check browser console (F12) for errors
   - Verify network tab shows successful API calls

## 📝 Post-Deployment Steps

1. **Custom Domain** (optional):
   ```bash
   # For frontend
   az storage account update \
     --name your-storage \
     --custom-domain your-domain.com
   
   # For backend
   az webapp config hostname add \
     --webapp-name your-app \
     --resource-group your-rg \
     --hostname api.your-domain.com
   ```

2. **Enable HTTPS**:
   ```bash
   az webapp update \
     --name your-app \
     --resource-group your-rg \
     --https-only true
   ```

3. **Setup Monitoring**:
   ```bash
   # Enable Application Insights
   az monitor app-insights component create \
     --app scout-analytics \
     --location eastus \
     --resource-group your-rg
   ```

## 🔄 Updating the Application

To deploy updates:
1. Commit changes to your repository
2. Push to `main` branch
3. Pipeline will automatically trigger
4. Monitor in Azure DevOps → Pipelines

## 📞 Support

If you encounter issues:
1. Check pipeline logs in Azure DevOps
2. Review Azure resource logs
3. Verify all prerequisites are met
4. Check the troubleshooting section above

---

**Ready to deploy?** Update the variables in `azure-pipelines.yml` and run the pipeline!