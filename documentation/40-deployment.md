# Scout Analytics - Deployment Guide

## Deployment Overview

Scout Analytics uses a cloud-native deployment strategy with containerized services, automated CI/CD pipelines, and infrastructure as code. The deployment architecture supports multiple environments with consistent configuration and zero-downtime updates.

## Environment Strategy

### Development Environment
- **Purpose**: Local development and testing
- **Database**: SQLite with sample data
- **Frontend**: Vite dev server with HMR
- **Backend**: Flask development server
- **URL**: http://localhost:5173

### Production Environment
- **Purpose**: Live production deployment
- **Database**: Azure SQL Database
- **Frontend**: Manus Cloud Static Hosting
- **Backend**: Manus Cloud Container Hosting
- **URLs**: 
  - Dashboard: https://ewlwkasq.manus.space
  - API: https://g8h3ilc786zz.manus.space/api

## Container Configuration

### Dockerfile (Backend)
```dockerfile
# ─── Dockerfile ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# 1. install deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. copy source
COPY . /app

# 3. run the API with Gunicorn + Uvicorn worker
#    ⚠️  `main:app` =  path.to.file:FastAPI/Flask-ASGI variable
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "main:app", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
```

### Requirements.txt
```
flask==3.0.0
flask-cors==4.0.0
pandas==2.1.4
numpy==1.24.3
gunicorn==21.2.0
uvicorn[standard]==0.24.0
```

## Build and Deployment Process

### Backend Deployment
```bash
# 1. Build container image
docker build -t scout-api:3.0 .

# 2. Tag for registry
docker tag scout-api:3.0 <your-acr>.azurecr.io/scout-api:3.0

# 3. Push to registry
docker push <your-acr>.azurecr.io/scout-api:3.0

# 4. Deploy to Azure Web App
az webapp config container set \
  --name g8h3ilc786zz --resource-group scout-ai-group \
  --docker-custom-image-name <your-acr>.azurecr.io/scout-api:3.0
```

### Frontend Deployment
```bash
# 1. Install dependencies
npm install

# 2. Build production bundle
npm run build

# 3. Deploy to Manus Cloud
# (Automated through Manus Cloud deployment pipeline)
```

## Environment Variables

### Development Environment
```bash
# Frontend (.env.development)
NODE_ENV=development
VITE_API_BASE_URL=http://localhost:8000/api

# Backend
DATABASE_URL=sqlite:///scout_analytics.db
DEBUG=true
LOG_LEVEL=debug
FLASK_ENV=development
```

### Production Environment
```bash
# Frontend (.env.production)
NODE_ENV=production
VITE_API_BASE_URL=https://g8h3ilc786zz.manus.space/api

# Backend
DATABASE_URL=<azure_sql_connection_string>
DEBUG=false
LOG_LEVEL=info
FLASK_ENV=production
CORS_ORIGINS=https://ewlwkasq.manus.space
```

## Database Migration

### Development Setup
```bash
# 1. Create SQLite database
python load_to_sqlite.py

# 2. Verify data loading
python inspect_csv.py
```

### Production Migration
```bash
# 1. Prepare Azure SQL Database
python migrate_to_azure_sql.py

# 2. Load production data
python enhance_dataset.py
python generate_supporting_data.py

# 3. Validate data quality
python inspect_csv.py --production
```

## CORS Configuration

### Backend CORS Setup
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "https://ewlwkasq.manus.space",  # Production dashboard
    "http://localhost:5173"          # Development dashboard
])
```

### Azure Web App CORS
```bash
# Add CORS rule for production
az webapp cors add --name g8h3ilc786zz \
  --resource-group scout-ai-group \
  --allowed-origins https://ewlwkasq.manus.space
```

## Health Checks and Monitoring

### Application Health Check
```python
@app.route('/api/health')
def health_check():
    return {
        "status": "success",
        "data": {
            "service": "healthy",
            "database": "connected",
            "version": "3.0",
            "uptime_seconds": get_uptime()
        }
    }
