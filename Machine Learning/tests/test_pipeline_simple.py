"""
Simplified ML Pipeline Test
Tests core functionality without complex imports.
"""

import sys
import os
from pathlib import Path

# Setup paths
ml_path = Path(__file__).parent.parent
project_root = ml_path.parent

# Add to path
if str(ml_path) not in sys.path:
    sys.path.insert(0, str(ml_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"ML Path: {ml_path}")
print(f"Project Root: {project_root}")
print(f"Python Path: {sys.path[:3]}")
print()

# Test results
results = []

def test_imports():
    """Test 1: Basic imports."""
    print("Test 1: Imports")
    try:
        # Test model imports
        from Machine_Learning.models.fraud_detection_model import get_fraud_model
        from Machine_Learning.models.anomaly_detector import get_anomaly_detector
        from Machine_Learning.models.user_clustering import get_clustering_model
        from Machine_Learning.models.risk_scoring_heuristic import get_risk_scoring_heuristic
        
        print("  ✅ Model imports OK")
        results.append(("Imports", True))
        return True
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        results.append(("Imports", False))
        return False

def test_models():
    """Test 2: Model instantiation."""
    print("\nTest 2: Model Instantiation")
    try:
        from Machine_Learning.models.fraud_detection_model import get_fraud_model
        from Machine_Learning.models.anomaly_detector import get_anomaly_detector
        from Machine_Learning.models.user_clustering import get_clustering_model
        from Machine_Learning.models.risk_scoring_heuristic import get_risk_scoring_heuristic
        
        fraud = get_fraud_model()
        anomaly = get_anomaly_detector()
        cluster = get_clustering_model()
        risk = get_risk_scoring_heuristic()
        
        print("  ✅ All models instantiated")
        results.append(("Model Instantiation", True))
        return True
    except Exception as e:
        print(f"  ❌ Instantiation error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Model Instantiation", False))
        return False

def test_model_execution():
    """Test 3: Model execution."""
    print("\nTest 3: Model Execution")
    try:
        from Machine_Learning.models.fraud_detection_model import get_fraud_model
        from Machine_Learning.models.anomaly_detector import get_anomaly_detector
        from Machine_Learning.models.user_clustering import get_clustering_model
        from Machine_Learning.models.risk_scoring_heuristic import get_risk_scoring_heuristic
        
        test_features = {
            'txn_velocity_1h': 2,
            'wallet_age_days': 30.5,
            'avg_ticket_hold_time': 48.0,
            'event_popularity_score': 0.75,
            'price_deviation_ratio': 0.1,
            'cross_event_attendance': 3,
            'geo_velocity_flag': 0,
            'payment_method_diversity': 1,
            'social_graph_centrality': 0.5,
            'time_to_first_resale': 0.0
        }
        
        fraud = get_fraud_model()
        fraud_result = fraud.predict(test_features)
        print(f"  Fraud: {fraud_result.get('decision')} (prob: {fraud_result.get('fraud_probability')})")
        
        anomaly = get_anomaly_detector()
        anomaly_result = anomaly.detect(test_features)
        print(f"  Anomaly: outlier={anomaly_result.get('is_outlier')}")
        
        cluster = get_clustering_model()
        cluster_result = cluster.predict_cluster(test_features)
        print(f"  Cluster: {cluster_result.get('cluster_label')}")
        
        risk = get_risk_scoring_heuristic()
        risk_result = risk.score(test_features)
        print(f"  Risk: {risk_result.get('risk_band')} (score: {risk_result.get('risk_score')})")
        
        print("  ✅ All models executed")
        results.append(("Model Execution", True))
        return True
    except Exception as e:
        print(f"  ❌ Execution error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Model Execution", False))
        return False

def test_duckdb():
    """Test 4: DuckDB storage."""
    print("\nTest 4: DuckDB Storage")
    try:
        from Machine_Learning.integration.duckdb_storage import get_duckdb_storage
        
        storage = get_duckdb_storage()
        
        # Test write
        inference_id = storage.store_inference_result(
            request_id="simple_test_123",
            model_name="test",
            model_version="v1.0",
            input_features={'test': 'data'},
            output_scores={'score': 0.5},
            decision="APPROVED"
        )
        
        print(f"  Stored inference ID: {inference_id}")
        
        # Test read
        results_db = storage.get_inference_results(request_id="simple_test_123", limit=1)
        print(f"  Retrieved {len(results_db)} result(s)")
        
        print("  ✅ DuckDB storage working")
        results.append(("DuckDB Storage", True))
        return True
    except Exception as e:
        print(f"  ❌ DuckDB error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("DuckDB Storage", False))
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("SIMPLIFIED ML PIPELINE TEST")
    print("=" * 70)
    print()
    
    # Try with space in path (Machine Learning)
    try:
        test_imports()
        test_models()
        test_model_execution()
        test_duckdb()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

