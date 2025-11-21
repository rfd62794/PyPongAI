# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PyPongAI is an advanced neuroevolution research platform that trains AI agents to play Pong using NEAT (NeuroEvolution of Augmenting Topologies). It combines competitive ELO-based matchmaking, novelty search, recurrent neural networks (RNNs), and curriculum learning to produce sophisticated AI behaviors.

**Key Features:**
- Recurrent neural networks for temporal reasoning
- ELO-based competitive training with novelty search
- Comprehensive match recording and analytics system
- State-based UI architecture with modern dark theme
- Gamified tier system (Bronze/Silver/Gold/Platinum)
- Human vs AI gameplay with adaptive rival system

## Common Commands

### Running the Application
```bash
# Run main GUI application (requires pygame and neat-python)
python main.py

# Play against trained AI
python play.py

# Train new AI models
python train.py

# Train with seeding from existing models
python train.py --seed models/model_20251119_fitness1876.pkl
python train.py --seed_dir models/
```

### Testing
```bash
# Run all tests (requires pytest, neat-python, and pygame)
python -m pytest

# Run specific test files
python -m pytest test_game_simulator.py
python -m pytest test_elo_calculation.py

# Run tests without NEAT/pygame dependencies
python -m pytest test_elo_calculation.py test_game_simulator.py
```

### Validation
```bash
# Python syntax checks (no imports needed)
python -m py_compile ai_module.py
python -m py_compile game_simulator.py
```

## Architecture

### Core Game Logic
The project has two parallel game implementations:
- **`game_engine.py`**: Visual Pygame-based game for UI and human play
- **`game_simulator.py`**: Headless simulation for high-speed training

Both maintain **identical physics** and use the same coordinate system. The simulator uses custom `Rect`, `Paddle`, and `Ball` classes that mirror Pygame's API without rendering overhead.

### AI Training Pipeline
1. **`ai_module.py`**: Core NEAT fitness functions
   - `eval_genomes()`: Single-opponent evaluation
   - `eval_genomes_competitive()`: ELO-based matchmaking
   - `eval_genomes_self_play()`: Population self-play with Hall of Fame
2. **`novelty_search.py`**: Behavioral diversity tracking via contact Y-coordinates
3. **`train.py`**: Training orchestration with CSV logging and validation
4. **`validation.py`**: Best genome testing against rule-based AI

### State Management System
Located in `states/` directory with a clean separation of concerns:
- **`manager.py`**: StateManager handles state transitions and game loop
- **`base.py`**: BaseState provides interface (enter/exit/handle_input/update/draw)
- Individual states: `menu.py`, `game.py`, `train.py`, `models.py`, `analytics.py`, `league.py`, `replay.py`, `settings.py`

Each state is self-contained and registered in `main.py`. States communicate via the manager's `change_state()` method with keyword arguments.

### Data Storage Structure
```
data/
├── models/              # Trained genomes (.pkl files)
│   └── tiers/          # God/Master/Challenger/Archive subdirs
├── logs/
│   ├── training/       # CSV training logs
│   ├── matches/        # Match recordings (JSON)
│   └── human/          # Human gameplay recordings
├── match_index.json    # Match database index
└── human_stats.json    # Player stats and rival tracking
```

### NEAT Configuration
- **`neat_config.txt`**: NEAT-Python configuration
- **`patch_neat.py`**: Monkeypatch for `min_species_size` parameter support (must be imported first)
- RNNs enabled via `feed_forward = False`
- 8 inputs: paddle_y, ball_x, ball_y, ball_vel_x, ball_vel_y, relative_y, incoming_flag, opponent_y
- 3 outputs: UP, DOWN, STAY

### Match Recording System
- **`match_recorder.py`**: Frame-by-frame state logging
- **`match_database.py`**: JSON indexing for match retrieval
- **`game_recorder.py`**: Human gameplay recording with rematch support

## Important Patterns

### NEAT Network Creation
Always use `RecurrentNetwork` for consistency with the configuration:
```python
import neat
net = neat.nn.RecurrentNetwork.create(genome, config_neat)
net.reset()  # MUST reset RNN state before each game
```

