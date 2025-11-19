# visual_train.py
import patch_neat
import pygame
import neat
import os
import pickle
import game_engine
import ai_module
import config
import datetime

class VisualReporter(neat.reporting.BaseReporter):
    def __init__(self, config_neat):
        self.config_neat = config_neat
        self.generation = 0
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def start_generation(self, generation):
        self.generation = generation
        print(f"--- Starting Generation {generation} ---")

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
        
        # Setup Game
        pygame.init()
        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(f"Generation {self.generation} - Best Genome Visualization")
        clock = pygame.time.Clock()
        game = game_engine.Game()
        
        # Create Network
        net = neat.nn.FeedForwardNetwork.create(genome, self.config_neat)
        
        running = True
        # Run for a short match (e.g., first to 3 points) or until skipped
        while running:
            clock.tick(config.FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False # Just stop visualization, not training
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
                state["ball_vel_y"]
            )
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = "UP" if action_idx == 0 else "DOWN" if action_idx == 1 else None
            
            # Rule-Based AI (Right) - Opponent
            # We need a dummy paddle object for the rule based AI function
            # But the function expects a paddle object with .rect.y
            # Let's just implement simple tracking here or use the module
            # The ai_module.get_rule_based_move expects (game_state, paddle)
            # We can reconstruct a lightweight paddle obj or just use the game's paddle
            right_move = ai_module.get_rule_based_move(state, "right")
            
            # Update
            score_data = game.update(left_move, right_move)
            
            # Draw
            game.draw(screen)
            
            # Overlay Info
            font = pygame.font.Font(None, 36)
            info_text = font.render("Press SPACE to Resume Training", True, config.WHITE)
            screen.blit(info_text, (10, config.SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            
            # Check end condition (quick match to 3)
            if game.score_left >= 3 or game.score_right >= 3:
                running = False
                
        pygame.display.quit() # Close window but keep pygame init? No, safer to quit display
        # pygame.quit() # Don't call full quit, might break things if re-init? 
        # Actually pygame.quit() is fine if we re-init next time.

def run_visual_training(seed_genome=None):
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
                              
    p = neat.Population(config_neat)
    
    if seed_genome:
        print("Seeding population with selected model...")
        # Seed the first genome
        target_id = list(p.population.keys())[0]
        seed_genome.key = target_id
        p.population[target_id] = seed_genome
        # Re-speciate to ensure species set references the new genome object
        p.species.speciate(config_neat, p.population, p.generation)
        
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    p.add_reporter(VisualReporter(config_neat))
    
    winner = p.run(ai_module.eval_genomes, 50)
    
    # Save final winner
    with open(os.path.join(config.MODEL_DIR, "visual_winner.pkl"), "wb") as f:
        pickle.dump(winner, f)

def show_start_menu():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Visual Training - Select Seed")
    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 30)
    
    # Scan models
    models = []
    for root, dirs, files in os.walk(config.MODEL_DIR):
        for file in files:
            if file.endswith(".pkl"):
                full_path = os.path.join(root, file)
                models.append(full_path)
    
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
            
    models.sort(key=get_fitness, reverse=True)
    
    # Pagination
    page = 0
    per_page = 5
    
    selected_model_path = None
    running = True
    
    while running:
        screen.fill(config.BLACK)
        
        title = font.render("Select Seed Model for Training", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        sub = small_font.render("(Press N for New Run / No Seed)", True, config.GRAY)
        screen.blit(sub, (config.SCREEN_WIDTH//2 - sub.get_width()//2, 70))

        mx, my = pygame.mouse.get_pos()
        
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(models))
        
        for i in range(start_idx, end_idx):
            model_path = models[i]
            filename = os.path.basename(model_path)
            fitness = get_fitness(model_path)
            parent = os.path.basename(os.path.dirname(model_path))
            display_text = f"{filename} (Fit: {fitness}) [{parent}]"
            
            y_pos = 150 + (i - start_idx) * 60
            rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
            
            color = (50, 50, 50)
            if rect.collidepoint((mx, my)):
                color = (100, 100, 100)
                
            pygame.draw.rect(screen, color, rect)
            
            text_surf = small_font.render(display_text, True, config.WHITE)
            screen.blit(text_surf, (rect.x + 10, rect.centery - text_surf.get_height()//2))
            
            if pygame.mouse.get_pressed()[0] and rect.collidepoint((mx, my)):
                selected_model_path = model_path
                running = False
                pygame.time.wait(200) # Debounce

        # Navigation
                elif event.key == pygame.K_RIGHT:
                    if (page + 1) * per_page < len(models):
                        page += 1
                elif event.key == pygame.K_LEFT:
                    if page > 0:
                        page -= 1

    pygame.quit()
    return selected_model_path

if __name__ == "__main__":
    try:
        seed_path = show_start_menu()
        seed_genome = None
        if seed_path:
            print(f"Loading seed: {seed_path}")
            with open(seed_path, "rb") as f:
                seed_genome = pickle.load(f)
                
        run_visual_training(seed_genome)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting...")
        pygame.quit()
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
        pygame.quit()
