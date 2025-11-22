"""Settings State for PyPongAI.

Allows users to view and modify configurable parameters with a clean UI.
"""

import pygame
import json
import os
from core import config
from states.base import BaseState


SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.json")


def load_settings():
    """Loads settings from JSON file.
    
    Returns:
        dict: User settings, or defaults if file doesn't exist.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Return defaults
    return {
        "MAX_SCORE": config.MAX_SCORE,
        "VISUAL_MAX_SCORE": config.VISUAL_MAX_SCORE,
        "ELO_K_FACTOR": config.ELO_K_FACTOR,
        "NOVELTY_WEIGHT": config.NOVELTY_WEIGHT,
        "INITIAL_BALL_SPEED": config.INITIAL_BALL_SPEED,
        "SPEED_INCREASE_PER_GEN": config.SPEED_INCREASE_PER_GEN
    }


def save_settings(settings):
    """Saves settings to JSON file.
    
    Args:
        settings: Dictionary of settings to save.
    """
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def apply_settings(settings):
    """Applies settings to config module.
    
    Args:
        settings: Dictionary of settings to apply.
    """
    config.MAX_SCORE = settings.get("MAX_SCORE", 20)
    config.VISUAL_MAX_SCORE = settings.get("VISUAL_MAX_SCORE", 5)
    config.ELO_K_FACTOR = settings.get("ELO_K_FACTOR", 32)
    config.NOVELTY_WEIGHT = settings.get("NOVELTY_WEIGHT", 0.1)
    config.INITIAL_BALL_SPEED = settings.get("INITIAL_BALL_SPEED", 2)
    config.SPEED_INCREASE_PER_GEN = settings.get("SPEED_INCREASE_PER_GEN", 0.05)


class SettingsState(BaseState):
    """Settings configuration interface.
    
    Provides UI for viewing and modifying game configuration parameters.
    """
    
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 28)
        self.tiny_font = pygame.font.Font(None, 24)
        
        self.settings = load_settings()
        self.selected_setting = None
        self.input_text = ""
        
        # Setting definitions
        self.setting_defs = [
            {"key": "MAX_SCORE", "label": "Max Score (Training)", "type": "int", "min": 1, "max": 100},
            {"key": "VISUAL_MAX_SCORE", "label": "Max Score (Visual)", "type": "int", "min": 1, "max": 20},
            {"key": "ELO_K_FACTOR", "label": "ELO K-Factor", "type": "int", "min": 1, "max": 100},
            {"key": "NOVELTY_WEIGHT", "label": "Novelty Weight", "type": "float", "min": 0.0, "max": 1.0},
            {"key": "INITIAL_BALL_SPEED", "label": "Initial Ball Speed", "type": "float", "min": 1.0, "max": 10.0},
            {"key": "SPEED_INCREASE_PER_GEN", "label": "Speed Increase/Gen", "type": "float", "min": 0.0, "max": 1.0}
        ]
        
        # Buttons
        self.btn_save = pygame.Rect(config.SCREEN_WIDTH // 2 - 100, config.SCREEN_HEIGHT - 120, 200, 50)
        self.btn_reset = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, config.SCREEN_HEIGHT - 120, 120, 50)
        self.btn_back = pygame.Rect(config.SCREEN_WIDTH - 150, 20, 100, 40)
    
    def enter(self, **kwargs):
        """Called when entering this state."""
        self.settings = load_settings()
        self.selected_setting = None
        self.input_text = ""
    
    def handle_input(self, event):
        """Handles user input events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Back button
            if self.btn_back.collidepoint((mx, my)):
                self.manager.change_state("menu")
                return
            
            # Save button
            if self.btn_save.collidepoint((mx, my)):
                save_settings(self.settings)
                apply_settings(self.settings)
                print("Settings saved!")
                return
            
            # Reset button
            if self.btn_reset.collidepoint((mx, my)):
                self.settings = {
                    "MAX_SCORE": 20,
                    "VISUAL_MAX_SCORE": 5,
                    "ELO_K_FACTOR": 32,
                    "NOVELTY_WEIGHT": 0.1,
                    "INITIAL_BALL_SPEED": 2,
                    "SPEED_INCREASE_PER_GEN": 0.05
                }
                self.selected_setting = None
                print("Settings reset to defaults!")
                return
            
            # Setting selection
            y_pos = 120
            for setting_def in self.setting_defs:
                rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
                if rect.collidepoint((mx, my)):
                    self.selected_setting = setting_def["key"]
                    self.input_text = str(self.settings.get(setting_def["key"], ""))
                    return
                y_pos += 70
        
        elif event.type == pygame.KEYDOWN:
            if self.selected_setting:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Apply the input
                    self._apply_input()
                    self.selected_setting = None
                elif event.key == pygame.K_ESCAPE:
                    self.selected_setting = None
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    # Only allow valid characters
                    if event.unicode in "0123456789.-":
                        self.input_text += event.unicode
    
    def _apply_input(self):
        """Applies the current input text to the selected setting."""
        if not self.selected_setting or not self.input_text:
            return
        
        # Find setting definition
        setting_def = next((s for s in self.setting_defs if s["key"] == self.selected_setting), None)
        if not setting_def:
            return
        
        try:
            if setting_def["type"] == "int":
                value = int(self.input_text)
                value = max(setting_def["min"], min(setting_def["max"], value))
            else:  # float
                value = float(self.input_text)
                value = max(setting_def["min"], min(setting_def["max"], value))
            
            self.settings[self.selected_setting] = value
        except ValueError:
            pass  # Invalid input, ignore
    
    def draw(self, screen):
        """Draws the settings interface."""
        screen.fill((20, 20, 30))
        
        # Header
        title = self.font.render("⚙ Settings", True, (100, 200, 255))
        screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 30))
        
        hint = self.tiny_font.render("Click a setting to edit | Press ENTER to confirm", True, (150, 150, 150))
        screen.blit(hint, (config.SCREEN_WIDTH // 2 - hint.get_width() // 2, 80))
        
        # Settings list
        y_pos = 120
        for setting_def in self.setting_defs:
            key = setting_def["key"]
            label = setting_def["label"]
            value = self.settings.get(key, "N/A")
            
            # Background rect
            rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
            is_selected = (self.selected_setting == key)
            
            # Color based on selection
            if is_selected:
                color = (60, 60, 100)
            else:
                mx, my = pygame.mouse.get_pos()
                if rect.collidepoint((mx, my)):
                    color = (40, 40, 60)
                else:
                    color = (30, 30, 40)
            
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (100, 200, 255) if is_selected else (80, 80, 80), rect, 2)
            
            # Label
            label_surf = self.small_font.render(label, True, (200, 200, 200))
            screen.blit(label_surf, (120, y_pos + 15))
            
            # Value (or input box)
            if is_selected:
                value_text = self.input_text + "_"
            else:
                value_text = str(value)
            
            value_surf = self.small_font.render(value_text, True, (255, 255, 100) if is_selected else (150, 255, 150))
            screen.blit(value_surf, (config.SCREEN_WIDTH - 250, y_pos + 15))
            
            y_pos += 70
        
        # Buttons
        # Save
        color = (50, 150, 50)
        mx, my = pygame.mouse.get_pos()
        if self.btn_save.collidepoint((mx, my)):
            color = (70, 170, 70)
        pygame.draw.rect(screen, color, self.btn_save)
        pygame.draw.rect(screen, (100, 255, 100), self.btn_save, 2)
        save_text = self.font.render("Save", True, (255, 255, 255))
        screen.blit(save_text, (self.btn_save.centerx - save_text.get_width() // 2,
                                 self.btn_save.centery - save_text.get_height() // 2))
        
        # Reset
        color = (150, 100, 50)
        if self.btn_reset.collidepoint((mx, my)):
            color = (170, 120, 70)
        pygame.draw.rect(screen, color, self.btn_reset)
        pygame.draw.rect(screen, (255, 200, 100), self.btn_reset, 2)
        reset_text = self.small_font.render("Reset", True, (255, 255, 255))
        screen.blit(reset_text, (self.btn_reset.centerx - reset_text.get_width() // 2,
                                  self.btn_reset.centery - reset_text.get_height() // 2))
        
        # Back
        pygame.draw.rect(screen, (100, 50, 50), self.btn_back)
        pygame.draw.rect(screen, (255, 100, 100), self.btn_back, 2)
        back_text = self.small_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, (self.btn_back.centerx - back_text.get_width() // 2,
                                 self.btn_back.centery - back_text.get_height() // 2))


# Auto-apply settings on module load
apply_settings(load_settings())
