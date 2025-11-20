"""Validation utilities for NEAT genomes in PyPongAI.

This module provides functions for validating trained genomes by testing them
against opponents and recording match statistics.
"""

import neat
import config
import game_engine
from opponents import get_rule_based_move


def validate_genome(genome, config_neat, generation=0, record_matches=True):
    """Validates a genome by playing matches against rule-based AI.
    
    The genome plays multiple validation games against a simple rule-based
    opponent to assess its performance. Match data can be optionally recorded
    for later analysis.
    
    Args:
        genome: A NEAT genome to validate.
        config_neat: NEAT configuration object.
        generation: Current generation number for metadata. Defaults to 0.
        record_matches: Whether to record matches to disk. Defaults to True.
    
    Returns:
        tuple: A 2-tuple containing:
            - avg_rally: Average hits per game across all validation games.
            - win_rate: Fraction of games won (0.0 to 1.0).
    """
    from match_recorder import MatchRecorder
    import match_database
    
    net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
    
    total_rallies = 0
    total_hits = 0
    wins = 0
    num_games = 5  # Play 5 validation games
    
    for game_idx in range(num_games):
        game = game_engine.Game()
        run = True
        frame_count = 0
        max_frames = 5000
        
        current_rally = 0
        
        # Initialize recorder if enabled
        recorder = None
        if record_matches:
            metadata = {
                "generation": generation,
                "fitness": genome.fitness if hasattr(genome, 'fitness') and genome.fitness else 0
            }
            recorder = MatchRecorder(
                f"gen{generation}_trainee",
                "rule_based_ai",
                match_type="training_validation",
                metadata=metadata
            )
        
        while run and frame_count < max_frames:
            frame_count += 1
            state = game.get_state()
            
            # Record frame
            if recorder:
                recorder.record_frame(state)
            
            # AI plays Left
            inputs = (
                state["paddle_left_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] < 0 else 0.0,
                state["paddle_right_y"] / config.SCREEN_HEIGHT
            )
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = "UP" if action_idx == 0 else "DOWN" if action_idx == 1 else None
            
            # Rule-Based plays Right
            right_move = get_rule_based_move(state, "right")
            
            score_data = game.update(left_move, right_move)
            
            if score_data:
                if score_data.get("hit_left") or score_data.get("hit_right"):
                    current_rally += 1
                    total_hits += 1
                
                if score_data.get("scored"):
                    if score_data.get("scored") == "left":
                        wins += 1
                    run = False
        
        total_rallies += current_rally
        
        # Save and index recording
        if recorder:
            match_metadata = recorder.save()
            if match_metadata:
                match_database.index_match(match_metadata)

    avg_rally = total_hits / num_games
    win_rate = wins / num_games
    return avg_rally, win_rate