```

### Monitoring Endpoints
- **Health Check**: `GET /api/health`
- **Metrics**: Built-in Flask metrics
- **Logs**: Structured logging with request IDs
- **Uptime**: 24/7 availability monitoring

## Deployment Checklist

### Pre-Deployment
- [ ] Code review and testing completed
- [ ] Environment variables configured
- [ ] Database migration scripts tested
- [ ] CORS configuration updated
- [ ] SSL certificates validated

### Deployment Steps
1. **Backend Deployment**
   ```bash
   # Build and deploy container
   docker build -t scout-api:3.0 .
   docker tag scout-api:3.0 <registry>/scout-api:3.0
   docker push <registry>/scout-api:3.0
   
   # Update Azure Web App
   az webapp config container set \
     --name g8h3ilc786zz \
     --resource-group scout-ai-group \
     --docker-custom-image-name <registry>/scout-api:3.0
   ```

2. **Verify API Health**
   ```bash
   curl https://g8h3ilc786zz.manus.space/api/health
   ```

3. **Frontend Deployment**
   ```bash
   # Update API base URL
   export VITE_API_BASE_URL=https://g8h3ilc786zz.manus.space/api
   
   # Build and deploy
   npm run build
   # Deploy via Manus Cloud pipeline
   ```

4. **CORS Configuration**
   ```bash
   az webapp cors add --name g8h3ilc786zz \
     --resource-group scout-ai-group \
     --allowed-origins https://ewlwkasq.manus.space
   ```

### Post-Deployment Verification
- [ ] API health check returns 200
- [ ] Dashboard loads without errors
- [ ] All charts display data correctly
- [ ] No hardcoded fallback data visible
- [ ] Performance metrics within targets

## Rollback Procedures

### Backend Rollback
```bash
# Rollback to previous container version
az webapp config container set \
  --name g8h3ilc786zz \
  --resource-group scout-ai-group \
  --docker-custom-image-name <registry>/scout-api:2.9
```

### Frontend Rollback
```bash
# Redeploy previous build
git checkout <previous-commit>
npm run build
# Deploy via Manus Cloud pipeline
```

### Database Rollback
```bash
# Restore from backup (if needed)
az sql db restore \
  --dest-name scout-analytics-restored \
  --edition Standard \
  --name scout-analytics \
  --resource-group scout-ai-group \
  --server scout-sql-server \
  --time "2025-06-21T10:00:00Z"
```

## Performance Optimization

### Container Optimization
- **Multi-stage builds** for smaller image sizes
- **Layer caching** for faster builds
- **Resource limits** for predictable performance
- **Health checks** for automatic recovery

### Database Optimization
- **Connection pooling** for efficient database usage
- **Query optimization** with proper indexing
- **Caching strategy** for frequently accessed data
- **Monitoring** for performance bottlenecks

### CDN Configuration
- **Static asset caching** with appropriate TTL
- **Compression** for faster content delivery
- **Geographic distribution** for global performance
- **Cache invalidation** for content updates

## Security Configuration

### Container Security
- **Non-root user** for container execution
- **Minimal base image** to reduce attack surface
- **Dependency scanning** for vulnerability detection
- **Secret management** for sensitive configuration

### Network Security
- **HTTPS enforcement** for all communications
- **CORS restrictions** to allowed origins only
- **Rate limiting** to prevent abuse
- **Input validation** for all API endpoints

### Data Security
- **Encryption in transit** with TLS 1.3
- **Encryption at rest** for database storage
- **Access logging** for audit trails
- **Backup encryption** for data protection

## Troubleshooting Guide

### Common Issues

#### API Returns 404 Errors
```bash
# Check container status
az webapp show --name g8h3ilc786zz --resource-group scout-ai-group

# Check application logs
az webapp log tail --name g8h3ilc786zz --resource-group scout-ai-group
```

#### Dashboard Shows "URL not found"
```bash
# Verify API base URL configuration
echo $VITE_API_BASE_URL

# Check CORS configuration
curl -H "Origin: https://ewlwkasq.manus.space" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://g8h3ilc786zz.manus.space/api/health
```

#### Database Connection Errors
```bash
# Test database connectivity
python -c "
import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
print('Connection successful')
"
```

### Performance Issues
- **Slow API responses**: Check database query performance
- **High memory usage**: Monitor container resource utilization
- **Connection timeouts**: Verify network connectivity and CORS
- **Cache misses**: Review caching strategy and TTL values

## Monitoring and Alerting

### Application Monitoring
- **Response time tracking** with percentile analysis
- **Error rate monitoring** with automatic alerting
- **Throughput monitoring** for capacity planning
- **Resource utilization** tracking for optimization

### Business Metrics
- **Dashboard usage analytics** for feature adoption
- **API endpoint popularity** for optimization priorities
- **User behavior patterns** for UX improvements
- **Data quality metrics** for accuracy validation

### Alert Configuration
- **API downtime** - Immediate notification
- **High error rate** - Alert if >5% error rate
- **Slow responses** - Alert if P95 >500ms
- **Database issues** - Connection failure alerts

## Future Deployment Enhancements

### Phase 2 Improvements
- **Blue-green deployment** for zero-downtime updates
- **Automated testing** in deployment pipeline
- **Infrastructure as code** with Terraform
- **Multi-region deployment** for high availability

### Phase 3 Scalability
- **Kubernetes orchestration** for advanced scaling
- **Service mesh** for microservices communication
- **Advanced monitoring** with distributed tracing
- **Automated scaling** based on demand patterns

