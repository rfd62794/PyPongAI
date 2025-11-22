from core import config
from core import simulator as game_simulator
from .analyzer import MatchAnalyzer
from .recorder import MatchRecorder
from .game_runner import GameRunner
import os

class MatchSimulator:
    """Orchestrates a match between two agents. Single responsibility: match coordination."""
    
    def __init__(self, agent1, agent2, p1_name="Player 1", p2_name="Player 2", record_match=False, metadata=None):
        self.agent1 = agent1
        self.agent2 = agent2
        self.analyzer = MatchAnalyzer()
        self.recorder = MatchRecorder(
            p1_name, 
            p2_name,
            match_type="tournament",
            metadata=metadata
        ) if record_match else None
        
        # Use GameRunner for execution (SRP: separated concerns)
        self.runner = GameRunner(agent1, agent2)
            
    def run(self):
        """
        Runs the match simulation loop until completion.
        Returns a dictionary containing scores, stats, and match metadata.
        """
        # Run game to completion with batched callbacks
        score_left, score_right = self.runner.run_to_completion(
            analyzer_callback=self.analyzer.update,
            recorder_callback=self.recorder.record_frame if self.recorder else None
        )
                
        # Compile Results
        stats = self.analyzer.get_stats()
        match_metadata = None
        if self.recorder:
            match_metadata = self.recorder.save()
        
        return {
            "score_left": score_left,
            "score_right": score_right,
            "stats": stats,
            "match_metadata": match_metadata
        }
