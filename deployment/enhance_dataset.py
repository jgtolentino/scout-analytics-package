#!/usr/bin/env python3
"""
Scout Analytics Dataset Enhancement Script
Upscales and improves the existing dataset for better dashboard analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import random
from faker import Faker
import json

# Initialize Faker for Philippine locale
fake = Faker(['en_PH', 'en_US'])

# Philippine-specific data
PHILIPPINE_REGIONS = [
    'National Capital Region (NCR)',
    'Central Luzon',
    'CALABARZON',
    'Central Visayas',
    'Northern Mindanao'
]

PHILIPPINE_CITIES = {
    'National Capital Region (NCR)': ['Manila', 'Quezon City', 'Makati', 'Taguig', 'Pasig'],
    'Central Luzon': ['Angeles', 'San Fernando', 'Olongapo', 'Cabanatuan', 'Malolos'],
    'CALABARZON': ['Antipolo', 'Dasmarinas', 'Bacoor', 'Calamba', 'Lipa'],
    'Central Visayas': ['Cebu City', 'Lapu-Lapu', 'Mandaue', 'Talisay', 'Toledo'],
    'Northern Mindanao': ['Cagayan de Oro', 'Iligan', 'Butuan', 'Malaybalay', 'Valencia']
}

BARANGAYS = [
    'Poblacion', 'San Antonio', 'Santa Cruz', 'Bagong Silang', 'Tondo',
    'Sampaloc', 'Malate', 'Ermita', 'Binondo', 'Quiapo',
    'Lahug', 'Banilad', 'Mabolo', 'Capitol Site', 'Guadalupe'
]

PRODUCT_CATEGORIES = [
    'Beverages', 'Snacks', 'Personal Care', 'Household Items', 'Fresh Food',
    'Dairy Products', 'Frozen Foods', 'Health & Wellness', 'Baby Care', 'Electronics'
]

BRANDS = [
    'Coca-Cola', 'Pepsi', 'Nestle', 'Unilever', 'P&G',
    'San Miguel', 'Universal Robina', 'Monde Nissin', 'Del Monte', 'Alaska'
]

PAYMENT_METHODS = ['cash', 'card', 'gcash', 'paymaya', 'grabpay']
REQUEST_TYPES = ['branded', 'unbranded', 'pointing']
SUBSTITUTION_REASONS = ['out_of_stock', 'price_difference', 'customer_preference', 'promotion']

def generate_enhanced_transactions(target_count=15000):
    """Generate enhanced transaction dataset with better distribution"""
    print(f"Generating {target_count} enhanced transactions...")
    
    transactions = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 6, 21)
    
    for i in range(target_count):
        # Generate realistic timestamp with business patterns
        random_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        # Business hours bias (7 AM to 10 PM)
        if random.random() < 0.8:  # 80% during business hours
            hour = random.randint(7, 22)
            random_date = random_date.replace(hour=hour)
        
        # Weekend vs weekday patterns
        is_weekend = random_date.weekday() >= 5
        
        # Regional distribution
        region = np.random.choice(PHILIPPINE_REGIONS, p=[0.4, 0.2, 0.15, 0.15, 0.1])
        city = random.choice(PHILIPPINE_CITIES[region])
        barangay = random.choice(BARANGAYS)
        
        # Generate realistic amounts based on time and region
        base_amount = random.uniform(50, 800)
        if region == 'National Capital Region (NCR)':
            base_amount *= 1.3  # Higher prices in NCR
        if is_weekend:
            base_amount *= 1.1  # Weekend premium
            
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'customer_id': str(uuid.uuid4()),
            'created_at': random_date.strftime('%Y-%m-%d %H:%M:%S'),
            'total_amount': round(base_amount, 2),
            'customer_age': random.randint(18, 70),
            'customer_gender': np.random.choice(['Male', 'Female', 'Other'], p=[0.45, 0.45, 0.1]),
            'store_location': f"{fake.street_address()}\n{city}, {region}",
            'store_id': f"STORE-{random.randint(1, 25):03d}",
            'checkout_seconds': random.randint(30, 180),
            'is_weekend': is_weekend,
            'nlp_processed': True,
            'nlp_processed_at': (random_date + timedelta(seconds=random.randint(1, 10))).strftime('%Y-%m-%d %H:%M:%S'),
            'nlp_confidence_score': round(random.uniform(0.7, 0.98), 2),
            'device_id': f"DEV-{random.randint(100, 999)}",
            'payment_method': np.random.choice(PAYMENT_METHODS, p=[0.4, 0.25, 0.2, 0.1, 0.05]),
            'checkout_time': (random_date + timedelta(seconds=random.randint(30, 180))).strftime('%Y-%m-%d %H:%M:%S'),
            'request_type': np.random.choice(REQUEST_TYPES, p=[0.4, 0.35, 0.25]),
            'transcription_text': fake.sentence(),
            'suggestion_accepted': random.choice([True, False]),
            'region': region,
            'city': city,
            'barangay': barangay
        }
        
        transactions.append(transaction)
        
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1} transactions...")
    
    return pd.DataFrame(transactions)

def generate_enhanced_substitutions(transactions_df, target_count=1500):
    """Generate enhanced substitution data"""
    print(f"Generating {target_count} substitution records...")
    
    substitutions = []
    transaction_ids = transactions_df['transaction_id'].tolist()
    
    # Load existing products for realistic substitutions
    try:
        products_df = pd.read_csv('/home/ubuntu/output/products.csv')
        product_ids = products_df['id'].tolist()
    except:
        # Generate synthetic product IDs if file not found
        product_ids = [str(uuid.uuid4()) for _ in range(50)]
    
    for i in range(target_count):
        substitution = {
            'substitution_id': str(uuid.uuid4()),
            'transaction_id': random.choice(transaction_ids),
            'original_product_id': random.choice(product_ids),
            'substituted_product_id': random.choice(product_ids),
            'reason': random.choice(SUBSTITUTION_REASONS),
            'timestamp': fake.date_time_between(start_date='-6M', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        }
        substitutions.append(substitution)
        
        if (i + 1) % 500 == 0:
            print(f"Generated {i + 1} substitutions...")
    
    return pd.DataFrame(substitutions)

def generate_enhanced_request_behaviors(transactions_df, target_count=2000):
    """Generate enhanced request behavior data"""
    print(f"Generating {target_count} request behavior records...")
    
    behaviors = []
    transaction_ids = transactions_df['transaction_id'].tolist()
    device_ids = transactions_df['device_id'].unique().tolist()
    
    for i in range(target_count):
        behavior = {
            'request_id': str(uuid.uuid4()),
            'transaction_id': random.choice(transaction_ids),
            'device_id': random.choice(device_ids),
            'request_method': random.choice(REQUEST_TYPES),
            'timestamp': fake.date_time_between(start_date='-6M', end_date='now').isoformat(),
            'response_time_ms': random.randint(200, 2000),
            'success': random.choice([True, False]),
            'confidence_score': round(random.uniform(0.6, 0.95), 2)
        }
        behaviors.append(behavior)
        
        if (i + 1) % 500 == 0:
            print(f"Generated {i + 1} request behaviors...")
    
    return pd.DataFrame(behaviors)

def generate_enhanced_stores(count=25):
    """Generate enhanced store data with Philippine locations"""
    print(f"Generating {count} store records...")
    
    stores = []
    
    for i in range(count):
        region = random.choice(PHILIPPINE_REGIONS)
        city = random.choice(PHILIPPINE_CITIES[region])
        barangay = random.choice(BARANGAYS)
        
        # Generate realistic coordinates for Philippines
        if region == 'National Capital Region (NCR)':
            lat = random.uniform(14.4, 14.8)
            lng = random.uniform(120.9, 121.2)
        elif region == 'Central Visayas':
            lat = random.uniform(10.2, 10.4)
            lng = random.uniform(123.8, 124.0)
        else:
            lat = random.uniform(6.0, 18.0)
            lng = random.uniform(118.0, 126.0)
        
        store = {
            'store_id': f"STORE-{i+1:03d}",
            'name': f"Scout Store {city} {barangay}",
            'location': f"{fake.street_address()}, {barangay}",
            'barangay': barangay,
            'city': city,
            'region': region,
            'latitude': round(lat, 6),
            'longitude': round(lng, 6),
            'store_type': random.choice(['Supermarket', 'Convenience', 'Hypermarket']),
            'opening_hours': '07:00-22:00',
            'contact_number': fake.phone_number()
        }
        stores.append(store)
    
    return pd.DataFrame(stores)

def main():
    """Main function to generate enhanced dataset"""
    print("=== Scout Analytics Dataset Enhancement ===")
    print("Generating enhanced dataset for better dashboard analytics...")
    
    # Generate enhanced datasets
    transactions_df = generate_enhanced_transactions(15000)
    substitutions_df = generate_enhanced_substitutions(transactions_df, 1500)
    behaviors_df = generate_enhanced_request_behaviors(transactions_df, 2000)
    stores_df = generate_enhanced_stores(25)
    
    # Save enhanced datasets
    output_dir = '/home/ubuntu/enhanced_output'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("\nSaving enhanced datasets...")
    transactions_df.to_csv(f'{output_dir}/transactions.csv', index=False)
    substitutions_df.to_csv(f'{output_dir}/substitutions.csv', index=False)
    behaviors_df.to_csv(f'{output_dir}/request_behaviors.csv', index=False)
    stores_df.to_csv(f'{output_dir}/stores.csv', index=False)
    
    # Generate summary statistics
    print("\n=== Dataset Summary ===")
    print(f"Transactions: {len(transactions_df):,}")
    print(f"Substitutions: {len(substitutions_df):,}")
    print(f"Request Behaviors: {len(behaviors_df):,}")
    print(f"Stores: {len(stores_df):,}")
    
    print(f"\nRegional Distribution:")
    region_dist = transactions_df['region'].value_counts()
    for region, count in region_dist.items():
        print(f"  {region}: {count:,} ({count/len(transactions_df)*100:.1f}%)")
    
    print(f"\nPayment Method Distribution:")
    payment_dist = transactions_df['payment_method'].value_counts()
    for method, count in payment_dist.items():
        print(f"  {method}: {count:,} ({count/len(transactions_df)*100:.1f}%)")
    
    print(f"\nRequest Type Distribution:")
    request_dist = transactions_df['request_type'].value_counts()
    for req_type, count in request_dist.items():
        print(f"  {req_type}: {count:,} ({count/len(transactions_df)*100:.1f}%)")
    
    print(f"\nSubstitution Reason Distribution:")
    sub_dist = substitutions_df['reason'].value_counts()
    for reason, count in sub_dist.items():
        print(f"  {reason}: {count:,} ({count/len(substitutions_df)*100:.1f}%)")
    
    print(f"\nFiles saved to: {output_dir}/")
    print("Enhanced dataset generation complete!")

if __name__ == "__main__":
    main()

