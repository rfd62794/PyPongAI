# File Structure Reference

Complete directory and file organization for PyPongAI.

## Root Directory

```
PyPongAI/
├── main.py              # Application entry point
├── train.py             # Training script
├── play.py              # Human vs AI gameplay
├── config.py            # Configuration constants
├── patch_neat.py        # NEAT library patches (must import first)
├── neat_config.txt      # NEAT algorithm parameters
├── WARP.md              # Warp AI development guide
├── PROJECT_COMPLETE.md  # Project completion summary
├── data/                # Data storage (created at runtime)
├── docs/                # Documentation
├── states/              # UI state management
├── models/              # Legacy models directory
├── logs/                # Legacy logs directory
├── human_data/          # Legacy human data directory
└── venv/                # Python virtual environment
```

## Core Game Files

### `game_engine.py`
Visual Pygame-based game implementation.

**Classes:**
- `Paddle` - Visual paddle with movement
- `Ball` - Visual ball with physics
- `Game` - Main game loop with rendering

**Used for:**
- Human gameplay (`play.py`)
- Visual training mode
- Demonstrations

### `game_simulator.py`
Headless game simulation for fast training.

**Classes:**
- `Rect` - Custom rectangle for collision detection
- `Paddle` - Lightweight paddle
- `Ball` - Lightweight ball
- `GameSimulator` - Headless game logic

**Used for:**
- AI training (10-100x faster than visual)
- Batch evaluation
- Testing

**Key:** Maintains **identical physics** to `game_engine.py`

## AI Training Files

### `ai_module.py`
Core NEAT evaluation functions.

**Functions:**
- `eval_genomes()` - Basic single-opponent evaluation
- `eval_genomes_competitive()` - ELO-based matchmaking
- `eval_genomes_self_play()` - Self-play with Hall of Fame
- `calculate_expected_score()` - ELO calculation
- `calculate_new_rating()` - ELO update

**Global Variables:**
- `NOVELTY_ARCHIVE` - Behavioral diversity tracker
- `HALL_OF_FAME` - Elite genome storage

### `train.py`
Training orchestration and logging.

**Functions:**
- `run_training()` - Main training loop
- CSV logging setup
- Model saving
- Validation reporting

**Command-line args:**
- `--seed` - Path to seed model
- `--seed_dir` - Directory of seed models

### `validation.py`
Genome testing against baselines.

**Functions:**
- `validate_genome()` - Test genome vs rule-based AI

**Returns:**
- `avg_rally` - Average paddle hits per game
- `win_rate` - Win percentage

### `novelty_search.py`
Behavioral diversity system.

**Classes:**
- `NoveltyArchive` - BC storage and novelty calculation

**Functions:**
- `calculate_bc_from_contacts()` - Behavioral characteristic extraction

**Behavioral Characteristic:** Average Y-coordinate of paddle-ball contacts

### `opponents.py`
Rule-based AI implementations.

**Functions:**
- `get_rule_based_move()` - Simple tracking AI

**Used for:**
- Validation baseline
- Early training opponent
- Human-difficulty reference

## State Management (`states/`)

### `manager.py`
State machine controller.

**Class: `StateManager`**
- `register_state()` - Add state
- `change_state()` - Transition between states
- `run()` - Main game loop

### `base.py`
State interface definition.

**Class: `BaseState`**
- `enter(**kwargs)` - Initialize state
- `exit()` - Cleanup
- `handle_input(event)` - Process events
- `update(dt)` - Update logic
- `draw(screen)` - Render

### Individual States

```
states/
├── menu.py          # Main menu
├── game.py          # Human vs AI gameplay
├── train.py         # Visual training interface
├── lobby.py         # Match setup
├── models.py        # Model management
├── analytics.py     # Performance visualization
├── league.py        # Tournament system
├── replay.py        # Match playback
└── settings.py      # Configuration editor
```

**Each state:**
- Inherits from `BaseState`
- Self-contained UI logic
- Registered in `main.py`

## Data Management

### `match_recorder.py`
Frame-by-frame match recording.

**Class: `MatchRecorder`**
- `record_frame()` - Log game state
- `save()` - Write to JSON

**Output:** `data/logs/matches/match_*.json`

### `match_database.py`
Match indexing and retrieval.

**Functions:**
- `index_match()` - Add match to database
- `get_match()` - Retrieve match by ID
- `query_matches()` - Search matches

**Database:** `data/match_index.json`

### `game_recorder.py`
Human gameplay recording.

**Class: `GameRecorder`**
- `log_frame()` - Record frame
- `save_recording()` - Save with timestamp

**Output:** `data/logs/human/game_*.json`

## Utilities

### `elo_manager.py`
ELO rating calculations and tier management.

**Functions:**
- `get_elo_tier()` - Determine rank (Bronze/Silver/Gold/Platinum)

**Thresholds:**
- Bronze: 1200
- Silver: 1400
- Gold: 1600
- Platinum: 1800+

### `league_history.py`
Tournament and championship tracking.

**Data:**
- Season champions
- All-time leaderboard
- Historical records

**Storage:** Persistent JSON

### `human_rival.py`
Adaptive rival system for human players.

**Class: `HumanRival`**
- `get_rival_model()` - Select appropriate AI opponent
- `update_match_result()` - Adjust difficulty
- `update_score()` - Track personal bests

**Dynamic Difficulty Adjustment (DDA):**
- Tracks human win/loss record
- Adjusts AI opponent difficulty
- Maintains engagement

## Data Directory (`data/`)

Runtime-created storage:

