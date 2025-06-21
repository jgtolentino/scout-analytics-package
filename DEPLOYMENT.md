# Scout Analytics - Quick Deployment Guide

## 🚀 Rapid Deployment Instructions

This guide provides step-by-step instructions for deploying Scout Analytics in various environments.

## 📋 Prerequisites Checklist

- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Docker installed (for containerized deployment)
- [ ] Azure CLI installed (for cloud deployment)
- [ ] Git installed

## ⚡ 5-Minute Local Setup

### 1. Frontend Development Server
```bash
cd frontend/scout-analytics-dashboard
npm install
npm run dev
```
**Access**: http://localhost:5173

### 2. Backend Development Server
```bash
cd backend/scout-analytics-api-flask
pip install -r requirements.txt
python main.py
```
**Access**: http://localhost:8000

### 3. Load Sample Data
```bash
cd deployment
python load_to_sqlite.py
```

## 🌐 Production Deployment

### Option 1: Container Deployment
```bash
# Build and deploy backend
cd backend/scout-analytics-api-flask
docker build -t scout-api:latest .
docker run -p 8000:8000 scout-api:latest

# Build and deploy frontend
cd frontend/scout-analytics-dashboard
npm run build
# Deploy dist/ folder to your static hosting service
```

### Option 2: Cloud Deployment (Azure)
```bash
# Backend deployment
cd backend/scout-analytics-api-flask
./deploy.sh

# Frontend deployment
cd frontend/scout-analytics-dashboard
npm run build
# Use your preferred static hosting service
```

## 🔧 Environment Configuration

### Frontend (.env.production)
```bash
VITE_API_BASE_URL=https://your-api-domain.com/api
NODE_ENV=production
```

### Backend (Environment Variables)
```bash
DATABASE_URL=your_database_connection_string
CORS_ORIGINS=https://your-frontend-domain.com
DEBUG=false
FLASK_ENV=production
```

## ✅ Deployment Verification

### Health Checks
```bash
# API Health Check
curl https://your-api-domain.com/api/health

# Frontend Accessibility
curl https://your-frontend-domain.com
```

### Expected Responses
- **API Health**: `{"status": "success", "data": {"service": "healthy"}}`
- **Frontend**: HTML page with Scout Analytics title

## 🐛 Common Issues & Solutions

### Issue: CSS Not Loading (Wireframe Look)
**Solution**: Ensure Tailwind CSS is properly configured
```bash
cd frontend/scout-analytics-dashboard
npm run build
# Check dist/assets/*.css file size (should be >50KB)
```

### Issue: API CORS Errors
**Solution**: Update CORS configuration
```bash
# Add your frontend domain to CORS_ORIGINS
export CORS_ORIGINS=https://your-frontend-domain.com
```

### Issue: Database Connection Errors
**Solution**: Verify database configuration
```bash
# Check DATABASE_URL format
# SQLite: sqlite:///path/to/database.db
# Azure SQL: mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server
```

## 📊 Performance Optimization

### Frontend Optimization
- Enable gzip compression
- Configure CDN for static assets
- Implement service worker for caching

### Backend Optimization
- Use connection pooling for database
- Enable Redis caching for API responses
- Configure load balancing for high traffic

## 🔐 Security Configuration

### Production Security Checklist
- [ ] HTTPS enabled for all endpoints
- [ ] CORS restricted to authorized domains
- [ ] Environment variables secured
- [ ] Database access restricted
- [ ] API rate limiting enabled

## 📈 Monitoring Setup

### Health Monitoring
```bash
# Set up automated health checks
curl -f https://your-api-domain.com/api/health || alert_team
```

### Performance Monitoring
- Monitor API response times (<200ms target)
- Track frontend load times (<2s target)
- Monitor database query performance
- Set up error rate alerting

## 🎯 Success Criteria

### Deployment Success Indicators
- [ ] API health check returns 200 OK
- [ ] Frontend loads with proper styling
- [ ] All dashboard pages display data
- [ ] Charts render correctly
- [ ] No console errors in browser
- [ ] Performance targets met

### Business Validation
- [ ] Transaction data displays correctly (15,000+ records)
- [ ] Philippine regional data shows authentic distribution
- [ ] AI insights generate relevant recommendations
- [ ] All navigation links work properly
- [ ] Mobile responsiveness verified

## 📞 Support Resources

### Documentation
- **Complete Documentation**: `/documentation` folder
- **API Reference**: `/backend/scout-analytics-api-flask/openapi.yaml`
- **Architecture Guide**: `/documentation/10-architecture.md`

### Troubleshooting
- **Deployment Issues**: `/documentation/40-deployment.md`
- **Performance Problems**: `/documentation/50-qa-testing.md`
- **Configuration Help**: `/backend/scout-analytics-api-flask/env.template`

---

**Need Help?** Check the complete documentation in the `/documentation` folder for detailed guides and troubleshooting information.

