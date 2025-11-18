Software Design Document: Project PaddleMind
Version: 1.2
Date: 2025-11-18
Author: Manus AI
1. Introduction
1.1 Project Title
Project PaddleMind
1.2 Project Overview
"Project PaddleMind" is a Python-based implementation of the classic arcade game Pong, designed primarily as a training and evaluation environment for an AI agent. The project repository and folder will be named PyPongAI. The Minimum Viable Product (MVP) will deliver a stable game environment, a detailed analytics logger, and a Reinforcement Learning (RL) agent using the neat-python library.
1.3 Core Priority (MVP)
The primary goal is to create a robust AI vs. AI training loop. Player vs. AI and Player vs. Player modes are secondary and exist mainly for testing and demonstration of the trained AI agents.
2. System Architecture
2.1 Core Technologies
Language: Python 3.10+
Game Engine: pygame
Data Handling: pandas
AI/ML: neat-python
Configuration: A dedicated config.py file.
Standard Library: datetime, os
2.2 File Structure
The project will be organized into the following structure to ensure separation of concerns.
Plain Text
PyPongAI/
├── main.py             # Main driver, handles mode selection and initializes the game
├── game_engine.py      # Core game logic, classes for Ball, Paddle, Game
├── ai_module.py        # Contains AI logic (Rule-based and NEAT integration)
├── analytics.py        # Handles all data logging
├── config.py           # Centralized configuration for game and AI parameters
├── train.py            # Script dedicated to running the NEAT training loop
├── play.py             # Script to play against a trained AI model
├── logs/               # Directory to store all generated CSV log files
└── neat_config.txt     # Configuration file required by the neat-python library
3. Detailed Design
3.1 Configuration (config.py)
A centralized file will hold all constants and tunable parameters to avoid hard-coding and facilitate easy adjustments.
Constants:
SCREEN_WIDTH, SCREEN_HEIGHT
PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED
BALL_RADIUS, BALL_SPEED_X, BALL_SPEED_Y
FPS (Frames Per Second)
FONT_SIZE, WHITE, BLACK (Color definitions)
NEAT_CONFIG_PATH: Path to neat_config.txt.
MODEL_DIR: Directory to save trained AI models.
LOG_DIR: Directory to save log files.
3.2 Game Engine (game_engine.py)
This module encapsulates the core game mechanics.
Paddle Class:
Attributes: rect (a pygame.Rect object), speed.
Methods: move(direction), draw(screen).
Ball Class:
Attributes: rect, velocity_x, velocity_y.
Methods: move(), draw(screen), reset().
Game Class:
__init__(self, screen, paddle1, paddle2): Initializes a game session.
update(self): Advances the game by one frame. Handles movement, collision detection, and scoring.
get_state(self): Returns a tuple of the current game state required by the AI, e.g., (self.paddle1.rect.y, self.paddle2.rect.y, self.ball.rect.x, self.ball.rect.y, self.ball.velocity_x, self.ball.velocity_y).
draw_elements(self): Renders all game objects and the current score.
3.3 Analytics Module (analytics.py)
Handles all data logging operations.
Functions:
create_log_file(log_dir):
Ensures the log_dir (e.g., "logs/") exists using os.makedirs.
Generates a unique filename: log_YYYYMMDD_HHMMSS.csv.
Creates the file and writes the header row.
Returns the full path to the newly created file.
log_score(log_filepath, score_data): Appends a single row of detailed score data to the specified log file.
Data Schema (CSV Columns):
timestamp: datetime when the point was scored.
game_mode: e.g., 'AI_vs_AI', 'Player_vs_AI'.
scoring_player: 'Player1' or 'Player2'.
ball_x, ball_y: Ball's position at the moment of the score.
ball_velocity_x, ball_velocity_y: Ball's velocity at the moment of the score.
paddle1_y, paddle2_y: Y-position of both paddles at the moment of the score.
3.4 AI Module (ai_module.py)
Contains all AI-related logic.
Rule-Based AI:
get_rule_based_move(game_state): A simple function that takes the game state and returns a move (UP, DOWN, or STAY). Logic: Move paddle towards the ball's Y position.
NEAT Fitness Function:
eval_genomes(genomes, config): This is the core of the training process and will be passed to the neat-python runner.
It will iterate through genomes, creating a neural network for each one.
It will pit two genomes against each other in a game instance.
Fitness Calculation: A genome's fitness score starts at 0 and is incremented for every frame it successfully keeps the ball in play. Hitting the ball can provide a small fitness bonus.
The game loop runs until one AI misses, at which point the fitness evaluation for that pair of genomes is complete.
3.5 Main Driver Scripts
train.py (High Priority):
Loads the NEAT configuration from the path specified in config.py.
Creates a neat.Population object.
Adds standard reporters (neat.StdOutReporter, neat.StatisticsReporter).
Calls population.run(ai_module.eval_genomes, n=50), where n is the number of generations to train.
After training, serializes the best-performing genome using pickle and saves it to the MODEL_DIR.
play.py (High Priority):
Provides an interface to select a saved AI model from MODEL_DIR.
Loads the selected model using pickle.
Initializes a Game in Player vs. AI mode, rendering to the screen.
The player controls one paddle via keyboard input.
The AI's paddle is controlled by feeding the game state into the loaded neural network on every frame.
main.py (Low Priority):
A simple entry point that can present a command-line menu to the user to either:
Start a new training session (run train.py).
Play against a trained AI (run play.py).
Start a Player vs. Player match.
4. MVP Feature & Priority Summary
Feature
Description
Priority
AI Training Environment
train.py script to run headless AI vs. AI games for NEAT training.
High
Save/Load Best AI
The training process saves the best AI model to a file.
High
AI Playback Mode
play.py script to load a trained AI and play against it.
High
Centralized Config
config.py for easy tuning of game and AI parameters.
High
Detailed Logging
analytics.py logs score-event details to unique CSV files.
Medium
Rule-Based AI
A simple AI for baseline comparison and initial testing.
Medium
Player vs. Player Mode
Basic two-player mode for demonstration.
Low