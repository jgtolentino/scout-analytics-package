#!/usr/bin/env python3
"""
Generate supporting data for Scout Analytics - Products, Brands, Transaction Items
"""

import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime

# Product categories and brands mapping
PRODUCT_DATA = {
    'Beverages': {
        'brands': ['Coca-Cola', 'Pepsi', 'San Miguel', 'Del Monte'],
        'products': ['Coke 330ml', 'Pepsi 330ml', 'Red Horse Beer', 'Pineapple Juice', 'Orange Juice', 'Sprite 330ml']
    },
    'Snacks': {
        'brands': ['Universal Robina', 'Monde Nissin', 'Oishi', 'Ricoa'],
        'products': ['Potato Chips', 'Corn Chips', 'Chocolate Bar', 'Cookies', 'Crackers', 'Nuts Mix']
    },
    'Personal Care': {
        'brands': ['Unilever', 'P&G', 'Colgate', 'Johnson & Johnson'],
        'products': ['Shampoo 200ml', 'Soap Bar', 'Toothpaste', 'Deodorant', 'Body Wash', 'Face Wash']
    },
    'Household Items': {
        'brands': ['Unilever', 'P&G', 'SC Johnson', 'Reckitt'],
        'products': ['Detergent Powder', 'Fabric Softener', 'Dishwashing Liquid', 'All-Purpose Cleaner', 'Toilet Paper', 'Paper Towels']
    },
    'Fresh Food': {
        'brands': ['Local Farm', 'Fresh Market', 'Organic Plus', 'Farm Fresh'],
        'products': ['Rice 5kg', 'Chicken Breast', 'Pork Chops', 'Fish Fillet', 'Vegetables Mix', 'Fruits Assorted']
    },
    'Dairy Products': {
        'brands': ['Alaska', 'Nestle', 'Magnolia', 'Selecta'],
        'products': ['Fresh Milk 1L', 'Cheese Slices', 'Yogurt Cup', 'Butter 200g', 'Ice Cream', 'Condensed Milk']
    },
    'Frozen Foods': {
        'brands': ['CDO', 'Purefoods', 'Tender Juicy', 'Magnolia'],
        'products': ['Frozen Hotdog', 'Frozen Chicken', 'Ice Cream Tub', 'Frozen Vegetables', 'Frozen Fish', 'Frozen Meat']
    },
    'Health & Wellness': {
        'brands': ['Unilab', 'Pfizer', 'GSK', 'Bayer'],
        'products': ['Vitamins', 'Pain Reliever', 'Cough Syrup', 'Antiseptic', 'Band-aids', 'Thermometer']
    },
    'Baby Care': {
        'brands': ['Johnson & Johnson', 'Pampers', 'Huggies', 'Gerber'],
        'products': ['Baby Diapers', 'Baby Shampoo', 'Baby Powder', 'Baby Food', 'Baby Wipes', 'Baby Lotion']
    },
    'Electronics': {
        'brands': ['Samsung', 'Apple', 'Xiaomi', 'Oppo'],
        'products': ['Phone Charger', 'Earphones', 'Power Bank', 'Phone Case', 'Screen Protector', 'USB Cable']
    }
}

def generate_brands():
    """Generate brands dataset"""
    print("Generating brands dataset...")
    
    brands = []
    brand_id_map = {}
    
    for category, data in PRODUCT_DATA.items():
        for brand_name in data['brands']:
            if brand_name not in brand_id_map:
                brand_id = str(uuid.uuid4())
                brand_id_map[brand_name] = brand_id
                
                brand = {
                    'id': brand_id,
                    'name': brand_name,
                    'category': category,
                    'country_origin': 'Philippines' if brand_name in ['San Miguel', 'Universal Robina', 'CDO', 'Magnolia'] else 'International',
                    'established_year': random.randint(1950, 2020),
                    'market_share': round(random.uniform(5, 25), 1)
                }
                brands.append(brand)
    
    return pd.DataFrame(brands), brand_id_map

def generate_products(brand_id_map):
    """Generate products dataset"""
    print("Generating products dataset...")
    
    products = []
    product_id_map = {}
    
    for category, data in PRODUCT_DATA.items():
        for product_name in data['products']:
            # Find appropriate brand for this product
            brand_name = random.choice(data['brands'])
            brand_id = brand_id_map[brand_name]
            
            product_id = str(uuid.uuid4())
            product_id_map[product_name] = product_id
            
            # Generate realistic pricing based on category
            base_prices = {
                'Beverages': (25, 80),
                'Snacks': (15, 60),
                'Personal Care': (50, 200),
                'Household Items': (40, 150),
                'Fresh Food': (100, 500),
                'Dairy Products': (60, 180),
                'Frozen Foods': (80, 300),
                'Health & Wellness': (100, 400),
                'Baby Care': (80, 250),
                'Electronics': (200, 1500)
            }
            
            min_price, max_price = base_prices.get(category, (50, 200))
            price = round(random.uniform(min_price, max_price), 2)
            
            product = {
                'id': product_id,
                'name': product_name,
                'category': category,
                'brand_id': brand_id,
                'brand_name': brand_name,
                'price': price,
                'sku': f"SKU-{random.randint(10000, 99999)}",
                'barcode': f"{random.randint(1000000000000, 9999999999999)}",
                'weight_grams': random.randint(50, 2000) if category != 'Electronics' else random.randint(100, 500),
                'in_stock': random.choice([True, False]),
                'stock_quantity': random.randint(0, 100),
                'supplier': f"Supplier {random.randint(1, 20)}"
            }
            products.append(product)
    
    return pd.DataFrame(products), product_id_map

