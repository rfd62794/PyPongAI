# Quick Start Guide

Get PyPongAI running in 5 minutes.

## Prerequisites

- Python 3.7 or higher
- Windows/Linux/macOS

## Installation

1. **Install dependencies:**
```bash
pip install pygame neat-python numpy pytest
```

2. **Verify installation:**
```bash
python -c "import pygame, neat, numpy; print('All dependencies installed!')"
```

## Running the Application

### Launch the Main GUI
```bash
python main.py
```

This opens the main menu with options to:
- Play vs AI
- Train AI
- View AI League
- Manage Models
- View Analytics
- Adjust Settings

### Train Your First AI
```bash
python train.py
```

Training will:
- Run for 50 generations (configurable)
- Save models to `data/models/`
- Log statistics to `data/logs/training/`
- Display progress in the console

**Expected output:**
```
Generation 0 Best Fitness: 1234.56
Generation 1 Best Fitness: 1289.42
...
```

Training takes ~1 second per generation on modern hardware.

### Play Against a Trained AI
```bash
python play.py
```

Controls:
- **UP Arrow** - Move paddle up
- **DOWN Arrow** - Move paddle down
- **R** - Rematch (after game over)
- **M** - Return to menu
- **Q** - Quit

## What's Next?

- **Customize training** - See [Training Guide](training-guide.md)
- **Understand the algorithms** - Read [NEAT Algorithm](neat-algorithm.md)
- **Explore features** - Try the Analytics and League systems in the GUI
- **Adjust settings** - Use the Settings menu in the GUI or edit `config.py`

## Quick Commands Reference

```bash
# Run main application
python main.py

# Train new AI (headless, fast)
python train.py

# Train with seeding
python train.py --seed data/models/best_genome.pkl

# Play against AI
python play.py

# Run tests
python -m pytest

# Run specific test file
python -m pytest test_game_simulator.py
```

## File Locations

After running the application:
- **Trained models**: `data/models/`
- **Training logs**: `data/logs/training/`
- **Match recordings**: `data/logs/matches/`
- **Human gameplay**: `data/logs/human/`
- **Settings**: `data/human_stats.json`, `data/match_index.json`

## Troubleshooting

**Import errors?**
```bash
pip install --upgrade pygame neat-python numpy
```

**No models found?**
- Run `python train.py` first to create models
- Models are saved to `data/models/`

**Training is slow?**
- Training runs headless by default (no visualization)
- 1-2 seconds per generation is normal
- For visual training, use the GUI's "Train AI" option

**Need help?** See [Troubleshooting](reference/troubleshooting.md) for more solutions.
