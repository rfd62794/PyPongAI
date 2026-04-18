import subprocess
import json
import time
import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
PRJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PRJ_ROOT not in sys.path:
    sys.path.insert(0, PRJ_ROOT)

def test_ipc_emission():
    print(f"Testing IPC emission from PyPongAI (Root: {PRJ_ROOT})...")
    
    try:
        import pygame
        # Initialize pygame in headless mode for testing
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        
        from states.game import GameState
        from core import config
        
        # Setup mock manager and state
        mock_manager = MagicMock()
        state = GameState(mock_manager)
        
        # Mock game object to avoid starting real threads/windows
        state.game = MagicMock()
        state.game.score_left = 5
        state.game.score_right = 3
        state.match_start_time = pygame.time.get_ticks() - 30000 # 30s ago
        
        print("Instantiated GameState, triggering IPC event...")
        
        # Call the actual emission method
        state.emit_match_complete_event()
        
        print("\nTest completed. If you see a JSON object above, the IPC logic is working.")
        
    except Exception as e:
        print(f"Error during IPC logic test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ipc_emission()
