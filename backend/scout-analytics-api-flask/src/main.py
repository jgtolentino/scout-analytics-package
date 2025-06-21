#!/usr/bin/env python3
"""
Scout Analytics Flask API - Cloud Version with Mock Data
Provides mock data for cloud deployment without database dependencies
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "database": "mock", "timestamp": datetime.now().isoformat()})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get mock transactions data"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Generate mock transactions
        transactions = []
        for i in range(min(limit, 50)):  # Limit to 50 for demo
            transaction = {
                "transaction_id": f"TXN_{offset + i + 1:06d}",
                "customer_id": f"CUST_{random.randint(1, 1000):04d}",
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "total_amount": round(random.uniform(50, 500), 2),
                "customer_age": random.randint(18, 65),
                "customer_gender": random.choice(["Male", "Female"]),
                "store_location": random.choice(["Manila", "Cebu", "Davao", "Quezon City", "Makati"]),
                "payment_method": random.choice(["Cash", "Card", "GCash", "PayMaya", "GrabPay"]),
                "region": random.choice(["NCR", "Central Luzon", "Central Visayas", "CALABARZON", "Northern Mindanao"])
            }
            transactions.append(transaction)
        
        return jsonify({
            "transactions": transactions,
            "total": 15000,  # Mock total
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/overview', methods=['GET'])
def get_overview_analytics():
    """Get overview analytics data"""
    try:
        metrics = {
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
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/trends', methods=['GET'])
def get_trends_analytics():
    """Get transaction trends analytics"""
    try:
        # Mock hourly data
        hourly_volume = []
        for hour in range(24):
            count = random.randint(200, 800) if 6 <= hour <= 22 else random.randint(50, 200)
            hourly_volume.append({
                "hour": f"{hour:02d}:00",
                "count": count,
                "amount": round(count * random.uniform(150, 250), 2)
            })
        
        # Mock regional data
        regional_distribution = [
            {"region": "NCR", "count": 5970, "amount": 1133000.00},
            {"region": "Central Luzon", "count": 3060, "amount": 580000.00},
            {"region": "Central Visayas", "count": 2250, "amount": 427000.00},
            {"region": "CALABARZON", "count": 2160, "amount": 410000.00},
            {"region": "Northern Mindanao", "count": 1560, "amount": 297000.00}
        ]
        
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
        categories = [
            {"category": "Beverages", "count": 4250, "revenue": 812456.00},
            {"category": "Food & Snacks", "count": 3630, "revenue": 689234.00},
            {"category": "Personal Care", "count": 2805, "revenue": 532891.00},
            {"category": "Household Items", "count": 2295, "revenue": 435678.00},
            {"category": "Others", "count": 2020, "revenue": 378123.00}
        ]
        
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
        age_distribution = [
            {"age_group": "26-35", "count": 4680, "avg_amount": 189.83},
            {"age_group": "36-45", "count": 4320, "avg_amount": 195.45},
            {"age_group": "18-25", "count": 3375, "avg_amount": 167.20},
            {"age_group": "46-55", "count": 1815, "avg_amount": 210.15},
            {"age_group": "55+", "count": 810, "avg_amount": 225.80}
        ]
        
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
    app.run(host="0.0.0.0", port=5000, debug=True)

