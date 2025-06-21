#!/usr/bin/env python3
"""
SQLite Database Loader for Scout Analytics - Updated with correct schemas
Loads enhanced CSV data into SQLite database for local development
"""

import sqlite3
import pandas as pd
import argparse
import os
from pathlib import Path

def create_tables(cursor):
    """Create all necessary tables with proper schema matching actual CSV structure"""
    
    # Stores table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stores (
        store_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT,
        barangay TEXT,
        city TEXT,
        region TEXT,
        latitude REAL,
        longitude REAL,
        store_type TEXT,
        opening_hours TEXT,
        contact_number TEXT
    )
    ''')
    
    # Brands table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS brands (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        country_origin TEXT,
        established_year INTEGER,
        market_share REAL
    )
    ''')
    
    # Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        brand_id TEXT,
        brand_name TEXT,
        price REAL,
        sku TEXT,
        barcode TEXT,
        weight_grams INTEGER,
        in_stock INTEGER,
        stock_quantity INTEGER,
        supplier TEXT
    )
    ''')
    
    # Customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        age INTEGER,
        gender TEXT,
        region TEXT,
        city TEXT,
        barangay TEXT,
        registration_date TEXT,
        total_transactions INTEGER,
        total_spent REAL,
        avg_transaction_amount REAL,
        preferred_payment_method TEXT,
        loyalty_tier TEXT,
        email TEXT,
        phone TEXT
    )
    ''')
    
    # Devices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY,
        store_id TEXT,
        device_type TEXT,
        model TEXT,
        serial_number TEXT,
        installation_date TEXT,
        last_maintenance TEXT,
        status TEXT,
        software_version TEXT,
        total_transactions INTEGER,
        avg_response_time_ms REAL,
        uptime_percentage REAL
    )
    ''')
    
    # Transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        customer_id TEXT,
        created_at TEXT,
        total_amount REAL,
        customer_age INTEGER,
        customer_gender TEXT,
        store_location TEXT,
        store_id TEXT,
        checkout_seconds REAL,
        is_weekend INTEGER,
        nlp_processed INTEGER,
        nlp_processed_at TEXT,
        nlp_confidence_score REAL,
        device_id TEXT,
        payment_method TEXT,
        checkout_time TEXT,
        request_type TEXT,
        transcription_text TEXT,
        suggestion_accepted INTEGER,
        region TEXT,
        city TEXT,
        barangay TEXT
    )
    ''')
    
    # Transaction Items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_items (
        id TEXT PRIMARY KEY,
        transaction_id TEXT,
        product_id TEXT,
        quantity INTEGER,
        unit_price REAL,
        total_price REAL,
        discount_amount REAL,
        tax_amount REAL,
        line_number INTEGER
    )
    ''')
    
    # Request Behaviors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS request_behaviors (
        request_id TEXT PRIMARY KEY,
        transaction_id TEXT,
        device_id TEXT,
        request_method TEXT,
        timestamp TEXT,
        response_time_ms REAL,
        success INTEGER,
        confidence_score REAL
    )
    ''')
    
    # Substitutions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS substitutions (
        substitution_id TEXT PRIMARY KEY,
        transaction_id TEXT,
        original_product_id TEXT,
        substituted_product_id TEXT,
        reason TEXT,
        timestamp TEXT
    )
    ''')

def load_csv_to_table(csv_path, table_name, cursor, conn):
    """Load CSV data into specified table"""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found, skipping {table_name}")
        return 0
    
    try:
        df = pd.read_csv(csv_path)
        
        # Clean column names (remove spaces, special chars)
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
        
        # Insert data
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
        row_count = len(df)
        print(f"✅ Loaded {row_count:,} rows into {table_name}")
        return row_count
        
    except Exception as e:
        print(f"❌ Error loading {table_name}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Load Scout Analytics CSV data into SQLite')
    parser.add_argument('--csv_dir', required=True, help='Directory containing CSV files')
    parser.add_argument('--db_path', required=True, help='Output SQLite database path')
    
    args = parser.parse_args()
    
    csv_dir = Path(args.csv_dir)
    db_path = Path(args.db_path)
    
    # Create database directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print(f"🗑️  Removed existing database: {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print(f"📊 Creating Scout Analytics database: {db_path}")
    
    # Create tables
    create_tables(cursor)
    print("✅ Created database schema")
    
    # Load data in dependency order
    tables_to_load = [
        ('stores.csv', 'stores'),
        ('brands.csv', 'brands'),
        ('products.csv', 'products'),
        ('customers.csv', 'customers'),
        ('devices.csv', 'devices'),
        ('transactions.csv', 'transactions'),
        ('transaction_items.csv', 'transaction_items'),
        ('request_behaviors.csv', 'request_behaviors'),
        ('substitutions.csv', 'substitutions')
    ]
    
    total_rows = 0
    for csv_file, table_name in tables_to_load:
        csv_path = csv_dir / csv_file
        rows_loaded = load_csv_to_table(csv_path, table_name, cursor, conn)
        total_rows += rows_loaded
    
    # Commit changes
    conn.commit()
    
    # Print summary
    print(f"\n🎉 Database loading complete!")
    print(f"📁 Database: {db_path}")
    print(f"📊 Total rows loaded: {total_rows:,}")
    
    # Verify data
    print(f"\n📋 Table Summary:")
    for _, table_name in tables_to_load:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count:,} records")
        except:
            print(f"   {table_name}: ❌ error")
    
    conn.close()
    print(f"\n✅ Ready for local development!")
    print(f"🚀 Next: cd scout-analytics-api && uvicorn main:app --reload --port 8000")

if __name__ == "__main__":
    main()

