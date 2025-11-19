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
BALL_SPEED_X = 3
BALL_SPEED_Y = 3
BALL_SPEED_INCREMENT = 1.05
BALL_MAX_SPEED = 15
MAX_SCORE = 20
PADDLE_MAX_SPEED = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# File Paths
NEAT_CONFIG_PATH = "neat_config.txt"

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
LOG_DIR = os.path.join(DATA_DIR, "logs")
LOGS_TRAINING_DIR = os.path.join(LOG_DIR, "training")
LOGS_MATCHES_DIR = os.path.join(LOG_DIR, "matches")
LOGS_HUMAN_DIR = os.path.join(LOG_DIR, "human")

# Tournament Settings
TOURNAMENT_MIN_FITNESS_DEFAULT = 200
TOURNAMENT_SIMILARITY_THRESHOLD = 10
TOURNAMENT_DELETE_SHUTOUTS = True
TOURNAMENT_VISUAL_DEFAULT = True

# Create directories if they don't exist
for d in [DATA_DIR, MODEL_DIR, LOG_DIR, LOGS_TRAINING_DIR, LOGS_MATCHES_DIR, LOGS_HUMAN_DIR]:
    os.makedirs(d, exist_ok=True)
