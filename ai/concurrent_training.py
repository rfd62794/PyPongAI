"""Concurrent training support for faster genome evaluation.

This module provides concurrent execution of matches during training,
significantly speeding up competitive and self-play training modes.
"""

import multiprocessing
import sys
import os
from functools import partial

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config
from core import simulator as game_simulator


def _run_training_match(match_data):
    """Worker function to run a single training match.
    
    Args:
        match_data: Dict with:
            - genome_left_pickle: Pickled genome for left player
            - genome_right_pickle: Pickled genome for right player
            - config_path: Path to NEAT config file
            - ball_speed: Optional ball speed
    
    Returns:
        Dict with match results and contact metrics
    """
    import pickle
    import neat
    
    genome_left_pickle = match_data["genome_left_pickle"]
    genome_right_pickle = match_data["genome_right_pickle"]
    config_path = match_data["config_path"]
    ball_speed = match_data.get("ball_speed")
    
    try:
        # Unpickle genomes
        genome_left = pickle.loads(genome_left_pickle)
        genome_right = pickle.loads(genome_right_pickle)
        
        # Load config
        config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  config_path)
        
        # Create networks (use RecurrentNetwork for RNN support)
        try:
            net_left = neat.nn.RecurrentNetwork.create(genome_left, config_neat)
            net_left.reset()
        except:
            net_left = neat.nn.FeedForwardNetwork.create(genome_left, config_neat)
        
        try:
            net_right = neat.nn.RecurrentNetwork.create(genome_right, config_neat)
            net_right.reset()
        except:
            net_right = neat.nn.FeedForwardNetwork.create(genome_right, config_neat)
        
        # Play match
        game = game_simulator.GameSimulator(ball_speed=ball_speed)
        frame_count = 0
        max_frames = 3000
        contact_metrics = []
        match_result = 0.5  # Draw by default
        
        while frame_count < max_frames:
            frame_count += 1
            state = game.get_state()
            
            # Left paddle (genome being evaluated)
            inputs_left = (
                state["paddle_left_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] < 0 else 0.0,
                state["paddle_right_y"] / config.SCREEN_HEIGHT
            )
            output_left = net_left.activate(inputs_left)
            action_idx_left = output_left.index(max(output_left))
            
            left_move = None
            if action_idx_left == 0:
                left_move = "UP"
            elif action_idx_left == 1:
                left_move = "DOWN"
            
            # Right paddle (opponent)
            inputs_right = (
                state["paddle_right_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_right_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] > 0 else 0.0,
                state["paddle_left_y"] / config.SCREEN_HEIGHT
            )
            output_right = net_right.activate(inputs_right)
            action_idx_right = output_right.index(max(output_right))
            
            right_move = None
            if action_idx_right == 0:
                right_move = "UP"
            elif action_idx_right == 1:
                right_move = "DOWN"
            
            # Update game
            score_data = game.update(left_move, right_move)
            
            # Collect contact metrics
            if score_data and (score_data.get("hit_left") or score_data.get("hit_right")):
                contact_metrics.append(score_data)
            
            # Check for scoring
            if score_data:
                if score_data.get("scored") == "left":
                    match_result = 1.0
                    break
                elif score_data.get("scored") == "right":
                    match_result = 0.0
                    break
        
        return {
            "match_result": match_result,
            "contact_metrics": contact_metrics,
            "score_left": game.score_left,
            "score_right": game.score_right
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "match_result": 0.5,
            "contact_metrics": [],
            "score_left": 0,
            "score_right": 0,
            "error": str(e)
        }


class ConcurrentTrainingExecutor:
    """Executes training matches concurrently."""
    
    def __init__(self, max_workers=None, config_path=None):
        """Initialize with worker pool.
        
        Args:
            max_workers: Number of worker processes
            config_path: Path to NEAT config file
        """
        self.config_path = config_path
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        if sys.platform == 'win32':
            multiprocessing.set_start_method('spawn', force=True)
        self.pool = multiprocessing.Pool(processes=self.max_workers)
    
    def execute_matches(self, genome_pairs, config_path=None):
        """Execute multiple training matches concurrently.
        
        Args:
            genome_pairs: List of (genome_left, genome_right) tuples
            config_path: Path to NEAT config (uses self.config_path if not provided)
        
        Returns:
            List of match results
        """
        import pickle
        
        config_path = config_path or self.config_path
        if not config_path:
            raise ValueError("config_path must be provided")
        
        # Prepare match data with pickled genomes
        match_data_list = []
        for genome_left, genome_right in genome_pairs:
            match_data_list.append({
                "genome_left_pickle": pickle.dumps(genome_left),
                "genome_right_pickle": pickle.dumps(genome_right),
                "config_path": config_path,
                "ball_speed": None  # Can be added later if needed
            })
        
        return self.pool.map(_run_training_match, match_data_list)
    
    def close(self):
        """Close the process pool."""
        if self.pool:
            self.pool.close()
            self.pool.join()
            self.pool = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

