# Training Guide

Complete guide to training AI agents in PyPongAI.

## Overview

PyPongAI uses **NEAT (NeuroEvolution of Augmenting Topologies)** to evolve neural networks that play Pong. The system supports multiple training modes with advanced features like ELO-based matchmaking, novelty search, and curriculum learning.

## Training Modes

### 1. Basic Training (`eval_genomes`)

Single-opponent evaluation where each genome plays against a rule-based AI.

```bash
python train.py
```

**Characteristics:**
- Fastest training mode
- Good for initial exploration
- Fixed opponent difficulty
- Limited strategic diversity

**Fitness Function:**
- +0.1 per frame survived
- +10 for scoring a point
- -5 for opponent scoring
- +1 for paddle hits

### 2. Competitive Training (`eval_genomes_competitive`)

ELO-based matchmaking where genomes compete against each other.

**Characteristics:**
- Stable fitness assessment
- Multiple matches per genome (5 default)
- ELO rating system
- Combined with novelty search

**How It Works:**
1. Each genome plays 5 matches against random opponents
2. ELO ratings updated after each match
3. Behavioral characteristics captured during play
4. Final fitness = ELO + (0.1 × Novelty Score)

### 3. Self-Play Training (`eval_genomes_self_play`)

Population self-play with Hall of Fame integration.

**Characteristics:**
- Continuous improvement
- Hall of Fame prevents forgetting
- 20% matches against HOF members
- Best for long-term training

**Hall of Fame:**
- Best genome saved every 5 generations
- Ensures new strategies beat old champions
- Prevents cyclic learning

## Training Workflow

### Step 1: Basic Training

Start with 50 generations of basic training:

```bash
python train.py
```

**What Happens:**
- Population of 50 genomes initialized
- Each generation takes ~1 second
- Best genome saved to `data/models/best_genome.pkl`
- Statistics logged to `data/logs/training/training_*.csv`

**Expected Progress:**
```
Generation 0: Best Fitness: 23.5
Generation 10: Best Fitness: 156.8
Generation 25: Best Fitness: 478.3
Generation 50: Best Fitness: 1234.6
```

### Step 2: Competitive Training

Switch to competitive mode for better skill assessment:

**Modify `train.py`:**
```python
# Change line 156 from:
winner = p.run(ai_module.eval_genomes_self_play, 50)

# To:
winner = p.run(ai_module.eval_genomes_competitive, 50)
```

### Step 3: Curriculum Learning

Gradually increase difficulty:

```python
def eval_with_curriculum(genomes, config_neat):
    generation = p.generation
    current_speed = min(
        config.INITIAL_BALL_SPEED + (generation * config.SPEED_INCREASE_PER_GEN),
        config.MAX_CURRICULUM_SPEED
    )
    return ai_module.eval_genomes_competitive(
        genomes, config_neat, ball_speed=current_speed
    )

winner = p.run(eval_with_curriculum, 100)
```

**Benefits:**
- Faster early convergence
- More robust final agents
- Better generalization

## Configuration

### NEAT Parameters (`neat_config.txt`)

Key parameters to adjust:

```ini
[NEAT]
pop_size = 50              # Population size (more = slower but better exploration)
fitness_threshold = 10000  # Stop when this fitness is reached

[DefaultGenome]
# Network starts with 1 hidden node, can evolve more
num_hidden = 1
num_inputs = 8
num_outputs = 3

# Enable recurrent connections
feed_forward = False

# Mutation rates
conn_add_prob = 0.5        # Chance to add connection
conn_delete_prob = 0.5     # Chance to remove connection
node_add_prob = 0.2        # Chance to add node
node_delete_prob = 0.2     # Chance to remove node
```

### Training Settings (`config.py`)

```python
# Game settings
MAX_SCORE = 20              # Points to win match
BALL_SPEED_X = 3            # Initial ball speed
BALL_MAX_SPEED = 1500       # Speed cap

# ELO settings
ELO_K_FACTOR = 32           # Rating volatility (higher = faster changes)
ELO_INITIAL_RATING = 1200   # Starting rating

# Novelty search
NOVELTY_WEIGHT = 0.1        # Weight of novelty in fitness
NOVELTY_K_NEAREST = 15      # Neighbors for novelty calculation

# Curriculum learning
INITIAL_BALL_SPEED = 2
SPEED_INCREASE_PER_GEN = 0.05
MAX_CURRICULUM_SPEED = 10
```

