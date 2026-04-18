import pygame
import os
import json
from states.base import BaseState
from core import config

class CompareState(BaseState):
    """
    Side-by-side comparison of two match recordings.
    Used for research presentation: Gen 0 (random) vs Gen 50 (trained).
    """
    
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 30)
        self.label_font = pygame.font.Font(None, 24)
        
        self.mode = "SELECTION"  # SELECTION or PLAYBACK
        
        # Recordings for selection
        self.recordings = []
        self.selected_left = None
        self.selected_right = None
        
        # Playback state
        self.left_data = None
        self.right_data = None
        self.current_frame = 0
        self.is_playing = False
        self.max_frames = 0
        
        # UI Rects
        self.play_button = pygame.Rect(config.SCREEN_WIDTH // 2 - 100, config.SCREEN_HEIGHT - 70, 200, 45)
        self.back_button = pygame.Rect(config.SCREEN_WIDTH - 110, 20, 100, 35)
        self.progress_bar = pygame.Rect(50, config.SCREEN_HEIGHT - 110, config.SCREEN_WIDTH - 100, 15)
        
        # Selection UI metrics
        self.scroll_y = 0
        self.item_height = 40
        self.list_rect = pygame.Rect(50, 100, 700, 400)
    
    def enter(self, **kwargs):
        self.mode = "SELECTION"
        self.selected_left = None
        self.selected_right = None
        self.scan_recordings()
    
    def scan_recordings(self):
        """Find all available match recordings in the matches directory."""
        self.recordings = []
        path = config.MATCH_RECORDINGS_DIR
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith(".json")]
            # Sort by modification time (most recent first)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
            self.recordings = files

    def load_comparison(self):
        """Load the two selected recordings."""
        if not self.selected_left or not self.selected_right:
            return
            
        try:
            with open(os.path.join(config.MATCH_RECORDINGS_DIR, self.selected_left), 'r') as f:
                self.left_data = json.load(f)
            with open(os.path.join(config.MATCH_RECORDINGS_DIR, self.selected_right), 'r') as f:
                self.right_data = json.load(f)
                
            self.max_frames = max(len(self.left_data["frames"]), len(self.right_data["frames"]))
            self.current_frame = 0
            self.is_playing = True
            self.mode = "PLAYBACK"
        except Exception as e:
            print(f"Error loading recordings: {e}")

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.back_button.collidepoint(mx, my):
                if self.mode == "PLAYBACK":
                    self.mode = "SELECTION"
                    self.is_playing = False
                else:
                    self.manager.change_state("menu")
                    
            if self.mode == "SELECTION":
                if self.list_rect.collidepoint(mx, my):
                    # Find which item was clicked
                    relative_y = my - self.list_rect.y
                    idx = int((relative_y) // self.item_height)
                    if idx < len(self.recordings):
                        file = self.recordings[idx]
                        if event.button == 1: # Left click for left side
                            self.selected_left = file
                        elif event.button == 3: # Right click for right side
                            self.selected_right = file
                
                # Compare button logic
                compare_btn = pygame.Rect(config.SCREEN_WIDTH // 2 - 100, 520, 200, 50)
                if compare_btn.collidepoint(mx, my) and self.selected_left and self.selected_right:
                    self.load_comparison()
                    
            elif self.mode == "PLAYBACK":
                if self.play_button.collidepoint(mx, my):
                    self.is_playing = not self.is_playing
                elif self.progress_bar.collidepoint(mx, my):
                    # Seek
                    rel_x = mx - self.progress_bar.x
                    progress = rel_x / self.progress_bar.width
                    self.current_frame = int(progress * self.max_frames)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.mode == "PLAYBACK":
                self.is_playing = not self.is_playing
            elif event.key == pygame.K_ESCAPE:
                if self.mode == "PLAYBACK":
                    self.mode = "SELECTION"
                    self.is_playing = False
                else:
                    self.manager.change_state("menu")
            else:
                # Route other keys (P, S, etc.) to BaseState
                super().handle_input(event)

    def update(self, dt):
        if self.mode == "PLAYBACK" and self.is_playing:
            self.current_frame += 1
            if self.current_frame >= self.max_frames:
                self.current_frame = self.max_frames - 1
                self.is_playing = False

    def _draw_frame_data(self, screen, data, frame_idx, x_offset, width, height):
        """Draws one side of the pong simulation from recorded data."""
        if not data: return
        
        # Get frame, capping at max
        f_idx = min(frame_idx, len(data["frames"]) - 1)
        frame = data["frames"][f_idx]
        
        # Scaling factors (if original resolution differs, but we assume it matches config)
        # Note: MatchRecorder uses 'bx', 'by', 'ply', 'pry', 'sl', 'sr'
        
        # Draw background area for this side
        pygame.draw.rect(screen, (20, 20, 30), (x_offset, 60, width, height))
        
        # Draw Ball
        ball_pos = (x_offset + int(frame["bx"]), 60 + int(frame["by"]))
        pygame.draw.circle(screen, config.COLOR_ACCENT, ball_pos, config.BALL_RADIUS)
        
        # Draw Paddles
        p_width = config.PADDLE_WIDTH
        p_height = config.PADDLE_HEIGHT
        
        # Left Paddle
        pygame.draw.rect(screen, config.COLOR_TEXT_PRIMARY, 
                        (x_offset + 10, 60 + int(frame["ply"]), p_width, p_height), border_radius=4)
        # Right Paddle
        pygame.draw.rect(screen, config.COLOR_TEXT_PRIMARY, 
                        (x_offset + width - 10 - p_width, 60 + int(frame["pry"]), p_width, p_height), border_radius=4)
        
        # Draw Scores
        score_txt = self.font.render(f"{frame['sl']} : {frame['sr']}", True, config.COLOR_TEXT_PRIMARY)
        screen.blit(score_txt, (x_offset + width // 2 - score_txt.get_width() // 2, 80))
        
        # Player names or description
        desc = f"{data.get('p1', 'AI')} vs {data.get('p2', 'AI')}"
        desc_txt = self.label_font.render(desc, True, config.COLOR_TEXT_SECONDARY)
        screen.blit(desc_txt, (x_offset + 10, 70))

    def draw(self, screen):
        screen.fill(config.COLOR_BACKGROUND)
        
        # Header
        title_str = "Comparison View" if self.mode == "PLAYBACK" else "Select Recordings"
        title = self.font.render(title_str, True, config.COLOR_ACCENT)
        screen.blit(title, (config.SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Back Button
        btn_color = config.COLOR_BUTTON_HOVER if self.back_button.collidepoint(pygame.mouse.get_pos()) else config.COLOR_BUTTON_DEFAULT
        pygame.draw.rect(screen, btn_color, self.back_button, border_radius=8)
        back_txt = self.small_font.render("Back", True, config.COLOR_TEXT_PRIMARY)
        screen.blit(back_txt, (self.back_button.centerx - back_txt.get_width() // 2, self.back_button.centery - back_txt.get_height() // 2))

        if self.mode == "SELECTION":
            self._draw_selection(screen)
        else:
            self._draw_playback(screen)

    def _draw_selection(self, screen):
        # Draw instructions
        instr = self.small_font.render("L-Click: Select Left | R-Click: Select Right", True, config.COLOR_TEXT_SECONDARY)
        screen.blit(instr, (config.SCREEN_WIDTH // 2 - instr.get_width() // 2, 65))
        
        # Selection area
        pygame.draw.rect(screen, (30, 30, 45), self.list_rect, border_radius=10)
        pygame.draw.rect(screen, config.COLOR_ACCENT, self.list_rect, width=2, border_radius=10)
        
        # List items
        for i, rec in enumerate(self.recordings):
            item_rect = pygame.Rect(self.list_rect.x, self.list_rect.y + i * self.item_height, self.list_rect.width, self.item_height)
            if item_rect.bottom > self.list_rect.bottom: break
            
            # Highlight selected
            if rec == self.selected_left:
                pygame.draw.rect(screen, (50, 80, 50), item_rect)
            elif rec == self.selected_right:
                pygame.draw.rect(screen, (80, 50, 50), item_rect)
            
            # Hover highlight
            if item_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, (60, 60, 80), item_rect, width=1)
                
            txt = self.label_font.render(rec, True, config.COLOR_TEXT_PRIMARY)
            screen.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() // 2))
            
        # Selection feedback
        left_lbl = self.small_font.render(f"Left: {self.selected_left or 'None'}", True, config.COLOR_SUCCESS)
        right_lbl = self.small_font.render(f"Right: {self.selected_right or 'None'}", True, config.COLOR_FAILURE)
        screen.blit(left_lbl, (50, 520))
        screen.blit(right_lbl, (50, 550))
        
        # Compare Button
        compare_btn = pygame.Rect(config.SCREEN_WIDTH // 2 + 100, 520, 200, 50)
        btn_col = config.COLOR_ACCENT if (self.selected_left and self.selected_right) else config.COLOR_BUTTON_DEFAULT
        pygame.draw.rect(screen, btn_col, compare_btn, border_radius=10)
        comp_txt = self.small_font.render("Start Comparison", True, config.BLACK if btn_col == config.COLOR_ACCENT else config.COLOR_TEXT_SECONDARY)
        screen.blit(comp_txt, (compare_btn.centerx - comp_txt.get_width() // 2, compare_btn.centery - comp_txt.get_height() // 2))

    def _draw_playback(self, screen):
        side_width = config.SCREEN_WIDTH // 2 - 15
        sim_height = config.SCREEN_HEIGHT - 200
        
        # Left Side
        self._draw_frame_data(screen, self.left_data, self.current_frame, 10, side_width, sim_height)
        
        # Right Side
        self._draw_frame_data(screen, self.right_data, self.current_frame, config.SCREEN_WIDTH // 2 + 5, side_width, sim_height)
        
        # Progress Bar
        pygame.draw.rect(screen, config.COLOR_BUTTON_DEFAULT, self.progress_bar, border_radius=5)
        progress = self.current_frame / max(self.max_frames, 1)
        progress_rect = pygame.Rect(self.progress_bar.x, self.progress_bar.y, int(self.progress_bar.width * progress), self.progress_bar.height)
        pygame.draw.rect(screen, config.COLOR_ACCENT, progress_rect, border_radius=5)
        
        # Frame Text
        f_txt = self.label_font.render(f"Frame: {self.current_frame} / {self.max_frames}", True, config.COLOR_TEXT_SECONDARY)
        screen.blit(f_txt, (self.progress_bar.centerx - f_txt.get_width() // 2, self.progress_bar.y + 20))
        
        # Play Button
        is_hover_play = self.play_button.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, config.COLOR_BUTTON_HOVER if is_hover_play else config.COLOR_BUTTON_DEFAULT, self.play_button, border_radius=10)
        play_label = "⏸ PAUSE" if self.is_playing else "▶ PLAY"
        ptxt = self.small_font.render(play_label, True, config.COLOR_TEXT_PRIMARY)
        screen.blit(ptxt, (self.play_button.centerx - ptxt.get_width() // 2, self.play_button.centery - ptxt.get_height() // 2))
