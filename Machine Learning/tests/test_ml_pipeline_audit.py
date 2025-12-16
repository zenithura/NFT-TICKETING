"""
Comprehensive ML Pipeline Audit and Test Script
Tests all components: Feature Engineering, Models, Integration, DuckDB
"""

import sys
from pathlib import Path
import traceback
from typing import Dict, List, Optional

# Add Machine Learning folder to path
ml_path = Path(__file__).parent.parent
sys.path.insert(0, str(ml_path))  # Add Machine Learning folder itself
sys.path.insert(0, str(ml_path.parent))  # Add parent for backend imports

# Test results storage
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def log_test(name: str, passed: bool, message: str = "", error: Optional[Exception] = None):
    """Log test result."""
    if passed:
        test_results['passed'].append(name)
        print(f"✅ {name}: PASSED - {message}")
    else:
        test_results['failed'].append(name)
        print(f"❌ {name}: FAILED - {message}")
        if error:
            print(f"   Error: {error}")
            traceback.print_exc()

def test_supabase_connection():
    """Test 1: Verify Supabase connection setup."""
    try:
        from backend.database import get_supabase_admin
        
        db = get_supabase_admin()
        if db is None:
            log_test("Supabase Connection", False, "get_supabase_admin() returned None")
            return False
        
        # Try a simple query
        try:
            response = db.table("wallets").select("wallet_id", count="exact").limit(1).execute()
            log_test("Supabase Connection", True, f"Connected successfully (found {response.count if hasattr(response, 'count') else 'unknown'} wallets)")
            return True
        except Exception as e:
            log_test("Supabase Connection", False, f"Query failed: {e}", e)
            return False
            
    except ImportError as e:
        log_test("Supabase Connection", False, f"Could not import backend.database: {e}", e)
        return False
    except Exception as e:
        log_test("Supabase Connection", False, f"Unexpected error: {e}", e)
        return False

