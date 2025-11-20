import neat
import os

def inspect_neat():
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
                         
    print("Genome Config Type:", type(config.genome_config))
    print("Attributes:", dir(config.genome_config))
    
    if hasattr(config.genome_config, 'get_new_node_key'):
        print("Has get_new_node_key")
        
    # Create a dummy node dict
    nodes = {0: 'a', 1: 'b', 2: 'c'}
    try:
        new_key = config.genome_config.get_new_node_key(nodes)
        print(f"New Key for {nodes.keys()}: {new_key}")
    except Exception as e:
        print(f"Error calling get_new_node_key: {e}")

    # Check if there is an indexer
    if hasattr(config.genome_config, 'indexer'):
        print("Indexer found:", config.genome_config.indexer)
    elif hasattr(config.genome_config, 'node_indexer'):
        print("Node Indexer found:", config.genome_config.node_indexer)

if __name__ == "__main__":
    inspect_neat()