def generate_transaction_items(transactions_df, product_id_map):
    """Generate transaction items dataset"""
    print("Generating transaction items dataset...")
    
    transaction_items = []
    product_ids = list(product_id_map.values())
    
    for _, transaction in transactions_df.iterrows():
        # Each transaction has 1-5 items
        num_items = random.randint(1, 5)
        
        for i in range(num_items):
            item = {
                'id': str(uuid.uuid4()),
                'transaction_id': transaction['transaction_id'],
                'product_id': random.choice(product_ids),
                'quantity': random.randint(1, 3),
                'unit_price': round(random.uniform(20, 200), 2),
                'total_price': 0,  # Will calculate below
                'discount_amount': round(random.uniform(0, 20), 2) if random.random() < 0.3 else 0,
                'tax_amount': 0,  # Will calculate below
                'line_number': i + 1
            }
            
            # Calculate totals
            subtotal = item['unit_price'] * item['quantity']
            item['total_price'] = round(subtotal - item['discount_amount'], 2)
            item['tax_amount'] = round(item['total_price'] * 0.12, 2)  # 12% VAT in Philippines
            
            transaction_items.append(item)
    
    return pd.DataFrame(transaction_items)

def generate_customers(transactions_df):
    """Generate customers dataset"""
    print("Generating customers dataset...")
    
    customers = []
    customer_ids = transactions_df['customer_id'].unique()
    
    for customer_id in customer_ids:
        # Get customer info from transactions
        customer_transactions = transactions_df[transactions_df['customer_id'] == customer_id]
        first_transaction = customer_transactions.iloc[0]
        
        customer = {
            'id': customer_id,
            'age': first_transaction['customer_age'],
            'gender': first_transaction['customer_gender'],
            'region': first_transaction['region'],
            'city': first_transaction['city'],
            'barangay': first_transaction['barangay'],
            'registration_date': first_transaction['created_at'],
            'total_transactions': len(customer_transactions),
            'total_spent': round(customer_transactions['total_amount'].sum(), 2),
            'avg_transaction_amount': round(customer_transactions['total_amount'].mean(), 2),
            'preferred_payment_method': customer_transactions['payment_method'].mode().iloc[0],
            'loyalty_tier': random.choice(['Bronze', 'Silver', 'Gold', 'Platinum']),
            'email': f"customer{random.randint(1000, 9999)}@email.com",
            'phone': f"+63{random.randint(9000000000, 9999999999)}"
        }
        customers.append(customer)
    
    return pd.DataFrame(customers)

def generate_devices(transactions_df):
    """Generate devices dataset"""
    print("Generating devices dataset...")
    
    devices = []
    device_ids = transactions_df['device_id'].unique()
    
    device_types = ['Tablet', 'Smartphone', 'Kiosk', 'POS Terminal']
    device_models = ['iPad Pro', 'Samsung Galaxy Tab', 'Scout Kiosk v2', 'Scout POS Pro']
    
    for device_id in device_ids:
        device_transactions = transactions_df[transactions_df['device_id'] == device_id]
        most_common_store = device_transactions['store_id'].mode().iloc[0]
        
        device = {
            'id': device_id,
            'store_id': most_common_store,
            'device_type': random.choice(device_types),
            'model': random.choice(device_models),
            'serial_number': f"SN{random.randint(100000, 999999)}",
            'installation_date': '2024-01-15',
            'last_maintenance': '2025-05-01',
            'status': random.choice(['Active', 'Maintenance', 'Inactive']),
            'software_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            'total_transactions': len(device_transactions),
            'avg_response_time_ms': random.randint(200, 1500),
            'uptime_percentage': round(random.uniform(95, 99.9), 1)
        }
        devices.append(device)
    
    return pd.DataFrame(devices)

def main():
    """Main function to generate all supporting datasets"""
    print("=== Generating Supporting Datasets ===")
    
    # Load enhanced transactions
    transactions_df = pd.read_csv('/home/ubuntu/enhanced_output/transactions.csv')
    
    # Generate all datasets
    brands_df, brand_id_map = generate_brands()
    products_df, product_id_map = generate_products(brand_id_map)
    transaction_items_df = generate_transaction_items(transactions_df, product_id_map)
    customers_df = generate_customers(transactions_df)
    devices_df = generate_devices(transactions_df)
    
    # Save all datasets
    output_dir = '/home/ubuntu/enhanced_output'
    
    print("\nSaving supporting datasets...")
    brands_df.to_csv(f'{output_dir}/brands.csv', index=False)
    products_df.to_csv(f'{output_dir}/products.csv', index=False)
    transaction_items_df.to_csv(f'{output_dir}/transaction_items.csv', index=False)
    customers_df.to_csv(f'{output_dir}/customers.csv', index=False)
    devices_df.to_csv(f'{output_dir}/devices.csv', index=False)
    
    # Generate summary
    print("\n=== Supporting Datasets Summary ===")
    print(f"Brands: {len(brands_df):,}")
    print(f"Products: {len(products_df):,}")
    print(f"Transaction Items: {len(transaction_items_df):,}")
    print(f"Customers: {len(customers_df):,}")
    print(f"Devices: {len(devices_df):,}")
    
    print(f"\nProduct Categories:")
    category_dist = products_df['category'].value_counts()
    for category, count in category_dist.items():
        print(f"  {category}: {count}")
    
    print(f"\nBrand Distribution:")
    brand_dist = products_df['brand_name'].value_counts().head(10)
    for brand, count in brand_dist.items():
        print(f"  {brand}: {count}")
    
    print(f"\nCustomer Loyalty Tiers:")
    loyalty_dist = customers_df['loyalty_tier'].value_counts()
    for tier, count in loyalty_dist.items():
        print(f"  {tier}: {count:,}")
    
    print("\nAll supporting datasets generated successfully!")

if __name__ == "__main__":
    main()

