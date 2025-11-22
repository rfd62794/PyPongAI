"""Concurrent Match Executor for parallel match execution.

This module provides concurrent execution of multiple matches when visual mode is off.
Uses multiprocessing to run matches in parallel, significantly speeding up
tournaments and training.
"""

import multiprocessing
import os
import sys
from functools import partial

# Prevent importing main.py in worker processes
if __name__ == "__main__" or "__mp_main__" in sys.modules:
    # This is a worker process - don't import pygame-dependent modules
    pass

# Add root directory to path
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# Import only what we need - avoid importing main.py
try:
    from ai.agent_factory import AgentFactory
    from match.simulator import MatchSimulator
except ImportError as e:
    # If imports fail in worker process, we'll handle it in the function
    AgentFactory = None
    MatchSimulator = None


def _run_single_match(match_config):
    """Worker function to run a single match in a process.
    
    Args:
        match_config: Dict with keys:
            - p1_path: Path to player 1 model
            - p2_path: Path to player 2 model
            - neat_config_path: Path to NEAT config
            - record_match: Whether to record the match
            - metadata: Optional match metadata
    
    Returns:
        Dict with match results (score_left, score_right, stats, match_metadata, error)
    """
    # Import here to avoid issues in worker processes
    try:
        from ai.agent_factory import AgentFactory
        from match.simulator import MatchSimulator
    except ImportError:
        return {
            "score_left": 0,
            "score_right": 0,
            "stats": {
                "left": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0},
                "right": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0}
            },
            "match_metadata": match_config.get("metadata"),
            "error": "Failed to import required modules in worker process"
        }
    
    p1_path = match_config["p1_path"]
    p2_path = match_config["p2_path"]
    neat_config_path = match_config["neat_config_path"]
    record_match = match_config.get("record_match", False)
    metadata = match_config.get("metadata")
    
    try:
        # Check if files exist
        if not os.path.exists(p1_path):
            raise FileNotFoundError(f"Model file not found: {p1_path}")
        if not os.path.exists(p2_path):
            raise FileNotFoundError(f"Model file not found: {p2_path}")
        
        # Load agents
        agent1 = AgentFactory.create_agent(p1_path, neat_config_path)
        agent2 = AgentFactory.create_agent(p2_path, neat_config_path)
        
        # Run match
        simulator = MatchSimulator(
            agent1,
            agent2,
            p1_name=os.path.basename(p1_path),
            p2_name=os.path.basename(p2_path),
            record_match=record_match,
            metadata=metadata
        )
        
        result = simulator.run()
        return result
        
    except FileNotFoundError as e:
        return {
            "score_left": 0,
            "score_right": 0,
            "stats": {
                "left": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0},
                "right": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0}
            },
            "match_metadata": metadata,
            "error": str(e)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "score_left": 0,
            "score_right": 0,
            "stats": {
                "left": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0},
                "right": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0}
            },
            "match_metadata": metadata,
            "error": str(e)
        }


class ConcurrentMatchExecutor:
    """Executes multiple matches concurrently using a process pool.
    
    This class manages a pool of worker processes to run matches in parallel.
    Only used when visual_mode is False for maximum performance.
    """
    
    def __init__(self, max_workers=None, visual_mode=False):
        """Initialize the concurrent executor.
        
        Args:
            max_workers: Maximum number of worker processes. If None, uses CPU count.
            visual_mode: If True, disables concurrent execution (must be sequential for visuals).
        """
        self.visual_mode = visual_mode
        if visual_mode:
            self.pool = None
            self.max_workers = 0
        else:
            self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
            # Use spawn method for better compatibility (especially on Windows)
            # Only set start method if not already set
            try:
                if sys.platform == 'win32':
                    current_method = multiprocessing.get_start_method(allow_none=True)
                    if current_method != 'spawn':
                        multiprocessing.set_start_method('spawn', force=True)
            except RuntimeError:
                # Start method already set, ignore
                pass
            self.pool = multiprocessing.Pool(processes=self.max_workers)
    
    def execute_matches(self, match_configs):
        """Execute multiple matches concurrently.
        
        Args:
            match_configs: List of match configuration dicts (see _run_single_match)
        
        Returns:
            List of match results in the same order as match_configs
        """
        if self.visual_mode or not self.pool:
            # Sequential execution for visual mode
            return [_run_single_match(config) for config in match_configs]
        
        # Concurrent execution
        results = self.pool.map(_run_single_match, match_configs)
        return results
    
    def execute_match(self, match_config):
        """Execute a single match (for compatibility).
        
        Args:
            match_config: Match configuration dict
        
        Returns:
            Match result dict
        """
        return _run_single_match(match_config)
    
    def close(self):
        """Close the process pool."""
        if self.pool:
            self.pool.close()
            self.pool.join()
            self.pool = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

