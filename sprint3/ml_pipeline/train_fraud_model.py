# File header: XGBoost model training script for fraud detection.
# Trains a binary classifier on transaction features and saves the model with metadata.

"""
Train XGBoost fraud detection model on sample data.
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc,
    confusion_matrix, classification_report, f1_score
)
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns

# Purpose: Feature column names used for model training and prediction.
# Side effects: None - constant list.
FEATURE_COLS = [
    'txn_velocity_1h',
    'wallet_age_days',
    'avg_ticket_hold_time',
    'event_popularity_score',
    'price_deviation_ratio',
    'cross_event_attendance',
    'geo_velocity_flag',
    'payment_method_diversity',
    'social_graph_centrality',
    'time_to_first_resale'
]

# Purpose: Load transaction data from CSV file for model training.
# Params: data_path (str) — path to CSV file with transaction data.
# Returns: DataFrame with transaction features and fraud labels.
# Side effects: Reads CSV file from filesystem, converts boolean to int.
def load_data(data_path='sprint3/demos/data/sample_transactions.csv'):
    """Load and prepare training data."""
    print(f"Loading data from {data_path}...")
    df = pd.DataFrame(pd.read_csv(data_path))
    
    # Convert boolean to int
    df['geo_velocity_flag'] = df['geo_velocity_flag'].astype(int)
    
    print(f"Loaded {len(df)} transactions")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")
    
    return df

# Purpose: Extract feature matrix and target vector from dataframe.
# Params: df (DataFrame) — transaction data with features and labels.
# Returns: X (DataFrame) — feature matrix; y (Series) — binary fraud labels.
# Side effects: Fills missing values, converts target to integer.
def prepare_features(df):
    """Prepare feature matrix and target vector."""
    X = df[FEATURE_COLS].fillna(0)
    y = df['is_fraud'].astype(int)
    
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    return X, y

# Purpose: Train XGBoost binary classifier for fraud detection.
# Params: X_train (DataFrame) — training features; y_train (Series) — training labels.
# Returns: Trained XGBClassifier model.
# Side effects: Trains model, prints training progress.
def train_model(X_train, y_train):
    """Train XGBoost classifier."""
    print("\nTraining XGBoost model...")
    
    # Purpose: Calculate class imbalance ratio to handle fraud/legit imbalance.
    # Side effects: Computes weight for positive class.
    fraud_count = y_train.sum()
    legit_count = len(y_train) - fraud_count
    scale_pos_weight = legit_count / fraud_count
    
    print(f"Class imbalance ratio: {scale_pos_weight:.1f}")
    
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        eval_metric='aucpr',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    print("✅ Model training complete")
    
    return model

# Purpose: Evaluate trained model performance on test set with metrics and visualizations.
# Params: model (XGBClassifier) — trained model; X_test (DataFrame) — test features; y_test (Series) — test labels.
# Returns: Dictionary with performance metrics and feature importance.
# Side effects: Generates predictions, calculates metrics, prints evaluation results.
def evaluate_model(model, X_test, y_test):
    """Evaluate model performance."""
    print("\nEvaluating model...")
    
    # Purpose: Generate probability predictions and binary predictions using 0.65 threshold.
    # Side effects: Runs model inference on test set.
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba > 0.65).astype(int)  # Threshold = 0.65
    
    # Metrics
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    auc_pr = auc(recall, precision)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\n📊 Performance Metrics:")
    print(f"  AUC-ROC: {auc_roc:.3f}")
    print(f"  AUC-PR:  {auc_pr:.3f}")
    print(f"  F1 Score: {f1:.3f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"                Predicted")
    print(f"              Fraud  Legit")
    print(f"Actual Fraud   {cm[1,1]:4d}   {cm[1,0]:4d}   (Recall: {cm[1,1]/(cm[1,1]+cm[1,0]):.1%})")
    print(f"       Legit   {cm[0,1]:4d}  {cm[0,0]:5d}   (Specificity: {cm[0,0]/(cm[0,0]+cm[0,1]):.1%})")
    
    # False positive rate
    fpr = cm[0,1] / (cm[0,0] + cm[0,1])
    print(f"\nFalse Positive Rate: {fpr:.2%}")
    
    # Classification report
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': FEATURE_COLS,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🎯 Top 5 Features:")
    for idx, row in feature_importance.head(5).iterrows():
        print(f"  {row['feature']:30s} {row['importance']:.3f}")
    
    return {
        'auc_roc': auc_roc,
        'auc_pr': auc_pr,
        'f1_score': f1,
        'confusion_matrix': cm.tolist(),
        'feature_importance': feature_importance.to_dict('records'),
        'false_positive_rate': fpr
    }

# Purpose: Save trained model to pickle file and metadata to JSON.
# Params: model (XGBClassifier) — trained model; metrics (dict) — performance metrics; output_dir (str) — output directory.
# Returns: Tuple of (model_path, metadata_path).
# Side effects: Creates directory if needed, writes model and metadata files.
def save_model(model, metrics, output_dir='sprint3/ml_pipeline/models'):
    """Save trained model and metadata."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = f'{output_dir}/fraud_model_v1.2.3.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n💾 Saved model: {model_path}")
    
    # Save metadata
    metadata = {
        'model_version': 'v1.2.3',
        'training_date': pd.Timestamp.now().isoformat(),
        'features': FEATURE_COLS,
        'metrics': metrics,
        'hyperparameters': model.get_params()
    }
    
    metadata_path = f'{output_dir}/model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"💾 Saved metadata: {metadata_path}")
    
    return model_path, metadata_path

# Purpose: Main training pipeline orchestrating data loading, training, evaluation, and saving.
# Side effects: Loads data, splits train/test, trains model, evaluates, performs cross-validation, saves model.
def main():
    """Main training pipeline."""
    print("=" * 60)
    print("XGBoost Fraud Detection Model Training")
    print("=" * 60)
    
    # Load data
    df = load_data()
    
    # Prepare features
    X, y = prepare_features(df)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Test set:  {len(X_test)} samples")
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Cross-validation
    print("\nRunning 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc', n_jobs=-1)
    print(f"CV AUC-ROC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    # Save model
    model_path, metadata_path = save_model(model, metrics)
    
    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print("=" * 60)
    print(f"\nModel files:")
    print(f"  {model_path}")
    print(f"  {metadata_path}")
    print(f"\nTo use the model:")
    print(f"  import pickle")
    print(f"  with open('{model_path}', 'rb') as f:")
    print(f"      model = pickle.load(f)")

if __name__ == '__main__':
    main()
