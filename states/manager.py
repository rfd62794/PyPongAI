import pygame
import sys
from core import config

class StateManager:
    def __init__(self, screen):
        self.screen = screen
        self.states = {}
        self.active_state = None
        self.running = True
        self.clock = pygame.time.Clock()

    def register_state(self, name, state_instance):
        self.states[name] = state_instance

    def change_state(self, name, **kwargs):
        if self.active_state:
            self.active_state.exit()
        
        self.active_state = self.states.get(name)
        if self.active_state:
            self.active_state.enter(**kwargs)

    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                    return # Exit immediately from the run loop
                
                if self.active_state:
                    self.active_state.handle_input(event)

            if not self.running:
                break

            if self.active_state:
                self.active_state.update(dt)
                self.active_state.draw(self.screen)
            
            pygame.display.flip()
        
        # Cleanup
        if self.active_state:
            self.active_state.exit()
        pygame.quit()

    def stop(self):
        """Gracefully stop the application and clean up current state."""
        self.running = False
        if self.active_state:
            try:
                self.active_state.exit()
            except Exception as e:
                print(f"Error during state exit: {e}")
