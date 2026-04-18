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
        manager.stop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Unexpected error: {e}")
        manager.stop()
    finally:
        bridge.stop()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger = logging.getLogger(__name__)

    manager = None
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received (CTRL+C)")
        # We need access to the manager here. 
        # I'll modify main() to return the manager or handle it differently.
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Unexpected error: {e}")
    finally:
        pygame.quit()
        logger.info("PyPongAI exited cleanly")
