import patch_neat
import pygame
import config
from states.manager import StateManager
from states.menu import MenuState
from states.game import GameState
from states.lobby import LobbyState
from states.train import TrainState
from states.models import ModelState
from states.analytics import AnalyticsState
from states.league import LeagueState
from states.replay import ReplayState

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Project PaddleMind")
    
    manager = StateManager(screen)
    
    # Register States
    manager.register_state("menu", MenuState(manager))
    manager.register_state("lobby", LobbyState(manager))
    manager.register_state("game", GameState(manager))
    manager.register_state("train", TrainState(manager))
    manager.register_state("models", ModelState(manager))
    manager.register_state("analytics", AnalyticsState(manager))
    manager.register_state("league", LeagueState(manager))
    manager.register_state("replay", ReplayState(manager))
    
    # Start with Menu
    manager.change_state("menu")
    
    manager.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        pygame.quit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        pygame.quit()
