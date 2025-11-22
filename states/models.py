import pygame
import os
import config
from ai import model_manager
from utils import elo_manager
from states.base import BaseState

class ModelState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.models = []
        self.page = 0
        self.per_page = 8
        self.selected_index = -1
        
        # Buttons
        self.btn_organize = pygame.Rect(50, config.SCREEN_HEIGHT - 80, 200, 50)
        self.btn_convert = pygame.Rect(270, config.SCREEN_HEIGHT - 80, 200, 50)
        self.btn_back = pygame.Rect(config.SCREEN_WIDTH - 150, 20, 100, 40)

    def enter(self, **kwargs):
        self.refresh_models()
        
    def refresh_models(self):
        self.models = model_manager.scan_models()
        self.models.sort(key=lambda x: model_manager.get_fitness_from_filename(os.path.basename(x)), reverse=True)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.btn_back.collidepoint((mx, my)):
                self.manager.change_state("menu")
                return

            if self.btn_organize.collidepoint((mx, my)):
                print("Organizing models...")
                model_manager.organize_models()
                self.refresh_models()
                
            if self.btn_convert.collidepoint((mx, my)):
                print("Converting models to ELO format...")
                model_manager.convert_models_to_elo_format()
                self.refresh_models()
            
            # Pagination clicks
            if config.SCREEN_HEIGHT - 150 < my < config.SCREEN_HEIGHT - 100:
                 if mx < config.SCREEN_WIDTH // 2:
                     self.page = max(0, self.page - 1)
                 else:
                     max_page = (len(self.models) - 1) // self.per_page
                     self.page = min(max_page, self.page + 1)
                     
            # Model Selection (Optional, maybe for delete later)
            start_idx = self.page * self.per_page
            end_idx = min(start_idx + self.per_page, len(self.models))
            
            list_y = 120
            for i in range(start_idx, end_idx):
                rect = pygame.Rect(50, list_y, config.SCREEN_WIDTH - 100, 40)
                if rect.collidepoint((mx, my)):
                    self.selected_index = i
                list_y += 50

    def draw(self, screen):
        from utils import elo_manager
        elo_ratings = elo_manager.load_elo_ratings()
        
        screen.fill(config.BLACK)
        
        # Header
        title = self.font.render("Model Manager", True, config.WHITE)
        screen.blit(title, (50, 30))
        
        stats = f"Total Models: {len(self.models)}"
        stats_surf = self.small_font.render(stats, True, config.GRAY)
        screen.blit(stats_surf, (50, 70))
        
        # Model List
        start_idx = self.page * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.models))
        
        list_y = 120
        for i in range(start_idx, end_idx):
            model_path = self.models[i]
            filename = os.path.basename(model_path)
            fitness = model_manager.get_fitness_from_filename(filename)
            parent_dir = os.path.basename(os.path.dirname(model_path))
            elo = elo_ratings.get(filename, "-")
            
            # Get ELO tier
            if isinstance(elo, (int, float)):
                tier = elo_manager.get_elo_tier(elo)
            else:
                tier = "N/A"
            
            # Highlight selected
            rect = pygame.Rect(50, list_y, config.SCREEN_WIDTH - 100, 40)
            color = (70, 70, 100) if i == self.selected_index else (40, 40, 40)
            
            # Hover effect
            mx, my = pygame.mouse.get_pos()
            if rect.collidepoint((mx, my)):
                color = (60, 60, 80) if i != self.selected_index else (80, 80, 120)
                
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, config.WHITE, rect, 1)
            
            text = f"{i+1}. {filename} | Fit: {fitness} | ELO: {elo} [{tier}] | Loc: {parent_dir}"
            text_surf = self.small_font.render(text, True, config.WHITE)
            screen.blit(text_surf, (60, list_y + 10))
            
            list_y += 50
            
        # Pagination Controls
        if len(self.models) > self.per_page:
            page_text = f"Page {self.page + 1} / {(len(self.models) - 1) // self.per_page + 1}"
            page_surf = self.small_font.render(page_text, True, config.WHITE)
            screen.blit(page_surf, (config.SCREEN_WIDTH // 2 - page_surf.get_width() // 2, list_y + 10))
            
            hint = self.small_font.render("Click Left/Right side to Navigate", True, config.GRAY)
            screen.blit(hint, (config.SCREEN_WIDTH // 2 - hint.get_width() // 2, list_y + 30))

        # Action Buttons
        # Organize
        pygame.draw.rect(screen, (50, 100, 50), self.btn_organize)
        pygame.draw.rect(screen, config.WHITE, self.btn_organize, 2)
        org_text = self.font.render("Auto-Organize", True, config.WHITE)
        screen.blit(org_text, (self.btn_organize.centerx - org_text.get_width()//2, self.btn_organize.centery - org_text.get_height()//2))
        
        # Convert
        pygame.draw.rect(screen, (50, 50, 100), self.btn_convert)
        pygame.draw.rect(screen, config.WHITE, self.btn_convert, 2)
        conv_text = self.font.render("Convert ELO", True, config.WHITE)
        screen.blit(conv_text, (self.btn_convert.centerx - conv_text.get_width()//2, self.btn_convert.centery - conv_text.get_height()//2))
        
        # Back
        pygame.draw.rect(screen, (100, 50, 50), self.btn_back)
        pygame.draw.rect(screen, config.WHITE, self.btn_back, 2)
        back_text = self.small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (self.btn_back.centerx - back_text.get_width()//2, self.btn_back.centery - back_text.get_height()//2))
