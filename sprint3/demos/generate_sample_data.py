"""
Generate sample transaction data for testing and demo purposes.
Creates realistic NFT ticketing transaction data with fraud patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

np.random.seed(42)
random.seed(42)

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
    
    # Generate base data
    data = []
    start_date = datetime.now() - timedelta(days=90)
    
    # Create wallet pool (some wallets will have multiple transactions)
    wallet_pool = [generate_wallet_address() for _ in range(n_transactions // 3)]
    
    # Event pool
    events = [f"evt_{i:04d}" for i in range(100)]
    event_capacities = {evt: random.randint(100, 5000) for evt in events}
    event_floor_prices = {evt: random.uniform(20, 200) for evt in events}
    
    for i in range(n_transactions):
        # Determine if this is a fraud transaction
        is_fraud = random.random() < fraud_rate
        
        # Select wallet (fraudsters reuse wallets more)
        if is_fraud and random.random() < 0.7:
            wallet = random.choice(wallet_pool[:50])  # Fraudsters from small pool
        else:
            wallet = random.choice(wallet_pool)
        
        # Transaction details
        event_id = random.choice(events)
        timestamp = start_date + timedelta(
            seconds=random.randint(0, 90 * 24 * 3600)
        )
        
        # Price (fraudsters often pay unusual prices)
        floor_price = event_floor_prices[event_id]
        if is_fraud:
            # Fraudulent transactions have unusual pricing
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
    
    df = pd.DataFrame(data)
    
    # Add derived features
    print("Computing features...")
    
    # Wallet age (days since first transaction)
    wallet_first_txn = df.groupby('wallet_address')['timestamp'].min()
    df['wallet_first_txn'] = df['wallet_address'].map(wallet_first_txn)
    df['wallet_age_days'] = (df['timestamp'] - df['wallet_first_txn']).dt.total_seconds() / 86400
    
    # Transaction velocity (transactions in last hour)
    df = df.sort_values('timestamp')
    df['txn_velocity_1h'] = 0
    
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
    
    # Price deviation ratio
    df['price_deviation_ratio'] = (df['price_paid'] - df['floor_price']) / df['floor_price']
    
    # Cross-event attendance
    wallet_event_counts = df.groupby('wallet_address')['event_id'].nunique()
    df['cross_event_attendance'] = df['wallet_address'].map(wallet_event_counts)
    
    # Payment method diversity
    wallet_payment_diversity = df.groupby('wallet_address')['payment_method'].nunique()
    df['payment_method_diversity'] = df['wallet_address'].map(wallet_payment_diversity)
    
    # Geo velocity flag (simplified - random for demo)
    df['geo_velocity_flag'] = df['is_fraud'] & (random.random() < 0.3)
    
    # Event popularity score (simplified)
    event_ticket_counts = df.groupby('event_id').size()
    df['event_popularity_score'] = df['event_id'].map(
        lambda x: event_ticket_counts[x] / event_capacities[x] if x in event_ticket_counts else 0
    )
    
    # Avg ticket hold time (hours) - random for demo
    df['avg_ticket_hold_time'] = np.random.exponential(48, size=len(df))
    
    # Social graph centrality (random for demo)
    df['social_graph_centrality'] = np.random.beta(2, 5, size=len(df))
    
    # Time to first resale (minutes) - random for demo
    df['time_to_first_resale'] = np.where(
        df['is_resale'],
        np.random.exponential(1200, size=len(df)),  # 20 hours avg
        0
    )
    
    print(f"Generated {len(df)} transactions")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def save_sample_data(df, output_dir='sprint3/demos/data'):
    """Save sample data to CSV and JSON."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save full dataset
    csv_path = f'{output_dir}/sample_transactions.csv'
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")
    
    # Save a subset as JSON for API testing
    sample_json = df.head(100).to_dict('records')
    # Convert timestamps and other non-serializable types to strings
    for record in sample_json:
        record['timestamp'] = str(record['timestamp'])
        record['wallet_first_txn'] = str(record['wallet_first_txn'])
    
    json_path = f'{output_dir}/sample_transactions.json'
    with open(json_path, 'w') as f:
        json.dump(sample_json, f, indent=2)
    print(f"Saved JSON: {json_path}")
    
    # Save train/test split
    from sklearn.model_selection import train_test_split
    
    train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['is_fraud'], random_state=42)
    
    train_df.to_csv(f'{output_dir}/train_data.csv', index=False)
    test_df.to_csv(f'{output_dir}/test_data.csv', index=False)
    print(f"Saved train/test split: {len(train_df)} train, {len(test_df)} test")
    
    return csv_path, json_path

if __name__ == '__main__':
    # Generate sample data
    df = generate_sample_data(n_transactions=10000, fraud_rate=0.012)
    
    # Save to files
    csv_path, json_path = save_sample_data(df)
    
    print("\n✅ Sample data generation complete!")
    print(f"\nData summary:")
    print(f"  Total transactions: {len(df)}")
    print(f"  Fraudulent: {df['is_fraud'].sum()} ({df['is_fraud'].mean():.2%})")
    print(f"  Unique wallets: {df['wallet_address'].nunique()}")
    print(f"  Unique events: {df['event_id'].nunique()}")
    print(f"\nFiles created:")
    print(f"  {csv_path}")
    print(f"  {json_path}")
