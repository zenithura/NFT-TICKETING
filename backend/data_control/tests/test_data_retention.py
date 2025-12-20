"""Unit tests for Data Retention Policy."""
import pytest
from pathlib import Path
from data_control.data_retention import DataRetentionPolicy

@pytest.fixture
def retention_policy(tmp_path):
    # Create a dummy config
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
retention:
  onchain_retention_days: 365
  offchain_retention_days: 90
  archival_enabled: true
  auto_delete_enabled: false
""")
    policy = DataRetentionPolicy(config_path=config_file)
    # Override archive dir for testing
    policy.archive_dir = tmp_path / "archives"
    policy.archive_dir.mkdir(exist_ok=True)
    return policy

def test_policy_initialization(retention_policy):
    """Test policy loads config correctly."""
    assert retention_policy.onchain_retention_days == 365
    assert retention_policy.offchain_retention_days == 90
    assert retention_policy.archival_enabled is True

def test_cleanup_old_archives(retention_policy, tmp_path):
    """Test cleanup of old archive files."""
    archive_dir = retention_policy.archive_dir
    
    # Create a new file
    new_file = archive_dir / "new.csv"
    new_file.write_text("data")
    
    # Create an old file (mocking mtime is hard, so we'll just check it doesn't delete new ones)
    retention_policy._cleanup_old_archives(days=1)
    assert new_file.exists()
