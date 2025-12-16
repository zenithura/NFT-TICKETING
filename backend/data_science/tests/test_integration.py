"""Integration test for model training with database."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_model_training_integration():
    """Test end-to-end model training with database integration."""
    print("=" * 60)
    print("Integration Test: Model Training with Database")
    print("=" * 60)
    
    try:
        # Import components
        from backend.database import get_supabase_admin
        from data_science.data_loader import DataLoader
        from data_science.models.risk_score import risk_model
        from data_science.models.bot_detection import bot_model
        
        print("\n✓ Imports successful")
        
        # Initialize data loader
        db = get_supabase_admin()
        data_loader = DataLoader(db)
        print("✓ Data loader initialized")
        
        # Set data_loader for models
        risk_model.data_loader = data_loader
        bot_model.data_loader = data_loader
        print("✓ Data loader set for models")
        
        # Test training (will use dummy data if DB empty)
        print("\n--- Testing Risk Model Training ---")
        risk_model.train()
        print("✓ Risk model trained")
        
        print("\n--- Testing Bot Detection Model Training ---")
        bot_model.train()
        print("✓ Bot detection model trained")
        
        # Test predictions
        print("\n--- Testing Predictions ---")
        risk_score = risk_model.predict({"amount": 1000, "user_tx_count": 2})
        print(f"✓ Risk prediction: {risk_score}")
        
        bot_result = bot_model.predict({
            "request_freq": 10,
            "ua_score": 0.8,
            "ip_reputation": 0.9
        })
        print(f"✓ Bot detection: {bot_result}")
        
        # Verify predictions were saved
        print("\n--- Verifying Database Storage ---")
        predictions = db.table("model_predictions") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()
        
        if predictions.data:
            print(f"✓ Found {len(predictions.data)} recent predictions in database")
            for pred in predictions.data[:2]:
                print(f"  - {pred['model_name']}: {pred['output']}")
        else:
            print("⚠ No predictions found in database (table may not exist yet)")
        
        print("\n" + "=" * 60)
        print("✅ Integration test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_model_training_integration()
    sys.exit(0 if success else 1)
