import os
import sys
import logging
import joblib
import numpy as np

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_science.models.risk_score import risk_model
from data_science.models.bot_detection import bot_model
from data_science.models.fair_price import fair_price_model
from data_science.models.scalping_detection import scalping_model
from data_science.models.wash_trading import wash_trading_model
from data_science.models.recommender import recommender_model
from data_science.models.segmentation import segmentation_model
from data_science.models.market_trend import market_trend_model
from data_science.models.decision_rule import decision_rule_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_data_loader():
    """
    Get data loader instance with Supabase connection.
    Returns None if database not available.
    """
    try:
        # Import here to avoid circular dependency
        from backend.database import get_supabase_admin
        from data_science.data_loader import DataLoader
        
        db = get_supabase_admin()
        data_loader = DataLoader(db)
        logger.info("✓ Data loader initialized with Supabase connection")
        return data_loader
    except Exception as e:
        logger.warning(f"Could not initialize data loader: {e}")
        logger.warning("Models will train on dummy data")
        return None


def train_all(use_real_data: bool = True):
    """
    Train all models.
    
    Args:
        use_real_data: If True, attempts to fetch real data from database.
                      If False or database unavailable, uses dummy data.
    """
    logger.info("=" * 60)
    logger.info("Starting model training pipeline...")
    logger.info("=" * 60)
    
    # Initialize data loader if requested
    data_loader = None
    if use_real_data:
        data_loader = get_data_loader()
    
    # Set data_loader for all models
    if data_loader:
        logger.info("✓ Using REAL DATA from database")
        risk_model.data_loader = data_loader
        bot_model.data_loader = data_loader
        fair_price_model.data_loader = data_loader
        scalping_model.data_loader = data_loader
        wash_trading_model.data_loader = data_loader
        recommender_model.data_loader = data_loader
        segmentation_model.data_loader = data_loader
        market_trend_model.data_loader = data_loader
        decision_rule_model.data_loader = data_loader
    else:
        logger.info("⚠ Using DUMMY DATA (database not available)")
    
    # Train models
    logger.info("\n" + "-" * 60)
    logger.info("Training Risk Score Model...")
    logger.info("-" * 60)
    risk_model.train()
    
    logger.info("\n" + "-" * 60)
    logger.info("Training Bot Detection Model...")
    logger.info("-" * 60)
    bot_model.train()
    
    logger.info("\n" + "-" * 60)
    logger.info("Training Fair Price Model...")
    logger.info("-" * 60)
    fair_price_model.train()
    
    logger.info("\n" + "-" * 60)
    logger.info("Training Scalping Detection Model...")
    logger.info("-" * 60)
    scalping_model.train()

    logger.info("\n" + "-" * 60)
    logger.info("Initializing Wash Trading Model...")
    logger.info("-" * 60)
    wash_trading_model.train()

    logger.info("\n" + "-" * 60)
    logger.info("Training Recommender Model...")
    logger.info("-" * 60)
    recommender_model.train()

    logger.info("\n" + "-" * 60)
    logger.info("Training Segmentation Model...")
    logger.info("-" * 60)
    segmentation_model.train()

    logger.info("\n" + "-" * 60)
    logger.info("Training Market Trend Model...")
    logger.info("-" * 60)
    market_trend_model.train()

    logger.info("\n" + "-" * 60)
    logger.info("Training Decision Rule Model...")
    logger.info("-" * 60)
    decision_rule_model.train()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ All models trained and saved successfully!")
    logger.info("=" * 60)
    
    # Print summary
    if data_loader:
        logger.info("\n📊 Training Summary:")
        logger.info("  - Data Source: Supabase Database")
        logger.info("  - Models Trained: 5")
        logger.info("  - Metrics Saved: Yes")
        logger.info("  - Predictions Logged: Yes")
    else:
        logger.info("\n📊 Training Summary:")
        logger.info("  - Data Source: Dummy Data")
        logger.info("  - Models Trained: 5")
        logger.info("  - Note: Connect to database for real data training")


if __name__ == "__main__":
    # Check for command line argument
    import argparse
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Use dummy data instead of database"
    )
    args = parser.parse_args()
    
    train_all(use_real_data=not args.dummy)
