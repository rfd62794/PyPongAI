import pickle
import neat
import os
import config

class NeatAgent:
    def __init__(self, net):
        self.net = net

    def get_move(self, state, side):
        """
        Calculates the move based on game state and side ('left' or 'right').
        """
        if side == "left":
            my_y = state["paddle_left_y"]
            op_y = state["paddle_right_y"]
            ball_incoming = 1.0 if state["ball_vel_x"] < 0 else 0.0
        else:
            my_y = state["paddle_right_y"]
            op_y = state["paddle_left_y"]
            ball_incoming = 1.0 if state["ball_vel_x"] > 0 else 0.0

        # Inputs:
        # 1. My Paddle Y (normalized)
        # 2. Ball X (normalized)
        # 3. Ball Y (normalized)
        # 4. Ball Vel X (normalized)
        # 5. Ball Vel Y (normalized)
        # 6. Vertical Distance to Ball (normalized)
        # 7. Ball Incoming? (1.0 or 0.0)
        # 8. Opponent Paddle Y (normalized)
        
        inputs = (
            my_y / config.SCREEN_HEIGHT,
            state["ball_x"] / config.SCREEN_WIDTH,
            state["ball_y"] / config.SCREEN_HEIGHT,
            state["ball_vel_x"] / config.BALL_MAX_SPEED,
            state["ball_vel_y"] / config.BALL_MAX_SPEED,
            (my_y - state["ball_y"]) / config.SCREEN_HEIGHT,
            ball_incoming,
            op_y / config.SCREEN_HEIGHT
        )
        
        out = self.net.activate(inputs)
        act = out.index(max(out))
        return "UP" if act == 0 else "DOWN" if act == 1 else None

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
        net = AgentFactory.create_network(genome, config_path)
        return NeatAgent(net)
