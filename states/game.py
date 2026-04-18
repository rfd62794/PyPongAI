import pygame
import neat
import pickle
import os
from core import config
from states.base import BaseState
from match.parallel_engine import ParallelGameEngine
from core.recorder import GameRecorder
from human_rival import HumanRival
import json
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GameState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.game = None
        self.net = None
        self.recorder = None
        self.rival_sys = HumanRival()
        self.game_over = False
        self.model_path = None

    def enter(self, model_path=None, **kwargs):
        self.model_path = model_path
        
        # Use single-process engine in automation mode to avoid pipe inheritance deadlocks
        automation_mode = os.getenv("PYPONGAI_AUTOMATION", "false").lower() == "true"
        if automation_mode:
            from core.engine import Game
            self.game = Game()
            logger.info("Using stable single-process engine for automation.")
        else:
            self.game = ParallelGameEngine(visual_mode=True, target_fps=config.FPS)
            self.game.start()
            
        self.recorder = GameRecorder()
        self.game_over = False
        self.match_start_time = pygame.time.get_ticks()
        
        # Load Model
        if self.model_path:
            with open(self.model_path, "rb") as f:
                genome = pickle.load(f)
            
            local_dir = os.path.dirname(os.path.dirname(__file__)) # Go up one level from states/
            config_path = os.path.join(local_dir, "neat_config.txt")
            neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                      neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                      config_path)
            self.net = neat.nn.FeedForwardNetwork.create(genome, neat_config)
        else:
            print("Error: No model path provided to GameState")
            self.manager.change_state("menu")

    def handle_input(self, event):
        """Override to support both game-over logic and universal keyboard commands."""
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Rematch
                    self.enter(model_path=self.model_path)
                elif event.key == pygame.K_m:
                    self.manager.change_state("menu")
                elif event.key == pygame.K_q:
                    self.manager.stop()
        else:
            # Route to BaseState for universal navigation keys (P, ESC, etc.)
            super().handle_input(event)

    def exit(self):
        """Clean up game engine on state exit."""
        if self.game and hasattr(self.game, "stop"):
            self.game.stop()

    def on_start_action(self):
        """Handle 'S' key as a rematch command if game is over."""
        if self.game_over:
            self.enter(model_path=self.model_path)

    def update(self, dt):
        if self.game_over:
            return

        # Human Input
        keys = pygame.key.get_pressed()
        right_move = None
        if keys[pygame.K_UP]:
            right_move = "UP"
        if keys[pygame.K_DOWN]:
            right_move = "DOWN"

        # AI Input
        if self.net:
            # Get state from parallel engine
            state = self.game.get_state()
            
            inputs = (
                state["paddle_left_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] < 0 else 0.0,
                state["paddle_right_y"] / config.SCREEN_HEIGHT
            )
            output = self.net.activate(inputs)
            decision = output.index(max(output))
            
            if decision == 0:
                left_move = "UP"
            elif decision == 1:
                left_move = "DOWN"
            else:
                left_move = None

        # Update Game (Logic for both single-proc and parallel-proc engines)
        if hasattr(self.game, "update"):
            score_data = self.game.update(left_move, right_move)
        
        # Check Game Over
        score_left = self.game.score_left
        score_right = self.game.score_right
        
        if (score_left >= config.VISUAL_MAX_SCORE or
                score_right >= config.VISUAL_MAX_SCORE):
            self.game_over = True
            self.handle_game_over()

    def handle_game_over(self):
        final_score_human = self.game.score_right
        final_score_ai = self.game.score_left
        won = final_score_human > final_score_ai
        
        if self.rival_sys.update_score(final_score_human):
            print(f"New Personal Best! {final_score_human}")
            
        self.rival_sys.update_match_result(final_score_human, final_score_ai, won)
        self.recorder.save_recording()
        self.emit_match_complete_event()
        
        # Only call stop if it's the parallel engine
        if hasattr(self.game, "stop"):
            self.game.stop()

    def emit_match_complete_event(self):
        """Emit a JSON event to stdout for IPC with ContentEngine."""
        event = {
            "type": "match_complete",
            "data": {
                "winner": "ai" if self.game.score_left > self.game.score_right else "human",
                "ai_score": self.game.score_left,
                "human_score": self.game.score_right,
                "duration_seconds": (pygame.time.get_ticks() - self.match_start_time) // 1000,
            },
            "timestamp": datetime.now().isoformat(),
        }
        try:
            # Using a prefix to make filtering easier for the parent process
            print(json.dumps({"event": event}), flush=True)
            sys.stdout.flush()
        except Exception:
            pass

    def draw(self, screen):
        # Draw game elements using state from ParallelGameEngine
        state = self.game.get_state()
        
        # Clear screen
        screen.fill(config.BLACK)
        
        # Draw Net
        pygame.draw.line(screen, config.WHITE, (config.SCREEN_WIDTH // 2, 0), (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT), 2)
        
        # Draw Scores
        if pygame.font.get_init():
            font = pygame.font.Font(None, 74)
            text_left = font.render(str(state["score_left"]), 1, config.WHITE)
            screen.blit(text_left, (config.SCREEN_WIDTH // 4, 10))
            text_right = font.render(str(state["score_right"]), 1, config.WHITE)
            screen.blit(text_right, (config.SCREEN_WIDTH * 3 // 4, 10))
        
        # Draw Left Paddle
        pygame.draw.rect(screen, config.WHITE, (10, int(state["paddle_left_y"]), config.PADDLE_WIDTH, config.PADDLE_HEIGHT))
        
        # Draw Right Paddle
        pygame.draw.rect(screen, config.WHITE, (config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH, int(state["paddle_right_y"]), config.PADDLE_WIDTH, config.PADDLE_HEIGHT))
        
        # Draw Ball (state stores top-left corner, but circle needs center)
        ball_center_x = int(state["ball_x"]) + config.BALL_RADIUS
        ball_center_y = int(state["ball_y"]) + config.BALL_RADIUS
        pygame.draw.circle(screen, config.WHITE, (ball_center_x, ball_center_y), config.BALL_RADIUS)
        
        if self.game_over:
            # Overlay
            s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill((0,0,0))
            screen.blit(s, (0,0))
            
            res_text = "YOU WON!" if self.game.score_right > self.game.score_left else "YOU LOST!"
            color = (50, 255, 50) if self.game.score_right > self.game.score_left else (255, 50, 50)
            
            title_surf = self.font.render(res_text, True, color)
            screen.blit(title_surf, (config.SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))
            
            score_surf = self.font.render(f"{self.game.score_left} - {self.game.score_right}", True, config.WHITE)
            screen.blit(score_surf, (config.SCREEN_WIDTH//2 - score_surf.get_width()//2, 220))
            
            info_surf = self.small_font.render("Press R to Rematch, M for Menu, Q to Quit", True, config.GRAY)
            screen.blit(info_surf, (config.SCREEN_WIDTH//2 - info_surf.get_width()//2, 400))
