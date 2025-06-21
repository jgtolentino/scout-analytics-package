# Scout Analytics - API Documentation

## API Overview

The Scout Analytics API provides comprehensive retail intelligence capabilities through a RESTful interface. Built with Flask and optimized for Philippine retail market analysis, the API delivers real-time analytics, transaction data, and business insights.

## OpenAPI Specification

**Interactive Documentation**: [OpenAPI 3.0 Specification](./openapi.yaml)

The complete API specification is available in OpenAPI 3.0 format, providing:
- Interactive endpoint testing
- Request/response schemas
- Authentication requirements
- Error handling documentation

## Base URLs

### Production Environment
- **Base URL**: `https://g8h3ilc786zz.manus.space/api`
- **Health Check**: `https://g8h3ilc786zz.manus.space/api/health`
- **Interactive Docs**: `https://g8h3ilc786zz.manus.space/api/docs`

### Development Environment
- **Base URL**: `http://localhost:8000/api`
- **Health Check**: `http://localhost:8000/api/health`

## API Endpoints Overview

| Endpoint | Method | Purpose | Cache TTL |
|----------|--------|---------|-----------|
| `/health` | GET | System health check | No cache |
| `/analytics/overview` | GET | Dashboard KPIs and summary | 5 minutes |
| `/analytics/transactions` | GET | Transaction data with filtering | No cache |
| `/analytics/trends` | GET | Temporal and regional analysis | 10 minutes |
| `/analytics/products` | GET | Product mix and category analysis | 15 minutes |
| `/analytics/demographics` | GET | Consumer insights and demographics | 30 minutes |
| `/substitutions` | GET | Brand substitution patterns | No cache |
| `/stores` | GET | Store locations and performance | 1 hour |
| `/products` | GET | Product catalog with metrics | 1 hour |

## Response Format Standards

### Success Response Structure
```json
{
  "status": "success",
  "data": {
    // Endpoint-specific data
  },
  "metadata": {
    "timestamp": "2025-06-21T10:30:00Z",
    "request_id": "req_abc123",
    "processing_time_ms": 145
  }
}
```

### Error Response Structure
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid date format provided",
    "details": "Date must be in ISO 8601 format (YYYY-MM-DD)"
  },
  "metadata": {
    "timestamp": "2025-06-21T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Pagination Format
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total_items": 15000,
    "total_pages": 150,
    "has_next": true,
    "has_prev": false
  },
  "metadata": {...}
}
```

## Core Analytics Endpoints

### 1. Overview Analytics
**GET** `/analytics/overview`

Dashboard KPIs and summary metrics for the overview page.

**Response Data:**
- `total_revenue` - Total revenue in Philippine Pesos
- `transaction_count` - Total number of transactions
- `avg_order_value` - Average order value in PHP
- `customer_count` - Total unique customers
- `revenue_trend` - 6-month revenue trend data
- `top_products` - Top 5 products by revenue
- `ai_insights` - AI-generated business insights

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "total_revenue": 2847392.50,
    "transaction_count": 15000,
    "avg_order_value": 189.83,
    "customer_count": 12750,
    "revenue_trend": [
      {"date": "2025-01-01", "value": 450000.00},
      {"date": "2025-02-01", "value": 475000.00}
    ],
    "top_products": [
      {"name": "Coca-Cola 500ml", "revenue": 125000.00, "rank": 1}
    ],
    "ai_insights": [
      {
        "category": "Operations",
        "message": "Evening peak (6-8 PM) shows 23% higher volume",
        "confidence": 92.5,
        "actions": ["Optimize staffing during peak hours"]
      }
    ]
  }
}
```

### 2. Transaction Data
**GET** `/analytics/transactions`

Transaction data with filtering and pagination support.

**Query Parameters:**
- `limit` (integer, 1-1000, default: 100) - Number of transactions to return
- `offset` (integer, default: 0) - Number of transactions to skip
- `date_from` (date, ISO 8601) - Start date filter
- `date_to` (date, ISO 8601) - End date filter
- `region` (string) - Philippine region filter
- `category` (string) - Product category filter

**Example Request:**
```
GET /analytics/transactions?limit=50&region=NCR&date_from=2025-06-01
```

### 3. Trends Analytics
**GET** `/analytics/trends`

Temporal analysis and regional distribution patterns.

**Response Data:**
- `hourly_volume` - Transaction volume by hour of day
- `regional_distribution` - Transaction distribution by region
- `peak_hours` - Morning, lunch, and evening peak analysis
- `weekly_patterns` - Average transactions by day of week

### 4. Product Analytics
**GET** `/analytics/products`

Product mix and category analysis with brand performance.

**Response Data:**
- `category_distribution` - Product category distribution and revenue
- `brand_performance` - Brand performance ranking
- `top_products` - Top performing products by revenue
- `substitution_summary` - Brand substitution patterns

### 5. Demographics Analytics
**GET** `/analytics/demographics`

Consumer insights and demographic analysis.

**Response Data:**
- `age_distribution` - Customer age group distribution
- `regional_preferences` - Regional product preferences
- `store_performance` - Store-level performance metrics
- `customer_segments` - Customer segmentation analysis

