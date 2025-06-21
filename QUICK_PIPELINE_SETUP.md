# 🚀 Quick Pipeline Setup Guide

## Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
chmod +x create-azure-devops-pipeline.sh
./create-azure-devops-pipeline.sh
```

This script will:
- ✅ Create service principal
- ✅ Create service connection
- ✅ Create variable group with your resource names
- ✅ Create and configure the pipeline
- ✅ Update all configuration files

## Option 2: Manual Setup (5 Minutes)

### Step 1: Create Service Connection

1. Go to **Azure DevOps** → **Project Settings** → **Service connections**
2. Click **New service connection** → **Azure Resource Manager**
3. Choose **Service principal (automatic)**
4. Select:
   - **Subscription**: Your Azure subscription
   - **Resource group**: Your existing resource group
   - **Service connection name**: `scout-analytics-sc`
5. ✅ Check **Grant access permission to all pipelines**
6. Click **Save**

### Step 2: Create Pipeline

1. Go to **Pipelines** → **New pipeline**
2. Choose **GitHub** → Select **scout-analytics-package** repo
3. Choose **Existing Azure Pipelines YAML file**
4. Branch: `main`, Path: `/azure-pipelines.yml`
5. Click **Continue**

### Step 3: Update Variables

Before running, update these values in the pipeline YAML:

```yaml
variables:
  appName: YOUR_APP_SERVICE_NAME          # e.g., scout-ai-genie
  resourceGroup: YOUR_RESOURCE_GROUP      # e.g., scout-ai-group  
  storageAccount: YOUR_STORAGE_ACCOUNT    # e.g., scoutanalyticsweb
  sqlServerName: YOUR_SQL_SERVER          # e.g., scout-sql-server
  sqlDatabaseName: YOUR_DATABASE          # e.g., scout_analytics
```

### Step 4: Create Variable Group (Optional but Recommended)

1. Go to **Pipelines** → **Library** → **Variable groups**
2. Click **+ Variable group**
3. Name: `scout-analytics-vars`
4. Add variables:
   ```
   sqlUsername = your-sql-username
   sqlPassword = your-sql-password  [🔒 Make secret]
   ```
5. Save and link to your pipeline

### Step 5: Run Pipeline

1. Click **Run pipeline** in Azure DevOps
2. Monitor the 5 stages:
   - 🔨 **Build** - Creates SQLite DB, builds frontend/backend
   - 🗄️ **Deploy Database** - Creates MVP schema
   - 🔧 **Deploy Backend** - Deploys API to App Service
   - 🌐 **Deploy Frontend** - Deploys React to Storage
   - ✅ **Verify** - Health checks and smoke tests

## Expected Results

After successful deployment:

- **Backend API**: `https://your-app-service.azurewebsites.net/api/health`
- **Frontend Dashboard**: `https://your-storage.z13.web.core.windows.net`
- **30,000 transactions** loaded into MVP schema
- **Real-time analytics** dashboard with Philippine retail data

## Troubleshooting

### Service Connection Issues
```bash
# Test Azure CLI access
az account show
az group list --output table
```

### Pipeline Failed at Database Stage
```sql
-- Run manually in your SQL database
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mvp')
BEGIN
    EXEC('CREATE SCHEMA mvp')
END
```

### Frontend Not Loading Data
1. Check CORS settings in App Service
2. Verify API URL in browser network tab
3. Check `VITE_API_BASE_URL` in build logs

### App Service Not Starting
1. Check Application logs in Azure Portal
2. Verify Python 3.11 runtime is set
3. Check startup command: `bash startup.sh`

## Pipeline Stages Breakdown

| Stage | What It Does | Time | Success Criteria |
|-------|-------------|------|------------------|
| Build | Generate data, build frontend/backend | 3-5 min | ✅ Artifacts published |
| Deploy Database | Create MVP schema | 1 min | ✅ Schema created |
| Deploy Backend | Deploy API to App Service | 2-3 min | ✅ App deployed |
| Deploy Frontend | Deploy React to Storage | 1-2 min | ✅ Static site updated |
| Verify | Health checks | 1 min | ✅ All endpoints responding |

**Total time**: ~8-12 minutes for complete deployment

## Ready to Ship! 🚢

Once the pipeline runs successfully, you'll have:
- ✅ Live Scout Analytics dashboard
- ✅ 30k realistic Philippine retail transactions
- ✅ Real-time analytics and insights
- ✅ Automated deployment pipeline

**Visit your dashboard and watch the data come alive!**