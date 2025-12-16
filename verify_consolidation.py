
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

print("Checking imports...")

try:
    print("1. Importing monitoring...")
    from backend.monitoring import get_metrics
    print("   SUCCESS: monitoring imported")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("2. Importing dashboard...")
    from backend.monitoring.dashboard import app
    print("   SUCCESS: dashboard imported")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("3. Importing data_control...")
    from backend.data_control.etl_pipeline import get_etl_pipeline
    print("   SUCCESS: data_control imported")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("4. Importing ml_pipeline...")
    from backend.ml_pipeline.feature_engineering import get_feature_engineer
    print("   SUCCESS: ml_pipeline imported")
except ImportError as e:
    print(f"   FAIL: {e}")

print("\nVerification complete.")
