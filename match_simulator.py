import config
import game_simulator
from match_analyzer import MatchAnalyzer
from match_recorder import MatchRecorder
import os

class MatchSimulator:
    def __init__(self, agent1, agent2, p1_name="Player 1", p2_name="Player 2", record_match=False, metadata=None):
        self.agent1 = agent1
        self.agent2 = agent2
        self.game = game_simulator.GameSimulator()
        self.analyzer = MatchAnalyzer()
        self.recorder = None
        
        if record_match:
            self.recorder = MatchRecorder(
                p1_name, 
                p2_name,
                match_type="tournament",
                metadata=metadata
            )
            
    def run(self):
        """
        Runs the match simulation loop until completion.
        Returns a dictionary containing scores, stats, and match metadata.
        """
        target_score = config.MAX_SCORE
        running = True
        
        while running:
            state = self.game.get_state()
            
            # Update Analyzer & Recorder
            self.analyzer.update(state)
            if self.recorder:
                self.recorder.record_frame(state)
            
            # AI 1 (Left)
            left_move = self.agent1.get_move(state, "left")
            
            # AI 2 (Right)
            right_move = self.agent2.get_move(state, "right")
            
            # Update Game
            self.game.update(left_move, right_move)
            
            # Check End Condition
            if self.game.score_left >= target_score or self.game.score_right >= target_score:
                running = False
                
        # Compile Results
        stats = self.analyzer.get_stats()
        match_metadata = None
        if self.recorder:
            match_metadata = self.recorder.save()
        
        return {
            "score_left": self.game.score_left,
            "score_right": self.game.score_right,
            "stats": stats,
            "match_metadata": match_metadata
        }
