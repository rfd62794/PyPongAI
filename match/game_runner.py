"""GameRunner: Separated responsibility for running game loops.

This class handles the game loop execution, separating it from
match orchestration (MatchSimulator) and analysis (MatchAnalyzer).
"""

from core import config
from core import simulator as game_simulator


class GameRunner:
    """Runs a game loop between two agents. Single responsibility: game execution."""
    
    def __init__(self, agent1, agent2, game=None):
        """Initialize with two agents and optional game instance."""
        self.agent1 = agent1
        self.agent2 = agent2
        self.game = game if game is not None else game_simulator.GameSimulator()
        self.frame_count = 0
        self.max_frames = config.MAX_SCORE * 1000  # Safety limit
    
    def run_frame(self, state_callback=None, analyzer_callback=None, recorder_callback=None):
        """Run a single frame. Returns (score_left, score_right, game_over, event_data)."""
        self.frame_count += 1
        
        # Get current state
        state = self.game.get_state()
        
        # Callbacks for analysis/recording (batched)
        if state_callback:
            state_callback(state)
        if analyzer_callback:
            analyzer_callback(state)
        if recorder_callback:
            recorder_callback(state)
        
        # Get agent moves
        left_move = self.agent1.get_move(state, "left")
        right_move = self.agent2.get_move(state, "right")
        
        # Update game
        event_data = self.game.update(left_move, right_move)
        
        # Check end conditions
        game_over = (self.game.score_left >= config.MAX_SCORE or 
                    self.game.score_right >= config.MAX_SCORE or
                    self.frame_count >= self.max_frames)
        
        return (self.game.score_left, self.game.score_right, game_over, event_data)
    
    def run_to_completion(self, state_callback=None, analyzer_callback=None, recorder_callback=None):
        """Run game until completion. Returns final scores.
        
        Optimizations:
        - Early termination for obvious outcomes
        - Batched callbacks to reduce overhead
        """
        target_score = config.MAX_SCORE
        max_frames = target_score * 1000  # Safety limit
        
        while self.frame_count < max_frames:
            score_left, score_right, game_over, event_data = self.run_frame(
                state_callback, analyzer_callback, recorder_callback
            )
            
            if game_over:
                break
            
            # Early termination: if one player is far ahead with little time left
            score_diff = abs(score_left - score_right)
            if score_diff >= target_score - 1 and self.frame_count > target_score * 500:
                # One player needs 1 more point and we're past halfway
                break
        
        return self.game.score_left, self.game.score_right

