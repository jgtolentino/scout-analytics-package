# Scout Analytics - Data Model and Architecture

## Data Architecture Overview

Scout Analytics implements a comprehensive data architecture designed to support retail intelligence analytics for the Philippine market. The data model emphasizes authenticity, scalability, and analytical performance while maintaining data quality and consistency.

## Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Customers     │    │  Transactions   │    │     Stores      │
│                 │    │                 │    │                 │
│ • customer_id   │◄──►│ • transaction_id│◄──►│ • store_id      │
│ • age_group     │    │ • customer_id   │    │ • store_name    │
│ • region        │    │ • store_id      │    │ • location      │
│ • preferences   │    │ • total_amount  │    │ • region        │
└─────────────────┘    │ • payment_method│    │ • performance   │
                       │ • region        │    └─────────────────┘
                       │ • created_at    │
                       └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │ Transaction     │
                       │     Items       │
                       │                 │
                       │ • item_id       │
                       │ • transaction_id│◄──┐
                       │ • product_id    │   │
                       │ • quantity      │   │
                       │ • unit_price    │   │
                       │ • total_price   │   │
                       └─────────────────┘   │
                                │            │
                                ▼            │
                       ┌─────────────────┐   │
                       │    Products     │   │
                       │                 │   │
                       │ • product_id    │   │
                       │ • product_name  │   │
                       │ • category      │   │
                       │ • brand         │   │
                       │ • unit_price    │   │
                       └─────────────────┘   │
                                │            │
                                ▼            │
                       ┌─────────────────┐   │
                       │  Substitutions  │   │
                       │                 │   │
                       │ • substitution_id│  │
                       │ • transaction_id│◄──┘
                       │ • original_prod │
                       │ • substitute_prod│
                       │ • reason        │
                       │ • created_at    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Request         │
                       │  Behaviors      │
                       │                 │
                       │ • request_id    │
                       │ • transaction_id│
                       │ • request_type  │
                       │ • product_id    │
                       │ • fulfilled     │
                       │ • created_at    │
                       └─────────────────┘
