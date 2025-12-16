"""
KPI Calculator - Primary KPI Computation
Computes and tracks key performance indicators for ML models.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, stdev
import math


class KPICalculator:
    """
    Calculates primary KPIs for ML model evaluation.
    
    KPIs:
    1. Fraud Detection Precision-Recall
    2. Transaction Success Rate
    3. Revenue Per User (RPU)
    4. False Positive Rate (FPR)
    5. Recommendation Click-Through Rate (CTR)
    6. Average Anomaly Detection Latency
    """
    
    def __init__(self, baseline_path: Optional[Path] = None):
        """
        Initialize KPI calculator.
        
        Args:
            baseline_path: Path to baseline KPI snapshot
        """
        self.baseline_path = baseline_path or Path(__file__).parent / "kpi_baseline.json"
        self.baseline = self._load_baseline()
    
    def _load_baseline(self) -> Dict:
        """Load baseline KPIs."""
        if self.baseline_path.exists():
            with open(self.baseline_path, 'r') as f:
                return json.load(f)
        return {}
    
    def calculate_precision_recall(self, true_positives: int, false_positives: int,
                                  false_negatives: int) -> Dict:
        """
        Calculate precision and recall for fraud detection.
        
        Args:
            true_positives: Number of correctly identified fraud cases
            false_positives: Number of false fraud alerts
            false_negatives: Number of missed fraud cases
            
        Returns:
            Dict with precision, recall, f1_score, and confidence intervals
        """
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Calculate 95% confidence intervals (Wilson score interval)
        n_total = true_positives + false_positives + false_negatives
        precision_ci = self._wilson_confidence_interval(true_positives, true_positives + false_positives, 0.95)
        recall_ci = self._wilson_confidence_interval(true_positives, true_positives + false_negatives, 0.95)
        
        return {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1_score, 4),
            'precision_ci_95': precision_ci,
            'recall_ci_95': recall_ci,
            'baseline_precision': self.baseline.get('precision', 0.72),
            'baseline_recall': self.baseline.get('recall', 0.68),
            'improvement_precision': round((precision - self.baseline.get('precision', 0.72)) / self.baseline.get('precision', 0.72) * 100, 2),
            'improvement_recall': round((recall - self.baseline.get('recall', 0.68)) / self.baseline.get('recall', 0.68) * 100, 2)
        }
    
    def calculate_transaction_success_rate(self, successful: int, total: int) -> Dict:
        """
        Calculate transaction success rate.
        
        Args:
            successful: Number of successful transactions
            total: Total transaction attempts
            
        Returns:
            Dict with success_rate and confidence interval
        """
        success_rate = successful / total if total > 0 else 0.0
        ci = self._wilson_confidence_interval(successful, total, 0.95)
        
        return {
            'success_rate': round(success_rate, 4),
            'success_rate_pct': round(success_rate * 100, 2),
            'ci_95': ci,
            'baseline': self.baseline.get('transaction_success_rate', 0.923),
            'improvement': round((success_rate - self.baseline.get('transaction_success_rate', 0.923)) * 100, 2)
        }
    
    def calculate_revenue_per_user(self, total_revenue: float, n_users: int) -> Dict:
        """
        Calculate revenue per user.
        
        Args:
            total_revenue: Total revenue
            n_users: Number of active users
            
        Returns:
            Dict with rpu, mean, std_dev (if multiple periods)
        """
        rpu = total_revenue / n_users if n_users > 0 else 0.0
        
        baseline_rpu = self.baseline.get('revenue_per_user', 45.20)
        
        return {
            'revenue_per_user': round(rpu, 2),
            'baseline': baseline_rpu,
            'improvement_pct': round((rpu - baseline_rpu) / baseline_rpu * 100, 2),
            'absolute_improvement': round(rpu - baseline_rpu, 2)
        }
    
    def calculate_false_positive_rate(self, false_positives: int, true_negatives: int) -> Dict:
        """
        Calculate false positive rate.
        
        Args:
            false_positives: Number of false positives
            true_negatives: Number of true negatives
            
        Returns:
            Dict with fpr and confidence interval
        """
        fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
        ci = self._wilson_confidence_interval(false_positives, false_positives + true_negatives, 0.95)
        
        baseline_fpr = self.baseline.get('false_positive_rate', 0.15)
        
        return {
            'false_positive_rate': round(fpr, 4),
            'fpr_pct': round(fpr * 100, 2),
            'ci_95': ci,
            'baseline': baseline_fpr,
            'improvement_pct': round((baseline_fpr - fpr) / baseline_fpr * 100, 2)  # Negative is good
        }
    
    def calculate_recommendation_ctr(self, clicks: int, impressions: int) -> Dict:
        """
        Calculate recommendation click-through rate.
        
        Args:
            clicks: Number of recommendation clicks
            impressions: Number of recommendations shown
            
        Returns:
            Dict with ctr and confidence interval
        """
        ctr = clicks / impressions if impressions > 0 else 0.0
        ci = self._wilson_confidence_interval(clicks, impressions, 0.95)
        
        baseline_ctr = self.baseline.get('recommendation_ctr', 0.032)
        
        return {
            'ctr': round(ctr, 4),
            'ctr_pct': round(ctr * 100, 2),
            'ci_95': ci,
            'baseline': baseline_ctr,
            'improvement_pct': round((ctr - baseline_ctr) / baseline_ctr * 100, 2)
        }
    
    def calculate_anomaly_detection_latency(self, latencies: List[float]) -> Dict:
        """
        Calculate average anomaly detection latency.
        
        Args:
            latencies: List of latency values in seconds
            
        Returns:
            Dict with mean, std_dev, percentiles
        """
        if not latencies:
            return {'mean': 0.0, 'std_dev': 0.0, 'p50': 0.0, 'p95': 0.0, 'p99': 0.0}
        
        mean_latency = mean(latencies)
        std_latency = stdev(latencies) if len(latencies) > 1 else 0.0
        
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if len(sorted_latencies) > 100 else sorted_latencies[-1]
        
        baseline_latency = self.baseline.get('anomaly_detection_latency', 45.0)
        
        return {
            'mean': round(mean_latency, 3),
            'std_dev': round(std_latency, 3),
            'p50': round(p50, 3),
            'p95': round(p95, 3),
            'p99': round(p99, 3),
            'baseline': baseline_latency,
            'improvement_pct': round((baseline_latency - mean_latency) / baseline_latency * 100, 2)
        }
    
    def _wilson_confidence_interval(self, successes: int, total: int, confidence: float = 0.95) -> tuple:
        """
        Calculate Wilson score confidence interval.
        
        Args:
            successes: Number of successes
            total: Total trials
            confidence: Confidence level (default 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if total == 0:
            return (0.0, 0.0)
        
        z = 1.96 if confidence == 0.95 else 1.645  # For 95% or 90% CI
        
        p = successes / total
        n = total
        
        denominator = 1 + (z**2 / n)
        center = (p + (z**2 / (2 * n))) / denominator
        margin = (z / denominator) * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))
        
        return (round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4))
    
    def get_all_kpis(self) -> Dict:
        """
        Get all KPIs (placeholder - would calculate from actual data).
        
        Returns:
            Dict with all KPIs
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'baseline_loaded': len(self.baseline) > 0,
            'note': 'Use specific KPI calculation methods with actual data'
        }


# Singleton instance
_kpi_calculator = None

def get_kpi_calculator() -> KPICalculator:
    """Get singleton KPI calculator instance."""
    global _kpi_calculator
    if _kpi_calculator is None:
        _kpi_calculator = KPICalculator()
    return _kpi_calculator

