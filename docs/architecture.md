# Architecture Overview

PyPongAI is designed as a modular research platform with clear separation between game logic, AI training, data management, and user interface.

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Menu    │ │  Game    │ │  Train   │ │ Settings │ ...  │
│  │  State   │ │  State   │ │  State   │ │  State   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                    StateManager                              │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────┐
│              Game Logic   │   AI Training                  │
│  ┌────────────────────┐   │   ┌────────────────────┐      │
│  │  game_engine.py    │   │   │  ai_module.py      │      │
│  │  (Visual/Pygame)   │   │   │  (Fitness Eval)    │      │
│  └────────────────────┘   │   └────────────────────┘      │
│  ┌────────────────────┐   │   ┌────────────────────┐      │
│  │ game_simulator.py  │───┼──▶│  train.py          │      │
│  │  (Headless/Fast)   │   │   │  (Orchestration)   │      │
│  └────────────────────┘   │   └────────────────────┘      │
│                            │   ┌────────────────────┐      │
│                            │   │ novelty_search.py  │      │
│                            │   │  (Diversity)       │      │
│                            │   └────────────────────┘      │
└───────────────────────────┴───────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────┐
│              Data Layer   │                                │
│  ┌────────────────────┐   │   ┌────────────────────┐      │
│  │ match_recorder.py  │   │   │ match_database.py  │      │
│  │  (Frame logging)   │   │   │  (JSON indexing)   │      │
│  └────────────────────┘   │   └────────────────────┘      │
│  ┌────────────────────┐   │   ┌────────────────────┐      │
│  │ config.py          │   │   │ data/ directory    │      │
│  │  (Constants)       │   │   │  (Files)           │      │
│  └────────────────────┘   │   └────────────────────┘      │
└───────────────────────────┴───────────────────────────────┘
```

## Core Architectural Patterns

### 1. Dual Game Implementation

The system maintains two parallel implementations of Pong:

**Visual Game (`game_engine.py`)**
- Uses Pygame for rendering
- Human-playable interface
- Full visual feedback
- ~60 FPS gameplay
- Used for: Human play, visual training, demonstrations

**Headless Simulator (`game_simulator.py`)**
- No rendering overhead
- Custom Rect/Paddle/Ball classes
- Identical physics to visual version
- 10-100x faster than visual
- Used for: AI training, batch evaluation

**Why Both?**
- Training speed: Headless simulation is critical for rapid iteration
- Verification: Visual mode ensures AI behavior is interpretable
- User experience: Humans need visual feedback to play

### 2. State Management System

The UI uses a state machine pattern:

```python
# states/base.py
class BaseState:
    def enter(self, **kwargs):  # Initialize state
    def exit(self):              # Cleanup
    def handle_input(event):     # Process events
    def update(dt):              # Update logic
    def draw(screen):            # Render
```

**States:**
- `MenuState` - Main menu navigation
- `GameState` - Human vs AI gameplay
- `TrainState` - Visual training interface
- `LobbyState` - Match setup
- `ModelsState` - Model management
- `AnalyticsState` - Performance visualization
- `LeagueState` - Tournament system
- `ReplayState` - Match playback
- `SettingsState` - Configuration editor

**State Transitions:**
```python
manager.change_state("game", opponent_model="best_genome.pkl")
```

### 3. AI Training Pipeline

```
Population (50 genomes)
    │
    ├──▶ eval_genomes()              # Basic evaluation
    ├──▶ eval_genomes_competitive()  # ELO matchmaking
    └──▶ eval_genomes_self_play()    # Self-play + Hall of Fame
         │
         ├──▶ GameSimulator (headless)
         │    └──▶ Physics simulation
         │
         ├──▶ Fitness calculation
         │    ├─▶ ELO rating
         │    └─▶ Novelty score
         │
         └──▶ Validation (vs rule-based AI)
              └──▶ Objective metrics
```

### 4. Data Flow

**Training Data Flow:**
```
NEAT Population
    │
    └──▶ Evaluation
         ├──▶ Genomes play matches
         ├──▶ Calculate fitness (ELO + Novelty)
         ├──▶ Validate best genome
         └──▶ Log to CSV
              │
              ├──▶ data/logs/training/training_*.csv
              └──▶ data/models/model_*_fitness*.pkl
```

**Match Recording Flow:**
```
Game/Simulator
    │
    └──▶ Frame-by-frame state capture
         └──▶ MatchRecorder
              ├──▶ Serialize to JSON
              ├──▶ Save to data/logs/matches/
              └──▶ Index in match_database
```

### 5. Configuration System

Three-level configuration:
1. **`config.py`** - Core constants (game physics, file paths)
2. **`neat_config.txt`** - NEAT algorithm parameters
3. **Settings State** - Runtime adjustments (persisted to JSON)

### 6. Input/Output Normalization

All neural network inputs are normalized:

```python
inputs = (
    paddle_y / SCREEN_HEIGHT,      # [0, 1]
    ball_x / SCREEN_WIDTH,          # [0, 1]
    ball_y / SCREEN_HEIGHT,         # [0, 1]
    ball_vel_x / BALL_MAX_SPEED,    # [-1, 1]
    ball_vel_y / BALL_MAX_SPEED,    # [-1, 1]
    relative_y / SCREEN_HEIGHT,     # [-1, 1]
    incoming_flag,                  # {0, 1}
    opponent_y / SCREEN_HEIGHT      # [0, 1]
)
```

Outputs are interpreted as:
```python
action = argmax([up_signal, down_signal, stay_signal])
```

## Design Principles

### Modularity
- Each component has a single responsibility
- Clear interfaces between modules
- Easy to test in isolation

### Performance
- Headless simulation for training
- Efficient data structures
- Minimal I/O during training

### Extensibility
- State pattern allows new UI screens
- Multiple evaluation functions for different training modes
- Pluggable fitness calculations

### Research-Friendly
- Comprehensive logging
- Match recordings for analysis
- Configurable parameters
- Validation against baselines

## Key Files by Function

**Game Logic:**
- `game_engine.py` - Visual Pygame implementation
- `game_simulator.py` - Headless training implementation

**AI Training:**
- `ai_module.py` - NEAT evaluation functions
- `train.py` - Training orchestration
- `novelty_search.py` - Behavioral diversity
- `validation.py` - Genome testing

**State Management:**
- `states/manager.py` - State machine
- `states/base.py` - State interface
- `states/*.py` - Individual states

**Data:**
- `match_recorder.py` - Frame logging
- `match_database.py` - Match indexing
- `game_recorder.py` - Human gameplay
- `config.py` - Configuration

**Utilities:**
- `patch_neat.py` - NEAT library patches
- `opponents.py` - Rule-based AI
- `elo_manager.py` - ELO calculations
- `league_history.py` - Tournament tracking

## Performance Characteristics

- **Training speed**: ~1 second per generation (50 genomes, 5 matches each)
- **Headless vs Visual**: 10-100x speedup
- **Memory footprint**: <100MB typical
- **Model size**: ~10-50KB per genome
- **Match recording**: ~1MB per 1000 frames

## Testing Architecture

Tests are organized by dependency requirements:
- **No dependencies**: `test_game_simulator.py`, `test_elo_calculation.py`
- **NEAT required**: `test_ai_logic.py`, `test_competitive_training.py`
- **Pygame required**: `test_parallel_engine.py`
- **Full stack**: `test_recorder.py`, `test_model_manager.py`

This allows rapid development with partial dependency installation.
