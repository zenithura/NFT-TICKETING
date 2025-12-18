"""Storage module for ML analytics and results."""
from .duckdb_storage import DuckDBStorage, get_duckdb_storage

__all__ = ['DuckDBStorage', 'get_duckdb_storage']


