"""Verify devlog mode settings are applied correctly."""

import os
import sys
from pathlib import Path
import importlib

# Ensure we are in the root of PyPongAI and can import core
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Test 1: Normal mode (no PYPONGAI_AUTOMATION)
print("Test 1: Normal mode (no PYPONGAI_AUTOMATION)")
print("-" * 50)

# Clear env var
if "PYPONGAI_AUTOMATION" in os.environ:
    del os.environ["PYPONGAI_AUTOMATION"]

# Import config
from core import config
importlib.reload(config)

print(f"VISUAL_MAX_SCORE: {config.VISUAL_MAX_SCORE} (expected: 5)")
print(f"BALL_SPEED_X: {config.BALL_SPEED_X} (expected: 3)")
print(f"PADDLE_SPEED: {config.PADDLE_SPEED} (expected: 7)")

assert config.VISUAL_MAX_SCORE == 5, f"Normal mode should use 5-point matches, got {config.VISUAL_MAX_SCORE}"
assert config.BALL_SPEED_X == 3, f"Normal mode should use ball speed 3, got {config.BALL_SPEED_X}"
assert config.PADDLE_SPEED == 7, f"Normal mode should use paddle speed 7, got {config.PADDLE_SPEED}"

print("[OK] Normal mode settings correct\n")

# Test 2: Devlog mode (PYPONGAI_AUTOMATION=true)
print("Test 2: Devlog mode (PYPONGAI_AUTOMATION=true)")
print("-" * 50)

os.environ["PYPONGAI_AUTOMATION"] = "true"

# Reload config to apply overrides
importlib.reload(config)

print(f"VISUAL_MAX_SCORE: {config.VISUAL_MAX_SCORE} (expected: 3)")
print(f"BALL_SPEED_X: {config.BALL_SPEED_X} (expected: 4)")
print(f"PADDLE_SPEED: {config.PADDLE_SPEED} (expected: 10)")

assert config.VISUAL_MAX_SCORE == 3, f"Devlog mode should use 3-point matches, got {config.VISUAL_MAX_SCORE}"
assert config.BALL_SPEED_X == 4, f"Devlog mode should use ball speed 4, got {config.BALL_SPEED_X}"
assert config.PADDLE_SPEED == 10, f"Devlog mode should use paddle speed 10, got {config.PADDLE_SPEED}"

print("[OK] Devlog mode settings correct\n")

print("=" * 50)
print("All configuration tests passed! [OK]")
