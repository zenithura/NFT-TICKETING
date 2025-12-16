import time
import logging
from typing import Dict, Any, Optional
from ..core import data_logger, ModelManager
from ..feature_store import feature_store
import numpy as np

# Try to import sklearn
try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class RiskScoreModel(ModelManager):
    def __init__(self):
        super().__init__("risk_score", "config/model_configs/risk_score.json")
        self.data_loader = None  # Will be set externally
        
        # If no model loaded, train a dummy one
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None) # Train dummy

    def train(self, data: Any = None):
        """
        Trains the model. 
        If data is None and data_loader is available, fetches from database.
        Otherwise uses dummy data.
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return
        
        # Try to fetch real data from database
        if data is None and self.data_loader:
            logger.info("Fetching real transaction data from database...")
            try:
                transactions = self.data_loader.fetch_transaction_history(limit=500)
                
                if transactions and len(transactions) > 10:
                    # Extract features from real data
                    X_list = []
                    y_list = []
                    
                    for tx in transactions:
                        user_id = tx.get("user_id")
                        if not user_id:
                            continue
                        
                        # Get user stats
                        user_stats = self.data_loader.get_user_transaction_stats(user_id)
                        
                        # Extract features
                        features = feature_store.extract_risk_features(tx, user_stats)
                        
                        # Create feature vector
                        X_list.append([
                            features["amount"],
                            features["user_tx_count"]
                        ])
                        
                        # Label: high risk if amount > 1000 or (amount > 500 and tx_count < 3)
                        # This is a heuristic label - in production you'd have actual fraud labels
                        is_high_risk = (
                            features["amount"] > 1000 or 
                            (features["amount"] > 500 and features["user_tx_count"] < 3)
                        )
                        y_list.append(1 if is_high_risk else 0)
                    
                    if len(X_list) > 10:
                        X = np.array(X_list)
                        y = np.array(y_list)
                        logger.info(f"Training on {len(X)} real transactions from database")
                        data = (X, y)
                else:
                    logger.warning("Insufficient data from database, using dummy data")
            except Exception as e:
                logger.error(f"Error fetching training data: {e}")
                logger.warning("Falling back to dummy data")
        
        # Use provided data or dummy data
        if data is None:
            logger.info("Using dummy training data")
            # Dummy data
            X = np.array([[10, 1], [100, 5], [1000, 10], [50, 2], [2000, 2]])
            y = np.array([0, 0, 1, 0, 1])
        else:
            X, y = data
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.model.fit(X, y)
        self.save()
        
        # Save metrics if data_loader available
        if self.data_loader:
            try:
                # Calculate training metrics
                train_score = self.model.score(X, y)
                metrics = {
                    "train_accuracy": train_score,
                    "n_samples": len(X),
                    "n_features": X.shape[1]
                }
                self.data_loader.save_model_metrics(
                    model_name="risk_score",
                    metrics=metrics,
                    metadata={"training_date": time.strftime("%Y-%m-%d")}
                )
                logger.info(f"Saved training metrics: {metrics}")
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")

    def predict(self, inputs: Dict[str, Any]) -> float:
        """
        Predict risk score for a transaction.
        
        Args:
            inputs: Can contain:
                - amount: Transaction amount
                - user_tx_count: User transaction count
                OR
                - transaction_id: Transaction ID (will fetch from DB)
                - user_id: User ID (will fetch stats from DB)
        
        Returns:
            Risk score (0.0 - 1.0)
        """
        start_time = time.time()
        
        # Extract features
        amount = inputs.get("amount", 0)
        tx_count = inputs.get("user_tx_count", 0)
        
        # If data_loader available and we have IDs, fetch real data
        if self.data_loader:
            try:
                # Fetch transaction data if transaction_id provided
                if "transaction_id" in inputs:
                    tx_data = self.data_loader.fetch_transaction_by_id(inputs["transaction_id"])
                    if tx_data:
                        amount = tx_data.get("amount", amount)
                        user_id = tx_data.get("user_id")
                        if user_id:
                            user_stats = self.data_loader.get_user_transaction_stats(user_id)
                            tx_count = user_stats.get("count", 0)
                
                # Or fetch user stats if user_id provided
                elif "user_id" in inputs:
                    user_stats = self.data_loader.get_user_transaction_stats(inputs["user_id"])
                    tx_count = user_stats.get("count", 0)
            except Exception as e:
                logger.error(f"Error fetching data for prediction: {e}")

        risk_score = 0.0

        if SKLEARN_AVAILABLE and self.model:
            input_vector = np.array([[amount, tx_count]])
            risk_score = self.model.predict_proba(input_vector)[0][1]
        else:
            # Fallback heuristic
            if amount > 1000:
                risk_score = 0.8
            elif amount > 500 and tx_count < 3:
                risk_score = 0.6
            else:
                risk_score = 0.1

        latency = (time.time() - start_time) * 1000
        
        # Log to data_logger
        data_logger.log("risk_score_model", inputs, risk_score, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="risk_score",
                    input_data={"amount": amount, "user_tx_count": tx_count},
                    output=float(risk_score),
                    confidence=None,
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return float(risk_score)

    def _to_float(self, val):
        """Helper to safely convert numpy types to python float."""
        if isinstance(val, (list, tuple, np.ndarray)):
            if len(val) == 1:
                return float(val[0])
            # If it's an array with more than 1 element, take the first one (hacky but prevents crash)
            # ideally we shouldn't be here if logic is correct
            return float(val[0])
        return float(val)

    def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Returns SHAP values for the prediction."""
        try:
            import shap
        except ImportError:
            return {"error": "SHAP not installed"}

        if not SKLEARN_AVAILABLE or not self.model:
            return {"error": "Model not available"}

        amount = inputs.get("amount", 0)
        tx_count = inputs.get("user_tx_count", 0)
        input_vector = np.array([[amount, tx_count]])

        # Create explainer (TreeExplainer is best for Random Forest)
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(input_vector)

        # For binary classification, shap_values is a list of arrays [class0, class1]
        # We want class 1 (High Risk)
        if isinstance(shap_values, list):
            # shap_values[1] is the array for class 1
            # shap_values[1][0] is the explanation for the first (and only) sample
            values = shap_values[1][0]
        else:
            values = shap_values[0]

        # Handle expected_value
        base_value = explainer.expected_value
        if isinstance(base_value, list) or isinstance(base_value, np.ndarray):
            if len(base_value) > 1:
                base_value = base_value[1]
            else:
                base_value = base_value[0]

        return {
            "base_value": self._to_float(base_value),
            "features": {
                "amount": self._to_float(values[0]),
                "user_tx_count": self._to_float(values[1])
            }
        }

risk_model = RiskScoreModel()
