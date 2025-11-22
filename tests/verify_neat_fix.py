import neat
import os
import pickle
import itertools
import sys

# Mock config path
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'neat_config.txt')

def verify_fix():
    print("Verifying NEAT seeding fix...")
    
    # 1. Create a dummy genome with high node IDs
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    genome = neat.DefaultGenome(1)
    genome.configure_new(config.genome_config)
    
    # Manually add a high node ID
    genome.nodes[1000] = genome.create_node(config.genome_config, 1000)
    print(f"Created dummy genome with max node ID: {max(genome.nodes.keys())}")
    
    # 2. Simulate the training startup
    print("Simulating training startup...")
    p = neat.Population(config)
    
    # Seed
    target_id = list(p.population.keys())[0]
    genome.key = target_id
    p.population[target_id] = genome
    p.species.speciate(config, p.population, p.generation)
    
    # APPLY FIX
    max_node_id = max(genome.nodes.keys()) if genome.nodes else 0
    print(f"Updating node indexer to start from {max_node_id + 1}")
    config.genome_config.node_indexer = itertools.count(max_node_id + 1)
    
    # 3. Try to mutate (add node)
    print("Attempting mutation...")
    try:
        genome.mutate_add_node(config.genome_config)
        new_max = max(genome.nodes.keys())
        print(f"Mutation successful! New max node ID: {new_max}")
        assert new_max > 1000
        print("Fix verified: Node ID collision avoided.")
    except AssertionError as e:
        print("Fix FAILED: AssertionError during mutation.")
        sys.exit(1)
    except Exception as e:
        print(f"Fix FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_fix()
