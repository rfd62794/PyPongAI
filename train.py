# train.py
import patch_neat
import os
import neat
import pickle
import ai_module
import config

def run_training():
    """
    Runs the NEAT training process.
    """
    # Load configuration
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, config.NEAT_CONFIG_PATH)
    
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)

    # Create the population
    p = neat.Population(neat_config)

    # Add reporters
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Run for 50 generations
    print("Starting training...")
    winner = p.run(ai_module.eval_genomes, 1)

    # Save the winner
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fitness = int(winner.fitness) if winner.fitness else 0
    model_filename = f"model_{timestamp}_fitness{fitness}.pkl"
    model_path = os.path.join(config.MODEL_DIR, model_filename)
    
    with open(model_path, "wb") as f:
        pickle.dump(winner, f)
        
    print(f"Training finished. Best genome saved to {model_path}")
    
    # Also save as 'best_genome.pkl' for easy access if needed, or just keep unique ones
    latest_path = os.path.join(config.MODEL_DIR, "best_genome.pkl")
    with open(latest_path, "wb") as f:
        pickle.dump(winner, f)

if __name__ == "__main__":
    run_training()
