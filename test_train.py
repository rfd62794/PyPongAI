# test_train.py
import patch_neat
import neat
import os
from ai import ai_module
import config

def test_training():
    print("Starting test training...")
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, config.NEAT_CONFIG_PATH)
    
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)

    # Create the population
    p = neat.Population(neat_config)

    # Run for 1 generation
    winner = p.run(ai_module.eval_genomes, 1)
    print("Test training finished successfully.")

if __name__ == "__main__":
    test_training()
