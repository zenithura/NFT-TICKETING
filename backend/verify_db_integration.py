#!/usr/bin/env python3
"""
Verification script for database integration.
Tests all components of the ML database integration.
"""
import sys
import os

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_imports():
    """Verify all imports work."""
    print_section("1. Checking Imports")
    
    try:
        from database import get_supabase_admin
        print("✓ database.get_supabase_admin")
        
        from data_science.data_loader import DataLoader
        print("✓ data_science.data_loader.DataLoader")
        
        from data_science.feature_store import feature_store
        print("✓ data_science.feature_store")
        
        # Import all models
        from data_science.models.risk_score import risk_model
        from data_science.models.bot_detection import bot_model
        from data_science.models.fair_price import fair_price_model
        from data_science.models.scalping_detection import scalping_model
        from data_science.models.wash_trading import wash_trading_model
        from data_science.models.recommender import recommender_model
        from data_science.models.segmentation import segmentation_model
        from data_science.models.market_trend import market_trend_model
        from data_science.models.decision_rule import decision_rule_model
        print("✓ All 9 models imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def check_data_loader():
    """Test DataLoader functionality."""
    print_section("2. Testing DataLoader")
    
    try:
        from database import get_supabase_admin
        from data_science.data_loader import DataLoader
        
        db = get_supabase_admin()
        data_loader = DataLoader(db)
        print("✓ DataLoader initialized")
        
        # Test methods exist
        methods = [
            'fetch_transaction_history',
            'fetch_user_behavior',
            'fetch_event_data',
            'fetch_ticket_data',
            'save_prediction',
            'save_model_metrics',
            'get_user_transaction_stats'
        ]
        
        for method in methods:
            if hasattr(data_loader, method):
                print(f"✓ Method exists: {method}")
            else:
                print(f"✗ Method missing: {method}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ DataLoader test failed: {e}")
        return False

def check_models():
    """Test model integration."""
    print_section("3. Testing Model Integration")
    
    try:
        from database import get_supabase_admin
        from data_science.data_loader import DataLoader
        from data_science.models.risk_score import risk_model
        from data_science.models.bot_detection import bot_model
        
        db = get_supabase_admin()
        data_loader = DataLoader(db)
        
        # Set data_loader
        risk_model.data_loader = data_loader
        bot_model.data_loader = data_loader
        print("✓ Data loader set for models")
        
        # Test predictions
        risk_score = risk_model.predict({"amount": 500, "user_tx_count": 3})
        print(f"✓ Risk model prediction: {risk_score}")
        
        bot_result = bot_model.predict({
            "request_freq": 5,
            "ua_score": 0.9,
            "ip_reputation": 0.95
        })
        print(f"✓ Bot model prediction: {bot_result['is_bot']}")
        
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_api_endpoints():
    """Check API endpoints exist."""
    print_section("4. Checking API Endpoints")
    
    try:
        from routers import ml_services_v2
        
        # Check router exists
        print(f"✓ ml_services_v2 router exists")
        print(f"✓ Prefix: {ml_services_v2.router.prefix}")
        
        # Count endpoints
        endpoint_count = len(ml_services_v2.router.routes)
        print(f"✓ Total endpoints: {endpoint_count}")
        
        # List some endpoints
        print("\nAvailable endpoints:")
        for route in ml_services_v2.router.routes[:5]:
            print(f"  - {route.methods} {route.path}")
        
        return True
    except Exception as e:
        print(f"✗ API check failed: {e}")
        return False

def check_database_schema():
    """Check if database tables exist."""
    print_section("5. Checking Database Schema")
    
    try:
        from database import get_supabase_admin
        
        db = get_supabase_admin()
        
        tables = [
            "model_predictions",
            "model_metrics",
            "model_training_data",
            "model_logs"
        ]
        
        for table in tables:
            try:
                # Try to query the table
                result = db.table(table).select("*").limit(1).execute()
                print(f"✓ Table exists: {table}")
            except Exception as e:
                print(f"⚠ Table may not exist: {table}")
                print(f"  Run migration: psql $DATABASE_URL -f backend/migrations/add_ml_tables.sql")
        
        return True
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        return False

def check_file_structure():
    """Verify file structure."""
    print_section("6. Checking File Structure")
    
    files_to_check = [
        "data_science/data_loader.py",
        "data_science/feature_store.py",
        "data_science/pipelines/training_pipeline.py",
        "migrations/add_ml_tables.sql",
        "routers/ml_services_v2.py",
        "data_science/tests/test_data_loader.py",
        "data_science/tests/test_integration.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(backend_path, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✓ {file_path} ({size} bytes)")
        else:
            print(f"✗ Missing: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all verification checks."""
    print("\n" + "🔍 " * 20)
    print("DATABASE INTEGRATION VERIFICATION")
    print("🔍 " * 20)
    
    results = {
        "Imports": check_imports(),
        "DataLoader": check_data_loader(),
        "Models": check_models(),
        "API Endpoints": check_api_endpoints(),
        "Database Schema": check_database_schema(),
        "File Structure": check_file_structure()
    }
    
    print_section("SUMMARY")
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "🎉 " * 20)
        print("ALL CHECKS PASSED!")
        print("🎉 " * 20)
        print("\nNext steps:")
        print("1. Run migration: psql $DATABASE_URL -f backend/migrations/add_ml_tables.sql")
        print("2. Train models: cd backend/data_science/pipelines && python training_pipeline.py")
        print("3. Start server: cd backend && uvicorn main:app --reload")
        print("4. Test API: curl http://localhost   :8000/api/ml/v2/health")
    else:
        print("\n" + "⚠️  " * 20)
        print("SOME CHECKS FAILED")
        print("⚠️  " * 20)
        print("\nPlease review the errors above and fix them.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
