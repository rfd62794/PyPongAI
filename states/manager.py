import pygame
import sys
import config

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
                    self.running = False
                    sys.exit(0)
                
                if self.active_state:
                    self.active_state.handle_input(event)

            if self.active_state:
                self.active_state.update(dt)
                self.active_state.draw(self.screen)
            
            pygame.display.flip()
        
        pygame.quit()
