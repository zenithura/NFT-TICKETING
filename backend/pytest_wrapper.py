#!/usr/bin/env python
"""Pytest wrapper that prevents web3 pytest plugin from loading."""
import sys
from types import ModuleType

# Prevent web3 pytest plugin from being imported
# This must happen before pytest is imported
# Create proper module mocks to prevent import errors
web3_tools = ModuleType('web3.tools')
web3_pytest = ModuleType('web3.tools.pytest_ethereum')
web3_plugins = ModuleType('web3.tools.pytest_ethereum.plugins')
web3_deployer = ModuleType('web3.tools.pytest_ethereum.deployer')

sys.modules['web3.tools'] = web3_tools
sys.modules['web3.tools.pytest_ethereum'] = web3_pytest
sys.modules['web3.tools.pytest_ethereum.plugins'] = web3_plugins
sys.modules['web3.tools.pytest_ethereum.deployer'] = web3_deployer

# Now import and run pytest
import pytest

if __name__ == '__main__':
    sys.exit(pytest.main(sys.argv[1:]))

