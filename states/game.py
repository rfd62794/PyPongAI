import pygame
import neat
import pickle
import os
import config
from states.base import BaseState
from match.parallel_engine import ParallelGameEngine
from game_recorder import GameRecorder
from human_rival import HumanRival

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
        self.game = ParallelGameEngine(visual_mode=True, target_fps=config.FPS)
        self.game.start()
        self.recorder = GameRecorder()
        self.game_over = False
        
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
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Rematch
                    # Reload rival if needed (logic from play.py)
                    # For now, just restart with same model
                    self.enter(model_path=self.model_path)
                elif event.key == pygame.K_m:
                    self.game.stop()
                    self.manager.change_state("menu")
                elif event.key == pygame.K_q:
                    self.game.stop()
                    self.manager.running = False
        else:
            # In-game input is handled in update via key polling, 
            # but we can handle specific events here if needed
            pass

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

        # Update Game
        score_data = self.game.update(left_move, right_move)
        
        # Check Game Over
        if self.game.score_left >= config.MAX_SCORE or self.game.score_right >= config.MAX_SCORE:
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
        self.game.stop()

    def draw(self, screen):
        self.game.draw(screen)
        
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
