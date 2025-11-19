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
from model_manager import get_best_model

class VisualReporter(neat.reporting.BaseReporter):
    def __init__(self, config_neat, champion_genome=None):
        self.config_neat = config_neat
        self.generation = 0
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.champion_genome = champion_genome  # Best existing model to compete against

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
            
            # Visualize against champion if available, otherwise against second best
            opponent = self.champion_genome if self.champion_genome else None
            if not opponent:
                # Find second best for visualization opponent
                second_best = None
                second_fitness = -float('inf')
                for g in population.values():
                    if g.fitness is not None and g.fitness > second_fitness and g != best_genome:
                        second_fitness = g.fitness
                        second_best = g
                opponent = second_best if second_best else best_genome
            
            self.visualize_match(best_genome, opponent)

    def save_checkpoint(self, genome):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{self.generation}_fit_{int(genome.fitness)}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        with open(filepath, "wb") as f:
            pickle.dump(genome, f)
        print(f"Saved checkpoint: {filename}")

    def visualize_match(self, genome1, genome2):
        opponent_label = "Champion" if genome2 == self.champion_genome else "2nd Best"
        print(f"Visualizing Best vs {opponent_label}... (Press SPACE to skip)")
        
        # Setup Game
        pygame.init()
        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(f"Generation {self.generation} - Best (Left) vs {opponent_label} (Right)")
        clock = pygame.time.Clock()
        game = game_engine.Game()
        
        # Create Networks
        net1 = neat.nn.FeedForwardNetwork.create(genome1, self.config_neat)
        net2 = neat.nn.FeedForwardNetwork.create(genome2, self.config_neat)
        
        running = True
        # Run for a match to 5 points
        while running:
            clock.tick(config.FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    sys.exit(100)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        running = False
            
            state = game.get_state()
            
            # AI 1 (Left)
            inputs1 = (
                state["paddle_left_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] < 0 else 0.0,
                state["paddle_right_y"] / config.SCREEN_HEIGHT
            )
            out1 = net1.activate(inputs1)
            act1 = out1.index(max(out1))
            left_move = "UP" if act1 == 0 else "DOWN" if act1 == 1 else None
            
            # AI 2 (Right)
            inputs2 = (
                state["paddle_right_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_right_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] > 0 else 0.0,
                state["paddle_left_y"] / config.SCREEN_HEIGHT
            )
            out2 = net2.activate(inputs2)
            act2 = out2.index(max(out2))
            right_move = "UP" if act2 == 0 else "DOWN" if act2 == 1 else None
            
            # Update
            score_data = game.update(left_move, right_move)
            
            # Draw
            game.draw(screen)
            
            # Overlay Info
            font = pygame.font.Font(None, 36)
            info_text = font.render("Press SPACE to Resume Training", True, config.WHITE)
            screen.blit(info_text, (10, config.SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            
            # Check end condition
            if game.score_left >= 5 or game.score_right >= 5:
                running = False
                
        pygame.display.quit()

def run_visual_training(seed_genome=None):
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
                              
    p = neat.Population(config_neat)
    
    # Load best existing model as champion
    champion_genome = None
    best_model_path = get_best_model()
    if best_model_path:
        try:
            with open(best_model_path, "rb") as f:
                champion_genome = pickle.load(f)
            print(f"Loaded champion model: {os.path.basename(best_model_path)}")
            # Add to Hall of Fame
            ai_module.HALL_OF_FAME = [champion_genome]
        except Exception as e:
            print(f"Failed to load champion model: {e}")
    
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
    p.add_reporter(VisualReporter(config_neat, champion_genome))
    
    winner = p.run(ai_module.eval_genomes_self_play, 50)
    
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
        # Navigation
        if len(models) > per_page:
            nav_text = f"Page {page + 1} / {(len(models) - 1) // per_page + 1} (Arrows to change)"
            nav_surf = small_font.render(nav_text, True, config.WHITE)
            screen.blit(nav_surf, (config.SCREEN_WIDTH//2 - nav_surf.get_width()//2, config.SCREEN_HEIGHT - 120))

        # START Button (Auto-Seed)
        start_btn_rect = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 500, 300, 60)
        btn_color = (50, 200, 50) if start_btn_rect.collidepoint((mx, my)) else (30, 150, 30)
        pygame.draw.rect(screen, btn_color, start_btn_rect)
        pygame.draw.rect(screen, config.WHITE, start_btn_rect, 3)
        
        start_text = font.render("START AUTO-SEED", True, config.WHITE)
        start_rect = start_text.get_rect(center=start_btn_rect.center)
        screen.blit(start_text, start_rect)
        
        if pygame.mouse.get_pressed()[0] and start_btn_rect.collidepoint((mx, my)):
            pygame.quit()
            return get_best_model()

    # Back Button
        back_rect = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
        pygame.draw.rect(screen, (150, 50, 50), back_rect)
        pygame.draw.rect(screen, config.WHITE, back_rect, 2)
        back_text = font.render("Back", True, config.WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(100)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit(0) # Exit cleanly to return to menu
                
                # Check model selection
                start_idx = page * per_page
                end_idx = min(start_idx + per_page, len(models))
                for i in range(start_idx, end_idx):
                    y_pos = 150 + (i - start_idx) * 60
                    rect = pygame.Rect(100, y_pos, config.SCREEN_WIDTH - 200, 50)
                    if rect.collidepoint(event.pos):
                        selected_model_path = models[i]
                        running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.quit()
                    return get_best_model()
                elif event.key == pygame.K_n:
                    running = False # No seed
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
        sys.exit(100)
    except SystemExit as e:
        if e.code == 100:
            sys.exit(100)
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
        pygame.quit()
