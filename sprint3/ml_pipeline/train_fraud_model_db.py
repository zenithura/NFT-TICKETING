"""
Train XGBoost fraud detection model using data from PostgreSQL database.

This script:
1. Connects to the database
2. Extracts transaction data with features
3. Engineers features using FeatureEngineer
4. Trains the model
5. Evaluates and saves the model
"""

import pandas as pd
import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    confusion_matrix,
    classification_report,
    f1_score,
)
from xgboost import XGBClassifier
import sys

sys.path.append(str(Path(__file__).parent.parent))

from data_control.db_connection import get_db_connection, return_db_connection
from data_control.etl_pipeline import get_etl_pipeline
from ml_pipeline.feature_engineering import get_feature_engineer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature columns used for model training
FEATURE_COLS = [
    "txn_velocity_1h",
    "wallet_age_days",
    "avg_ticket_hold_time",
    "event_popularity_score",
    "price_deviation_ratio",
    "cross_event_attendance",
    "geo_velocity_flag",
    "payment_method_diversity",
    "social_graph_centrality",
    "time_to_first_resale",
]


def load_data_from_db(since_days: int = 90, min_samples: int = 100):
    """
    Load transaction data from database and engineer features.

    Args:
        since_days: Number of days to look back for training data
        min_samples: Minimum number of samples required

    Returns:
        DataFrame with transaction features and fraud labels
    """
    logger.info(f"Loading data from database (last {since_days} days)...")

    # Get ETL pipeline
    etl = get_etl_pipeline()
    feature_engineer = get_feature_engineer()

    # Extract transactions
    since = datetime.now() - timedelta(days=since_days)
    df = etl.extract_transactions(since=since, until=datetime.now())

    if df.empty:
        logger.error("No transactions found in database")
        return pd.DataFrame()

    logger.info(f"Extracted {len(df)} raw transactions")

    # Transform features
    df_transformed = etl.transform_features(df)

    # Engineer ML features for each transaction
    logger.info("Engineering ML features...")
    features_list = []

    for idx, row in df_transformed.iterrows():
        try:
            # Compute features using FeatureEngineer
            features = feature_engineer.compute_features(
                transaction_id=str(row.get("transaction_id", idx)),
                wallet_address=str(row.get("wallet_address", "")),
                event_id=row.get("event_id"),
            )

            # Add transaction metadata
            features["transaction_id"] = row.get("transaction_id")
            features["wallet_address"] = row.get("wallet_address")
            features["event_id"] = row.get("event_id")
            features["price_paid"] = row.get("price_paid", 0)
            features["created_at"] = row.get("created_at")

            # Determine fraud label (simplified - in production, use actual fraud detection results)
            # For now, we'll use a heuristic based on features
            features["is_fraud"] = _determine_fraud_label(features)

            features_list.append(features)

        except Exception as e:
            logger.warning(f"Error computing features for transaction {idx}: {e}")
            continue

    if not features_list:
        logger.error("No features computed")
        return pd.DataFrame()

    df_features = pd.DataFrame(features_list)

    # Ensure all feature columns exist
    for col in FEATURE_COLS:
        if col not in df_features.columns:
            df_features[col] = 0.0

    logger.info(f"Engineered features for {len(df_features)} transactions")
    logger.info(f"Fraud rate: {df_features['is_fraud'].mean():.2%}")

    if len(df_features) < min_samples:
        logger.warning(
            f"Only {len(df_features)} samples found, minimum {min_samples} recommended"
        )

    return df_features


