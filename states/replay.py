import pygame
import os
import json
import config
from states.base import BaseState

class ReplayState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        self.match_data = None
        self.frames = []
        self.current_frame_idx = 0
        self.playing = True
        self.playback_speed = 1.0
        
        # UI
        self.btn_back = pygame.Rect(config.SCREEN_WIDTH - 120, 10, 100, 40)
        self.btn_play = pygame.Rect(config.SCREEN_WIDTH // 2 - 50, config.SCREEN_HEIGHT - 60, 100, 40)
        
    def enter(self, **kwargs):
        match_file = kwargs.get("match_file")
        if match_file and os.path.exists(match_file):
            self.load_match(match_file)
        else:
            print(f"Error: Match file not found: {match_file}")
            self.manager.change_state("analytics")

    def load_match(self, filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                
            self.match_data = data
            self.frames = data.get("frames", [])
            self.current_frame_idx = 0
            self.playing = True
            print(f"Loaded match: {len(self.frames)} frames")
            
        except Exception as e:
            print(f"Failed to load match replay: {e}")
            self.manager.change_state("analytics")

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.btn_back.collidepoint((mx, my)):
                self.manager.change_state("analytics")
                return
                
            if self.btn_play.collidepoint((mx, my)):
                self.playing = not self.playing
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.playing = not self.playing
            elif event.key == pygame.K_LEFT:
                self.current_frame_idx = max(0, self.current_frame_idx - 60) # Back 1s
            elif event.key == pygame.K_RIGHT:
                self.current_frame_idx = min(len(self.frames) - 1, self.current_frame_idx + 60) # Fwd 1s
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_state("analytics")

    def update(self, dt):
        if self.playing and self.frames:
            self.current_frame_idx += 1
            if self.current_frame_idx >= len(self.frames):
                self.current_frame_idx = len(self.frames) - 1
                self.playing = False

    def draw(self, screen):
        screen.fill(config.BLACK)
        
        if not self.frames:
            text = self.font.render("No Replay Data", True, config.WHITE)
            screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
            return

        # Get current frame state
        state = self.frames[self.current_frame_idx]
        
        # Draw Game State
        # Paddles
        pygame.draw.rect(screen, config.WHITE, (10, state["paddle_left_y"], config.PADDLE_WIDTH, config.PADDLE_HEIGHT))
        pygame.draw.rect(screen, config.WHITE, (config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH, state["paddle_right_y"], config.PADDLE_WIDTH, config.PADDLE_HEIGHT))
        
        # Ball
        pygame.draw.circle(screen, config.WHITE, (int(state["ball_x"]), int(state["ball_y"])), config.BALL_RADIUS)
        
        # UI Overlay
        # Header
        p1 = self.match_data.get("p1", "Player 1")
        p2 = self.match_data.get("p2", "Player 2")
        header = self.small_font.render(f"{p1} vs {p2}", True, config.GRAY)
        screen.blit(header, (config.SCREEN_WIDTH//2 - header.get_width()//2, 20))
        
        # Progress Bar
        progress = self.current_frame_idx / len(self.frames)
        bar_width = config.SCREEN_WIDTH - 100
        pygame.draw.rect(screen, (50, 50, 50), (50, config.SCREEN_HEIGHT - 100, bar_width, 10))
        pygame.draw.rect(screen, config.GREEN, (50, config.SCREEN_HEIGHT - 100, bar_width * progress, 10))
        
        # Controls
        # Play/Pause
        pygame.draw.rect(screen, (0, 100, 0) if self.playing else (100, 100, 0), self.btn_play)
        play_text = self.small_font.render("PAUSE" if self.playing else "PLAY", True, config.WHITE)
        screen.blit(play_text, (self.btn_play.centerx - play_text.get_width()//2, self.btn_play.centery - play_text.get_height()//2))
        
        # Back
        pygame.draw.rect(screen, (100, 0, 0), self.btn_back)
        back_text = self.small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (self.btn_back.centerx - back_text.get_width()//2, self.btn_back.centery - back_text.get_height()//2))
        
        # Instructions
        hint = self.tiny_font.render("SPACE: Play/Pause | LEFT/RIGHT: Seek", True, config.GRAY)
        screen.blit(hint, (config.SCREEN_WIDTH//2 - hint.get_width()//2, config.SCREEN_HEIGHT - 30))
