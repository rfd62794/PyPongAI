import pygame
import sys
import config
from states.base import BaseState

class MenuState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        
        # Buttons
        self.btn_play = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 150, 300, 50)
        self.btn_train = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 220, 300, 50)
        self.btn_manage = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 290, 300, 50)
        self.btn_dash = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 360, 300, 50)
        self.btn_quit = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 430, 300, 50)

    def draw_button(self, screen, rect, text, hover=False):
        color = (100, 100, 100) if hover else (50, 50, 50)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, config.WHITE, rect, 2) # Border
        
        text_surf = self.small_font.render(text, True, config.WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                
                if self.btn_play.collidepoint((mx, my)):
                    self.manager.change_state("lobby")
                elif self.btn_train.collidepoint((mx, my)):
                    self.manager.change_state("train")
                elif self.btn_manage.collidepoint((mx, my)):
                    # Placeholder for ModelState
                    print("Model State not implemented yet")
                elif self.btn_dash.collidepoint((mx, my)):
                    # Placeholder for DashboardState
                    print("Dashboard State not implemented yet")
                elif self.btn_quit.collidepoint((mx, my)):
                    self.manager.running = False

    def draw(self, screen):
        screen.fill(config.BLACK)
        
        # Title
        title = self.font.render("Project PaddleMind", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mx, my = pygame.mouse.get_pos()
        
        self.draw_button(screen, self.btn_play, "Play Game", self.btn_play.collidepoint((mx, my)))
        self.draw_button(screen, self.btn_train, "Visual Training", self.btn_train.collidepoint((mx, my)))
        self.draw_button(screen, self.btn_manage, "Manage Models", self.btn_manage.collidepoint((mx, my)))
        self.draw_button(screen, self.btn_dash, "Analytics Dashboard", self.btn_dash.collidepoint((mx, my)))
        self.draw_button(screen, self.btn_quit, "Quit", self.btn_quit.collidepoint((mx, my)))
