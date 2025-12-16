"""
Risk Scoring Heuristic Model - Rule-Based Risk Assessment
Complementary to XGBoost fraud detection model.
Uses rule-based heuristics for fast risk assessment.
"""

from typing import Dict, Optional
from datetime import datetime


class RiskScoringHeuristic:
    """
    Rule-based risk scoring heuristic for transaction risk assessment.
    
    This is a complementary model to the XGBoost fraud detection model.
    It provides fast, interpretable risk scoring based on business rules.
    
    Input: Feature dict (from Supabase)
    Output: Risk score [0, 1], risk band (LOW/MEDIUM/HIGH), reasons
    """
    
    MODEL_VERSION = "v1.0.0"
    MODEL_TYPE = "rule_based_heuristic"
    
    def __init__(self):
        """Initialize risk scoring heuristic with thresholds."""
        self.thresholds = {
            'high_risk': 0.75,
            'medium_risk': 0.50,
            'low_risk': 0.25
        }
    
    def score(self, features: Dict) -> Dict:
        """
        Calculate risk score using rule-based heuristic.
        
        Risk Rules:
        - High transaction velocity (>10/hour) → +0.3
        - New wallet (<7 days) → +0.2
        - High price deviation (>50%) → +0.2
        - Geo velocity flag (rapid location changes) → +0.3
        - Low attendance (<2 events) → +0.1
        
        Maximum score: 1.0 (normalized)
        
        Args:
            features: Feature dict from feature engineering
            
        Returns:
            Dict with:
                - risk_score: float [0, 1]
                - risk_band: str (LOW/MEDIUM/HIGH)
                - reasons: list of risk factors
                - model_version: str
                - model_type: str
        """
        score = 0.0
        reasons = []
        
        # Rule 1: High transaction velocity
        txn_velocity = features.get('txn_velocity_1h', 0)
        if txn_velocity > 10:
            score += 0.3
            reasons.append('high_transaction_velocity')
        
        # Rule 2: New wallet
        wallet_age = features.get('wallet_age_days', 30)
        if wallet_age < 7:
            score += 0.2
            reasons.append('new_wallet')
        
        # Rule 3: High price deviation
        price_dev = abs(features.get('price_deviation_ratio', 0))
        if price_dev > 0.5:
            score += 0.2
            reasons.append('high_price_deviation')
        
        # Rule 4: Geo velocity flag
        geo_velocity = features.get('geo_velocity_flag', 0)
        if geo_velocity == 1:
            score += 0.3
            reasons.append('geo_velocity_flag')
        
        # Rule 5: Low attendance
        attendance = features.get('cross_event_attendance', 0)
        if attendance < 2:
            score += 0.1
            reasons.append('low_attendance')
        
        # Normalize to [0, 1]
        score = min(score, 1.0)
        
        # Determine risk band
        if score >= self.thresholds['high_risk']:
            band = 'HIGH'
        elif score >= self.thresholds['medium_risk']:
            band = 'MEDIUM'
        else:
            band = 'LOW'
        
        return {
            'risk_score': round(score, 3),
            'risk_band': band,
            'reasons': reasons,
            'model_version': self.MODEL_VERSION,
            'model_type': self.MODEL_TYPE,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict(self, features: Dict) -> Dict:
        """
        Alias for score() to match interface with other models.
        
        Args:
            features: Feature dict from feature engineering
            
        Returns:
            Dict with risk score and band
        """
        return self.score(features)


# Singleton instance
_risk_scoring_heuristic = None

def get_risk_scoring_heuristic() -> RiskScoringHeuristic:
    """Get singleton risk scoring heuristic instance."""
    global _risk_scoring_heuristic
    if _risk_scoring_heuristic is None:
        _risk_scoring_heuristic = RiskScoringHeuristic()
    return _risk_scoring_heuristic


if __name__ == "__main__":
    # Example usage
    heuristic = get_risk_scoring_heuristic()
    
    # Example features
    test_features = {
        'txn_velocity_1h': 15,  # High velocity
        'wallet_age_days': 3,  # New wallet
        'price_deviation_ratio': 0.6,  # High deviation
        'geo_velocity_flag': 1,  # Geo velocity
        'cross_event_attendance': 1  # Low attendance
    }
    
    result = heuristic.score(test_features)
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Band: {result['risk_band']}")
    print(f"Reasons: {result['reasons']}")