def _determine_fraud_label(features: dict) -> int:
    """
    Determine fraud label based on features.

    In production, this should use actual fraud detection results from:
    - security_alerts table
    - bot_detection table
    - manual reviews

    For now, using heuristic based on suspicious patterns.
    """
    # High transaction velocity
    if features.get("txn_velocity_1h", 0) > 10:
        return 1

    # Very new wallet with high activity
    if (
        features.get("wallet_age_days", 30) < 1
        and features.get("txn_velocity_1h", 0) > 5
    ):
        return 1

    # Geo velocity flag
    if features.get("geo_velocity_flag", 0) == 1:
        return 1

    # Very short ticket hold time (potential scalping)
    if features.get("avg_ticket_hold_time", 48) < 1:
        return 1

    # High price deviation (potential manipulation)
    if abs(features.get("price_deviation_ratio", 0)) > 2.0:
        return 1

    return 0


def load_data_with_fraud_labels():
    """
    Load data with actual fraud labels from database.

    This queries the security_alerts and bot_detection tables to get
    actual fraud labels.
    """
    logger.info("Loading data with fraud labels from security tables...")

    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return pd.DataFrame()

    try:
        with conn.cursor() as cur:
            # Query to get transactions with fraud labels
            query = """
                SELECT DISTINCT
                    o.order_id as transaction_id,
                    w.address as wallet_address,
                    o.event_id,
                    o.price as price_paid,
                    o.created_at,
                    CASE 
                        WHEN sa.alert_id IS NOT NULL THEN 1
                        WHEN bd.detection_id IS NOT NULL THEN 1
                        ELSE 0
                    END as is_fraud
                FROM orders o
                JOIN wallets w ON w.wallet_id = o.buyer_wallet_id
                LEFT JOIN security_alerts sa ON sa.wallet_address = w.address
                LEFT JOIN bot_detection bd ON bd.wallet_address = w.address
                WHERE o.status = 'COMPLETED'
                AND o.created_at >= NOW() - INTERVAL '90 days'
                ORDER BY o.created_at DESC
            """

            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            df = pd.DataFrame(rows, columns=columns)
            logger.info(f"Loaded {len(df)} transactions with fraud labels")

            if df.empty:
                logger.warning(
                    "No transactions found, falling back to heuristic labels"
                )
                return load_data_from_db()

            # Engineer features for each transaction
            feature_engineer = get_feature_engineer()
            features_list = []

            for idx, row in df.iterrows():
                try:
                    features = feature_engineer.compute_features(
                        transaction_id=str(row["transaction_id"]),
                        wallet_address=row["wallet_address"],
                        event_id=row.get("event_id"),
                    )

                    # Add metadata
                    for col in [
                        "transaction_id",
                        "wallet_address",
                        "event_id",
                        "price_paid",
                        "created_at",
                        "is_fraud",
                    ]:
                        features[col] = row[col]

                    features_list.append(features)

                except Exception as e:
                    logger.warning(f"Error computing features: {e}")
                    continue

            df_features = pd.DataFrame(features_list)

            # Ensure all feature columns exist
            for col in FEATURE_COLS:
                if col not in df_features.columns:
                    df_features[col] = 0.0

            logger.info(f"Fraud rate: {df_features['is_fraud'].mean():.2%}")
            return df_features

    except Exception as e:
        logger.error(f"Error loading data with fraud labels: {e}")
        logger.info("Falling back to heuristic labels")
        return load_data_from_db()
    finally:
        return_db_connection(conn)


def prepare_features(df):
    """Prepare feature matrix and target vector."""
    if df.empty:
        return pd.DataFrame(), pd.Series()

    # Select feature columns
    X = df[FEATURE_COLS].fillna(0)

    # Handle missing columns
    for col in FEATURE_COLS:
        if col not in X.columns:
            X[col] = 0.0

    # Target
    y = df["is_fraud"].astype(int)

    logger.info(f"\nFeature matrix shape: {X.shape}")
    logger.info(f"Target distribution: {y.value_counts().to_dict()}")

    return X, y


