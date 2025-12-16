"""
Baseline Comparison - Model vs Baseline Evaluation
Compares ML model performance against baseline system.
"""

import json
from pathlib import Path
from typing import Dict
from evaluation.statistical_tests import mcnemar_test, t_test_paired, confidence_interval, calculate_statistics


def compare_fraud_detection(y_true: list, y_pred_baseline: list, y_pred_model: list) -> Dict:
    """
    Compare fraud detection model against baseline.
    
    Args:
        y_true: True labels
        y_pred_baseline: Baseline predictions
        y_pred_model: Model predictions
        
    Returns:
        Dict with comparison metrics
    """
    from sklearn.metrics import precision_score, recall_score, f1_score
    
    # Calculate metrics
    baseline_precision = precision_score(y_true, y_pred_baseline)
    baseline_recall = recall_score(y_true, y_pred_baseline)
    baseline_f1 = f1_score(y_true, y_pred_baseline)
    
    model_precision = precision_score(y_true, y_pred_model)
    model_recall = recall_score(y_true, y_pred_model)
    model_f1 = f1_score(y_true, y_pred_model)
    
    # Statistical significance test
    chi2, p_value = mcnemar_test(y_true, y_pred_baseline, y_pred_model)
    
    return {
        'baseline': {
            'precision': round(baseline_precision, 4),
            'recall': round(baseline_recall, 4),
            'f1_score': round(baseline_f1, 4)
        },
        'model': {
            'precision': round(model_precision, 4),
            'recall': round(model_recall, 4),
            'f1_score': round(model_f1, 4)
        },
        'improvement': {
            'precision_pct': round((model_precision - baseline_precision) / baseline_precision * 100, 2),
            'recall_pct': round((model_recall - baseline_recall) / baseline_recall * 100, 2),
            'f1_pct': round((model_f1 - baseline_f1) / baseline_f1 * 100, 2)
        },
        'statistical_test': {
            'test': 'mcnemar',
            'chi2': round(chi2, 4),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05
        }
    }


def compare_revenue(revenue_baseline: list, revenue_model: list) -> Dict:
    """
    Compare revenue between baseline and model.
    
    Args:
        revenue_baseline: Baseline revenue per period
        revenue_model: Model revenue per period
        
    Returns:
        Dict with comparison metrics
    """
    baseline_stats = calculate_statistics(revenue_baseline)
    model_stats = calculate_statistics(revenue_model)
    
    baseline_ci = confidence_interval(revenue_baseline)
    model_ci = confidence_interval(revenue_model)
    
    # Paired t-test
    t_stat, p_value = t_test_paired(revenue_baseline, revenue_model)
    
    improvement_pct = (model_stats['mean'] - baseline_stats['mean']) / baseline_stats['mean'] * 100
    
    return {
        'baseline': {
            **baseline_stats,
            'ci_95': baseline_ci
        },
        'model': {
            **model_stats,
            'ci_95': model_ci
        },
        'improvement': {
            'absolute': round(model_stats['mean'] - baseline_stats['mean'], 2),
            'pct': round(improvement_pct, 2)
        },
        'statistical_test': {
            'test': 'paired_t_test',
            't_statistic': round(t_stat, 4),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05
        }
    }


if __name__ == "__main__":
    # Example usage
    print("Baseline Comparison Utilities")
    print("Use these functions to compare model performance against baselines")

