# config.py
import os

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Game Settings
FPS = 60
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
PADDLE_SPEED = 7
BALL_RADIUS = 7
BALL_SPEED_X = 8
BALL_SPEED_Y = 8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# File Paths
NEAT_CONFIG_PATH = "neat_config.txt"
MODEL_DIR = "models"
LOG_DIR = "logs"

# Ensure directories exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
