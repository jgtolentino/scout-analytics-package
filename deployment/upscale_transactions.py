import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta

def upscale_transactions(df_transactions, target_count=10000):
    current_count = len(df_transactions)
    if current_count >= target_count:
        print(f"Current transaction count {current_count} is already >= {target_count}. No upscaling needed.")
        return df_transactions

    upscale_factor = (target_count // current_count) + 1
    print(f"Upscaling transactions by factor: {upscale_factor}")

    upscaled_transactions = pd.DataFrame()
    for _ in range(upscale_factor):
        temp_df = df_transactions.copy()
        # Generate new transaction_id and customer_id for each upscaled batch
        temp_df["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(temp_df))]
        temp_df["customer_id"] = [str(uuid.uuid4()) for _ in range(len(temp_df))]
        upscaled_transactions = pd.concat([upscaled_transactions, temp_df], ignore_index=True)

    # Trim to exactly target_count if needed
    upscaled_transactions = upscaled_transactions.head(target_count)
    print(f"Upscaled transactions to {len(upscaled_transactions)} records.")
    return upscaled_transactions

# Load existing data
df_transactions = pd.read_csv("/home/ubuntu/output/transactions.csv")

# Upscale transactions
df_transactions_upscaled = upscale_transactions(df_transactions, target_count=10000)

# Save upscaled transactions
df_transactions_upscaled.to_csv("/home/ubuntu/output/transactions.csv", index=False)

