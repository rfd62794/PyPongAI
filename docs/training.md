# Training Documentation

## Overview
The PyPongAI training system uses **NEAT (NeuroEvolution of Augmenting Topologies)** to evolve neural networks that play Pong. The training has been upgraded to use **Self-Play** to create a competitive environment where agents evolve by playing against each other.

## Training Process

### 1. Self-Play (Competitive Co-Evolution)
Instead of playing against a static rule-based opponent, agents in the population are paired up to play matches against each other.
- **Matchmaking**: Genomes are paired randomly within the population.
- **Scoring**:
    - **Volleys (Hits)**: The primary driver of fitness. Agents are rewarded (+1.0) for every successful paddle hit. This encourages long rallies and defensive stability.
    - **Winning/Losing**: Bonus points (+5.0) for winning a point, penalties (-2.0) for losing.
    - **Survival**: Small reward (+0.01) for keeping the game going.

### 2. Hall of Fame (HOF)
To prevent "cyclic learning" (where agents forget how to beat older strategies), we implemented a Hall of Fame.
- **Mechanism**: Every 5 generations, the best genome is added to the Hall of Fame.
- **Challenge**: During training, there is a **20% chance** that an agent will play against a randomly selected member of the Hall of Fame instead of a current peer.
- **Benefit**: This ensures that new generations must maintain the ability to defeat past champions, leading to more robust strategies.

### 3. Neural Network Architecture
*   **Inputs (8)**:
    1.  Paddle Y (Self)
    2.  Ball X
    3.  Ball Y
    4.  Ball Velocity X
    5.  Ball Velocity Y
    6.  Relative Y (Paddle Y - Ball Y)
    7.  Incoming (1.0 if ball moving towards paddle, else 0.0)
    8.  **Opponent Paddle Y** (New: Allows AI to react to opponent positioning)
*   **Outputs (3)**:
    1.  Move UP
    2.  Move DOWN
    3.  Stay

### 4. Validation
To track "Real Progress", we validate the best model of each generation against a **Rule-Based AI**.
- **Why?** Self-play fitness can be relative (a bad agent beating another bad agent might look good). Validation against a fixed baseline gives us an objective metric.
- **Metrics**:
    - **Avg Rally Length**: How many times the ball is hit back and forth. Higher is better.
    - **Win Rate**: Percentage of games won against the Rule-Based AI.

## Running Training
### Headless Training
Run `train.py` to train in the background (faster).
```bash
python train.py
```
This will save:
- `models/best_genome.pkl`: The current best model.
- `logs/training_stats_....csv`: A CSV file containing fitness and validation stats per generation.

### Visual Training
Run `visual_train.py` to watch the training progress.
```bash
python visual_train.py
```
- You can select a seed model to start from.
- At the end of each generation, the system will visualize a match between the **Best** and **Second Best** agent.

## Configuration
Adjust `neat_config.txt` to change:
- `pop_size`: Number of agents per generation (default 50).
- `fitness_threshold`: Score required to stop training.
- Network parameters (inputs, outputs, mutation rates).
