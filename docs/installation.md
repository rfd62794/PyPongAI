# Installation Guide

Complete installation instructions for PyPongAI.

## System Requirements

### Minimum Requirements
- **OS**: Windows 7+, macOS 10.12+, or Linux (Ubuntu 18.04+)
- **Python**: 3.7 or higher
- **RAM**: 2 GB
- **Storage**: 500 MB free space
- **Display**: 800x600 resolution

### Recommended Requirements
- **Python**: 3.9+
- **RAM**: 4 GB+
- **Storage**: 2 GB (for models and logs)
- **CPU**: Multi-core for faster training

## Installation Methods

### Method 1: Standard Installation (Recommended)

#### Step 1: Verify Python Installation

```bash
python --version
# Should output: Python 3.7.x or higher
```

If Python is not installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

#### Step 2: Clone or Download Repository

**Option A: Git Clone**
```bash
git clone https://github.com/your-repo/PyPongAI.git
cd PyPongAI
```

**Option B: Direct Download**
- Download ZIP from repository
- Extract to desired location
- Navigate to extracted folder

#### Step 3: Install Dependencies

```bash
pip install pygame neat-python numpy pytest
```

**Expected output:**
```
Successfully installed pygame-2.x.x neat-python-0.x.x numpy-1.x.x pytest-7.x.x
```

#### Step 4: Verify Installation

```bash
python -c "import pygame, neat, numpy; print('All dependencies installed!')"
```

If successful, proceed to [Quick Start](quick-start.md).

### Method 2: Virtual Environment (Best Practice)

Isolate PyPongAI dependencies from system Python.

#### Step 1: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now show `(venv)`.

#### Step 2: Install Dependencies in Virtual Environment

```bash
pip install --upgrade pip
pip install pygame neat-python numpy pytest
```

#### Step 3: Verify

```bash
python -c "import pygame, neat, numpy; print('Virtual environment ready!')"
```

#### Deactivating Virtual Environment

When done working:
```bash
deactivate
```

To reactivate later:
- **Windows**: `venv\Scripts\activate`
- **macOS/Linux**: `source venv/bin/activate`

### Method 3: Requirements File (Future)

If a `requirements.txt` file is added:

```bash
pip install -r requirements.txt
```

## Dependency Details

### pygame (Graphics and Game Engine)

**Version**: 2.0.0+
**Purpose**: Visual game rendering, event handling, display management

**Installation Issues:**

**Windows:**
- Usually installs without issues
- If errors occur, try: `pip install pygame --pre`

**macOS:**
- May require Xcode Command Line Tools: `xcode-select --install`
- Alternative: `python3 -m pip install -U pygame --user`

**Linux:**
- May need SDL development libraries:
```bash
sudo apt-get install python3-dev libsdl2-dev libsdl2-image-dev \
  libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev
pip install pygame
```

### neat-python (NEAT Algorithm)

**Version**: 0.92+
**Purpose**: Neural network evolution, genetic algorithms

**Installation:**
```bash
pip install neat-python
```

**Verify:**
```python
import neat
print(neat.__version__)
```

### numpy (Numerical Computing)

**Version**: 1.19.0+
**Purpose**: Novelty search calculations, statistical analysis

**Installation:**
```bash
pip install numpy
```

**Common Issues:**
- Pre-built binaries usually available
- If compilation needed, may require C compiler
- Consider Anaconda distribution for problematic systems

### pytest (Testing Framework, Optional)

**Version**: 7.0.0+
**Purpose**: Running unit tests

**Installation:**
```bash
pip install pytest
```

**Only needed for:** Development and testing

## Platform-Specific Notes

### Windows