```

## Core Data Entities

### Transactions Table
Primary transaction records capturing all retail interactions.

```sql
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    store_id UUID NOT NULL,
    transaction_date DATETIME NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_region (region),
    INDEX idx_store_date (store_id, transaction_date),
    INDEX idx_customer (customer_id)
);
```

**Key Attributes:**
- `transaction_id` - Unique identifier for each transaction
- `customer_id` - Links to customer demographics
- `store_id` - Links to store location and performance data
- `transaction_date` - Timestamp for temporal analysis
- `total_amount` - Transaction value in Philippine Pesos
- `payment_method` - Cash, Card, GCash, PayMaya, GrabPay
- `region` - Philippine region for geographic analysis

### Products Table
Product catalog with category and brand information.

```sql
CREATE TABLE products (
    product_id UUID PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    unit_price DECIMAL(8,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_brand (brand),
    INDEX idx_category_brand (category, brand)
);
```

**Key Attributes:**
- `product_id` - Unique product identifier
- `product_name` - Full product name
- `category` - Product category (Beverages, Food & Snacks, etc.)
- `brand` - Brand name for substitution analysis
- `unit_price` - Standard retail price in PHP

### Transaction Items Table
Line-item details for each transaction.

```sql
CREATE TABLE transaction_items (
    item_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(8,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    INDEX idx_transaction (transaction_id),
    INDEX idx_product (product_id),
    INDEX idx_transaction_product (transaction_id, product_id)
);
```

### Substitutions Table
Brand and product substitution events.

```sql
CREATE TABLE substitutions (
    substitution_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    original_product_id UUID NOT NULL,
    substitute_product_id UUID NOT NULL,
    reason VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (original_product_id) REFERENCES products(product_id),
    FOREIGN KEY (substitute_product_id) REFERENCES products(product_id),
    
    INDEX idx_transaction (transaction_id),
    INDEX idx_original_product (original_product_id),
    INDEX idx_substitute_product (substitute_product_id),
    INDEX idx_reason (reason)
);
```

**Substitution Reasons:**
- "Out of stock" - Product unavailable
- "Promotion" - Promotional offer on substitute
- "Price difference" - Customer chose cheaper alternative
- "Customer preference" - Customer preference change

### Request Behaviors Table
Customer request patterns and fulfillment tracking.

```sql
CREATE TABLE request_behaviors (
    request_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    request_type VARCHAR(100) NOT NULL,
    product_id UUID,
    fulfilled BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    
    INDEX idx_transaction (transaction_id),
    INDEX idx_request_type (request_type),
    INDEX idx_fulfilled (fulfilled)
);
```

**Request Types:**
- "Branded" - Specific brand request
- "Unbranded" - Generic product request
- "Pointing" - Customer pointing to product

## Data Quality Standards

### Philippine Market Authenticity

#### Regional Distribution
Authentic Philippine regional representation based on population and economic activity:

| Region | Percentage | Transaction Count | Validation Status |
|--------|------------|-------------------|-------------------|
| NCR (Metro Manila) | 39.8% | 5,970 | ✅ Authentic |
| Central Luzon | 20.4% | 3,060 | ✅ Authentic |
| Central Visayas | 15.0% | 2,250 | ✅ Authentic |
| CALABARZON | 14.4% | 2,160 | ✅ Authentic |
| Northern Mindanao | 10.4% | 1,560 | ✅ Authentic |

#### Payment Method Distribution
Reflects actual Philippine payment preferences:

| Payment Method | Percentage | Usage Pattern | Market Reality |
|----------------|------------|---------------|----------------|
| Cash | 40.3% | High in rural areas | ✅ Accurate |
| Credit/Debit Card | 25.2% | Urban preference | ✅ Accurate |
| GCash | 19.8% | Growing digital adoption | ✅ Accurate |
| PayMaya | 9.8% | Secondary digital wallet | ✅ Accurate |
| GrabPay | 4.9% | Urban, tech-savvy users | ✅ Accurate |

#### Product Category Mix
Typical Philippine retail distribution:

| Category | Percentage | Revenue Share | Authenticity |
|----------|------------|---------------|--------------|
| Beverages | 28.5% | 31.2% | ✅ Realistic |
| Food & Snacks | 24.2% | 26.8% | ✅ Realistic |
| Personal Care | 18.7% | 19.4% | ✅ Realistic |
| Household Items | 15.3% | 14.1% | ✅ Realistic |
| Others | 13.3% | 8.5% | ✅ Realistic |

### Temporal Pattern Authenticity

#### Daily Transaction Patterns
Realistic Philippine shopping behavior:

| Time Period | Peak Hours | Transaction Count | Pattern Type |
|-------------|------------|-------------------|--------------|
| Morning Peak | 6-9 AM | 2,847 | Commuter shopping |
| Lunch Peak | 11 AM-2 PM | 3,456 | Lunch break shopping |
| Evening Peak | 6-8 PM | 4,123 | After-work shopping |
| Late Evening | 8-10 PM | 1,892 | Convenience shopping |

#### Weekly Patterns
Authentic weekly retail cycles:

| Day Type | Avg Transactions/Day | AOV (PHP) | Shopping Behavior |
|----------|---------------------|-----------|-------------------|
| Weekdays | 2,100 | 195.50 | Routine purchases |
| Weekends | 2,480 | 172.30 | Family shopping |

### Demographic Authenticity

#### Age Distribution
Reflects Philippine consumer demographics:

| Age Group | Percentage | Count | Shopping Characteristics |
|-----------|------------|-------|-------------------------|
| 18-25 years | 22.5% | 3,375 | Price-conscious, digital |
| 26-35 years | 31.2% | 4,680 | Highest AOV, brand-aware |
| 36-45 years | 28.8% | 4,320 | Family-focused, bulk buying |
| 46-55 years | 12.1% | 1,815 | Quality-focused, loyal |
| 55+ years | 5.4% | 810 | Traditional preferences |

## Data Volume Requirements

### Validated Minimums
Based on implementation experience and analytical requirements:

#### Transaction Data
- **Minimum Viable**: 2,000 transactions
- **Recommended**: 10,000 transactions
- **Implemented**: 15,000 transactions ✅
- **Status**: Exceeds recommendations
- **Validation**: Sufficient density for temporal, regional, and categorical analysis

#### Substitution Events
- **Minimum Viable**: 500 substitutions
- **Recommended**: 1,000 substitutions
- **Implemented**: 1,500 substitutions ✅
- **Status**: Exceeds recommendations
- **Validation**: Enables meaningful brand switching analysis and Sankey diagrams

#### Request Behaviors
- **Minimum Viable**: 500 request behaviors
- **Recommended**: 1,000 request behaviors
- **Implemented**: 2,000 request behaviors ✅
- **Status**: Exceeds recommendations
- **Validation**: Supports comprehensive customer interaction analysis

#### Geographic Coverage
- **Minimum Regions**: 3 Philippine regions
- **Recommended**: 5 Philippine regions
- **Implemented**: 5 regions ✅
- **Coverage**: NCR, Central Luzon, Central Visayas, CALABARZON, Northern Mindanao

#### Product Diversity
- **Minimum Products**: 30 products
- **Recommended**: 50 products
- **Implemented**: 60 products ✅
- **Categories**: 10 distinct categories
- **Brands**: 36 authentic brands

## Data Processing Pipeline

### Ingestion Strategy
- **Source Format**: CSV files with standardized schemas
- **Validation Rules**: Data type checking, range validation, referential integrity
- **Error Handling**: Comprehensive logging with data quality reports
- **Transformation**: Pandas-based ETL with statistical validation

### Storage Optimization
- **Indexing Strategy**: Composite indexes on date, region, product_category
- **Partitioning**: Date-based partitioning for temporal queries
- **Compression**: Database-level compression for historical data
- **Archival**: Automated archival of data older than 2 years

### Analytics Preparation
- **Aggregation Tables**: Pre-computed hourly, daily, weekly, monthly summaries
- **Materialized Views**: Regional performance, category analysis, customer segments
- **Real-time Processing**: Incremental updates for dashboard metrics
- **Cache Warming**: Automated cache population for common queries

## Data Governance

### Data Quality Monitoring
- **Automated Validation**: Daily data quality checks
- **Anomaly Detection**: Statistical outlier identification
- **Completeness Checks**: Missing data identification and reporting
- **Consistency Validation**: Cross-table referential integrity

### Data Privacy and Security
- **Data Anonymization**: Customer data anonymization for analytics
- **Access Controls**: Role-based access to sensitive data
- **Audit Logging**: Comprehensive data access logging
- **Retention Policies**: Configurable data retention periods

### Performance Monitoring
- **Query Performance**: Execution time monitoring and optimization
- **Storage Utilization**: Database size and growth tracking
- **Index Effectiveness**: Index usage analysis and optimization
- **Cache Hit Rates**: Caching effectiveness monitoring

## Future Data Architecture

### Phase 2 Enhancements
- **Real-time Data Streaming**: WebSocket-based live data ingestion
- **Advanced Analytics**: Machine learning model integration
- **External Data Sources**: Weather, social media, competitive data
- **Data Lake Architecture**: Scalable storage for diverse data types

### Phase 3 Scalability
- **Multi-tenant Data Model**: Support for multiple retail clients
- **Geographic Expansion**: Multi-country data models
- **Advanced Partitioning**: Horizontal scaling strategies
- **Data Mesh Architecture**: Decentralized data ownership model

