import pygame
import os
import config
from states.base import BaseState
from human_rival import HumanRival

class LobbyState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.rival_sys = HumanRival()
        
        # Buttons
        self.btn_challenge = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 150, 300, 50)
        self.btn_select = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 220, 300, 50)
        self.btn_rival = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 290, 300, 50)
        self.btn_back = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 360, 300, 50)

    def draw_button(self, screen, rect, text, hover=False, color_base=(50, 50, 50)):
        color = (min(color_base[0]+50, 255), min(color_base[1]+50, 255), min(color_base[2]+50, 255)) if hover else color_base
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, config.WHITE, rect, 2)
        
        text_surf = self.small_font.render(text, True, config.WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def get_best_model(self):
        models = []
        for root, dirs, files in os.walk(config.MODEL_DIR):
            for file in files:
                if file.endswith(".pkl"):
                    models.append(os.path.join(root, file))
        
        if not models:
            return None
            
        def get_fit(p):
            try:
                return int(p.split("fitness")[1].split(".")[0])
            except:
                return 0
        models.sort(key=get_fit, reverse=True)
        return models[0]

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                
                if self.btn_challenge.collidepoint((mx, my)):
                    best = self.get_best_model()
                    if best:
                        self.manager.change_state("game", model_path=best)
                    else:
                        print("No models found!")
                        
                elif self.btn_select.collidepoint((mx, my)):
                    # For now, just pick best. TODO: Add file selector state
                    best = self.get_best_model()
                    if best:
                        self.manager.change_state("game", model_path=best)
                        
                elif self.btn_rival.collidepoint((mx, my)):
                    rival = self.rival_sys.get_rival_model()
                    if rival:
                        self.manager.change_state("game", model_path=rival)
                    else:
                        print("No rival model found!")
                        
                elif self.btn_back.collidepoint((mx, my)):
                    self.manager.change_state("menu")

    def draw(self, screen):
        screen.fill(config.BLACK)
        
        title = self.font.render("Select Opponent", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mx, my = pygame.mouse.get_pos()
        
        self.draw_button(screen, self.btn_challenge, "Challenge Best AI", self.btn_challenge.collidepoint((mx, my)))
        self.draw_button(screen, self.btn_select, "Select Model File", self.btn_select.collidepoint((mx, my)))
        
        rival_path = self.rival_sys.get_rival_model()
        rival_text = "Challenge Rival"
        if rival_path:
            fit = self.rival_sys.stats.get('rival_fitness', '?')
            rival_text += f" (Fit: {fit})"
        
        self.draw_button(screen, self.btn_rival, rival_text, self.btn_rival.collidepoint((mx, my)), color_base=(80, 50, 20))
        self.draw_button(screen, self.btn_back, "Back", self.btn_back.collidepoint((mx, my)))