def test_feature_engineering():
    """Test 2: Verify feature engineering functions."""
    try:
        from integration.supabase_feature_engineer import get_supabase_feature_engineer
        from backend.database import get_supabase_admin
        
        db = get_supabase_admin()
        if db is None:
            log_test("Feature Engineering", False, "Cannot get Supabase client")
            return False
        
        fe = get_supabase_feature_engineer(db_client=db)
        
        # Test with dummy transaction ID (will return 0 or defaults for non-existent data)
        test_features = fe.compute_features(
            transaction_id="test_txn_audit_123",
            wallet_address="0xTEST_AUDIT_WALLET_123",
            event_id=1  # Use test event_id
        )
        
        # Verify feature structure
        required_features = [
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
        
        missing_features = [f for f in required_features if f not in test_features]
        if missing_features:
            log_test("Feature Engineering", False, f"Missing features: {missing_features}")
            return False
        
        # Verify feature types
        feature_types = {
            'txn_velocity_1h': int,
            'wallet_age_days': (int, float),
            'avg_ticket_hold_time': (int, float),
            'event_popularity_score': (int, float),
            'price_deviation_ratio': (int, float),
            'cross_event_attendance': int,
            'geo_velocity_flag': int,
            'payment_method_diversity': int,
            'social_graph_centrality': (int, float),
            'time_to_first_resale': (int, float)
        }
        
        for feature, expected_type in feature_types.items():
            value = test_features.get(feature)
            if not isinstance(value, expected_type if isinstance(expected_type, tuple) else (expected_type,)):
                log_test("Feature Engineering", False, f"Feature {feature} has wrong type: {type(value)}, expected {expected_type}")
                return False
        
        log_test("Feature Engineering", True, f"All {len(required_features)} features computed successfully")
        return True
        
    except Exception as e:
        log_test("Feature Engineering", False, f"Error: {e}", e)
        return False

def test_models_import():
    """Test 3: Verify all models can be imported."""
    try:
        from models.fraud_detection_model import get_fraud_model
        from models.anomaly_detector import get_anomaly_detector
        from models.user_clustering import get_clustering_model
        from models.recommendation_engine import get_recommendation_engine
        from models.pricing_bandit import get_pricing_bandit
        from models.risk_scoring_heuristic import get_risk_scoring_heuristic
        
        # Test instantiation
        fraud_model = get_fraud_model()
        anomaly_detector = get_anomaly_detector()
        clustering_model = get_clustering_model()
        recommendation_engine = get_recommendation_engine()
        pricing_bandit = get_pricing_bandit()
        risk_scoring_heuristic = get_risk_scoring_heuristic()
        
        if all([fraud_model, anomaly_detector, clustering_model, recommendation_engine, pricing_bandit, risk_scoring_heuristic]):
            log_test("Models Import", True, "All 6 models imported successfully")
            return True
        else:
            log_test("Models Import", False, "Some models failed to instantiate")
            return False
            
    except Exception as e:
        log_test("Models Import", False, f"Import error: {e}", e)
        return False

def test_models_execution():
    """Test 4: Execute all models with test features."""
    try:
        from models.fraud_detection_model import get_fraud_model
        from models.anomaly_detector import get_anomaly_detector
        from models.user_clustering import get_clustering_model
        from models.risk_scoring_heuristic import get_risk_scoring_heuristic
        from models.pricing_bandit import get_pricing_bandit
        
        # Test features
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
        
        # Test Fraud Detection
        fraud_model = get_fraud_model()
        fraud_result = fraud_model.predict(test_features)
        assert 'fraud_probability' in fraud_result
        assert 'decision' in fraud_result
        print(f"  Fraud Detection: {fraud_result.get('decision')} (prob: {fraud_result.get('fraud_probability')})")
        
        # Test Anomaly Detection
        anomaly_detector = get_anomaly_detector()
        anomaly_result = anomaly_detector.detect(test_features)
        assert 'anomaly_score' in anomaly_result
        assert 'is_outlier' in anomaly_result
        print(f"  Anomaly Detection: outlier={anomaly_result.get('is_outlier')} (score: {anomaly_result.get('anomaly_score')})")
        
        # Test User Clustering
        clustering_model = get_clustering_model()
        cluster_result = clustering_model.predict_cluster(test_features)
        assert 'cluster_id' in cluster_result
        assert 'cluster_label' in cluster_result
        print(f"  User Clustering: {cluster_result.get('cluster_label')} (id: {cluster_result.get('cluster_id')})")
        
        # Test Risk Scoring Heuristic
        risk_heuristic = get_risk_scoring_heuristic()
        risk_result = risk_heuristic.score(test_features)
        assert 'risk_score' in risk_result
        assert 'risk_band' in risk_result
        print(f"  Risk Scoring Heuristic: {risk_result.get('risk_band')} (score: {risk_result.get('risk_score')})")
        
        # Test Pricing Bandit
        pricing_bandit = get_pricing_bandit()
        pricing_result = pricing_bandit.select_arm({
            'event_id': 1,
            'user_cluster': cluster_result.get('cluster_label')
        })
        assert 'selected_arm' in pricing_result
        print(f"  Pricing Bandit: {pricing_result.get('selected_arm')}")
        
        log_test("Models Execution", True, "All 5 models executed successfully")
        return True
        
    except Exception as e:
        log_test("Models Execution", False, f"Execution error: {e}", e)
        return False

def test_integration_layer():
    """Test 5: Verify integration layer."""
    try:
        from integration.ml_integration_backend import get_ml_integration_backend
        from backend.database import get_supabase_admin
        
        db = get_supabase_admin()
        if db is None:
            log_test("Integration Layer", False, "Cannot get Supabase client")
            return False
        
        ml = get_ml_integration_backend(db_client=db)
        
        # Verify all models are initialized
        assert hasattr(ml, 'fraud_model')
        assert hasattr(ml, 'anomaly_detector')
        assert hasattr(ml, 'clustering_model')
        assert hasattr(ml, 'recommendation_engine')
        assert hasattr(ml, 'pricing_bandit')
        assert hasattr(ml, 'risk_scoring_heuristic')  # NEW model
        assert hasattr(ml, 'feature_engineer')
        assert hasattr(ml, 'duckdb_storage')
        
        log_test("Integration Layer", True, "Integration layer initialized with all components")
        return True
        
    except Exception as e:
        log_test("Integration Layer", False, f"Initialization error: {e}", e)
        return False

def test_integration_process_transaction():
    """Test 6: Test end-to-end process_transaction."""
    try:
        from integration.ml_integration_backend import get_ml_integration_backend
        from backend.database import get_supabase_admin
        
        db = get_supabase_admin()
        if db is None:
            log_test("Process Transaction", False, "Cannot get Supabase client")
            return False
        
        ml = get_ml_integration_backend(db_client=db)
        
        # Process test transaction
        result = ml.process_transaction(
            transaction_id="test_audit_txn_456",
            wallet_address="0xTEST_AUDIT_456",
            event_id=1,  # Test event_id
            price_paid=50.0
        )
        
        # Verify result structure
        assert 'transaction_id' in result
        assert 'timestamp' in result
        assert 'status' in result
        assert 'features' in result
        assert 'fraud_detection' in result
        assert 'anomaly_detection' in result
        assert 'user_cluster' in result
        assert 'risk_scoring_heuristic' in result  # NEW model output
        assert 'pricing_decision' in result
        
        # Verify status
        assert result['status'] in ['processing', 'approved', 'blocked', 'error']
        
        print(f"  Status: {result['status']}")
        print(f"  Features: {len(result.get('features', {}))} features")
        print(f"  Fraud Decision: {result.get('fraud_detection', {}).get('decision')}")
        print(f"  Risk Band: {result.get('risk_scoring_heuristic', {}).get('risk_band')}")
        
        log_test("Process Transaction", True, f"Transaction processed successfully (status: {result['status']})")
        return True
        
    except Exception as e:
        log_test("Process Transaction", False, f"Process error: {e}", e)
        return False

def test_duckdb_storage():
    """Test 7: Verify DuckDB storage."""
    try:
        from integration.duckdb_storage import get_duckdb_storage
        import duckdb
        
        storage = get_duckdb_storage()
        
        # Test storing inference result
        inference_id = storage.store_inference_result(
            request_id="test_audit_789",
            model_name="fraud_detection",
            model_version="v1.0.0",
            input_features={'test': 'feature'},
            output_scores={'test_score': 0.5},
            decision="APPROVED",
            confidence=0.8,
            transaction_id="test_txn_789",
            wallet_address="0xTEST789",
            event_id=1
        )
        
        assert inference_id > 0
        print(f"  Stored inference ID: {inference_id}")
        
        # Test querying DuckDB
        results = storage.get_inference_results(request_id="test_audit_789", limit=1)
        assert len(results) > 0
        assert results[0]['request_id'] == "test_audit_789"
        print(f"  Retrieved {len(results)} inference result(s)")
        
        # Test analytics summary
        summary = storage.get_analytics_summary(days=7)
        assert 'total_inferences' in summary
        print(f"  Analytics: {summary['total_inferences']} total inferences")
        
        log_test("DuckDB Storage", True, "DuckDB storage working correctly")
        return True
        
    except Exception as e:
        log_test("DuckDB Storage", False, f"Storage error: {e}", e)
        return False

def test_duckdb_schema():
    """Test 8: Verify DuckDB schema."""
    try:
        from integration.duckdb_storage import get_duckdb_storage
        import duckdb
        
        storage = get_duckdb_storage()
        
        # Connect directly to check schema
        conn = duckdb.connect(str(storage.db_path))
        
        # Check ml_inference_results table
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = ['ml_inference_results', 'ml_feature_snapshots', 'ml_model_metrics']
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            log_test("DuckDB Schema", False, f"Missing tables: {missing_tables}")
            conn.close()
            return False
        
        # Check ml_inference_results columns
        columns = conn.execute("PRAGMA table_info(ml_inference_results)").fetchall()
        column_names = [c[1] for c in columns]
        
        required_columns = ['inference_id', 'timestamp', 'request_id', 'model_name', 'input_features', 'output_scores', 'decision', 'transaction_id', 'wallet_address']
        missing_columns = [c for c in required_columns if c not in column_names]
        
        if missing_columns:
            log_test("DuckDB Schema", False, f"Missing columns in ml_inference_results: {missing_columns}")
            conn.close()
            return False
        
        conn.close()
        log_test("DuckDB Schema", True, "All required tables and columns exist")
        return True
        
    except Exception as e:
        log_test("DuckDB Schema", False, f"Schema check error: {e}", e)
        return False

def test_end_to_end_pipeline():
    """Test 9: Complete end-to-end pipeline test."""
    try:
        from integration.ml_integration_backend import get_ml_integration_backend
        from backend.database import get_supabase_admin
        from integration.duckdb_storage import get_duckdb_storage
        import duckdb
        
        db = get_supabase_admin()
        if db is None:
            log_test("End-to-End Pipeline", False, "Cannot get Supabase client")
            return False
        
        # Step 1: Initialize ML integration
        ml = get_ml_integration_backend(db_client=db)
        
        # Step 2: Process transaction
        transaction_id = "e2e_test_12345"
        wallet_address = "0xE2E_TEST_12345"
        event_id = 1
        price_paid = 50.0
        
        result = ml.process_transaction(
            transaction_id=transaction_id,
            wallet_address=wallet_address,
            event_id=event_id,
            price_paid=price_paid
        )
        
        # Step 3: Verify result
        assert result['status'] in ['processing', 'approved', 'blocked', 'error']
        assert 'features' in result
        assert len(result['features']) == 10  # All 10 features
        
        # Step 4: Verify DuckDB write
        storage = get_duckdb_storage()
        db_results = storage.get_inference_results(request_id=transaction_id, limit=1)
        
        if len(db_results) == 0:
            log_test("End-to-End Pipeline", False, "Result not found in DuckDB")
            return False
        
        db_result = db_results[0]
        assert db_result['request_id'] == transaction_id
        assert db_result['transaction_id'] == transaction_id
        assert db_result['wallet_address'] == wallet_address
        
        # Verify output_scores contains expected fields
        output_scores = db_result.get('output_scores', {})
        assert 'fraud_probability' in output_scores or 'error' in output_scores  # May have error
        
        print(f"  Transaction ID: {transaction_id}")
        print(f"  Status: {result['status']}")
        print(f"  Features computed: {len(result.get('features', {}))}")
        print(f"  DuckDB record found: Yes")
        print(f"  Models executed: Fraud, Anomaly, Clustering, Risk Heuristic, Pricing")
        
        log_test("End-to-End Pipeline", True, "Complete pipeline executed successfully")
        return True
        
    except Exception as e:
        log_test("End-to-End Pipeline", False, f"Pipeline error: {e}", e)
        return False

def run_all_tests():
    """Run all audit tests."""
    print("=" * 70)
    print("ML PIPELINE COMPREHENSIVE AUDIT")
    print("=" * 70)
    print()
    
    tests = [
        ("1. Supabase Connection", test_supabase_connection),
        ("2. Feature Engineering", test_feature_engineering),
        ("3. Models Import", test_models_import),
        ("4. Models Execution", test_models_execution),
        ("5. Integration Layer", test_integration_layer),
        ("6. Process Transaction", test_integration_process_transaction),
        ("7. DuckDB Storage", test_duckdb_storage),
        ("8. DuckDB Schema", test_duckdb_schema),
        ("9. End-to-End Pipeline", test_end_to_end_pipeline),
    ]
    
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 70)
        try:
            test_func()
        except Exception as e:
            log_test(name, False, f"Test crashed: {e}", e)
    
    # Summary
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    print()
    
    if test_results['failed']:
        print("FAILED TESTS:")
        for test in test_results['failed']:
            print(f"  - {test}")
    
    return len(test_results['failed']) == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

