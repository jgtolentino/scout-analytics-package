#!/usr/bin/env python3
"""
Azure SQL Database Migration Script for Scout Analytics
Migrates data from SQLite to Azure SQL Database (handles existing tables)
"""

import sqlite3
import pyodbc
import os
from datetime import datetime

# Azure SQL Connection String
AZURE_SQL_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=sqltbwaprojectscoutserver.database.windows.net;"
    "Database=SQL-TBWA-ProjectScout-Reporting-Prod;"
    "Uid=TBWA;"
    "Pwd=R@nd0mPA$$2025!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

# SQLite database path
SQLITE_DB_PATH = "/home/ubuntu/scout-analytics-api/scout_analytics.db"

def clear_existing_data(azure_conn):
    """Clear existing data from tables (preserve structure)"""
    cursor = azure_conn.cursor()
    
    # Clear data in reverse dependency order
    tables = ['substitutions', 'request_behaviors', 'transaction_items', 'transactions', 
              'devices', 'customers', 'products', 'brands', 'stores']
    
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

def main():
    """Main migration function"""
    print("🚀 Starting Scout Analytics data migration to Azure SQL Database")
    print(f"📁 Source SQLite: {SQLITE_DB_PATH}")
    print(f"🌐 Target Azure SQL: sqltbwaprojectscoutserver.database.windows.net")
    
    try:
        # Connect to SQLite
        print("📱 Connecting to SQLite database...")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        print("✅ Connected to SQLite")
        
        # Connect to Azure SQL
        print("🌐 Connecting to Azure SQL Database...")
        azure_conn = pyodbc.connect(AZURE_SQL_CONN_STR)
        print("✅ Connected to Azure SQL Database")
        
        # Clear existing data (preserve table structure)
        print("🧹 Clearing existing data...")
        clear_existing_data(azure_conn)
        
        # Migration order (respecting foreign key constraints)
        migration_order = [
            'stores',
            'brands', 
            'products',
            'customers',
            'devices',
            'transactions',
            'transaction_items',
            'request_behaviors',
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
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'azure_conn' in locals():
            azure_conn.close()

if __name__ == "__main__":
    main()

