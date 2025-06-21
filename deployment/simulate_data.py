import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta

def simulate_substitution_data(df_transactions, target_count=500):
    substitutions = []
    transaction_ids = df_transactions["transaction_id"].tolist()
    products = pd.read_csv("/home/ubuntu/output/products.csv")
    # Ensure products.csv has a product_id. If not, create one.
    if "product_id" not in products.columns:
        products["product_id"] = [str(uuid.uuid4()) for _ in range(len(products))]
        products.to_csv("/home/ubuntu/output/products.csv", index=False) # Save updated products.csv

    product_ids = products["product_id"].tolist()

    if not product_ids:
        print("No products found to simulate substitutions.")
        return pd.DataFrame(columns=["substitution_id", "transaction_id", "original_product_id", "substituted_product_id", "reason"])

    for _ in range(target_count):
        sub_id = str(uuid.uuid4())
        trans_id = np.random.choice(transaction_ids)
        original_prod_id = np.random.choice(product_ids)
        substituted_prod_id = np.random.choice(product_ids)
        while substituted_prod_id == original_prod_id:
            substituted_prod_id = np.random.choice(product_ids)
        reason = np.random.choice(["out_of_stock", "customer_preference", "promotion", "price_difference"])
        substitutions.append({
            "substitution_id": sub_id,
            "transaction_id": trans_id,
            "original_product_id": original_prod_id,
            "substituted_product_id": substituted_prod_id,
            "reason": reason
        })
    return pd.DataFrame(substitutions)

def simulate_request_behavior_data(df_transactions, target_count=500):
    request_behaviors = []
    transaction_ids = df_transactions["transaction_id"].tolist()
    devices = pd.read_csv("/home/ubuntu/output/devices.csv")
    # Ensure devices.csv has a device_id. If not, create one.
    if "device_id" not in devices.columns:
        devices["device_id"] = [str(uuid.uuid4()) for _ in range(len(devices))]
        devices.to_csv("/home/ubuntu/output/devices.csv", index=False) # Save updated devices.csv

    device_ids = devices["device_id"].tolist()

    if not device_ids:
        print("No devices found to simulate request behaviors.")
        return pd.DataFrame(columns=["request_id", "transaction_id", "device_id", "request_method", "timestamp"])

    for _ in range(target_count):
        req_id = str(uuid.uuid4())
        trans_id = np.random.choice(transaction_ids)
        dev_id = np.random.choice(device_ids)
        req_method = np.random.choice(["branded", "unbranded", "pointing"])
        timestamp = (datetime.now() - timedelta(days=np.random.randint(0, 30))).isoformat()
        request_behaviors.append({
            "request_id": req_id,
            "transaction_id": trans_id,
            "device_id": dev_id,
            "request_method": req_method,
            "timestamp": timestamp
        })
    return pd.DataFrame(request_behaviors)

# Load upscaled transactions
df_transactions = pd.read_csv("/home/ubuntu/output/transactions.csv")

# Simulate substitution data
df_substitutions = simulate_substitution_data(df_transactions, target_count=500)
df_substitutions.to_csv("/home/ubuntu/output/substitutions.csv", index=False)
print(f"Simulated {len(df_substitutions)} substitution records.")

# Simulate request behavior data
df_request_behaviors = simulate_request_behavior_data(df_transactions, target_count=500)
df_request_behaviors.to_csv("/home/ubuntu/output/request_behaviors.csv", index=False)
print(f"Simulated {len(df_request_behaviors)} request behavior records.")

