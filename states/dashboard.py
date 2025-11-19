import pygame
import os
import glob
import pandas as pd
import config
from states.base import BaseState

class DashboardState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.BG_COLOR = (30, 30, 30)
        self.TAB_COLOR = (50, 50, 50)
        self.TAB_ACTIVE_COLOR = (80, 80, 80)
        self.TEXT_COLOR = config.WHITE
        self.HIGHLIGHT_COLOR = (100, 100, 255)
        
        self.active_tab = "Overview"
        self.tabs = ["Overview", "Models", "Matches"]
        self.scroll_y = 0
        
        self.models = []
        self.matches = []
        self.human_stats = {'total_frames': 0, 'actions': {}}

    def enter(self, **kwargs):
        self.load_data()
        self.scroll_y = 0

    def load_data(self):
        self.models = self.load_models()
        self.matches = self.load_matches()
        self.human_stats = self.load_human_stats()

    def load_models(self):
        models = []
        for root, dirs, files in os.walk(config.MODEL_DIR):
            for file in files:
                if file.endswith(".pkl"):
                    full_path = os.path.join(root, file)
                    fitness = 0
                    try:
                        if "fitness" in file:
                            fitness = int(file.split("fitness")[1].split(".")[0])
                        elif "_fit_" in file:
                            fitness = int(file.split("_fit_")[1].split(".")[0])
                    except:
                        pass
                    
                    tier = os.path.basename(os.path.dirname(full_path))
                    if tier == "models": tier = "Unsorted"
                    
                    models.append({
                        "name": file,
                        "path": full_path,
                        "fitness": fitness,
                        "tier": tier
                    })
        models.sort(key=lambda x: x["fitness"], reverse=True)
        return models

    def load_matches(self):
        matches = []
        files = glob.glob(os.path.join(config.LOGS_MATCHES_DIR, "*.csv"))
        for f in files:
            try:
                df = pd.read_csv(f)
                if not df.empty:
                    matches.append({
                        "file": os.path.basename(f),
                        "frames": len(df),
                        "max_score_left": df['score_left'].max(),
                        "max_score_right": df['score_right'].max(),
                        "avg_ball_speed": df['ball_vel_x'].abs().mean()
                    })
            except:
                pass
        matches.sort(key=lambda x: x["file"], reverse=True)
        return matches

    def load_human_stats(self):
        stats = {'total_frames': 0, 'actions': {}}
        # Placeholder logic as original file had issues or was complex
        # Just scanning human_data dir if exists
        human_dir = os.path.join("human_data")
        if os.path.exists(human_dir):
            files = glob.glob(os.path.join(human_dir, "*.csv"))
            for f in files:
                try:
                    df = pd.read_csv(f)
                    stats['total_frames'] += len(df)
                    # Count actions if column exists
                    if 'action' in df.columns:
                        counts = df['action'].value_counts().to_dict()
                        for k, v in counts.items():
                            stats['actions'][k] = stats['actions'].get(k, 0) + v
                except: pass
        return stats

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Tab Click
            if my < 50:
                tab_width = config.SCREEN_WIDTH // len(self.tabs)
                idx = mx // tab_width
                if 0 <= idx < len(self.tabs):
                    self.active_tab = self.tabs[idx]
                    self.scroll_y = 0
                    
            # Back Button
            back_rect = pygame.Rect(config.SCREEN_WIDTH - 120, config.SCREEN_HEIGHT - 50, 100, 40)
            if back_rect.collidepoint((mx, my)):
                self.manager.change_state("menu")
                return
                
            # Scroll
            if event.button == 4: # Up
                self.scroll_y = max(0, self.scroll_y - 20)
            elif event.button == 5: # Down
                self.scroll_y += 20

    def draw_tabs(self, screen):
        tab_width = config.SCREEN_WIDTH // len(self.tabs)
        for i, tab in enumerate(self.tabs):
            rect = pygame.Rect(i * tab_width, 0, tab_width, 50)
            color = self.TAB_ACTIVE_COLOR if tab == self.active_tab else self.TAB_COLOR
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, config.WHITE, rect, 1)
            
            text = self.font.render(tab, True, self.TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

    def draw_overview(self, screen):
        y = 80
        
        title = self.font.render("System Overview", True, self.HIGHLIGHT_COLOR)
        screen.blit(title, (50, y))
        y += 50
        
        stats = [
            f"Total Models: {len(self.models)}",
            f"Total Matches Recorded: {len(self.matches)}",
            f"Human Training Data: {self.human_stats['total_frames']} frames",
            f"Top Fitness: {self.models[0]['fitness'] if self.models else 0}"
        ]
        
        for stat in stats:
            surf = self.small_font.render(stat, True, self.TEXT_COLOR)
            screen.blit(surf, (50, y))
            y += 30
            
        y += 30
        h_title = self.font.render("Human Play Style", True, self.HIGHLIGHT_COLOR)
        screen.blit(h_title, (50, y))
        y += 40
        
        for action, count in self.human_stats['actions'].items():
            surf = self.small_font.render(f"{action}: {count}", True, self.TEXT_COLOR)
            screen.blit(surf, (50, y))
            y += 30

    def draw_models(self, screen):
        y = 80 - self.scroll_y
        
        header = self.small_font.render(f"{'Name':<40} {'Tier':<15} {'Fitness':<10}", True, self.HIGHLIGHT_COLOR)
        screen.blit(header, (50, y))
        y += 30
        
        for model in self.models:
            if y > 50 and y < config.SCREEN_HEIGHT - 50:
                text = f"{model['name'][:35]:<40} {model['tier']:<15} {model['fitness']:<10}"
                surf = self.small_font.render(text, True, self.TEXT_COLOR)
                screen.blit(surf, (50, y))
            y += 30

    def draw_matches(self, screen):
        y = 80 - self.scroll_y
        
        header = self.small_font.render(f"{'File':<30} {'Frames':<10} {'Score (L-R)':<15} {'Avg Speed':<10}", True, self.HIGHLIGHT_COLOR)
        screen.blit(header, (50, y))
        y += 30
        
        for match in self.matches:
            if y > 50 and y < config.SCREEN_HEIGHT - 50:
                score = f"{match['max_score_left']}-{match['max_score_right']}"
                text = f"{match['file'][:25]:<30} {match['frames']:<10} {score:<15} {match['avg_ball_speed']:.2f}"
                surf = self.small_font.render(text, True, self.TEXT_COLOR)
                screen.blit(surf, (50, y))
            y += 30

    def draw(self, screen):
        screen.fill(self.BG_COLOR)
        self.draw_tabs(screen)
        
        if self.active_tab == "Overview":
            self.draw_overview(screen)
        elif self.active_tab == "Models":
            self.draw_models(screen)
        elif self.active_tab == "Matches":
            self.draw_matches(screen)
            
        # Back Button
        rect = pygame.Rect(config.SCREEN_WIDTH - 120, config.SCREEN_HEIGHT - 50, 100, 40)
        pygame.draw.rect(screen, (150, 50, 50), rect)
        pygame.draw.rect(screen, config.WHITE, rect, 2)
        text = self.small_font.render("Back", True, config.WHITE)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