def train_model(X_train, y_train):
    """Train XGBoost classifier."""
    logger.info("\nTraining XGBoost model...")

    # Calculate class imbalance
    fraud_count = y_train.sum()
    legit_count = len(y_train) - fraud_count

    if fraud_count == 0:
        logger.error("No fraud cases in training data!")
        return None

    scale_pos_weight = legit_count / fraud_count

    logger.info(f"Class imbalance ratio: {scale_pos_weight:.1f}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    logger.info("✅ Model training complete")

    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate model performance."""
    logger.info("\nEvaluating model...")

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba > 0.65).astype(int)  # Threshold = 0.65

    # Metrics
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    auc_pr = auc(recall, precision)
    f1 = f1_score(y_test, y_pred)

    logger.info("\n📊 Performance Metrics:")
    logger.info(f"  AUC-ROC: {auc_roc:.3f}")
    logger.info(f"  AUC-PR:  {auc_pr:.3f}")
    logger.info(f"  F1 Score: {f1:.3f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info("\nConfusion Matrix:")
    logger.info("                Predicted")
    logger.info("              Fraud  Legit")
    logger.info(
        f"Actual Fraud   {cm[1, 1]:4d}   {cm[1, 0]:4d}   (Recall: {cm[1, 1] / (cm[1, 1] + cm[1, 0]):.1%})"
    )
    logger.info(
        f"       Legit   {cm[0, 1]:4d}  {cm[0, 0]:5d}   (Specificity: {cm[0, 0] / (cm[0, 0] + cm[0, 1]):.1%})"
    )

    # False positive rate
    fpr = cm[0, 1] / (cm[0, 0] + cm[0, 1]) if (cm[0, 0] + cm[0, 1]) > 0 else 0
    logger.info(f"\nFalse Positive Rate: {fpr:.2%}")

    # Classification report
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))

    # Feature importance
    feature_importance = pd.DataFrame(
        {"feature": FEATURE_COLS, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    logger.info("\n🎯 Top 5 Features:")
    for idx, row in feature_importance.head(5).iterrows():
        logger.info(f"  {row['feature']:30s} {row['importance']:.3f}")

    return {
        "auc_roc": float(auc_roc),
        "auc_pr": float(auc_pr),
        "f1_score": float(f1),
        "confusion_matrix": cm.tolist(),
        "feature_importance": feature_importance.to_dict("records"),
        "false_positive_rate": float(fpr),
    }


def save_model(model, metrics, output_dir="sprint3/ml_pipeline/models"):
    """Save trained model and metadata."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = f"{output_dir}/fraud_model_v1.2.3.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"\n💾 Saved model: {model_path}")

    # Save metadata
    metadata = {
        "model_version": "v1.2.3",
        "training_date": pd.Timestamp.now().isoformat(),
        "features": FEATURE_COLS,
        "metrics": metrics,
        "hyperparameters": model.get_params(),
    }

    metadata_path = f"{output_dir}/model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"💾 Saved metadata: {metadata_path}")

    return model_path, metadata_path


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("XGBoost Fraud Detection Model Training (Database)")
    print("=" * 60)

    # Load data from database
    try:
        df = load_data_with_fraud_labels()
    except Exception as e:
        logger.error(f"Error loading data with fraud labels: {e}")
        logger.info("Falling back to heuristic-based labels")
        df = load_data_from_db()

    if df.empty:
        logger.error("No data available for training")
        return

    # Prepare features
    X, y = prepare_features(df)

    if X.empty or len(y) == 0:
        logger.error("Failed to prepare features")
        return

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    logger.info(f"\nTrain set: {len(X_train)} samples")
    logger.info(f"Test set:  {len(X_test)} samples")

    # Train model
    model = train_model(X_train, y_train)
    if model is None:
        logger.error("Model training failed")
        return

    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)

    # Cross-validation
    logger.info("\nRunning 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc", n_jobs=-1)
    logger.info(f"CV AUC-ROC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Save model
    model_path, metadata_path = save_model(model, metrics)

    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print("=" * 60)
    print("\nModel files:")
    print(f"  {model_path}")
    print(f"  {metadata_path}")


if __name__ == "__main__":
    main()
