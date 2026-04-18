import pygame
import sys
from core import config
from states.base import BaseState

class MenuState(BaseState):
    """Modern main menu with clean grid layout and premium aesthetics."""
    
    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = pygame.font.Font(None, config.FONT_TITLE_SIZE)
        self.font_button = pygame.font.Font(None, config.FONT_BODY_SIZE)
        self.font_subtitle = pygame.font.Font(None, config.FONT_SMALL_SIZE)
        
        # UI Metrics
        BUTTON_WIDTH = 280
        BUTTON_HEIGHT = 60
        GRID_SPACING = 30
        
        center_x = config.SCREEN_WIDTH // 2
        center_y = config.SCREEN_HEIGHT // 2 + 50 # Offset down to make room for title
        
        # Button layout (2 columns, 3 rows, centered)
        left_x = center_x - BUTTON_WIDTH - GRID_SPACING // 2
        right_x = center_x + GRID_SPACING // 2
        
        row1_y = center_y - (BUTTON_HEIGHT * 1.5 + GRID_SPACING)
        row2_y = center_y - (BUTTON_HEIGHT * 0.5)
        row3_y = center_y + (BUTTON_HEIGHT * 0.5 + GRID_SPACING)
        
        self.buttons = {
            "play": pygame.Rect(left_x, row1_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "train": pygame.Rect(right_x, row1_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "league": pygame.Rect(left_x, row2_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "models": pygame.Rect(right_x, row2_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "analytics": pygame.Rect(left_x, row3_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "settings": pygame.Rect(right_x, row3_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        }
        
        # Bottom row
        self.btn_quit = pygame.Rect(center_x - 100, config.SCREEN_HEIGHT - 70, 200, 45)
    
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
                sys.exit()
        
        # Route keyboard events to BaseState for universal navigation
        super().handle_input(event)
    
    def _draw_button(self, screen, rect, text, is_hovered):
        """Draws a themed button with hover effects and rounded corners."""
        color = config.COLOR_BUTTON_HOVER if is_hovered else config.COLOR_BUTTON_DEFAULT
        # Border
        border_color = config.COLOR_ACCENT if is_hovered else (80, 80, 100)
        
        pygame.draw.rect(screen, color, rect, border_radius=12)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=12)
        
        # Text
        text_color = config.COLOR_TEXT_PRIMARY if is_hovered else config.COLOR_TEXT_SECONDARY
        text_surf = self.font_button.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw(self, screen):
        screen.fill(config.COLOR_BACKGROUND)
        
        center_x = config.SCREEN_WIDTH // 2
        
        # Title with shadow effect
        title_text = config.BRAND_NAME
        title_surf = self.font_title.render(title_text, True, config.COLOR_ACCENT)
        shadow_surf = self.font_title.render(title_text, True, (0, 0, 0))
        
        title_rect = title_surf.get_rect(center=(center_x, 80))
        screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle = self.font_subtitle.render(config.BRAND_SUBTITLE, True, config.COLOR_TEXT_SECONDARY)
        sub_rect = subtitle.get_rect(center=(center_x, 135))
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
            self._draw_button(screen, rect, button_labels[key], rect.collidepoint((mx, my)))
        
        # Quit button (smaller, red-themed)
        is_hover_quit = self.btn_quit.collidepoint((mx, my))
        quit_bg = (120, 50, 50) if is_hover_quit else (80, 40, 40)
        pygame.draw.rect(screen, quit_bg, self.btn_quit, border_radius=10)
        pygame.draw.rect(screen, config.COLOR_FAILURE if is_hover_quit else (150, 70, 70), self.btn_quit, 2, border_radius=10)
        
        quit_surf = self.font_button.render("Quit", True, (255, 200, 200))
        quit_rect = quit_surf.get_rect(center=self.btn_quit.center)
        screen.blit(quit_surf, quit_rect)
