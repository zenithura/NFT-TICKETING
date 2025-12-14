"""
Initialize and train Multi-Armed Bandit (MAB) model using historical data.

The MAB model learns online, but we can initialize it with historical
performance data to give it a head start.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data_control.db_connection import (
    get_db_connection,
    return_db_connection,
    get_redis_client,
)
from ml_pipeline.mab_pricing import MultiArmedBandit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_historical_pricing_data(since_days: int = 90):
    """
    Load historical pricing data from database.

    Returns:
        DataFrame with historical transactions and pricing strategy outcomes
    """
    logger.info(f"Loading historical pricing data (last {since_days} days)...")

    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return pd.DataFrame()

    try:
        with conn.cursor() as cur:
            # Query to get historical transactions with pricing information
            # Note: This assumes you have a pricing_strategy column or can infer it
            query = """
                SELECT 
                    o.order_id,
                    o.event_id,
                    o.price as price_paid,
                    o.created_at,
                    e.base_price,
                    e.name as event_name,
                    e.capacity,
                    COUNT(t.ticket_id) as tickets_sold,
                    o.status
                FROM orders o
                JOIN events e ON e.event_id = o.event_id
                LEFT JOIN tickets t ON t.event_id = e.event_id
                WHERE o.status = 'COMPLETED'
                AND o.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY o.order_id, o.event_id, o.price, o.created_at, 
                         e.base_price, e.name, e.capacity, o.status
                ORDER BY o.created_at DESC
            """

            cur.execute(query, (since_days,))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            df = pd.DataFrame(rows, columns=columns)
            logger.info(f"Loaded {len(df)} historical transactions")

            return df

    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        return pd.DataFrame()
    finally:
        return_db_connection(conn)


def infer_pricing_strategy(row: pd.Series) -> str:
    """
    Infer which pricing strategy was used based on transaction data.

    In production, you would have a pricing_strategy column in your database.
    For now, we infer based on price patterns.
    """
    base_price = float(row.get("base_price", 0))
    price_paid = float(row.get("price_paid", 0))

    if base_price == 0:
        return "baseline"

    price_ratio = price_paid / base_price

    # Surge pricing: price > 1.1x base
    if price_ratio > 1.1:
        return "surge_pricing"

    # Early bird: price < 0.95x base
    elif price_ratio < 0.95:
        return "early_bird"

    # ML pricing: price between 0.95x and 1.1x (dynamic pricing)
    elif 0.95 <= price_ratio <= 1.1:
        return "ml_pricing"

    # Baseline: exactly base price
    else:
        return "baseline"


def calculate_reward(row: pd.Series, strategy: str) -> float:
    """
    Calculate reward for a pricing strategy.

    Reward metrics:
    - Revenue: price_paid
    - Conversion: 1.0 if completed, 0.0 if failed
    - Popularity: tickets_sold / capacity

    Combined reward: revenue * conversion * popularity_factor
    """
    price_paid = float(row.get("price_paid", 0))
    status = row.get("status", "")
    tickets_sold = int(row.get("tickets_sold", 0))
    capacity = int(row.get("capacity", 1))

    # Base reward: revenue
    reward = price_paid

    # Conversion factor
    conversion_factor = 1.0 if status == "COMPLETED" else 0.0

    # Popularity factor (normalized)
    popularity_factor = min(tickets_sold / max(capacity, 1), 1.0)

    # Combined reward
    final_reward = reward * conversion_factor * (0.5 + 0.5 * popularity_factor)

    return final_reward


def initialize_mab_with_history(mab: MultiArmedBandit, df: pd.DataFrame):
    """
    Initialize MAB model with historical data.

    Args:
        mab: MultiArmedBandit instance
        df: Historical transaction data
    """
    logger.info("Initializing MAB with historical data...")

    if df.empty:
        logger.warning("No historical data available, starting with default state")
        return

    # Group by inferred strategy and calculate average rewards
    strategy_rewards = {}

    for _, row in df.iterrows():
        strategy = infer_pricing_strategy(row)
        reward = calculate_reward(row, strategy)

        if strategy not in strategy_rewards:
            strategy_rewards[strategy] = []

        strategy_rewards[strategy].append(reward)

    # Update MAB arms with historical statistics
    for strategy, rewards in strategy_rewards.items():
        if strategy in mab.arms:
            arm = mab.arms[strategy]

            # Calculate statistics
            arm["count"] = len(rewards)
            arm["rewards"] = [
                {
                    "reward": r,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"source": "historical_init"},
                }
                for r in rewards[:1000]  # Keep last 1000
            ]
            arm["avg_reward"] = np.mean(rewards)
            arm["weight"] = 1.0

            logger.info(
                f"  {strategy}: {arm['count']} samples, avg_reward={arm['avg_reward']:.2f}"
            )

    # Save to Redis
    mab._save_to_redis()

    logger.info("✅ MAB initialized with historical data")


def train_mab_online(mab: MultiArmedBandit, df: pd.DataFrame, batch_size: int = 100):
    """
    Simulate online training by processing historical data in batches.

    This simulates how the MAB would learn in production.
    """
    logger.info(f"Simulating online training with {len(df)} samples...")

    # Shuffle data to simulate real-time arrival
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    total_rewards = {arm: 0.0 for arm in mab.arms.keys()}
    total_selections = {arm: 0 for arm in mab.arms.keys()}

    for i in range(0, len(df_shuffled), batch_size):
        batch = df_shuffled.iloc[i : i + batch_size]

        for _, row in batch.iterrows():
            # Infer strategy (in production, this would be the selected arm)
            strategy = infer_pricing_strategy(row)

            # Calculate reward
            reward = calculate_reward(row, strategy)

            # Update MAB
            mab.update_reward(
                strategy,
                reward,
                metadata={
                    "order_id": row.get("order_id"),
                    "event_id": row.get("event_id"),
                    "source": "historical_training",
                },
            )

            total_rewards[strategy] += reward
            total_selections[strategy] += 1

        # Log progress
        if (i // batch_size + 1) % 10 == 0:
            stats = mab.get_arm_stats()
            logger.info(f"  Processed {i + batch_size}/{len(df_shuffled)} samples")
            for arm_name, arm_stats in stats.items():
                logger.info(
                    f"    {arm_name}: count={arm_stats['count']}, avg_reward={arm_stats['avg_reward']:.2f}"
                )

    logger.info("✅ Online training simulation complete")
    logger.info("\nFinal Statistics:")
    for arm_name, arm_stats in mab.get_arm_stats().items():
        logger.info(f"  {arm_name}:")
        logger.info(f"    Count: {arm_stats['count']}")
        logger.info(f"    Avg Reward: {arm_stats['avg_reward']:.4f}")
        logger.info(f"    Total Reward: {arm_stats['total_reward']:.2f}")


def main():
    """Main MAB training pipeline."""
    print("=" * 60)
    print("Multi-Armed Bandit (MAB) Model Training")
    print("=" * 60)

    # Load historical data
    df = load_historical_pricing_data(since_days=90)

    if df.empty:
        logger.warning("No historical data available")
        logger.info("MAB will start with default state and learn online")
        return

    # Initialize MAB
    mab = MultiArmedBandit(epsilon=0.15)

    # Option 1: Initialize with historical statistics
    logger.info("\n[Step 1] Initializing MAB with historical statistics...")
    initialize_mab_with_history(mab, df)

    # Option 2: Simulate online training
    logger.info("\n[Step 2] Simulating online training...")
    train_mab_online(mab, df, batch_size=50)

    # Display final statistics
    print("\n" + "=" * 60)
    print("✅ MAB Training Complete!")
    print("=" * 60)

    stats = mab.get_arm_stats()
    print("\nFinal Arm Statistics:")
    for arm_name, arm_stats in stats.items():
        print(f"\n  {arm_name}:")
        print(f"    Selections: {arm_stats['count']}")
        print(f"    Avg Reward: {arm_stats['avg_reward']:.4f}")
        print(f"    Total Reward: {arm_stats['total_reward']:.2f}")
        print(f"    Weight: {arm_stats['weight']:.2f}")

    print("\n💾 MAB state saved to Redis")
    print("\nThe MAB model is now ready for production use!")


if __name__ == "__main__":
    main()
