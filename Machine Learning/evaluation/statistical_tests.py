"""
Statistical Tests - Significance Testing
Provides statistical testing utilities for model evaluation.
"""

from typing import List, Tuple
from scipy import stats
import numpy as np


def mcnemar_test(y_true: List[int], y_pred_baseline: List[int], 
                 y_pred_model: List[int]) -> Tuple[float, float]:
    """
    McNemar's test for paired binary classifiers.
    
    Tests if model performs significantly better than baseline.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred_baseline: Baseline predictions (0 or 1)
        y_pred_model: Model predictions (0 or 1)
        
    Returns:
        Tuple of (chi2_statistic, p_value)
    """
    # Create contingency table
    n00 = sum(1 for i in range(len(y_true)) 
              if y_pred_baseline[i] == 0 and y_pred_model[i] == 0)
    n01 = sum(1 for i in range(len(y_true)) 
              if y_pred_baseline[i] == 0 and y_pred_model[i] == 1)
    n10 = sum(1 for i in range(len(y_true)) 
              if y_pred_baseline[i] == 1 and y_pred_model[i] == 0)
    n11 = sum(1 for i in range(len(y_true)) 
              if y_pred_baseline[i] == 1 and y_pred_model[i] == 1)
    
    # McNemar's test (only uses discordant pairs)
    # Chi-square = (|n01 - n10| - 1)^2 / (n01 + n10)
    if (n01 + n10) == 0:
        return (0.0, 1.0)
    
    chi2 = ((abs(n01 - n10) - 1) ** 2) / (n01 + n10)
    p_value = 1 - stats.chi2.cdf(chi2, df=1)
    
    return (chi2, p_value)


def t_test_paired(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Paired t-test for comparing two samples.
    
    Args:
        sample1: First sample (baseline)
        sample2: Second sample (model)
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    t_stat, p_value = stats.ttest_rel(sample1, sample2)
    return (float(t_stat), float(p_value))


def chi_squared_test(observed: List[int], expected: List[int]) -> Tuple[float, float]:
    """
    Chi-squared test for categorical data.
    
    Args:
        observed: Observed frequencies
        expected: Expected frequencies
        
    Returns:
        Tuple of (chi2_statistic, p_value)
    """
    chi2, p_value = stats.chisquare(observed, expected)
    return (float(chi2), float(p_value))


def confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for a sample.
    
    Args:
        data: Sample data
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    n = len(data)
    mean_val = np.mean(data)
    std_err = stats.sem(data)
    
    h = std_err * stats.t.ppf((1 + confidence) / 2, n - 1)
    
    return (float(mean_val - h), float(mean_val + h))


def calculate_statistics(data: List[float]) -> dict:
    """
    Calculate basic statistics for a sample.
    
    Args:
        data: Sample data
        
    Returns:
        Dict with mean, std_dev, min, max, median
    """
    return {
        'mean': float(np.mean(data)),
        'std_dev': float(np.std(data)),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'median': float(np.median(data)),
        'n': len(data)
    }

