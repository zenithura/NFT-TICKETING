
import sys
import os
import shutil
from datetime import datetime

from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_duckdb_storage():
    print("\n--- Verifying DuckDB Storage ---")
    try:
        from data_science.storage.duckdb_storage import DuckDBStorage
        
        # Use a test DB file
        test_db_path = Path("test_analytics.duckdb")
        storage = DuckDBStorage(db_path=test_db_path)
        
        # Test storing a metric (simpler than inference result)
        metric_id = storage.store_model_metric(
            model_name="test_model",
            model_version="v1",
            metric_name="accuracy",
            metric_value=0.95,
            metadata={"env": "test"}
        )
        print(f"✓ Stored metric with ID: {metric_id}")
        
        # Test querying (using internal connection for raw query to verify)
        result = storage.conn.execute("SELECT * FROM ml_model_metrics WHERE metric_id = ?", (metric_id,)).fetchall()
        if len(result) > 0:
            print(f"✓ Retrieved {len(result)} metrics from DuckDB")
        else:
            print("❌ Failed to retrieve metrics from DuckDB")
            return False
            
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        # Verify real DB exists and is loadable
        print("\n--- Verifying Real DuckDB Artifact ---")
        real_db_path = Path(os.path.dirname(os.path.abspath(__file__))) / "data_science" / "artifacts" / "ml_analytics.duckdb"
        if real_db_path.exists():
            print(f"✓ Real DB found at {real_db_path}")
            try:
                real_storage = DuckDBStorage(db_path=real_db_path)
                # Just check connection
                real_storage.conn.execute("SELECT 1")
                print("✓ Successfully connected to real DB")
                real_storage.close()
            except Exception as e:
                print(f"❌ Failed to connect to real DB: {e}")
                return False
        else:
            print(f"⚠ Real DB not found at {real_db_path} (might be expected if new install)")
            
        return True
    except Exception as e:
        print(f"❌ DuckDB Storage verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_monitoring_api():
    print("\n--- Verifying Monitoring API Integration ---")
    try:
        # Check imports in monitoring_api.py
        # We need to make sure flask and flask_cors are installed
        import flask
        import flask_cors
        
        from monitoring.monitoring_api import get_monitoring
        
        print("✓ Successfully imported monitoring.monitoring_api")
        
        # Check if we can instantiate KPICalculator via monitoring
        monitoring = get_monitoring()
        if hasattr(monitoring, 'kpi_calculator'):
            print("✓ SystemMonitoring instance has kpi_calculator")
        else:
            print("⚠ SystemMonitoring instance missing kpi_calculator attribute")
            
        return True
    except ImportError as e:
        print(f"❌ Monitoring API import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Monitoring API verification failed: {e}")
        return False

def verify_etl_pipeline():
    print("\n--- Verifying ETL Pipeline Integration ---")
    try:
        # Check imports in etl_pipeline.py
        from data_control.etl_pipeline import ETLPipeline
        
        print("✓ Successfully imported data_control.etl_pipeline.ETLPipeline")
        
        pipeline = ETLPipeline()
        if hasattr(pipeline, 'feature_engineer'):
            print("✓ ETLPipeline has feature_engineer")
        else:
            print("⚠ ETLPipeline missing feature_engineer attribute")
            return False
            
        return True
    except ImportError as e:
        print(f"❌ ETL Pipeline import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ETL Pipeline verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Component Verification...")
    
    duckdb_ok = verify_duckdb_storage()
    monitoring_ok = verify_monitoring_api()
    etl_ok = verify_etl_pipeline()
    
    if duckdb_ok and monitoring_ok and etl_ok:
        print("\n✅ All components verified successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some components failed verification.")
        sys.exit(1)
