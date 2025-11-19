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

def run_visual_training():
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
                              
    p = neat.Population(config_neat)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    p.add_reporter(VisualReporter(config_neat))
    
    winner = p.run(ai_module.eval_genomes, 50)
    
    # Save final winner
    with open(os.path.join(config.MODEL_DIR, "visual_winner.pkl"), "wb") as f:
        pickle.dump(winner, f)

if __name__ == "__main__":
    run_visual_training()
