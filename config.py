# config.py
import os

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


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

# Create directories if they don't exist
for d in [DATA_DIR, MODEL_DIR, LOG_DIR, LOGS_TRAINING_DIR, LOGS_MATCHES_DIR, LOGS_HUMAN_DIR]:
    os.makedirs(d, exist_ok=True)
