# Data Science Consolidation Plan

## Current State Analysis

### Three Implementations Found:

1. **`backend/data_science/`** ✅ **PRIMARY** (Active)
   - Used in: `main.py`, `ml_services_v2.py`
   - 9 models, clean architecture
   - Supabase integration
   - **Status**: Keep as main implementation

2. **`Machine Learning/`** ⚠️ **ALTERNATIVE** (Partially Active)
   - Used in: `ml_services_backend.py`
   - DuckDB storage (valuable feature)
   - More advanced analytics
   - **Status**: Migrate DuckDB to main, then archive

3. **`backend/ml_pipeline/`** ❌ **LEGACY** (Deprecated)
   - Used in: `ml_services.py`, `monitoring_api.py`, `etl_pipeline.py`
   - XGBoost training script
   - Model ensemble
   - **Status**: Migrate useful parts, then remove

---

## Consolidation Strategy

### Phase 1: Migrate DuckDB Storage ✅
- [x] Copy DuckDB storage from `Machine Learning/integration/duckdb_storage.py`
- [ ] Integrate into `backend/data_science/`
- [ ] Update models to use DuckDB for analytics storage

### Phase 2: Update All Imports ✅
- [ ] Update `ml_services.py` to use `data_science/`
- [ ] Update `monitoring_api.py` to use `data_science/`
- [ ] Update `etl_pipeline.py` to use `data_science/`
- [ ] Update `ml_services_backend.py` to use `data_science/`

### Phase 3: Archive/Remove Duplicates ✅
- [ ] Archive `Machine Learning/` folder
- [ ] Remove `backend/ml_pipeline/` folder
- [ ] Update documentation

---

## Migration Steps

### Step 1: Add DuckDB Storage to Main Implementation
- Add `backend/data_science/storage/duckdb_storage.py`
- Integrate with existing models

### Step 2: Update Router Imports
- Consolidate all ML routers to use `data_science/`
- Remove duplicate endpoints

### Step 3: Clean Up
- Archive old implementations
- Update README


