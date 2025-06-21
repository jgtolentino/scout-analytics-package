#!/usr/bin/env python3
"""
Scout Analytics - Azure SQL Database Migration Script
Migrates SQLite data to Azure SQL Database
"""

import argparse
import sqlite3
import pyodbc
import sys
import os
from pathlib import Path
from datetime import datetime

def create_azure_tables(cursor):
    """Create tables in Azure SQL Database if they don't exist"""
    
    # Stores table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='stores' AND xtype='U')
    CREATE TABLE stores (
        store_id INT PRIMARY KEY,
        store_name NVARCHAR(255),
        barangay NVARCHAR(255),
        city NVARCHAR(255),
        province NVARCHAR(255),
        region NVARCHAR(255),
        latitude FLOAT,
        longitude FLOAT,
        store_type NVARCHAR(50)
    )
    """)
    
    # Customers table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='customers' AND xtype='U')
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        age INT,
        gender NVARCHAR(10),
        income_level NVARCHAR(50)
    )
    """)
    
    # Brands table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='brands' AND xtype='U')
    CREATE TABLE brands (
        brand_id INT PRIMARY KEY,
        brand_name NVARCHAR(255),
        category NVARCHAR(255)
    )
    """)
    
    # Products table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='products' AND xtype='U')
    CREATE TABLE products (
        product_id INT PRIMARY KEY,
        product_name NVARCHAR(255),
        brand_id INT,
        category NVARCHAR(255),
        unit_price DECIMAL(10,2),
        FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
    )
    """)
    
    # Transactions table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transactions' AND xtype='U')
    CREATE TABLE transactions (
        transaction_id INT PRIMARY KEY,
        store_id INT,
        customer_id INT,
        transaction_datetime DATETIME,
        total_amount DECIMAL(10,2),
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """)
    
    # Transaction items table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transaction_items' AND xtype='U')
    CREATE TABLE transaction_items (
        item_id INT IDENTITY(1,1) PRIMARY KEY,
        transaction_id INT,
        product_id INT,
        quantity INT,
        unit_price DECIMAL(10,2),
        discount DECIMAL(10,2),
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)
    
    # Substitutions table
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='substitutions' AND xtype='U')
    CREATE TABLE substitutions (
        substitution_id INT IDENTITY(1,1) PRIMARY KEY,
        transaction_id INT,
        original_product_id INT,
        substituted_product_id INT,
        reason NVARCHAR(255),
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
        FOREIGN KEY (original_product_id) REFERENCES products(product_id),
        FOREIGN KEY (substituted_product_id) REFERENCES products(product_id)
    )
    """)
    
    print("✅ Tables created successfully")

def clear_existing_data(azure_conn):
    """Clear existing data from tables (preserve structure)"""
    cursor = azure_conn.cursor()
    
    # Clear data in reverse dependency order
    tables = ['substitutions', 'transaction_items', 'transactions', 
              'customers', 'products', 'brands', 'stores']
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✅ Cleared data from table: {table}")
        except Exception as e:
            print(f"⚠️  Could not clear table {table}: {e}")
    
    azure_conn.commit()
    print("✅ Cleared all existing data")

def migrate_table_data(sqlite_conn, azure_conn, table_name, batch_size=1000):
    """Migrate data from SQLite to Azure SQL for a specific table"""
    print(f"📊 Migrating {table_name}...")
    
    # Get data from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    column_names = ', '.join(columns)
    placeholders = ', '.join(['?' for _ in columns])
    
    azure_cursor = azure_conn.cursor()
    
    # Process in batches
    total_rows = 0
    while True:
        rows = sqlite_cursor.fetchmany(batch_size)
        if not rows:
            break
            
        # Insert batch into Azure SQL
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        try:
            azure_cursor.executemany(insert_sql, rows)
            azure_conn.commit()
            
            total_rows += len(rows)
            print(f"  ✅ Migrated {total_rows} rows to {table_name}")
        except Exception as e:
            print(f"  ❌ Error inserting batch: {e}")
            # Try individual inserts for this batch
            for row in rows:
                try:
                    azure_cursor.execute(insert_sql, row)
                    azure_conn.commit()
                    total_rows += 1
                except Exception as row_error:
                    print(f"  ⚠️  Skipped row due to error: {row_error}")
    
    print(f"✅ Completed migration of {table_name}: {total_rows} total rows")
    return total_rows

def migrate_data(sqlite_path, azure_conn_str):
    """Migrate data from SQLite to Azure SQL"""
    
    # Connect to SQLite
    print("📊 Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    # Connect to Azure SQL
    print("☁️ Connecting to Azure SQL Database...")
    azure_conn = pyodbc.connect(azure_conn_str)
    azure_cursor = azure_conn.cursor()
    
    try:
        # Create tables
        print("📋 Creating tables in Azure SQL...")
        create_azure_tables(azure_cursor)
        azure_conn.commit()
        
        # Clear existing data
        print("🧹 Clearing existing data...")
        clear_existing_data(azure_conn)
        
        # Migration order (respecting foreign key constraints)
        migration_order = [
            'stores',
            'brands', 
            'products',
            'customers',
            'transactions',
            'transaction_items',
            'substitutions'
        ]
        
        total_migrated = 0
        for table in migration_order:
            rows_migrated = migrate_table_data(sqlite_conn, azure_conn, table)
            total_migrated += rows_migrated
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Total rows migrated: {total_migrated:,}")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
        # Verify migration
        print("\n📋 Verification:")
        azure_cursor = azure_conn.cursor()
        for table in migration_order:
            count = azure_cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count:,} rows")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        azure_conn.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate SQLite data to Azure SQL Database')
    parser.add_argument('--server', required=True, help='Azure SQL server name')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--sqlite-path', default='scout_analytics.db', help='Path to SQLite database')
    
    args = parser.parse_args()
    
    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={args.server};"
        f"DATABASE={args.database};"
        f"UID={args.username};"
        f"PWD={args.password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    # Check if SQLite database exists
    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        print("   Please run load_to_sqlite.py first to create the database")
        sys.exit(1)
    
    # Run migration
    try:
        migrate_data(sqlite_path, conn_str)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

