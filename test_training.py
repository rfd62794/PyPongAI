# Quick test for AI training after modifications
import neat, config, ai_module, game_engine

config_path = config.NEAT_CONFIG_PATH
neat_config = neat.Config(
    neat.DefaultGenome,
    neat.DefaultReproduction,
    neat.DefaultSpeciesSet,
    neat.DefaultStagnation,
    config_path
)

p = neat.Population(neat_config)
# Run for 1 generation to see fitness adjustments
winner = p.run(ai_module.eval_genomes, 1)
print("Test run completed. Winner fitness:", winner.fitness)
