"""Unit tests for KPI calculator."""
import pytest
from datetime import datetime, timedelta
from ml_pipeline.kpi_calculator import KPICalculator


def test_kpi_calculator_initialization():
    """Test KPI calculator can be initialized."""
    calc = KPICalculator()
    assert calc is not None


def test_conversion_rate_calculation():
    """Test conversion rate calculation."""
    calc = KPICalculator()
    result = calc.conversion_rate()
    
    assert 'kpi_name' in result
    assert result['kpi_name'] == 'conversion_rate'
    assert 'value' in result
    assert isinstance(result['value'], (int, float))


def test_time_to_finality_calculation():
    """Test time to finality calculation."""
    calc = KPICalculator()
    result = calc.time_to_finality()
    
    assert 'kpi_name' in result
    assert result['kpi_name'] == 'time_to_finality'
    assert 'value' in result
    assert isinstance(result['value'], (int, float))


def test_get_all_kpis():
    """Test getting all KPIs."""
    calc = KPICalculator()
    kpis = calc.get_all_kpis(time_window_hours=24)
    
    assert 'conversion_rate' in kpis
    assert 'time_to_finality' in kpis
    assert 'revenue_per_hour' in kpis
    assert 'fraud_detection_rate' in kpis

