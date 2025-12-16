import os
import sys
import pandas as pd
import joblib
import json
from datetime import datetime, timedelta
import logging
import uuid
import random
import numpy as np

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_supabase_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data_science", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
PREDICTIONS_DIR = os.path.join(DATA_DIR, "predictions")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "data_science", "artifacts")

def ensure_dirs():
    """Ensure data directories exist."""
    for d in [RAW_DIR, PROCESSED_DIR, PREDICTIONS_DIR]:
        os.makedirs(d, exist_ok=True)

import random
import numpy as np

def fetch_and_save_raw():
    """Fetch data from Supabase and save to raw folder."""
    logger.info("Fetching raw data from Supabase...")
    db = get_supabase_admin()
    
    tables = ["tickets", "events", "users", "wallets"]
    
    for table in tables:
        try:
            response = db.table(table).select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                output_path = os.path.join(RAW_DIR, f"{table}.csv")
                df.to_csv(output_path, index=False)
                logger.info(f"✓ Saved {len(df)} rows to {output_path}")
            else:
                logger.warning(f"⚠ No data found for table {table}")
        except Exception as e:
            logger.error(f"Error fetching {table}: {e}")

    # Generate synthetic transactions locally since table is missing in DB
    logger.info("Generating synthetic transactions locally...")
    users_path = os.path.join(RAW_DIR, "users.csv")
    if os.path.exists(users_path):
        users_df = pd.read_csv(users_path)
        user_ids = users_df['user_id'].tolist()
        
        transactions = []
        for _ in range(200):
            transactions.append({
                "transaction_id": f"tx_{uuid.uuid4().hex[:8]}",
                "user_id": random.choice(user_ids),
                "amount": round(random.uniform(10, 1000), 2),
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 10000))).isoformat(),
                "is_fraud": random.random() < 0.05
            })
        
        tx_df = pd.DataFrame(transactions)
        tx_path = os.path.join(RAW_DIR, "transactions.csv")
        tx_df.to_csv(tx_path, index=False)
        logger.info(f"✓ Generated {len(tx_df)} synthetic transactions to {tx_path}")

def process_data():
    """Process raw data and save to processed folder."""
    logger.info("Processing data...")
    
    try:
        # Load raw data
        tickets_path = os.path.join(RAW_DIR, "tickets.csv")
        events_path = os.path.join(RAW_DIR, "events.csv")
        transactions_path = os.path.join(RAW_DIR, "transactions.csv")
        
        # 1. Scalping Features
        if os.path.exists(tickets_path) and os.path.exists(events_path):
            tickets = pd.read_csv(tickets_path)
            events = pd.read_csv(events_path)
            merged = pd.merge(tickets, events, on="event_id", suffixes=("_ticket", "_event"))
            merged['price_diff'] = merged['purchase_price'] - merged['base_price']
            merged['created_at_ticket'] = pd.to_datetime(merged['created_at_ticket'], format='mixed')
            merged['event_date'] = pd.to_datetime(merged['event_date'], format='mixed')
            merged['days_until_event'] = (merged['event_date'] - merged['created_at_ticket']).dt.days
            
            features = merged[[
                'ticket_id', 'event_id', 'purchase_price', 'base_price', 
                'price_diff', 'days_until_event', 'owner_wallet_id'
            ]]
            features.to_csv(os.path.join(PROCESSED_DIR, "scalping_features.csv"), index=False)
            logger.info("✓ Processed scalping features")

        # 2. Risk/Bot Features (User Aggregates)
        if os.path.exists(transactions_path):
            tx_df = pd.read_csv(transactions_path)
            
            # Aggregate by user
            user_stats = tx_df.groupby('user_id').agg({
                'amount': ['mean', 'sum', 'count', 'max'],
                'is_fraud': 'mean'
            }).reset_index()
            user_stats.columns = ['user_id', 'avg_amount', 'total_amount', 'tx_count', 'max_amount', 'fraud_rate']
            
            # Add velocity (mock)
            user_stats['velocity'] = user_stats['tx_count'] / 24.0 # tx per hour (mock)
            
            user_stats.to_csv(os.path.join(PROCESSED_DIR, "user_risk_features.csv"), index=False)
            logger.info("✓ Processed user risk features")

        # 3. Market Trend Features (Time Series)
        if os.path.exists(transactions_path):
            tx_df = pd.read_csv(transactions_path)
            tx_df['timestamp'] = pd.to_datetime(tx_df['timestamp'])
            daily_vol = tx_df.groupby(tx_df['timestamp'].dt.date)['amount'].sum().reset_index()
            daily_vol.columns = ['date', 'total_volume']
            
            daily_vol.to_csv(os.path.join(PROCESSED_DIR, "market_trend_features.csv"), index=False)
            logger.info("✓ Processed market trend features")

    except Exception as e:
        logger.error(f"Error processing data: {e}")

