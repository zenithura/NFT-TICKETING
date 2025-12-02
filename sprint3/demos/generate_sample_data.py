# File header: Sample transaction data generator for fraud detection model training and testing.
# Creates synthetic NFT ticketing transactions with realistic fraud patterns and feature engineering.

"""
Generate sample transaction data for testing and demo purposes.
Creates realistic NFT ticketing transaction data with fraud patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

# Purpose: Set random seeds for reproducible data generation.
# Side effects: Ensures consistent output across runs.
np.random.seed(42)
random.seed(42)

# Purpose: Generate a random Ethereum wallet address for synthetic transactions.
# Returns: String with '0x' prefix followed by 40 hexadecimal characters.
# Side effects: None - pure function.
def generate_wallet_address():
    """Generate a random Ethereum wallet address."""
    return '0x' + ''.join(random.choices('0123456789abcdef', k=40))

def generate_sample_data(n_transactions=10000, fraud_rate=0.012):
    """
    Generate sample transaction data.
    
    Args:
        n_transactions: Number of transactions to generate
        fraud_rate: Percentage of fraudulent transactions (default 1.2%)
    
    Returns:
        DataFrame with transaction data
    """
    print(f"Generating {n_transactions} sample transactions...")
    
    # Purpose: Initialize data storage and set time range for transactions.
    # Side effects: Creates empty list, calculates start date.
    data = []
    start_date = datetime.now() - timedelta(days=90)
    
    # Purpose: Create wallet pool to simulate wallet reuse patterns.
    # Side effects: Generates unique wallet addresses (1/3 of transaction count).
    wallet_pool = [generate_wallet_address() for _ in range(n_transactions // 3)]
    
    # Purpose: Generate event pool with varying capacities and floor prices.
    # Side effects: Creates 100 event IDs with random capacity and pricing.
    events = [f"evt_{i:04d}" for i in range(100)]
    event_capacities = {evt: random.randint(100, 5000) for evt in events}
    event_floor_prices = {evt: random.uniform(20, 200) for evt in events}
    
    # Purpose: Generate individual transactions with fraud patterns.
    # Side effects: Creates transaction records and appends to data list.
    for i in range(n_transactions):
        # Purpose: Randomly mark transactions as fraudulent based on fraud_rate.
        # Side effects: Determines transaction fraud status.
        is_fraud = random.random() < fraud_rate
        
        # Purpose: Select wallet with bias - fraudsters reuse wallets more frequently.
        # Side effects: Assigns wallet address to transaction.
        if is_fraud and random.random() < 0.7:
            wallet = random.choice(wallet_pool[:50])  # Fraudsters from small pool
        else:
            wallet = random.choice(wallet_pool)
        
        # Purpose: Assign random event and timestamp within 90-day window.
        # Side effects: Sets event_id and timestamp for transaction.
        event_id = random.choice(events)
        timestamp = start_date + timedelta(
            seconds=random.randint(0, 90 * 24 * 3600)
        )
        
        # Purpose: Calculate transaction price with fraud-specific patterns.
        # Side effects: Sets price_paid based on floor price and fraud status.
        floor_price = event_floor_prices[event_id]
        if is_fraud:
            # Purpose: Fraudulent transactions use unusual pricing multipliers.
            # Side effects: Creates suspicious price patterns.
            price_multiplier = random.choice([0.3, 0.5, 2.5, 3.0])
        else:
            price_multiplier = random.uniform(0.9, 1.3)
        
        price_paid = floor_price * price_multiplier
        
        transaction = {
            'transaction_id': f'txn_{i:06d}',
            'wallet_address': wallet,
            'event_id': event_id,
            'ticket_id': f'ticket_{i:06d}',
            'price_paid': round(price_paid, 2),
            'floor_price': round(floor_price, 2),
            'payment_method': random.choice(['ETH', 'USDC', 'USDT', 'CARD']),
            'is_resale': random.random() < 0.15,
            'status': 'completed',
            'timestamp': timestamp,
            'is_fraud': is_fraud,
            # IP geolocation (simplified)
            'ip_address': f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            'country': random.choice(['US', 'UK', 'DE', 'FR', 'CA', 'AU', 'JP']),
            'latitude': random.uniform(-90, 90),
            'longitude': random.uniform(-180, 180)
        }
        
        data.append(transaction)
    
    # Purpose: Convert transaction list to pandas DataFrame for feature engineering.
    # Side effects: Creates DataFrame from collected transaction data.
    df = pd.DataFrame(data)
    
    # Purpose: Compute derived features required for fraud detection model.
    # Side effects: Adds feature columns to DataFrame.
    print("Computing features...")
    
    # Purpose: Calculate wallet age in days since first transaction.
    # Side effects: Adds wallet_first_txn and wallet_age_days columns.
    wallet_first_txn = df.groupby('wallet_address')['timestamp'].min()
    df['wallet_first_txn'] = df['wallet_address'].map(wallet_first_txn)
    df['wallet_age_days'] = (df['timestamp'] - df['wallet_first_txn']).dt.total_seconds() / 86400
    
    # Purpose: Calculate transaction velocity (number of transactions in last hour).
    # Side effects: Adds txn_velocity_1h column, sorts DataFrame by timestamp.
    df = df.sort_values('timestamp')
    df['txn_velocity_1h'] = 0
    
    # Purpose: Count transactions per wallet within 1-hour window before current transaction.
    # Side effects: Updates txn_velocity_1h for each transaction.
    for idx, row in df.iterrows():
        wallet = row['wallet_address']
        time = row['timestamp']
        hour_ago = time - timedelta(hours=1)
        
        count = len(df[
            (df['wallet_address'] == wallet) & 
            (df['timestamp'] < time) & 
            (df['timestamp'] >= hour_ago)
        ])
        df.at[idx, 'txn_velocity_1h'] = count
    
    # Purpose: Calculate price deviation ratio from floor price.
    # Side effects: Adds price_deviation_ratio column.
    df['price_deviation_ratio'] = (df['price_paid'] - df['floor_price']) / df['floor_price']
    
    # Purpose: Count unique events attended per wallet (cross-event attendance).
    # Side effects: Adds cross_event_attendance column.
    wallet_event_counts = df.groupby('wallet_address')['event_id'].nunique()
    df['cross_event_attendance'] = df['wallet_address'].map(wallet_event_counts)
    
    # Purpose: Count unique payment methods used per wallet.
    # Side effects: Adds payment_method_diversity column.
    wallet_payment_diversity = df.groupby('wallet_address')['payment_method'].nunique()
    df['payment_method_diversity'] = df['wallet_address'].map(wallet_payment_diversity)
    
    # Purpose: Generate geo velocity flag (simplified - random for demo).
    # Side effects: Adds geo_velocity_flag column (30% of fraud cases flagged).
    df['geo_velocity_flag'] = df['is_fraud'] & (random.random() < 0.3)
    
    # Purpose: Calculate event popularity as tickets sold / capacity.
    # Side effects: Adds event_popularity_score column.
    event_ticket_counts = df.groupby('event_id').size()
    df['event_popularity_score'] = df['event_id'].map(
        lambda x: event_ticket_counts[x] / event_capacities[x] if x in event_ticket_counts else 0
    )
    
    # Purpose: Generate average ticket hold time using exponential distribution (48h mean).
    # Side effects: Adds avg_ticket_hold_time column.
    df['avg_ticket_hold_time'] = np.random.exponential(48, size=len(df))
    
    # Purpose: Generate social graph centrality score using beta distribution.
    # Side effects: Adds social_graph_centrality column.
    df['social_graph_centrality'] = np.random.beta(2, 5, size=len(df))
    
    # Purpose: Calculate time to first resale in minutes (exponential, 20h mean for resales).
    # Side effects: Adds time_to_first_resale column (0 for non-resales).
    df['time_to_first_resale'] = np.where(
        df['is_resale'],
        np.random.exponential(1200, size=len(df)),  # 20 hours avg
        0
    )
    
    print(f"Generated {len(df)} transactions")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

# Purpose: Save generated sample data to CSV and JSON files, and create train/test split.
# Params: df (DataFrame) — transaction data; output_dir (str) — directory path for output files.
# Returns: Tuple of (csv_path, json_path) file paths.
# Side effects: Creates directory, writes files to filesystem.
def save_sample_data(df, output_dir='sprint3/demos/data'):
    """Save sample data to CSV and JSON."""
    import os
    # Purpose: Create output directory if it doesn't exist.
    # Side effects: Creates directory structure.
    os.makedirs(output_dir, exist_ok=True)
    
    # Purpose: Save full dataset as CSV for model training.
    # Side effects: Writes CSV file to filesystem.
    csv_path = f'{output_dir}/sample_transactions.csv'
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")
    
    # Purpose: Save subset as JSON for API testing (first 100 records).
    # Side effects: Converts timestamps to strings, writes JSON file.
    sample_json = df.head(100).to_dict('records')
    # Purpose: Convert timestamps and other non-serializable types to strings.
    # Side effects: Modifies record dictionaries in-place.
    for record in sample_json:
        record['timestamp'] = str(record['timestamp'])
        record['wallet_first_txn'] = str(record['wallet_first_txn'])
    
    json_path = f'{output_dir}/sample_transactions.json'
    with open(json_path, 'w') as f:
        json.dump(sample_json, f, indent=2)
    print(f"Saved JSON: {json_path}")
    
    # Purpose: Split data into train/test sets with stratified sampling on fraud label.
    # Side effects: Creates train_data.csv and test_data.csv files.
    from sklearn.model_selection import train_test_split
    
    train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['is_fraud'], random_state=42)
    
    train_df.to_csv(f'{output_dir}/train_data.csv', index=False)
    test_df.to_csv(f'{output_dir}/test_data.csv', index=False)
    print(f"Saved train/test split: {len(train_df)} train, {len(test_df)} test")
    
    return csv_path, json_path

# Purpose: Main execution block - generate sample data and save to files.
# Side effects: Generates 10,000 transactions with 1.2% fraud rate, writes output files.
if __name__ == '__main__':
    # Purpose: Generate 10,000 sample transactions with 1.2% fraud rate.
    # Side effects: Creates DataFrame with transaction data and features.
    df = generate_sample_data(n_transactions=10000, fraud_rate=0.012)
    
    # Purpose: Save generated data to CSV, JSON, and train/test split files.
    # Side effects: Writes files to sprint3/demos/data directory.
    csv_path, json_path = save_sample_data(df)
    
    # Purpose: Print summary statistics of generated data.
    # Side effects: Outputs to console.
    print("\n✅ Sample data generation complete!")
    print(f"\nData summary:")
    print(f"  Total transactions: {len(df)}")
    print(f"  Fraudulent: {df['is_fraud'].sum()} ({df['is_fraud'].mean():.2%})")
    print(f"  Unique wallets: {df['wallet_address'].nunique()}")
    print(f"  Unique events: {df['event_id'].nunique()}")
    print(f"\nFiles created:")
    print(f"  {csv_path}")
    print(f"  {json_path}")