### Input Normalization
All network inputs are normalized to [0, 1] or [-1, 1] ranges:
```python
inputs = (
    paddle_y / config.SCREEN_HEIGHT,
    ball_x / config.SCREEN_WIDTH,
    ball_y / config.SCREEN_HEIGHT,
    ball_vel_x / config.BALL_MAX_SPEED,
    ball_vel_y / config.BALL_MAX_SPEED,
    relative_y / config.SCREEN_HEIGHT,
    1.0 if ball_vel_x < 0 else 0.0,  # Incoming flag
    opponent_y / config.SCREEN_HEIGHT
)
```

### Output Interpretation
Network outputs are 3-dimensional (UP, DOWN, STAY):
```python
output = net.activate(inputs)
action_idx = output.index(max(output))
# 0 = UP, 1 = DOWN, 2 = STAY
```

### Curriculum Learning
Pass progressive difficulty to evaluation functions:
```python
current_speed = min(
    config.INITIAL_BALL_SPEED + (generation * config.SPEED_INCREASE_PER_GEN),
    config.MAX_CURRICULUM_SPEED
)
ai_module.eval_genomes_competitive(genomes, config_neat, ball_speed=current_speed)
```

### ELO + Novelty Fitness
Final fitness combines ELO rating with behavioral novelty:
```python
novelty_score = NOVELTY_ARCHIVE.calculate_novelty(bc_value)
genome.fitness = genome.elo_rating + (config.NOVELTY_WEIGHT * novelty_score)
```

## Configuration Management

Settings are managed via:
1. **`config.py`**: Core game constants and file paths
2. **`states/settings.py`**: UI for runtime parameter editing
3. **Persistent storage**: Settings saved to JSON when modified

Key configurable parameters:
- `MAX_SCORE`: Game win condition
- `ELO_K_FACTOR`: Rating volatility
- `NOVELTY_WEIGHT`: Influence of behavioral diversity
- `INITIAL_BALL_SPEED`, `SPEED_INCREASE_PER_GEN`: Curriculum learning

## Dependencies

Required packages (no requirements.txt present):
- `pygame`: Graphics and game engine
- `neat-python`: NEAT algorithm implementation
- `numpy`: Numerical operations for novelty search
- `pytest`: Testing framework (dev only)

Install with:
```bash
pip install pygame neat-python numpy pytest
```

## Testing Strategy

Tests are organized by component:
- `test_game_simulator.py`: Physics validation (18 tests, no pygame/neat required)
- `test_elo_calculation.py`: ELO math verification (5 tests)
- `test_ai_logic.py`, `test_competitive_training.py`, `test_train.py`, `test_training.py`: Require neat-python
- `test_parallel_engine.py`: Requires pygame
- `test_recorder.py`, `test_model_manager.py`: Integration tests

The codebase has 41 tests with some requiring full dependencies. For quick syntax validation, use `py_compile` instead.

## Code Style Notes

- Import `patch_neat` before any NEAT imports to enable custom parameters
- Use `config.SCREEN_WIDTH/HEIGHT` for coordinate bounds, never hardcode
- Ball and paddle velocities capped at `config.BALL_MAX_SPEED` and `config.PADDLE_MAX_SPEED`
- State classes should inherit from `BaseState` and implement all lifecycle methods
- Match recordings use `MatchRecorder` with metadata dicts for indexing
- File paths use `os.path.join()` with constants from `config.py`

## Known Quirks

- **Windows-specific**: Uses PowerShell conventions (CRLF line endings)
- **Monkeypatch required**: `patch_neat.py` must be imported before neat in all training scripts
- **State reset**: RNN networks must call `net.reset()` at the start of each game, or behavior degrades
- **GameSimulator vs Game**: Use simulator for training (10-100x faster), game engine for human play
- **Model naming**: Fitness extracted from filename patterns like `model_*_fitness1876.pkl` or `*_fit_1876.pkl`
- **Duplicate files**: Some states have desktop-specific backup copies (e.g., `menu-DESKTOP-HKF4HGE.py`) - ignore these

## Project Status

**Production-ready** research platform. Successfully trained for 50+ generations with stable evolution (best fitness: 1876). All core features implemented:
- ✅ RNNs with temporal memory
- ✅ ELO-based competitive training
- ✅ Novelty search for strategy diversity
- ✅ Curriculum learning infrastructure
- ✅ Gamification and tier system
- ✅ Match recording and analytics
- ✅ Settings management UI

See `PROJECT_COMPLETE.md` for detailed feature documentation.
