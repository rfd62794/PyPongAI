"""Test runner for PyPongAI unit tests.

Runs all test suites and provides a summary of test results.
"""

import unittest
import sys

# Discover and run all tests
if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test modules
    suite.addTests(loader.loadTestsFromName('test_game_simulator'))
    suite.addTests(loader.loadTestsFromName('test_ai_logic'))
    suite.addTests(loader.loadTestsFromName('test_model_manager'))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(not result.wasSuccessful())
