# Test Suite Configuration

This file contains shared configuration and utilities for the test suite.

import os
import sys

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Test configuration constants
TEST_TIMEOUT = 30  # seconds
TEST_DATA_DIR = os.path.join(PROJECT_ROOT, "tests", "test_data")
TEMP_TEST_FILES = []  # Track temporary files for cleanup

def cleanup_temp_files():
    """Clean up temporary test files."""
    for filepath in TEMP_TEST_FILES:
        if os.path.exists(filepath):
            os.remove(filepath)
    TEMP_TEST_FILES.clear()

def register_temp_file(filepath):
    """Register a temporary file for cleanup."""
    TEMP_TEST_FILES.append(filepath)
