import pickle
import neat
import os

class AgentFactory:
    @staticmethod
    def load_genome(path):
        """Loads a genome from a pickle file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Genome file not found: {path}")
            
        with open(path, "rb") as f:
            genome = pickle.load(f)
        return genome

    @staticmethod
    def create_network(genome, config_path):
        """Creates a NEAT FeedForwardNetwork from a genome and config path."""
        # Load NEAT config
        # Note: We re-load the config object here. In a highly optimized scenario 
        # we might want to cache this, but for now this is safe.
        config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  config_path)
                                  
        net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
        return net

    @staticmethod
    def create_agent(genome_path, config_path):
        """Convenience method to load a genome and create its network."""
        genome = AgentFactory.load_genome(genome_path)
        return AgentFactory.create_network(genome, config_path)