```
data/
├── models/
│   ├── best_genome.pkl
│   ├── model_20251119_fitness1876.pkl
│   └── tiers/
│       ├── God/
│       ├── Master/
│       ├── Challenger/
│       └── Archive/
├── logs/
│   ├── training/
│   │   └── training_stats_*.csv
│   ├── matches/
│   │   └── match_*.json
│   └── human/
│       └── game_*.json
├── match_index.json
└── human_stats.json
```

### Model Files (`.pkl`)

Pickled NEAT genomes containing:
- Node genes (inputs, outputs, hidden)
- Connection genes (weights, enabled status)
- Fitness metadata

**Naming:**
- `model_YYYYMMDD_HHMMSS_fitnessXXXX.pkl`
- `best_genome.pkl` (latest best)

### Training Logs (`.csv`)

```csv
generation,max_fitness,avg_fitness,std_dev,val_avg_rally,val_win_rate
0,1234.56,567.89,123.45,12.40,0.60
1,1289.42,601.23,115.67,13.20,0.65
```

### Match Recordings (`.json`)

```json
{
  "match_id": "match_20251119_123456",
  "players": ["genome_123", "genome_456"],
  "frames": [
    {
      "paddle_left_y": 250,
      "paddle_right_y": 275,
      "ball_x": 400,
      "ball_y": 300,
      ...
    },
    ...
  ],
  "metadata": {
    "duration": 1234,
    "final_score": [5, 3],
    ...
  }
}
```

## Configuration Files

### `config.py`
Python constants:

```python
# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Game physics
PADDLE_SPEED = 7
BALL_SPEED_X = 3
BALL_MAX_SPEED = 1500

# ELO settings
ELO_K_FACTOR = 32
ELO_INITIAL_RATING = 1200

# Novelty search
NOVELTY_WEIGHT = 0.1
NOVELTY_K_NEAREST = 15

# File paths
MODEL_DIR = "data/models"
LOG_DIR = "data/logs"
```

### `neat_config.txt`
NEAT-Python INI format:

```ini
[NEAT]
pop_size = 50
fitness_threshold = 10000

[DefaultGenome]
num_inputs = 8
num_outputs = 3
num_hidden = 1
feed_forward = False

[DefaultStagnation]
max_stagnation = 20
species_elitism = 2
```

## Test Files

```
PyPongAI/
├── test_ai_logic.py             # AI evaluation tests
├── test_competitive_training.py # ELO matchmaking tests
├── test_elo_calculation.py      # ELO math tests
├── test_game_simulator.py       # Physics tests
├── test_model_manager.py        # Model management tests
├── test_parallel_engine.py      # Parallel processing tests
├── test_recorder.py             # Match recording tests
└── test_training.py             # Training integration tests
```

**Dependencies:**
- `test_elo_calculation.py`, `test_game_simulator.py` - No dependencies
- `test_ai_logic.py`, `test_competitive_training.py` - Require NEAT
- `test_parallel_engine.py` - Requires Pygame
- Others - Full stack

## Documentation (`docs/`)

```
docs/
├── README.md                    # Documentation index
├── quick-start.md               # 5-minute setup
├── architecture.md              # System design
├── neat-algorithm.md            # NEAT explanation
├── training-guide.md            # Training workflows
├── competitive-training.md      # ELO matchmaking
├── novelty-search.md            # Behavioral diversity
├── curriculum-learning.md       # Progressive difficulty
├── match-recording.md           # Recording system
├── analytics.md                 # Metrics and visualization
├── league-system.md             # Tournaments
├── human-play.md                # Playing vs AI
├── state-management.md          # UI architecture
├── api/
│   ├── ai-module.md            # ai_module.py API
│   ├── game-engine.md          # game_engine.py API
│   ├── game-simulator.md       # game_simulator.py API
│   └── config.md               # config.py reference
├── advanced/
│   ├── rnn.md                  # Recurrent networks
│   ├── elo.md                  # ELO system details
│   ├── performance.md          # Optimization techniques
│   └── extending.md            # Adding features
└── reference/
    ├── file-structure.md       # This file
    ├── data-formats.md         # JSON schemas
    ├── testing.md              # Test guide
    └── troubleshooting.md      # Common issues
```

## Legacy Files

Some files/directories are legacy from earlier versions:

- `models/` (root) - Replaced by `data/models/`
- `logs/` (root) - Replaced by `data/logs/`
- `human_data/` - Replaced by `data/logs/human/`
- `states/*-DESKTOP-*.py` - Desktop-specific backups (ignore)

## File Size Guidelines

**Typical sizes:**
- Genome (`.pkl`): 10-50 KB
- Training log (`.csv`): 5-50 KB
- Match recording (`.json`): 100 KB - 1 MB per 1000 frames
- Match index: 1-10 MB (depending on recordings)

**Large files to watch:**
- `match_index.json` - Can grow indefinitely
- `data/logs/matches/` - Accumulates over time
- Hall of Fame size - Configure in code

## Path Conventions

**Absolute paths** (for root access):
```python
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
```

**Relative paths** (for local access):
```python
# From any file
from config import MODEL_DIR
model_path = os.path.join(MODEL_DIR, "best_genome.pkl")
```

## Import Order

Critical for proper operation:

```python
# 1. FIRST: Import patch before NEAT
import patch_neat

# 2. THEN: Standard library
import os
import sys

# 3. THEN: Third-party
import neat
import pygame

# 4. THEN: Local modules
import config
import game_simulator
```

**Why:** `patch_neat.py` monkeypatches NEAT library for `min_species_size` support.
