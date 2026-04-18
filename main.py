import patch_neat
import os
import pygame
from core.automation_bridge import AutomationBridge

def main():
    # Import pygame and other modules only when actually running main
    from core import config
    from states.manager import StateManager
    from states.menu import MenuState
    from states.game import GameState
    from states.lobby import LobbyState
    from states.train import TrainState
    from states.models import ModelState
    from states.analytics import AnalyticsState
    from states.compare import CompareState
    from states.league import LeagueState
    from states.replay import ReplayState
    from states.settings import SettingsState
    
    logger = logging.getLogger(__name__)
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.WINDOW_TITLE)
    
    # Start Automation Bridge if requested
    automation_enabled = os.getenv("PYPONGAI_AUTOMATION", "false").lower() == "true"
    bridge = AutomationBridge(enabled=automation_enabled)
    bridge.start()
    
    manager = StateManager(screen)
    
    # Register States
    manager.register_state("menu", MenuState(manager))
    manager.register_state("lobby", LobbyState(manager))
    manager.register_state("game", GameState(manager))
    manager.register_state("train", TrainState(manager))
    manager.register_state("models", ModelState(manager))
    manager.register_state("analytics", AnalyticsState(manager))
    manager.register_state("compare", CompareState(manager))
    manager.register_state("league", LeagueState(manager))
    manager.register_state("replay", ReplayState(manager))
    manager.register_state("settings", SettingsState(manager))
    
    # Start with Menu
    manager.change_state("menu")
    
    try:
        logger.info("PyPongAI started")
        manager.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received (CTRL+C)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Starting shutdown cleanup...")
        from ai import ai_module
        ai_module.cleanup_eval_pool()
        if manager:
            manager.stop()
        if bridge:
            bridge.stop()
        pygame.quit()
        logger.info("PyPongAI exited cleanly")

if __name__ == "__main__":
    import logging
    import sys
    import multiprocessing
    
    # Required for Windows multiprocessing support
    multiprocessing.freeze_support()
    
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    try:
        main()
    except KeyboardInterrupt:
        # Catch it here if it's not caught in main()
        pass
    finally:
        # Final safety exit to prevent atexit tracebacks from multiprocessing on Windows
        import os
        os._exit(0)
