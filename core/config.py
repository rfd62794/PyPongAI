# config.py
import os

# Brand
BRAND_NAME = "PyPongAI"
BRAND_SUBTITLE = "Neuroevolution Research Platform"
WINDOW_TITLE = "PyPongAI: Evolutionary Pong AI"

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Theme Colors (Dark Professional)
COLOR_BACKGROUND = (15, 15, 25)      # Deep dark blue
COLOR_ACCENT = (100, 200, 255)        # Bright cyan
COLOR_ACCENT_SECONDARY = (70, 150, 255)  # Darker cyan
COLOR_TEXT_PRIMARY = (255, 255, 255)   # White
COLOR_TEXT_SECONDARY = (200, 200, 220) # Light gray
COLOR_BUTTON_DEFAULT = (40, 40, 60)    # Dark gray
COLOR_BUTTON_HOVER = (70, 80, 110)     # Lighter gray
COLOR_SUCCESS = (100, 255, 150)        # Green (for wins)
COLOR_FAILURE = (255, 100, 100)        # Red (for losses)

# Legacy Color Aliases (for compatibility during migration)
WHITE = COLOR_TEXT_PRIMARY
BLACK = (0, 0, 0)
RED = COLOR_FAILURE
GREEN = COLOR_SUCCESS
BLUE = (0, 0, 255)
GRAY = COLOR_TEXT_SECONDARY
YELLOW = (255, 255, 0)

# Typography
FONT_TITLE_SIZE = 60
FONT_HEADING_SIZE = 40
FONT_BODY_SIZE = 30
FONT_SMALL_SIZE = 24

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
MAX_SCORE = 99
VISUAL_MAX_SCORE = 5
PADDLE_MAX_SPEED = 15

# Curriculum Learning Settings
INITIAL_BALL_SPEED = 2
SPEED_INCREASE_PER_GEN = 0.05
MAX_CURRICULUM_SPEED = 10

# File Paths
NEAT_CONFIG_PATH = "neat_config.txt"

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
LOG_DIR = os.path.join(DATA_DIR, "logs")
LOGS_TRAINING_DIR = os.path.join(LOG_DIR, "training")
LOGS_MATCHES_DIR = os.path.join(LOG_DIR, "matches")
LOGS_HUMAN_DIR = os.path.join(LOG_DIR, "human")
MATCH_RECORDINGS_DIR = LOGS_MATCHES_DIR # Added for comparison state

# Tournament Settings
TOURNAMENT_MIN_FITNESS_DEFAULT = 200
TOURNAMENT_SIMILARITY_THRESHOLD = 10
TOURNAMENT_DELETE_SHUTOUTS = True
TOURNAMENT_VISUAL_DEFAULT = True

# ELO Settings
ELO_K_FACTOR = 32
ELO_INITIAL_RATING = 1200

# ELO Tier System (Gamification)
BRONZE_ELO_THRESHOLD = 1200
SILVER_ELO_THRESHOLD = 1400
GOLD_ELO_THRESHOLD = 1600
PLATINUM_ELO_THRESHOLD = 1800

# Novelty Search Settings
NOVELTY_WEIGHT = 0.1
NOVELTY_K_NEAREST = 15

# Create directories if they don't exist
for d in [DATA_DIR, MODEL_DIR, LOG_DIR, LOGS_TRAINING_DIR, LOGS_MATCHES_DIR, LOGS_HUMAN_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================================
# AUTOMATION MODE CONFIGURATION
# ============================================================================

def apply_automation_overrides():
    """Apply devlog-optimized settings when running in automation mode."""
    global VISUAL_MAX_SCORE, BALL_SPEED_X, BALL_SPEED_Y, BALL_SPEED_INCREMENT
    global PADDLE_SPEED, PADDLE_WIDTH, SPEED_INCREASE_PER_GEN, MAX_CURRICULUM_SPEED 
    global BALL_MAX_SPEED, PADDLE_MAX_SPEED, FPS, PADDLE_HEIGHT
    
    if os.getenv("PYPONGAI_AUTOMATION") != "true":
        return  # No overrides needed
    
    # Override settings for devlog clip recording (Plaid Speed Mode)
    VISUAL_MAX_SCORE = 3
    FPS = 240                       # 4x simulation speed
    BALL_SPEED_X = 15               # Extreme initial launch
    BALL_SPEED_Y = 15
    BALL_SPEED_INCREMENT = 1.25     # Viral speed growth
    BALL_MAX_SPEED = 60             # No speed limits
    PADDLE_MAX_SPEED = 60
    PADDLE_SPEED = 50               # Instant response
    PADDLE_HEIGHT = 60              # Smaller paddles = more dynamic scoring
    PADDLE_WIDTH = 25
    SPEED_INCREASE_PER_GEN = 0
    MAX_CURRICULUM_SPEED = BALL_SPEED_X
    
    print("[DEVLOG MODE] Automation settings applied: PLAID SPEED (240 FPS), high-intensity smaller paddles")

# Apply overrides on module load
apply_automation_overrides()