**Python Installation:**
1. Download from [python.org](https://www.python.org/downloads/windows/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify: Open Command Prompt, run `python --version`

**PowerShell Execution Policy:**
If virtual environment activation fails:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Common Issues:**
- `pip` not found: Use `python -m pip` instead
- Long path errors: Enable long path support in Windows settings

### macOS

**Python Installation:**
```bash
# Using Homebrew (recommended)
brew install python3

# Or download from python.org
```

**Pygame Issues:**
- macOS may require latest Pygame: `pip install pygame --upgrade`
- If SDL errors occur: `brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer`

**Permission Issues:**
Use `--user` flag:
```bash
pip install --user pygame neat-python numpy
```

### Linux

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
  libsdl2-ttf-dev libfreetype6-dev libportmidi-dev libjpeg-dev
pip3 install pygame neat-python numpy pytest
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip
sudo dnf install SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
pip3 install pygame neat-python numpy pytest
```

**Arch:**
```bash
sudo pacman -S python python-pip
sudo pacman -S sdl2 sdl2_image sdl2_mixer sdl2_ttf
pip install pygame neat-python numpy pytest
```

## Verifying Complete Installation

Run the comprehensive check:

```bash
cd PyPongAI
python -c "
import sys
print(f'Python: {sys.version}')

import pygame
print(f'Pygame: {pygame.__version__}')

import neat
print(f'NEAT-Python: {neat.__version__}')

import numpy
print(f'NumPy: {numpy.__version__}')

try:
    import pytest
    print(f'Pytest: {pytest.__version__}')
except ImportError:
    print('Pytest: Not installed (optional)')

print('\nAll core dependencies installed!')
"
```

**Expected output:**
```
Python: 3.9.x
Pygame: 2.5.x
NEAT-Python: 0.92
NumPy: 1.24.x
Pytest: 7.4.x

All core dependencies installed!
```

## Testing Installation

### Quick Test

```bash
python main.py
```

Should open the main menu. If successful, installation is complete!

### Run Unit Tests

```bash
python -m pytest test_game_simulator.py test_elo_calculation.py -v
```

Should show passing tests:
```
test_game_simulator.py::TestRect::test_initialization PASSED
test_game_simulator.py::TestRect::test_collision PASSED
...
==================== X passed in X.XX s ====================
```

## Troubleshooting

### ImportError: No module named 'pygame'

**Solution:**
```bash
pip install pygame
# Or
python -m pip install pygame
```

### ImportError: No module named 'neat'

**Solution:**
```bash
pip install neat-python
# NOT just 'neat'
```

### pygame.error: No available video device

**Cause:** Running on a headless system (no display)

**Solution:** Use headless training only:
```bash
python train.py  # Works without display
# Avoid: python main.py (requires display)
```

### Module not found despite installation

**Cause:** Multiple Python installations

**Solution:**
1. Check which Python pip is using:
   ```bash
   pip --version
   python --version
   ```
2. Ensure they match
3. Use explicit Python:
   ```bash
   python3 -m pip install pygame neat-python numpy
   python3 main.py
   ```

### Permission denied errors

**Solution:**
```bash
# Use --user flag
pip install --user pygame neat-python numpy

# Or use virtual environment (recommended)
```

### Windows: 'python' is not recognized

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or use Python Launcher:
   ```bash
   py -3 main.py
   py -3 -m pip install pygame neat-python numpy
   ```

### macOS: Command not found: pip

**Solution:**
```bash
python3 -m ensurepip
python3 -m pip install --upgrade pip
```

## Post-Installation

### Create Data Directories

On first run, PyPongAI automatically creates:
```
data/
├── models/
├── logs/
│   ├── training/
│   ├── matches/
│   └── human/
```

To pre-create manually:
```bash
mkdir -p data/models data/logs/training data/logs/matches data/logs/human
```

### Configuration

Default configuration works out-of-the-box. To customize:

1. **Game settings**: Edit `config.py`
2. **NEAT parameters**: Edit `neat_config.txt`
3. **Runtime settings**: Use Settings menu in GUI

See [Configuration Guide](configuration.md) for details.

### Running First Training

```bash
python train.py
```

Will train for 50 generations (~1 minute) and create:
- `data/models/best_genome.pkl`
- `data/logs/training/training_stats_*.csv`

## Next Steps

- **Quick start**: [Quick Start Guide](quick-start.md)
- **First training run**: [Training Guide](training-guide.md)
- **Understand NEAT**: [NEAT Algorithm](neat-algorithm.md)
- **Explore features**: Run `python main.py`

## Getting Help

**Issues during installation?**

1. Check [Troubleshooting](reference/troubleshooting.md)
2. Verify Python version: `python --version` (must be 3.7+)
3. Try virtual environment method
4. Ensure all dependencies installed: Run verification script above
5. Check platform-specific notes

**Still stuck?**

Create an issue with:
- Operating system and version
- Python version (`python --version`)
- Pip version (`pip --version`)
- Full error message
- Steps already tried
