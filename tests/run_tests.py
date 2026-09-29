"""
Simple test runner script
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from tests.test_permissions import TestPermissionPolicy

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermissionPolicy)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
