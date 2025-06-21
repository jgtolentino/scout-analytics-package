#!/usr/bin/env python3
"""
Scout Analytics - Migrate to MVP Schema in Azure SQL Database
Specialized script for migrating data to the 'mvp' schema
"""

import argparse
import sqlite3
import pyodbc
import sys
import os
from pathlib import Path
from datetime import datetime

def create_mvp_schema_tables(cursor):
    """Create tables in the mvp schema"""
    
    print("📋 Creating MVP schema and tables...")
    
    # Create schema
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mvp')
    BEGIN
        EXEC('CREATE SCHEMA mvp')
    END
    """)
    
    # Create all tables with mvp schema prefix
    tables_sql = """
    -- Stores table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'stores')
    CREATE TABLE mvp.stores (
        store_id INT PRIMARY KEY,
        store_name NVARCHAR(255),
        barangay NVARCHAR(255),
        city NVARCHAR(255),
        province NVARCHAR(255),
        region NVARCHAR(255),
        latitude FLOAT,
        longitude FLOAT,
        store_type NVARCHAR(50)
    );

    -- Customers table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'customers')
    CREATE TABLE mvp.customers (
        customer_id INT PRIMARY KEY,
        age INT,
        gender NVARCHAR(10),
        income_level NVARCHAR(50)
    );

    -- Brands table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'brands')
    CREATE TABLE mvp.brands (
        brand_id INT PRIMARY KEY,
        brand_name NVARCHAR(255),
        category NVARCHAR(255)
    );

    -- Products table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'products')
    CREATE TABLE mvp.products (
        product_id INT PRIMARY KEY,
        product_name NVARCHAR(255),
        brand_id INT,
        category NVARCHAR(255),
        unit_price DECIMAL(10,2),
        FOREIGN KEY (brand_id) REFERENCES mvp.brands(brand_id)
    );

    -- Transactions table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'transactions')
    CREATE TABLE mvp.transactions (
        transaction_id INT PRIMARY KEY,
        store_id INT,
        customer_id INT,
        transaction_datetime DATETIME,
        total_amount DECIMAL(10,2),
        FOREIGN KEY (store_id) REFERENCES mvp.stores(store_id),
        FOREIGN KEY (customer_id) REFERENCES mvp.customers(customer_id)
    );

    -- Transaction items table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'transaction_items')
    CREATE TABLE mvp.transaction_items (
        item_id INT IDENTITY(1,1) PRIMARY KEY,
        transaction_id INT,
        product_id INT,
        quantity INT,
        unit_price DECIMAL(10,2),
        discount DECIMAL(10,2),
        FOREIGN KEY (transaction_id) REFERENCES mvp.transactions(transaction_id),
        FOREIGN KEY (product_id) REFERENCES mvp.products(product_id)
    );

    -- Substitutions table
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE schema_id = SCHEMA_ID('mvp') AND name = 'substitutions')
    CREATE TABLE mvp.substitutions (
        substitution_id INT IDENTITY(1,1) PRIMARY KEY,
        transaction_id INT,
        original_product_id INT,
        substituted_product_id INT,
        reason NVARCHAR(255),
        FOREIGN KEY (transaction_id) REFERENCES mvp.transactions(transaction_id),
        FOREIGN KEY (original_product_id) REFERENCES mvp.products(product_id),
        FOREIGN KEY (substituted_product_id) REFERENCES mvp.products(product_id)
    );
    """
    
    # Execute each statement separately
    for statement in tables_sql.split(';'):
        if statement.strip():
            cursor.execute(statement)
    
    print("✅ MVP schema and tables created successfully")

def clear_mvp_data(azure_conn):
    """Clear existing data from mvp schema tables"""
    cursor = azure_conn.cursor()
    
    # Clear data in reverse dependency order
    tables = ['mvp.substitutions', 'mvp.transaction_items', 'mvp.transactions', 
              'mvp.customers', 'mvp.products', 'mvp.brands', 'mvp.stores']
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✅ Cleared data from table: {table}")
        except Exception as e:
            print(f"⚠️  Could not clear table {table}: {e}")
    
    azure_conn.commit()
    print("✅ Cleared all existing data from MVP schema")

def migrate_table_to_mvp(sqlite_conn, azure_conn, table_name, batch_size=1000):
    """Migrate data from SQLite to Azure SQL mvp schema"""
    print(f"📊 Migrating {table_name} to mvp.{table_name}...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    column_names = ', '.join(columns)
    placeholders = ', '.join(['?' for _ in columns])
    
    azure_cursor = azure_conn.cursor()
    
    # Handle identity columns for transaction_items and substitutions
    if table_name in ['transaction_items', 'substitutions']:
        # Remove item_id/substitution_id from insert
        if 'item_id' in columns:
            columns.remove('item_id')
        if 'substitution_id' in columns:
            columns.remove('substitution_id')
        column_names = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
    
    total_rows = 0
    while True:
        rows = sqlite_cursor.fetchmany(batch_size)
        if not rows:
            break
        
        # Remove identity column values if present
        if table_name in ['transaction_items', 'substitutions']:
            rows = [row[1:] for row in rows]  # Skip first column (identity)
        
        insert_sql = f"INSERT INTO mvp.{table_name} ({column_names}) VALUES ({placeholders})"
        
        try:
            azure_cursor.executemany(insert_sql, rows)
            azure_conn.commit()
            total_rows += len(rows)
            print(f"  ✅ Migrated {total_rows} rows to mvp.{table_name}")
        except Exception as e:
            print(f"  ❌ Error inserting batch: {e}")
            # Try individual inserts
            for row in rows:
                try:
                    azure_cursor.execute(insert_sql, row)
                    azure_conn.commit()
                    total_rows += 1
                except Exception as row_error:
                    print(f"  ⚠️  Skipped row due to error: {row_error}")
    
    print(f"✅ Completed migration of mvp.{table_name}: {total_rows} total rows")
    return total_rows

def migrate_to_mvp_schema(sqlite_path, azure_conn_str):
    """Main migration function for MVP schema"""
    
    print("🚀 Starting Scout Analytics data migration to MVP schema")
    print("=" * 60)
    
    # Connect to SQLite
    print("📊 Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    # Connect to Azure SQL
    print("☁️ Connecting to Azure SQL Database...")
    azure_conn = pyodbc.connect(azure_conn_str)
    azure_cursor = azure_conn.cursor()
    
    try:
        # Create MVP schema and tables
        create_mvp_schema_tables(azure_cursor)
        azure_conn.commit()
        
        # Clear existing data
        print("\n🧹 Clearing existing data...")
        clear_mvp_data(azure_conn)
        
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
        
        print("\n📤 Starting data migration...")
        total_migrated = 0
        for table in migration_order:
            rows_migrated = migrate_table_to_mvp(sqlite_conn, azure_conn, table)
            total_migrated += rows_migrated
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Total rows migrated: {total_migrated:,}")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
        # Verify migration
        print("\n📋 Verification:")
        for table in migration_order:
            count = azure_cursor.execute(f"SELECT COUNT(*) FROM mvp.{table}").fetchone()[0]
            print(f"  mvp.{table}: {count:,} rows")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        azure_conn.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate SQLite data to Azure SQL MVP schema')
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
        migrate_to_mvp_schema(sqlite_path, conn_str)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()