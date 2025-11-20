# PyPongAI Test Suite

This directory contains comprehensive unit tests for the PyPongAI project.

## Test Files

### `test_game_simulator.py` - Game Physics Tests
Tests the headless game simulation logic:
- **Ball Movement**: Verifies ball position updates correctly with velocity
- **Scoring Mechanics**: Tests left/right scoring when ball passes paddles
- **Paddle Collisions**: Validates ball reflection upon paddle hits
- **Boundary Constraints**: Ensures paddles stay within screen bounds
- **Wall Collisions**: Tests ball reflection off top/bottom walls
- **Game State**: Verifies complete game state is returned
- **Physics Edge Cases**: Tests speed caps and dynamic paddle speed

**Coverage**: 18 tests covering `Rect`, `Paddle`, `Ball`, and `GameSimulator` classes

### `test_ai_logic.py` - AI and ELO Tests
Tests the AI evaluation and ELO rating system:
- **ELO Calculations**: Validates expected score and rating update formulas
- **Win/Loss/Draw**: Tests ELO changes for different match outcomes
- **Upset Victories**: Verifies larger ELO gains for unexpected wins
- **ELO Manager**: Tests ELO persistence and retrieval
- **Rule-Based AI**: Validates opponent logic (up/down/deadzone)
- **Fitness Rewards**: Tests survival, hit, and scoring rewards
- **Hall of Fame**: Verifies genome storage for self-play

**Coverage**: 20 tests covering ELO system, AI opponents, and fitness functions

### `test_model_manager.py` - Model Management Tests
Tests model file operations and conversions:
- **Model Scanning**: Tests finding .pkl files recursively
- **ELO Conversion**: Validates adding ELO attributes to legacy models
- **Best Model Selection**: Tests ELO-based model ranking
- **Fitness Extraction**: Validates parsing fitness from filenames
- **Model Deletion**: Tests safe model file removal
- **Metadata Handling**: Ensures models have required attributes

**Coverage**: 17 tests covering model utilities and file operations

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Individual Test Suites
```bash
python -m unittest test_game_simulator.py -v
python -m unittest test_ai_logic.py -v
python -m unittest test_model_manager.py -v
```

### Run Specific Test Class
```bash
python -m unittest test_game_simulator.TestGameSimulator -v
```

### Run Specific Test Method
```bash
python -m unittest test_game_simulator.TestGameSimulator.test_ball_movement -v
```

## Test Statistics

- **Total Tests**: 55
- **Test Classes**: 17
- **Test Coverage**: Core game logic, AI system, model management
- **Execution Time**: ~0.1 seconds

## Test Design Principles

1. **Isolation**: Each test is independent and doesn't affect others
2. **Mocking**: Uses mocks for file I/O and external dependencies
3. **Fast Execution**: All tests run in under a second
4. **Clear Assertions**: Each test has specific, documented expectations
5. **Edge Cases**: Tests include boundary conditions and error handling

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: python run_tests.py
```

## Adding New Tests

When adding features:
1. Create test methods following naming convention `test_feature_name`
2. Add docstrings explaining what is being tested
3. Use appropriate assertions (`assertEqual`, `assertTrue`, etc.)
4. Clean up resources in `tearDown` if needed
5. Run tests to ensure they pass

## Dependencies

- `unittest` (Python standard library)
- `unittest.mock` for mocking
- `tempfile` for temporary test files
- `pickle` for model serialization

No additional test frameworks required!
