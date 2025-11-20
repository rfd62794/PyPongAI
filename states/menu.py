import pygame
import sys
import config
from states.base import BaseState

class MenuState(BaseState):
    """Modern main menu with clean grid layout."""
    
    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = pygame.font.Font(None, 72)
        self.font_button = pygame.font.Font(None, 36)
        self.font_subtitle = pygame.font.Font(None, 24)
        
        # Theme colors
        self.bg_color = (15, 15, 25)
        self.accent_color = (100, 200, 255)
        self.button_color = (40, 40, 60)
        self.button_hover = (60, 60, 90)
        
        # Button layout (clean 2x3 grid)
        btn_width = 280
        btn_height = 70
        center_x = config.SCREEN_WIDTH // 2
        start_y = 200
        spacing = 90
        
        self.buttons = {
            "play": pygame.Rect(center_x - btn_width - 20, start_y, btn_width, btn_height),
            "train": pygame.Rect(center_x + 20, start_y, btn_width, btn_height),
            "league": pygame.Rect(center_x - btn_width - 20, start_y + spacing, btn_width, btn_height),
            "models": pygame.Rect(center_x + 20, start_y + spacing, btn_width, btn_height),
            "analytics": pygame.Rect(center_x - btn_width - 20, start_y + spacing * 2, btn_width, btn_height),
            "settings": pygame.Rect(center_x + 20, start_y + spacing * 2, btn_width, btn_height)
        }
        
        # Bottom row
        self.btn_quit = pygame.Rect(center_x - 100, config.SCREEN_HEIGHT - 80, 200, 50)
    
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.buttons["play"].collidepoint((mx, my)):
                self.manager.change_state("lobby")
            elif self.buttons["train"].collidepoint((mx, my)):
                self.manager.change_state("train")
            elif self.buttons["league"].collidepoint((mx, my)):
                self.manager.change_state("league")
            elif self.buttons["models"].collidepoint((mx, my)):
                self.manager.change_state("models")
            elif self.buttons["analytics"].collidepoint((mx, my)):
                self.manager.change_state("analytics")
            elif self.buttons["settings"].collidepoint((mx, my)):
                self.manager.change_state("settings")
            elif self.btn_quit.collidepoint((mx, my)):
                pygame.quit()
                exit()
    
    def draw(self, screen):
        screen.fill(self.bg_color)
        
        # Title with glow effect
        title = self.font_title.render("PyPongAI", True, self.accent_color)
        title_shadow = self.font_title.render("PyPongAI", True, (50, 100, 150))
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_subtitle.render("Advanced Neural Network Pong Training Platform", True, (150, 150, 150))
        sub_rect = subtitle.get_rect(center=(config.SCREEN_WIDTH // 2, 130))
        screen.blit(subtitle, sub_rect)
        
        # Draw buttons
        mx, my = pygame.mouse.get_pos()
        
        button_labels = {
            "play": "▶ Play vs AI",
            "train": "🧠 Train AI",
            "league": "🏆 AI League",
            "models": "📦 Models",
            "analytics": "📊 Analytics",
            "settings": "⚙ Settings"
        }
        
        for key, rect in self.buttons.items():
            # Button background
            is_hover = rect.collidepoint((mx, my))
            color = self.button_hover if is_hover else self.button_color
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, self.accent_color if is_hover else (80, 80, 100), rect, 2, border_radius=10)
            
            # Button text
            text = self.font_button.render(button_labels[key], True, (255, 255, 255) if is_hover else (200, 200, 200))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
        
        # Quit button
        is_hover_quit = self.btn_quit.collidepoint((mx, my))
        quit_color = (120, 50, 50) if is_hover_quit else (80, 40, 40)
        pygame.draw.rect(screen, quit_color, self.btn_quit, border_radius=8)
        pygame.draw.rect(screen, (255, 100, 100) if is_hover_quit else (150, 70, 70), self.btn_quit, 2, border_radius=8)
        
        quit_text = self.font_button.render("Quit", True, (255, 200, 200))
        quit_rect = quit_text.get_rect(center=self.btn_quit.center)
        screen.blit(quit_text, quit_rect)
