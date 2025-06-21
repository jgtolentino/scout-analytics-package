#!/usr/bin/env python3
"""
Scout Analytics Flask API - Database Version
Supports both SQLite (local) and Azure SQL Database (production)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import random
import pyodbc
from urllib.parse import quote_plus

app = Flask(__name__)

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_SCHEMA = os.environ.get('DATABASE_SCHEMA', 'dbo')
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'scout_analytics.db')

def get_db_connection():
    """Get database connection based on environment"""
    if DATABASE_URL and 'mssql' in DATABASE_URL:
        # Azure SQL Database
        return pyodbc.connect(DATABASE_URL)
    else:
        # SQLite (local development)
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            return None

def execute_query(query, params=None):
    """Execute query with proper schema handling"""
    conn = get_db_connection()
    
    if conn is None:
        # Return mock data if no database available
        return None
    
    try:
        if isinstance(conn, pyodbc.Connection):
            # Azure SQL - prepend schema to table names
            if DATABASE_SCHEMA != 'dbo':
                # Simple table name replacement for common tables
                tables = ['stores', 'customers', 'brands', 'products', 'transactions', 
                         'transaction_items', 'substitutions']
                for table in tables:
                    query = query.replace(f' {table}', f' {DATABASE_SCHEMA}.{table}')
                    query = query.replace(f'FROM {table}', f'FROM {DATABASE_SCHEMA}.{table}')
                    query = query.replace(f'JOIN {table}', f'JOIN {DATABASE_SCHEMA}.{table}')
            
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convert to list of dicts for consistency
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            # SQLite
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_mock_data():
    """Return mock data when database is not available"""
    return {
        "transactions": [
            {
                "transaction_id": f"TXN_{i+1:06d}",
                "customer_id": f"CUST_{random.randint(1, 1000):04d}",
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "total_amount": round(random.uniform(50, 500), 2),
                "customer_age": random.randint(18, 65),
                "customer_gender": random.choice(["Male", "Female"]),
                "store_location": random.choice(["Manila", "Cebu", "Davao", "Quezon City", "Makati"]),
                "payment_method": random.choice(["Cash", "Card", "GCash", "PayMaya", "GrabPay"]),
                "region": random.choice(["NCR", "Central Luzon", "Central Visayas", "CALABARZON", "Northern Mindanao"])
            } for i in range(20)
        ]
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    database_status = "connected" if get_db_connection() else "mock"
    return jsonify({
        "status": "ok", 
        "database": database_status, 
        "timestamp": datetime.now().isoformat(),
        "schema": DATABASE_SCHEMA if DATABASE_URL else "sqlite"
    })

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get transactions data"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Try database first
        query = """
        SELECT t.transaction_id, t.customer_id, t.transaction_datetime as created_at,
               t.total_amount, c.age as customer_age, c.gender as customer_gender,
               s.city as store_location, s.region
        FROM transactions t
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        LEFT JOIN stores s ON t.store_id = s.store_id
        ORDER BY t.transaction_datetime DESC
        LIMIT ? OFFSET ?
        """
        
        results = execute_query(query, (limit, offset))
        
        if results:
            # Add mock payment methods since we don't have that in our schema
            for result in results:
                result['payment_method'] = random.choice(["Cash", "Card", "GCash", "PayMaya", "GrabPay"])
            
            total_query = "SELECT COUNT(*) as total FROM transactions"
            total_result = execute_query(total_query)
            total = total_result[0]['total'] if total_result else len(results)
            
            return jsonify({
                "transactions": results,
                "total": total,
                "limit": limit,
                "offset": offset
            })
        else:
            # Fallback to mock data
            mock_data = get_mock_data()
            return jsonify({
                "transactions": mock_data["transactions"][:limit],
                "total": 15000,
                "limit": limit,
                "offset": offset
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/overview', methods=['GET'])
def get_overview_analytics():
    """Get overview analytics data"""
    try:
        # Try database queries
        overview_query = """
        SELECT 
            COUNT(*) as total_transactions,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM transactions
        """
        
        results = execute_query(overview_query)
        
        if results:
            metrics = results[0]
            
            # Get top products
            products_query = """
            SELECT p.product_name as name, SUM(ti.quantity * ti.unit_price) as revenue
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY revenue DESC
            LIMIT 5
            """
            
            top_products = execute_query(products_query) or []
            
            # Get revenue trend (mock for now)
            revenue_trend = [
                {"month": "Jan 2025", "revenue": float(metrics.get('total_revenue', 0)) * 0.8},
                {"month": "Feb 2025", "revenue": float(metrics.get('total_revenue', 0)) * 0.85},
                {"month": "Mar 2025", "revenue": float(metrics.get('total_revenue', 0)) * 0.9},
                {"month": "Apr 2025", "revenue": float(metrics.get('total_revenue', 0)) * 0.95},
                {"month": "May 2025", "revenue": float(metrics.get('total_revenue', 0)) * 0.98},
                {"month": "Jun 2025", "revenue": float(metrics.get('total_revenue', 0))}
            ]
            
            return jsonify({
                "total_transactions": metrics['total_transactions'],
                "total_revenue": float(metrics['total_revenue']) if metrics['total_revenue'] else 0,
                "avg_order_value": float(metrics['avg_order_value']) if metrics['avg_order_value'] else 0,
                "unique_customers": metrics['unique_customers'],
                "top_products": top_products,
                "revenue_trend": revenue_trend
            })
        else:
            # Fallback to mock data
            return jsonify({
                "total_transactions": 15000,
                "total_revenue": 2847392.50,
                "avg_order_value": 189.83,
                "unique_customers": 12750,
                "top_products": [
                    {"name": "Coca-Cola 330ml", "revenue": 245000.00},
                    {"name": "Lucky Me Instant Noodles", "revenue": 189500.00},
                    {"name": "Tide Detergent", "revenue": 156200.00},
                    {"name": "Nestle Coffee", "revenue": 134800.00},
                    {"name": "Palmolive Soap", "revenue": 98600.00}
                ],
                "revenue_trend": [
                    {"month": "Jan 2025", "revenue": 2400000.00},
                    {"month": "Feb 2025", "revenue": 2520000.00},
                    {"month": "Mar 2025", "revenue": 2680000.00},
                    {"month": "Apr 2025", "revenue": 2750000.00},
                    {"month": "May 2025", "revenue": 2820000.00},
                    {"month": "Jun 2025", "revenue": 2847392.50}
                ]
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/trends', methods=['GET'])
def get_trends_analytics():
    """Get transaction trends analytics"""
    try:
        # Regional distribution from database
        regional_query = """
        SELECT s.region, COUNT(*) as count, SUM(t.total_amount) as amount
        FROM transactions t
        JOIN stores s ON t.store_id = s.store_id
        GROUP BY s.region
        ORDER BY count DESC
        """
        
        regional_data = execute_query(regional_query)
        
        if regional_data:
            # Convert to expected format
            regional_distribution = [
                {
                    "region": row['region'],
                    "count": row['count'],
                    "amount": float(row['amount'])
                } for row in regional_data
            ]
        else:
            # Mock regional data
            regional_distribution = [
                {"region": "NCR", "count": 5970, "amount": 1133000.00},
                {"region": "Central Luzon", "count": 3060, "amount": 580000.00},
                {"region": "Central Visayas", "count": 2250, "amount": 427000.00},
                {"region": "CALABARZON", "count": 2160, "amount": 410000.00},
                {"region": "Northern Mindanao", "count": 1560, "amount": 297000.00}
            ]
        
        # Mock hourly data (would need datetime parsing for real implementation)
        hourly_volume = []
        for hour in range(24):
            count = random.randint(200, 800) if 6 <= hour <= 22 else random.randint(50, 200)
            hourly_volume.append({
                "hour": f"{hour:02d}:00",
                "count": count,
                "amount": round(count * random.uniform(150, 250), 2)
            })
        
        return jsonify({
            "hourly": hourly_volume,
            "regional": regional_distribution
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/products', methods=['GET'])
def get_product_analytics():
    """Get product mix analytics"""
    try:
        # Try to get categories from database
        categories_query = """
        SELECT p.category, COUNT(*) as count, SUM(ti.quantity * ti.unit_price) as revenue
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
        """
        
        categories_data = execute_query(categories_query)
        
        if categories_data:
            categories = [
                {
                    "category": row['category'],
                    "count": row['count'],
                    "revenue": float(row['revenue'])
                } for row in categories_data
            ]
        else:
            # Mock categories
            categories = [
                {"category": "Beverages", "count": 4250, "revenue": 812456.00},
                {"category": "Food & Snacks", "count": 3630, "revenue": 689234.00},
                {"category": "Personal Care", "count": 2805, "revenue": 532891.00},
                {"category": "Household Items", "count": 2295, "revenue": 435678.00},
                {"category": "Others", "count": 2020, "revenue": 378123.00}
            ]
        
        # Get substitutions from database
        substitutions_query = """
        SELECT p1.product_name as from_product, p2.product_name as to_product, COUNT(*) as count
        FROM substitutions s
        JOIN products p1 ON s.original_product_id = p1.product_id
        JOIN products p2 ON s.substituted_product_id = p2.product_id
        GROUP BY p1.product_name, p2.product_name
        ORDER BY count DESC
        LIMIT 5
        """
        
        substitutions_data = execute_query(substitutions_query)
        
        if substitutions_data:
            top_substitutions = [
                {
                    "from": row['from_product'],
                    "to": row['to_product'],
                    "count": row['count']
                } for row in substitutions_data
            ]
        else:
            # Mock substitutions
            top_substitutions = [
                {"from": "Coca-Cola", "to": "Pepsi", "count": 234},
                {"from": "Lucky Me", "to": "Nissin", "count": 189},
                {"from": "Tide", "to": "Surf", "count": 156}
            ]
        
        return jsonify({
            "categories": categories,
            "substitutions": top_substitutions
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/consumers', methods=['GET'])
def get_consumer_analytics():
    """Get consumer insights analytics"""
    try:
        # Age distribution from database
        age_query = """
        SELECT 
            CASE 
                WHEN age BETWEEN 18 AND 25 THEN '18-25'
                WHEN age BETWEEN 26 AND 35 THEN '26-35'
                WHEN age BETWEEN 36 AND 45 THEN '36-45'
                WHEN age BETWEEN 46 AND 55 THEN '46-55'
                ELSE '55+'
            END as age_group,
            COUNT(*) as count,
            AVG(t.total_amount) as avg_amount
        FROM customers c
        JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY CASE 
            WHEN age BETWEEN 18 AND 25 THEN '18-25'
            WHEN age BETWEEN 26 AND 35 THEN '26-35'
            WHEN age BETWEEN 36 AND 45 THEN '36-45'
            WHEN age BETWEEN 46 AND 55 THEN '46-55'
            ELSE '55+'
        END
        ORDER BY count DESC
        """
        
        age_data = execute_query(age_query)
        
        if age_data:
            age_distribution = [
                {
                    "age_group": row['age_group'],
                    "count": row['count'],
                    "avg_amount": float(row['avg_amount'])
                } for row in age_data
            ]
        else:
            # Mock age distribution
            age_distribution = [
                {"age_group": "26-35", "count": 4680, "avg_amount": 189.83},
                {"age_group": "36-45", "count": 4320, "avg_amount": 195.45},
                {"age_group": "18-25", "count": 3375, "avg_amount": 167.20},
                {"age_group": "46-55", "count": 1815, "avg_amount": 210.15},
                {"age_group": "55+", "count": 810, "avg_amount": 225.80}
            ]
        
        # Store locations from database
        stores_query = """
        SELECT store_name as name, city, region, latitude as lat, longitude as lng
        FROM stores
        LIMIT 10
        """
        
        stores_data = execute_query(stores_query)
        
        if stores_data:
            store_locations = [
                {
                    "name": row['name'],
                    "city": row['city'],
                    "region": row['region'],
                    "lat": float(row['lat']) if row['lat'] else 0,
                    "lng": float(row['lng']) if row['lng'] else 0
                } for row in stores_data
            ]
        else:
            # Mock store locations
            store_locations = [
                {"name": "Metro Manila Store", "city": "Manila", "region": "NCR", "lat": 14.5995, "lng": 120.9842},
                {"name": "Cebu Store", "city": "Cebu", "region": "Central Visayas", "lat": 10.3157, "lng": 123.8854},
                {"name": "Davao Store", "city": "Davao", "region": "Davao Region", "lat": 7.1907, "lng": 125.4553}
            ]
        
        return jsonify({
            "age_groups": age_distribution,
            "stores": store_locations
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ask', methods=['GET'])
def ask_ai():
    """AI chat endpoint (mock response)"""
    prompt = request.args.get('prompt', '')
    
    responses = [
        f"Based on the Scout Analytics data, here are insights about: {prompt}",
        f"The transaction patterns show interesting trends related to: {prompt}",
        f"From a retail perspective, {prompt} indicates strong performance in key metrics.",
        f"The data suggests that {prompt} is an important factor in customer behavior."
    ]
    
    return jsonify({
        "response": random.choice(responses),
        "confidence": round(random.uniform(0.7, 0.95), 2),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)