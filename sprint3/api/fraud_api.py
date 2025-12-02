# File header: Flask API service for real-time fraud detection using trained ML model.
# Provides endpoints for single and batch fraud predictions on ticket transactions.

"""
Fraud Detection API - Demo Version
Provides real-time fraud prediction endpoint with mock data support.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Purpose: Feature column names that must match the training data schema.
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

# Purpose: Path to trained fraud detection model file.
# Side effects: None - path configuration.
MODEL_PATH = Path('ml_pipeline/models/fraud_model_v1.2.3.pkl')
if not MODEL_PATH.exists():
    MODEL_PATH = Path('sprint3/ml_pipeline/models/fraud_model_v1.2.3.pkl')
model = None

# Purpose: Load trained XGBoost model from pickle file into memory.
# Returns: True if model loaded successfully, False otherwise.
# Side effects: Reads model file from filesystem, sets global model variable.
def load_model():
    """Load trained model."""
    global model
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ Loaded model from {MODEL_PATH}")
        return True
    except FileNotFoundError:
        print(f"⚠️  Model not found at {MODEL_PATH}")
        print("   Run: python sprint3/ml_pipeline/train_fraud_model.py")
        return False

# Purpose: Initialize model on module import for immediate availability.
# Side effects: Calls load_model() at import time.
load_model()

# Purpose: Extract feature vector from transaction data for model prediction.
# Params: transaction_data (dict) — transaction details with optional feature values.
# Returns: Dictionary of feature values, using defaults if not provided.
# Side effects: Calculates price deviation ratio if prices provided.
def extract_features(transaction_data):
    """
    Extract features from transaction data.
    For demo, uses mock values if not provided.
    """
    features = {}
    
    # Use provided values or defaults
    features['txn_velocity_1h'] = transaction_data.get('txn_velocity_1h', 1)
    features['wallet_age_days'] = transaction_data.get('wallet_age_days', 30)
    features['avg_ticket_hold_time'] = transaction_data.get('avg_ticket_hold_time', 48)
    features['event_popularity_score'] = transaction_data.get('event_popularity_score', 0.5)
    
    # Calculate price deviation if price provided
    price_paid = transaction_data.get('price_paid', 100)
    floor_price = transaction_data.get('floor_price', 100)
    features['price_deviation_ratio'] = (price_paid - floor_price) / floor_price if floor_price > 0 else 0
    
    features['cross_event_attendance'] = transaction_data.get('cross_event_attendance', 2)
    features['geo_velocity_flag'] = int(transaction_data.get('geo_velocity_flag', False))
    features['payment_method_diversity'] = transaction_data.get('payment_method_diversity', 1)
    features['social_graph_centrality'] = transaction_data.get('social_graph_centrality', 0.5)
    features['time_to_first_resale'] = transaction_data.get('time_to_first_resale', 0)
    
    return features

# Purpose: Health check endpoint to verify API and model status.
# Returns: JSON with service status, model version, and timestamp.
# Side effects: None - read-only endpoint.
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy' if model is not None else 'model_not_loaded',
        'model_version': 'v1.2.3',
        'timestamp': datetime.now().isoformat()
    })

# Purpose: Predict fraud probability for a single transaction.
# Params: JSON body with transaction_id, wallet_address, ticket_id, price_paid, optional fields.
# Returns: JSON with fraud_score, decision, confidence, and feature values.
# Side effects: Runs ML model inference, logs prediction result.
@app.route('/api/v1/ml/predict/fraud', methods=['POST'])
def predict_fraud():
    """
    Predict fraud probability for a transaction.
    
    Request Body:
        {
            "transaction_id": "txn_abc123",
            "wallet_address": "0x742d35Cc...",
            "ticket_id": "evt_xyz_001",
            "price_paid": 150.00,
            "floor_price": 100.00,  // optional
            "timestamp": "2025-11-28T14:30:00Z"  // optional
        }
    
    Response:
        {
            "fraud_score": 0.73,
            "decision": "MANUAL_REVIEW",
            "confidence": 0.89,
            "features": {...},
            "model_version": "v1.2.3"
        }
    """
    if model is None:
        return jsonify({'error': 'Model not loaded. Please train the model first.'}), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['transaction_id', 'wallet_address', 'ticket_id', 'price_paid']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
        
        # Purpose: Extract feature values from transaction data.
        features = extract_features(data)
        
        # Purpose: Convert features to numpy array format required by model.
        # Side effects: Creates feature vector array.
        feature_vector = np.array([[features[col] for col in FEATURE_COLS]])
        
        # Purpose: Run model inference to get fraud probability.
        # Returns: Probability score between 0 and 1.
        # Side effects: Executes ML model prediction.
        fraud_score = float(model.predict_proba(feature_vector)[0][1])
        
        # Purpose: Map fraud score to action decision based on risk thresholds.
        # Side effects: None - decision logic only.
        if fraud_score > 0.85:
            decision = "BLOCKED"
        elif fraud_score > 0.65:
            decision = "MANUAL_REVIEW"
        elif fraud_score > 0.40:
            decision = "REQUIRE_2FA"
        else:
            decision = "APPROVED"
        
        # Purpose: Calculate confidence as distance from decision boundary (0.5).
        confidence = float(1 - abs(fraud_score - 0.5) * 2)
        
        # Get feature importance
        feature_importance = dict(zip(FEATURE_COLS, [float(x) for x in model.feature_importances_]))
        top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3])
        
        response = {
            'transaction_id': data['transaction_id'],
            'fraud_score': round(fraud_score, 3),
            'decision': decision,
            'confidence': round(confidence, 3),
            'features': {k: round(v, 3) for k, v in features.items()},
            'top_features': {k: round(v, 3) for k, v in top_features.items()},
            'model_version': 'v1.2.3',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[{datetime.now()}] {data['transaction_id']}: {decision} (score: {fraud_score:.3f})")
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"Error in fraud prediction: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Purpose: Predict fraud for multiple transactions in a single request.
# Params: JSON body with 'transactions' array of transaction objects.
# Returns: JSON with predictions array containing fraud_score and decision for each transaction.
# Side effects: Runs model inference for each transaction, processes batch.
@app.route('/api/v1/ml/batch/predict', methods=['POST'])
def batch_predict():
    """Batch prediction endpoint for multiple transactions."""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503
    
    try:
        data = request.get_json()
        transactions = data.get('transactions', [])
        
        if not transactions:
            return jsonify({'error': 'No transactions provided'}), 400
        
        results = []
        for txn in transactions:
            features = extract_features(txn)
            feature_vector = np.array([[features[col] for col in FEATURE_COLS]])
            fraud_score = float(model.predict_proba(feature_vector)[0][1])
            
            if fraud_score > 0.85:
                decision = "BLOCKED"
            elif fraud_score > 0.65:
                decision = "MANUAL_REVIEW"
            elif fraud_score > 0.40:
                decision = "REQUIRE_2FA"
            else:
                decision = "APPROVED"
            
            results.append({
                'transaction_id': txn.get('transaction_id', 'unknown'),
                'fraud_score': round(fraud_score, 3),
                'decision': decision
            })
        
        return jsonify({
            'predictions': results,
            'count': len(results),
            'model_version': 'v1.2.3'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Purpose: Retrieve model metadata and training information.
# Returns: JSON with model version, features, and training metrics.
# Side effects: Reads metadata JSON file from filesystem.
@app.route('/api/v1/ml/model/info', methods=['GET'])
def model_info():
    """Get model information and metadata."""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503
    
    try:
        metadata_path = 'sprint3/ml_pipeline/models/model_metadata.json'
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata), 200
    except FileNotFoundError:
        return jsonify({
            'model_version': 'v1.2.3',
            'features': FEATURE_COLS,
            'status': 'metadata_not_found'
        }), 200

# Purpose: Main execution block - start Flask API server with environment-based configuration.
# Side effects: Starts HTTP server, loads ML model, configures debug mode from environment.
if __name__ == '__main__':
    import os
    
    # Purpose: Determine debug mode from environment variable (default: False for production).
    # Side effects: Reads DEBUG environment variable.
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print("=" * 60)
    print("Fraud Detection API")
    print(f"Mode: {'Development' if debug_mode else 'Production'}")
    print("=" * 60)
    
    # Purpose: Load ML model before starting server.
    # Side effects: Loads model from filesystem.
    if load_model():
        print("\n🚀 Starting API server on http://localhost:5001")
        print("\nEndpoints:")
        print("  GET  /health")
        print("  POST /api/v1/ml/predict/fraud")
        print("  POST /api/v1/ml/batch/predict")
        print("  GET  /api/v1/ml/model/info")
        print("\nExample request:")
        print('  curl -X POST http://localhost:5001/api/v1/ml/predict/fraud \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"transaction_id": "test_001", "wallet_address": "0x123", "ticket_id": "evt_001", "price_paid": 50.00}\'')
        print("\n" + "=" * 60)
        
        # Purpose: Start Flask server with environment-based debug configuration.
        # Side effects: Starts HTTP server, enables debug mode only if DEBUG=true.
        app.run(host='0.0.0.0', port=5001, debug=debug_mode)
    else:
        print("\n❌ Cannot start API: Model not found")
        print("   Please run: python sprint3/demos/generate_sample_data.py")
        print("   Then run:    python sprint3/ml_pipeline/train_fraud_model.py")
