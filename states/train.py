import pygame
import neat
import os
import pickle
import datetime
import config
import ai_module
import game_engine
import sys
import itertools
from states.base import BaseState
from model_manager import get_best_model, get_fitness_from_filename
from opponents import get_rule_based_move
import training_logger

class UIProgressReporter(neat.reporting.BaseReporter):
    def __init__(self, screen, logger=None):
        self.screen = screen
        self.logger = logger
        self.generation = 0
        self.font = pygame.font.Font(None, 36)
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def start_generation(self, generation):
        self.generation = generation
        print(f"--- Starting Generation {generation} ---")
        
        self.screen.fill(config.BLACK)
        text = self.font.render(f"Training Generation {generation} (Fast Mode)...", True, config.WHITE)
        self.screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
        
        sub = self.font.render("Check console for details.", True, config.GRAY)
        self.screen.blit(sub, (config.SCREEN_WIDTH//2 - sub.get_width()//2, config.SCREEN_HEIGHT//2 + 40))
        
        pygame.display.flip()
        pygame.event.pump()

    def end_generation(self, config, population, species_set):
        # Find best genome to save checkpoint
        best_genome = None
        best_fitness = -float('inf')
        total_fitness = 0
        count = 0
        best_elo = 0
        
        for g in population.values():
            if g.fitness is not None:
                total_fitness += g.fitness
                count += 1
                if g.fitness > best_fitness:
                    best_fitness = g.fitness
                    best_genome = g
                    if hasattr(g, 'elo_rating'):
                        best_elo = g.elo_rating
        
        avg_fitness = total_fitness / count if count > 0 else 0
        
        if best_genome:
            print(f"Generation {self.generation} Best Fitness: {best_fitness}")
            self.save_checkpoint(best_genome)
            
        if self.logger:
            self.logger.log_generation(self.generation, best_fitness, avg_fitness, best_elo, len(species_set.species))
            
        pygame.event.pump()

    def save_checkpoint(self, genome):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{self.generation}_fit_{int(genome.fitness)}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        with open(filepath, "wb") as f:
            pickle.dump(genome, f)

class VisualReporter(neat.reporting.BaseReporter):
    def __init__(self, config_neat, screen, logger=None):
        self.config_neat = config_neat
        self.screen = screen
        self.logger = logger
        self.generation = 0
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.font = pygame.font.Font(None, 36)

    def start_generation(self, generation):
        self.generation = generation
        print(f"--- Starting Generation {generation} ---")
        
        # Draw "Training..." status
        self.screen.fill(config.BLACK)
        text = self.font.render(f"Training Generation {generation}...", True, config.WHITE)
        self.screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
        pygame.display.flip()
        
        # Process events to prevent freezing
        pygame.event.pump()

    def end_generation(self, config, population, species_set):
        # Find best genome
        best_genome = None
        best_fitness = -float('inf')
        total_fitness = 0
        count = 0
        best_elo = 0
        
        for g in population.values():
            if g.fitness is not None:
                total_fitness += g.fitness
                count += 1
                if g.fitness > best_fitness:
                    best_fitness = g.fitness
                    best_genome = g
                    if hasattr(g, 'elo_rating'):
                        best_elo = g.elo_rating
        
        avg_fitness = total_fitness / count if count > 0 else 0
        
        if best_genome:
            print(f"Generation {self.generation} Best Fitness: {best_fitness}")
            self.save_checkpoint(best_genome)
            self.visualize_best(best_genome)
            
        if self.logger:
            self.logger.log_generation(self.generation, best_fitness, avg_fitness, best_elo, len(species_set.species))

    def save_checkpoint(self, genome):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{self.generation}_fit_{int(genome.fitness)}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        with open(filepath, "wb") as f:
            pickle.dump(genome, f)
        print(f"Saved checkpoint: {filename}")

    def visualize_best(self, genome):
        print("Visualizing best genome... (Press SPACE to skip)")
        
        clock = pygame.time.Clock()
        game = game_engine.Game()
        
        # Create Network
        net = neat.nn.FeedForwardNetwork.create(genome, self.config_neat)
        
        running = True
        while running:
            clock.tick(config.FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        running = False
            
            # AI (Left)
            state = game.get_state()
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
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = "UP" if action_idx == 0 else "DOWN" if action_idx == 1 else None
            
            # Rule-Based AI (Right)
            right_move = get_rule_based_move(state, "right")
            
            # Update
            game.update(left_move, right_move)
            
            # Draw
            game.draw(self.screen)
            
            # Overlay Info
            info_text = self.font.render(f"Gen {self.generation} Best - Press SPACE to Resume", True, config.WHITE)
            self.screen.blit(info_text, (10, config.SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            
            # Check end condition (quick match to VISUAL_MAX_SCORE)
            if game.score_left >= config.VISUAL_MAX_SCORE or game.score_right >= config.VISUAL_MAX_SCORE:
                running = False

class TrainState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        self.models = []
        self.page = 0
        self.per_page = 5
        self.mode = "SELECTION" # SELECTION or TRAINING
        self.visual_mode = True # Default to visual
        self.use_best_seed = True # Default to using best model as seed

    def enter(self, **kwargs):
        self.mode = "SELECTION"
        self.scan_models()
        
    def scan_models(self):
        self.models = []
        for root, dirs, files in os.walk(config.MODEL_DIR):
            for file in files:
                if file.endswith(".pkl"):
                    full_path = os.path.join(root, file)
                    self.models.append(full_path)
        
        def get_fitness(filepath):
            filename = os.path.basename(filepath)
            try:
                if "fitness" in filename:
                    return int(filename.split("fitness")[1].split(".")[0])
                elif "_fit_" in filename:
                    return int(filename.split("_fit_")[1].split(".")[0])
                return 0
            except:
                return 0
        self.models.sort(key=get_fitness, reverse=True)
    
    def get_best_model_path(self):
        """Get the best model path using the utility function"""
        return get_best_model()

    def start_training(self, seed_genome=None):
        self.mode = "TRAINING"
        # Render initial loading screen
        self.manager.screen.fill(config.BLACK)
        
        # Initialize Logger
        logger = training_logger.TrainingLogger()
        
        # If no seed provided and use_best_seed is True, load best model
        if seed_genome is None and self.use_best_seed:
            best_path = self.get_best_model_path()
            if best_path:
                try:
                    with open(best_path, "rb") as f:
                        seed_genome = pickle.load(f)
                    print(f"Auto-loaded best model as seed: {os.path.basename(best_path)}")
                    text = self.font.render(f"Loading Best Model: {os.path.basename(best_path)[:30]}...", True, config.WHITE)
                except Exception as e:
                    print(f"Failed to load best model: {e}")
                    text = self.font.render("Initializing Training...", True, config.WHITE)
            else:
                text = self.font.render("Initializing Training...", True, config.WHITE)
        else:
            text = self.font.render("Initializing Training...", True, config.WHITE)
        
        self.manager.screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
        pygame.display.flip()
        
        local_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(local_dir, 'neat_config.txt')
        
        config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  config_path)
                                  
        p = neat.Population(config_neat)
        
        if seed_genome:
            print("Seeding population...")
            target_id = list(p.population.keys())[0]
            seed_genome.key = target_id
            p.population[target_id] = seed_genome
            p.species.speciate(config_neat, p.population, p.generation)
            
            # Fix for node ID collision
            max_node_id = max(seed_genome.nodes.keys()) if seed_genome.nodes else 0
            print(f"Updating node indexer to start from {max_node_id + 1}")
            config_neat.genome_config.node_indexer = itertools.count(max_node_id + 1)
            
        p.add_reporter(neat.StdOutReporter(True))
        p.add_reporter(neat.StatisticsReporter())
        
        if self.visual_mode:
            p.add_reporter(VisualReporter(config_neat, self.manager.screen, logger=logger))
        else:
            p.add_reporter(UIProgressReporter(self.manager.screen, logger=logger))
        
        winner = p.run(ai_module.eval_genomes_competitive, 50)
        
        with open(os.path.join(config.MODEL_DIR, "visual_winner.pkl"), "wb") as f:
            pickle.dump(winner, f)
            
        # Return to menu or stay? Let's return to menu
        self.manager.change_state("menu")

    def handle_input(self, event):
        if self.mode == "SELECTION":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # Back Button
                back_rect = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
                if back_rect.collidepoint((mx, my)):
                    self.manager.change_state("menu")
                    return

                # Visual Toggle
                toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 60, 240, 40)
                if toggle_rect.collidepoint((mx, my)):
                    self.visual_mode = not self.visual_mode
                    return
                
                # Auto-seed Toggle
                seed_toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 110, 240, 40)
                if seed_toggle_rect.collidepoint((mx, my)):
                    self.use_best_seed = not self.use_best_seed
                    return
                    
                # START Button
                start_btn_rect = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 500, 300, 60)
                if start_btn_rect.collidepoint((mx, my)):
                    self.start_training(None) # Auto-seed logic handles it
                    return

                # Model Selection
                start_idx = self.page * self.per_page
                end_idx = min(start_idx + self.per_page, len(self.models))
                
                for i in range(start_idx, end_idx):
                    y_pos = 150 + (i - start_idx) * 60
                    rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
                    if rect.collidepoint((mx, my)):
                        # Load Seed
                        with open(self.models[i], "rb") as f:
                            seed = pickle.load(f)
                        self.start_training(seed)
                        return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.start_training(None) # Auto-seed
                elif event.key == pygame.K_n:
                    # Force new run (disable auto-seed temporarily)
                    prev = self.use_best_seed
                    self.use_best_seed = False
                    self.start_training(None)
                    self.use_best_seed = prev
                elif event.key == pygame.K_RIGHT:
                    if (self.page + 1) * self.per_page < len(self.models):
                        self.page += 1
                elif event.key == pygame.K_LEFT:
                    if self.page > 0:
                        self.page -= 1

    def draw(self, screen):
        if self.mode == "SELECTION":
            screen.fill(config.BLACK)
            
            title = self.font.render("Select Seed Model for Training", True, config.WHITE)
            screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 30))
            
            sub = self.small_font.render("(Select a model below OR click START to Auto-Seed)", True, config.GRAY)
            screen.blit(sub, (config.SCREEN_WIDTH//2 - sub.get_width()//2, 70))
            
            mx, my = pygame.mouse.get_pos()
            
            # Visual Toggle
            toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 60, 240, 40)
            color = (50, 150, 50) if self.visual_mode else (150, 50, 50)
            pygame.draw.rect(screen, color, toggle_rect)
            pygame.draw.rect(screen, config.WHITE, toggle_rect, 2)
            
            toggle_text = f"Visual Mode: {'ON' if self.visual_mode else 'OFF'}"
            text_surf = self.small_font.render(toggle_text, True, config.WHITE)
            text_rect = text_surf.get_rect(center=toggle_rect.center)
            screen.blit(text_surf, text_rect)
            
            # Auto-seed Toggle
            seed_toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 110, 240, 40)
            seed_color = (50, 150, 50) if self.use_best_seed else (150, 50, 50)
            pygame.draw.rect(screen, seed_color, seed_toggle_rect)
            pygame.draw.rect(screen, config.WHITE, seed_toggle_rect, 2)
            
            seed_toggle_text = f"Auto-Seed: {'ON' if self.use_best_seed else 'OFF'}"
            seed_text_surf = self.small_font.render(seed_toggle_text, True, config.WHITE)
            seed_text_rect = seed_text_surf.get_rect(center=seed_toggle_rect.center)
            screen.blit(seed_text_surf, seed_text_rect)
            
            start_idx = self.page * self.per_page
            end_idx = min(start_idx + self.per_page, len(self.models))
            
            for i in range(start_idx, end_idx):
                model_path = self.models[i]
                filename = os.path.basename(model_path)
                parent = os.path.basename(os.path.dirname(model_path))
                
                # Get fitness (lazy way, should optimize if slow)
                fit = 0
                try:
                    if "fitness" in filename:
                        fit = int(filename.split("fitness")[1].split(".")[0])
                    elif "_fit_" in filename:
                        fit = int(filename.split("_fit_")[1].split(".")[0])
                except: pass
                
                display_text = f"{filename} (Fit: {fit}) [{parent}]"
                
                y_pos = 150 + (i - start_idx) * 60
                rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
                
                color = (100, 100, 100) if rect.collidepoint((mx, my)) else (50, 50, 50)
                pygame.draw.rect(screen, color, rect)
                
                text_surf = self.small_font.render(display_text, True, config.WHITE)
                screen.blit(text_surf, (rect.x + 10, rect.centery - text_surf.get_height()//2))
            
            # Navigation
            if len(self.models) > self.per_page:
                nav_text = f"Page {self.page + 1} / {(len(self.models) - 1) // self.per_page + 1} (Arrows to change)"
                nav_surf = self.small_font.render(nav_text, True, config.WHITE)
                screen.blit(nav_surf, (config.SCREEN_WIDTH//2 - nav_surf.get_width()//2, config.SCREEN_HEIGHT - 120))

            # START Button
            start_btn_rect = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 500, 300, 60)
            btn_color = (50, 200, 50) if start_btn_rect.collidepoint((mx, my)) else (30, 150, 30)
            pygame.draw.rect(screen, btn_color, start_btn_rect)
            pygame.draw.rect(screen, config.WHITE, start_btn_rect, 3)
            
            start_text = self.font.render("START TRAINING", True, config.WHITE)
            start_rect = start_text.get_rect(center=start_btn_rect.center)
            screen.blit(start_text, start_rect)
            
            sub_start = self.tiny_font.render("(Uses Best Model if Auto-Seed ON)", True, config.WHITE)
            sub_rect = sub_start.get_rect(center=(start_btn_rect.centerx, start_btn_rect.bottom + 15))
            screen.blit(sub_start, sub_rect)

            # Back Button
            back_rect = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
            pygame.draw.rect(screen, (150, 50, 50), back_rect)
            pygame.draw.rect(screen, config.WHITE, back_rect, 2)
            back_text = self.font.render("Back", True, config.WHITE)
            back_text_rect = back_text.get_rect(center=back_rect.center)
            screen.blit(back_text, back_text_rect)
