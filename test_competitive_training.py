# Quick test for competitive AI training
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
# Run for 2 generations to see competitive fitness
winner = p.run(ai_module.eval_genomes_competitive, 2)
print("Competitive training test completed. Winner fitness:", winner.fitness)
