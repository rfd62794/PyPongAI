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
MAX_SCORE = 9

# Create directories if they don't exist
for d in [DATA_DIR, MODEL_DIR, LOG_DIR, LOGS_TRAINING_DIR, LOGS_MATCHES_DIR, LOGS_HUMAN_DIR]:
    os.makedirs(d, exist_ok=True)
