"""Unit tests for Alert Rules."""
import pytest
from monitoring.alert_rules import AlertRule, AlertSystem

def test_alert_rule_evaluation():
    """Test individual alert rule logic."""
    rule = AlertRule("test", ">", 100.0, "HIGH")
    
    assert rule.evaluate(150.0) is True
    assert rule.evaluate(50.0) is False
    assert rule.evaluate(100.0) is False

    rule_eq = AlertRule("test", "==", 10.0, "LOW")
    assert rule_eq.evaluate(10.0) is True
    assert rule_eq.evaluate(11.0) is False

def test_alert_system_initialization():
    """Test alert system loads default rules."""
    system = AlertSystem()
    assert len(system.rules) >= 3
    
    names = [r.name for r in system.rules]
    assert 'event_processing_lag_high' in names
    assert 'api_error_rate_high' in names