## Data Access Endpoints

### 1. Substitutions Data
**GET** `/substitutions`

Brand substitution patterns and flow analysis.

**Query Parameters:**
- `limit` (integer, default: 100) - Number of substitutions to return
- `brand` (string) - Filter by specific brand
- `category` (string) - Filter by product category

**Response Data:**
- `substitution_flows` - Individual substitution events
- `top_substitutions` - Most common substitution patterns
- `substitution_reasons` - Reason distribution analysis

### 2. Store Data
**GET** `/stores`

Store locations and performance metrics.

**Response Data:**
- `stores` - Store details with location and performance metrics
- `regional_summary` - Regional store performance summary

### 3. Product Data
**GET** `/products`

Product catalog with performance metrics.

**Query Parameters:**
- `category` (string) - Filter by product category
- `brand` (string) - Filter by brand

**Response Data:**
- `products` - Product details with performance metrics
- `category_summary` - Product count by category

## Authentication and Security

### Current Implementation
- **Authentication**: Not required for MVP
- **CORS**: Enabled for dashboard domain
- **Rate Limiting**: 1000 requests per hour per IP
- **HTTPS**: Required for production environment

### Future Security Enhancements
- **API Keys**: Client identification and usage tracking
- **JWT Tokens**: Stateless authentication for enterprise features
- **Role-Based Access**: Granular permissions for different user types
- **OAuth 2.0**: Third-party authentication integration

## Performance Optimization

### Caching Strategy
- **Application Cache**: In-memory caching for frequently accessed data
- **Database Optimization**: Indexed queries and connection pooling
- **CDN Caching**: Edge caching for static responses
- **Cache Invalidation**: Time-based TTL with manual invalidation

### Response Optimization
- **Compression**: Gzip compression for large responses
- **Field Selection**: Optional field filtering to reduce payload size
- **Pagination**: Efficient pagination for large datasets
- **Streaming**: Streaming responses for real-time data

## Error Handling

### HTTP Status Codes
- **200 OK** - Successful request
- **400 Bad Request** - Invalid parameters or request format
- **404 Not Found** - Endpoint or resource not found
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server-side error

### Error Response Codes
- `INVALID_PARAMETER` - Invalid or missing request parameter
- `INVALID_DATE_FORMAT` - Date parameter format error
- `INVALID_REGION` - Unknown Philippine region
- `INVALID_CATEGORY` - Unknown product category
- `DATABASE_ERROR` - Database connectivity or query error
- `INTERNAL_ERROR` - Unexpected server error

## API Usage Examples

### Python Example
```python
import requests

# Get overview analytics
response = requests.get('https://g8h3ilc786zz.manus.space/api/analytics/overview')
data = response.json()

if data['status'] == 'success':
    revenue = data['data']['total_revenue']
    print(f"Total Revenue: ₱{revenue:,.2f}")
else:
    print(f"Error: {data['error']['message']}")
```

### JavaScript Example
```javascript
// Fetch transaction trends
async function getTrends() {
  try {
    const response = await fetch('https://g8h3ilc786zz.manus.space/api/analytics/trends');
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('Peak Hours:', data.data.peak_hours);
    } else {
      console.error('API Error:', data.error.message);
    }
  } catch (error) {
    console.error('Network Error:', error);
  }
}
```

### cURL Example
```bash
# Get filtered transactions
curl -X GET "https://g8h3ilc786zz.manus.space/api/analytics/transactions?region=NCR&limit=10" \
  -H "Accept: application/json"
```

## API Testing

### Health Check Verification
```bash
curl -X GET "https://g8h3ilc786zz.manus.space/api/health"
```

Expected Response:
```json
{
  "status": "success",
  "data": {
    "service": "healthy",
    "database": "connected",
    "version": "3.0",
    "uptime_seconds": 86400
  }
}
```

### Performance Testing
- **Response Time Target**: <200ms for 95th percentile
- **Throughput Target**: 500 requests/second
- **Concurrent Users**: 100+ simultaneous connections
- **Error Rate Target**: <0.1% under normal load

## API Monitoring

### Health Monitoring
- **Endpoint Monitoring**: Automated health checks every 30 seconds
- **Response Time Tracking**: P50, P95, P99 percentile monitoring
- **Error Rate Monitoring**: Real-time error rate tracking
- **Uptime Monitoring**: 24/7 availability monitoring

### Business Metrics
- **API Usage Analytics**: Endpoint usage patterns and trends
- **Client Behavior**: Request patterns and feature utilization
- **Performance Insights**: Slow query identification and optimization
- **Capacity Planning**: Usage growth and scaling requirements

## Future API Enhancements

### Phase 2 Features
- **Real-time Endpoints**: WebSocket-based live data streaming
- **Advanced Filtering**: Complex query capabilities with SQL-like syntax
- **Bulk Operations**: Batch data processing endpoints
- **Export Capabilities**: PDF/Excel report generation

### Phase 3 Capabilities
- **GraphQL Support**: Flexible query language for complex data needs
- **Webhook Integration**: Event-driven notifications and integrations
- **API Versioning**: Backward compatibility with version management
- **Multi-tenant Support**: Client-specific data isolation and customization