def generate_predictions():
    """Generate predictions using trained models."""
    logger.info("Generating predictions...")
    
    try:
        # 1. Scalping Predictions
        if os.path.exists(os.path.join(PROCESSED_DIR, "scalping_features.csv")):
            df = pd.read_csv(os.path.join(PROCESSED_DIR, "scalping_features.csv"))
            predictions = []
            for _, row in df.iterrows():
                score = 0.1
                if row['price_diff'] > 0: score += 0.4
                if row['days_until_event'] < 2: score += 0.3
                predictions.append({
                    "ticket_id": row['ticket_id'],
                    "scalping_score": min(score, 1.0),
                    "model": "scalping_detection"
                })
            with open(os.path.join(PREDICTIONS_DIR, "scalping_predictions.json"), 'w') as f:
                json.dump(predictions, f, indent=2)
            logger.info(f"✓ Generated {len(predictions)} scalping predictions")

        # 2. Risk Score Predictions
        if os.path.exists(os.path.join(PROCESSED_DIR, "user_risk_features.csv")):
            df = pd.read_csv(os.path.join(PROCESSED_DIR, "user_risk_features.csv"))
            predictions = []
            for _, row in df.iterrows():
                # Mock logic mimicking Random Forest
                risk = 0.0
                if row['avg_amount'] > 500: risk += 0.4
                if row['tx_count'] > 10: risk += 0.3
                predictions.append({
                    "user_id": row['user_id'],
                    "risk_score": min(risk, 1.0),
                    "model": "risk_score"
                })
            with open(os.path.join(PREDICTIONS_DIR, "risk_predictions.json"), 'w') as f:
                json.dump(predictions, f, indent=2)
            logger.info(f"✓ Generated {len(predictions)} risk predictions")

        # 3. Bot Detection Predictions
        if os.path.exists(os.path.join(PROCESSED_DIR, "user_risk_features.csv")):
            df = pd.read_csv(os.path.join(PROCESSED_DIR, "user_risk_features.csv"))
            predictions = []
            for _, row in df.iterrows():
                # Mock logic mimicking Isolation Forest
                is_bot = False
                if row['velocity'] > 5: is_bot = True # High velocity
                predictions.append({
                    "user_id": row['user_id'],
                    "is_bot": is_bot,
                    "bot_probability": 0.9 if is_bot else 0.1,
                    "model": "bot_detection"
                })
            with open(os.path.join(PREDICTIONS_DIR, "bot_predictions.json"), 'w') as f:
                json.dump(predictions, f, indent=2)
            logger.info(f"✓ Generated {len(predictions)} bot predictions")

        # 4. Market Trend Predictions
        if os.path.exists(os.path.join(PROCESSED_DIR, "market_trend_features.csv")):
            df = pd.read_csv(os.path.join(PROCESSED_DIR, "market_trend_features.csv"))
            predictions = []
            for _, row in df.iterrows():
                # Mock logic
                trend = "STABLE"
                if row['total_volume'] > 5000: trend = "BULLISH"
                elif row['total_volume'] < 1000: trend = "BEARISH"
                predictions.append({
                    "date": str(row['date']),
                    "predicted_trend": trend,
                    "model": "market_trend"
                })
            with open(os.path.join(PREDICTIONS_DIR, "market_trend_predictions.json"), 'w') as f:
                json.dump(predictions, f, indent=2)
            logger.info(f"✓ Generated {len(predictions)} market trend predictions")

    except Exception as e:
        logger.error(f"Error generating predictions: {e}")


if __name__ == "__main__":
    ensure_dirs()
    fetch_and_save_raw()
    process_data()
    generate_predictions()
