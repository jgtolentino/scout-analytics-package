#!/usr/bin/env python3
"""
Quick CSV column inspector to match database schema
"""

import pandas as pd
import os

csv_files = [
    'stores.csv', 'brands.csv', 'products.csv', 'customers.csv', 
    'devices.csv', 'transactions.csv', 'transaction_items.csv',
    'request_behaviors.csv', 'substitutions.csv'
]

csv_dir = './enhanced_output'

for csv_file in csv_files:
    csv_path = os.path.join(csv_dir, csv_file)
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, nrows=0)  # Just read headers
        print(f"\n{csv_file}:")
        print(f"Columns: {list(df.columns)}")
    else:
        print(f"\n{csv_file}: NOT FOUND")

