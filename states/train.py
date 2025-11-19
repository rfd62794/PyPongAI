import pygame
import neat
import os
import pickle
import datetime
import config
import ai_module
import game_engine
import sys
from states.base import BaseState

class VisualReporter(neat.reporting.BaseReporter):
    def __init__(self, config_neat, screen):
        self.config_neat = config_neat
        self.screen = screen
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
        for g in population.values():
            if g.fitness is not None and g.fitness > best_fitness:
                best_fitness = g.fitness
                best_genome = g
        
        if best_genome:
            print(f"Generation {self.generation} Best Fitness: {best_fitness}")
            self.save_checkpoint(best_genome)
            self.visualize_best(best_genome)

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
                state["paddle_left_y"],
                state["ball_x"],
                state["ball_y"],
                state["ball_vel_x"],
                state["ball_vel_y"],
                state["paddle_left_y"] - state["ball_y"],
                1.0 if state["ball_vel_x"] < 0 else 0.0
            )
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = "UP" if action_idx == 0 else "DOWN" if action_idx == 1 else None
            
            # Rule-Based AI (Right)
            right_move = ai_module.get_rule_based_move(state, "right")
            
            # Update
            game.update(left_move, right_move)
            
            # Draw
            game.draw(self.screen)
            
            # Overlay Info
            info_text = self.font.render(f"Gen {self.generation} Best - Press SPACE to Resume", True, config.WHITE)
            self.screen.blit(info_text, (10, config.SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            
            # Check end condition (quick match to 3)
            if game.score_left >= 3 or game.score_right >= 3:
                running = False

class TrainState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 30)
        self.models = []
        self.page = 0
        self.per_page = 5
        self.mode = "SELECTION" # SELECTION or TRAINING

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

    def start_training(self, seed_genome=None):
        self.mode = "TRAINING"
        # Render initial loading screen
        self.manager.screen.fill(config.BLACK)
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
            
        p.add_reporter(neat.StdOutReporter(True))
        p.add_reporter(neat.StatisticsReporter())
        p.add_reporter(VisualReporter(config_neat, self.manager.screen))
        
        winner = p.run(ai_module.eval_genomes, 50)
        
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
                if event.key == pygame.K_n:
                    self.start_training(None) # New Run
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
            
            sub = self.small_font.render("(Press N for New Run / No Seed)", True, config.GRAY)
            screen.blit(sub, (config.SCREEN_WIDTH//2 - sub.get_width()//2, 70))
            
            mx, my = pygame.mouse.get_pos()
            
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
                screen.blit(nav_surf, (config.SCREEN_WIDTH//2 - nav_surf.get_width()//2, config.SCREEN_HEIGHT - 50))

            # Back Button
            back_rect = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
            pygame.draw.rect(screen, (150, 50, 50), back_rect)
            pygame.draw.rect(screen, config.WHITE, back_rect, 2)
            back_text = self.font.render("Back", True, config.WHITE)
            back_text_rect = back_text.get_rect(center=back_rect.center)
            screen.blit(back_text, back_text_rect)
