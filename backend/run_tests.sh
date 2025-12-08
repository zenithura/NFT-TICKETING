#!/bin/bash
# Backend test runner script using pytest wrapper

set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Use pytest wrapper to avoid web3 plugin issues
exec python pytest_wrapper.py "$@"