## Seeding Training

Continue from existing models:

### Seed from Single Model
```bash
python train.py --seed data/models/best_genome.pkl
```

### Seed from Multiple Models
```bash
python train.py --seed_dir data/models/
```

**Use Cases:**
- Continue interrupted training
- Fine-tune trained models
- Combine multiple lineages

## Monitoring Training

### Console Output

```
Generation 0 Best Fitness: 1234.56
   [Validation] Best Genome vs Rule-Based: Avg Rally=12.40, Win Rate=0.60
   [HOF] Added Best Genome to Hall of Fame. Size: 1
Generation 1 Best Fitness: 1289.42
...
```

### CSV Logs

Located in `data/logs/training/training_stats_*.csv`:

```csv
generation,max_fitness,avg_fitness,std_dev,val_avg_rally,val_win_rate
0,1234.56,567.89,123.45,12.40,0.60
1,1289.42,601.23,115.67,13.20,0.65
...
```

### Visual Training

Use the GUI for real-time visualization:

```bash
python main.py
# Select "Train AI"
```

**Features:**
- Watch best agents play
- Real-time fitness graphs
- Generation statistics
- Model selection

## Validation

Every generation, the best genome is validated against a rule-based AI:

**Metrics:**
- **Average Rally**: Paddle hits per game (higher = better defense)
- **Win Rate**: Fraction of games won (0.0 to 1.0)

**Why Validate?**
Self-play fitness is relative. Validation provides objective comparison against a fixed baseline.

## Common Training Issues

### Slow Convergence

**Symptoms:**
- Fitness plateaus early
- Little improvement after 25+ generations

**Solutions:**
1. Increase population size (`pop_size = 100`)
2. Enable curriculum learning
3. Adjust mutation rates
4. Add novelty search

### Unstable Fitness

**Symptoms:**
- Fitness oscillates wildly
- Best fitness decreases between generations

**Solutions:**
1. Switch to competitive training (ELO-based)
2. Increase matches per genome
3. Lower ELO K-factor (`ELO_K_FACTOR = 16`)

### Overfitting

**Symptoms:**
- High training fitness, poor validation
- Agents exploit specific opponent behaviors

**Solutions:**
1. Use Hall of Fame
2. Enable novelty search
3. Validate against multiple opponents
4. Increase opponent diversity

### Memory Issues

**Symptoms:**
- Training crashes after many generations
- Memory usage grows over time

**Solutions:**
1. Limit Hall of Fame size
2. Reduce novelty archive size
3. Disable match recording during training
4. Restart training periodically

## Advanced Training Techniques

### Multi-Stage Training

```python
# Stage 1: Basic training (50 gen)
winner = p.run(ai_module.eval_genomes, 50)

# Stage 2: Competitive training (50 gen)
# Load winner and seed new population
population = seed_from_genome(winner)
winner = p.run(ai_module.eval_genomes_competitive, 50)

# Stage 3: Self-play with HOF (100 gen)
winner = p.run(ai_module.eval_genomes_self_play, 100)
```

### Adaptive Curriculum

```python
class AdaptiveCurriculum:
    def __init__(self):
        self.speed = config.INITIAL_BALL_SPEED
    
    def adjust(self, avg_fitness):
        # Increase speed if population is performing well
        if avg_fitness > 1500:
            self.speed = min(self.speed + 0.1, config.MAX_CURRICULUM_SPEED)
        return self.speed
```

### Novelty-Driven Evolution

Emphasize exploration:

```python
# In config.py
NOVELTY_WEIGHT = 0.5  # Increase from 0.1
```

Higher novelty weight encourages diverse strategies but may slow fitness improvement.

## Best Practices

1. **Start simple**: Basic training for initial generations
2. **Monitor validation**: Use rule-based validation for objective progress
3. **Save checkpoints**: Periodically save best genomes
4. **Log everything**: CSV logs are invaluable for analysis
5. **Test frequently**: Play against trained agents to verify quality
6. **Be patient**: Good agents require 50-100+ generations
7. **Experiment**: Try different evaluation functions and parameters

## Expected Results

**After 50 generations:**
- Basic training: Fitness ~1200-1500
- Competitive training: ELO ~1400-1600
- Self-play: ELO ~1500-1800

**After 100 generations:**
- Competitive training: ELO ~1600-2000
- Self-play: ELO ~1800-2200

**Best ever recorded:** ELO 1876 (Platinum tier)
