# Pytest Web3 Plugin Fix

## Problem

Running `pytest tests/` was failing with:
```
ImportError: cannot import name 'ContractName' from 'eth_typing'
```

This is caused by the `web3` package's pytest plugin trying to import `ContractName` from `eth_typing`, but the installed version doesn't have it.

## Solution

Created a pytest wrapper script (`pytest_wrapper.py`) that mocks the web3 pytest plugin modules before pytest tries to load them.

## Usage

### Option 1: Use the wrapper script (Recommended)

```bash
cd backend
source venv/bin/activate
python pytest_wrapper.py tests/ -v
```

### Option 2: Use the run_tests.sh script

```bash
cd backend
./run_tests.sh tests/ -v
```

### Option 3: Use npm scripts (if package.json is configured)

```bash
cd backend
npm test
```

## What Changed

1. **pytest_wrapper.py**: Wrapper script that mocks web3 modules before pytest loads
2. **sentry_config.py**: Made SQLAlchemy integration optional (won't fail if not installed)
3. **tests/conftest.py**: Added module mocks to prevent web3 plugin loading
4. **pytest.ini**: Added `-p no:web3` flag (may not fully prevent loading but helps)

## Running Tests

```bash
# All tests
python pytest_wrapper.py tests/ -v

# With coverage
python pytest_wrapper.py tests/ --cov=. --cov-report=html

# Specific test file
python pytest_wrapper.py tests/test_auth.py -v

# By marker
python pytest_wrapper.py tests/ -m integration -v
```

## Notes

- The wrapper must be used because pytest loads plugins via setuptools entrypoints before conftest.py runs
- The web3 library itself still works fine, we just don't need its pytest plugin
- Tests run successfully with this fix

