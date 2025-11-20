"""NEAT-based AI training and evaluation for PyPongAI.

This module contains the core fitness functions for training AI agents using
the NEAT algorithm. It provides different evaluation strategies including
competitive ELO-based evaluation and self-play.
"""

import neat
import pygame
import config
import game_engine
import game_simulator
import random
from opponents import get_rule_based_move


def eval_genomes(genomes, config_neat):
    """Evaluates genomes by playing against a rule-based opponent.
    
    This is a basic fitness function where each genome plays a single game
    against a simple rule-based AI. Fitness is awarded for survival time,
    paddle hits, and scoring points.
    
    Args:
        genomes: List of (genome_id, genome) tuples from NEAT population.
        config_neat: NEAT configuration object.
    """
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
        genome.fitness = 0
        
        game = game_simulator.GameSimulator()
        
        # Genome plays as Left Paddle
        # Rule-based plays as Right Paddle
        
        run = True
        while run:
            # Get current game state
            state = game.get_state()
            
            # Prepare inputs for the network (normalized to 0-1 range)
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
            
            # Get network output
            output = net.activate(inputs)
            
            # Interpret output (UP, DOWN, STAY)
            # We'll take the index of the maximum value
            action_idx = output.index(max(output))
            
            left_move = None
            if action_idx == 0:
                left_move = "UP"
            elif action_idx == 1:
                left_move = "DOWN"
            # action_idx 2 is STAY
            
            # Get opponent move
            right_move = get_rule_based_move(state, paddle="right")
            
            # Update game
            score_data = game.update(left_move, right_move)
            
            # Fitness reward for surviving a frame
            genome.fitness += 0.1
            
            # Check for scoring and hit events
            if score_data:
                # Reward for scoring
                if score_data.get("scored") == "left":
                    genome.fitness += 10  # Genome scored
                elif score_data.get("scored") == "right":
                    genome.fitness -= 5   # Opponent scored, penalty
                # Reward for paddle hits
                if score_data.get("hit_left"):
                    genome.fitness += 1   # Successful hit by genome
                # End episode if a point was scored
                if score_data.get("scored"):
                    run = False
                # Optionally cap fitness
                if genome.fitness > 2000:
                    run = False
            
            # Optional: Cap fitness or duration to prevent infinite stalling if both are perfect
            if genome.fitness > 2000:
                run = False

def calculate_expected_score(rating_a, rating_b):
    """Calculates the expected score for player A against player B using ELO formula.
    
    Args:
        rating_a: ELO rating of player A.
        rating_b: ELO rating of player B.
    
    Returns:
        float: Expected score between 0.0 and 1.0.
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def calculate_new_rating(rating, expected_score, actual_score, k_factor=32):
    """Calculates the new ELO rating after a match.
    
    Args:
        rating: Current ELO rating.
        expected_score: Expected match outcome (from calculate_expected_score).
        actual_score: Actual match outcome (1.0 for win, 0.0 for loss, 0.5 for draw).
        k_factor: ELO K-factor controlling rating volatility. Defaults to 32.
    
    Returns:
        float: New ELO rating.
    """
    return rating + k_factor * (actual_score - expected_score)


def eval_genomes_competitive(genomes, config_neat):
    """Evaluates genomes using competitive ELO-based matchmaking.
    
    Each genome plays multiple matches against randomly selected opponents from
    the population. Fitness is determined by final ELO rating after all matches.
    This method encourages competitive evolution and provides more stable
    fitness assessments than single-opponent evaluation.
    
    Args:
        genomes: List of (genome_id, genome) tuples from NEAT population.
        config_neat: NEAT configuration object.
    """
    # Convert to list for easier indexing
    genome_list = list(genomes)
    
    # Initialize ELO ratings if not present
    for _, genome in genome_list:
        if not hasattr(genome, 'elo_rating'):
            genome.elo_rating = config.ELO_INITIAL_RATING
        # We don't reset fitness to 0 here because we want to track ELO over time.
        # However, NEAT expects fitness to be set for the current generation.
        # We will set genome.fitness = genome.elo_rating at the end.
    
    # Number of matches per genome
    matches_per_genome = min(5, len(genome_list) - 1)
    
    # Each genome plays multiple matches
    for idx, (genome_id, genome) in enumerate(genome_list):
        # Create network for this genome
        net_left = neat.nn.FeedForwardNetwork.create(genome, config_neat)
        
        # Select random opponents
        opponent_indices = [i for i in range(len(genome_list)) if i != idx]
        selected_opponents = random.sample(opponent_indices, min(matches_per_genome, len(opponent_indices)))
        
        for opp_idx in selected_opponents:
            opp_id, opp_genome = genome_list[opp_idx]
            net_right = neat.nn.FeedForwardNetwork.create(opp_genome, config_neat)
            
            # Play a match
            game = game_simulator.GameSimulator()
            run = True
            frame_count = 0
            max_frames = 3000  # Prevent infinite games
            
            # Match result: 1 for Left Win, 0 for Right Win, 0.5 for Draw
            match_result = 0.5 
            
            while run and frame_count < max_frames:
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
                    1.0 if state["ball_vel_x"] > 0 else 0.0,  # Incoming from right perspective
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
                
                # Check for scoring
                if score_data:
                    if score_data.get("scored") == "left":
                        match_result = 1.0 # Left Wins
                        run = False
                    elif score_data.get("scored") == "right":
                        match_result = 0.0 # Right Wins (Left Loses)
                        run = False
            
            # Calculate ELO updates
            # Left Genome (genome) vs Right Genome (opp_genome)
            rating_a = genome.elo_rating
            rating_b = opp_genome.elo_rating
            
            expected_a = calculate_expected_score(rating_a, rating_b)
            expected_b = calculate_expected_score(rating_b, rating_a)
            
            # Actual scores
            actual_a = match_result
            actual_b = 1.0 - match_result
            
            # Update ratings
            new_rating_a = calculate_new_rating(rating_a, expected_a, actual_a, config.ELO_K_FACTOR)
            new_rating_b = calculate_new_rating(rating_b, expected_b, actual_b, config.ELO_K_FACTOR)
            
            genome.elo_rating = new_rating_a
            opp_genome.elo_rating = new_rating_b
            
    # Set fitness to ELO rating
    for _, genome in genome_list:
        # Ensure fitness is at least 0, though ELO can technically be negative (unlikely with 1200 start)
        genome.fitness = max(0, genome.elo_rating)

def validate_genome(genome, config_neat, generation=0, record_matches=True):
    """
    Validates a genome by playing a match against the Rule-Based AI.
    Returns: (avg_rally_length, win_rate)
    """
    from match_recorder import MatchRecorder
    import match_database
    
    net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
    
    total_rallies = 0
    total_hits = 0
    wins = 0
    num_games = 5 # Play 5 validation games
    
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

# Hall of Fame Storage
HALL_OF_FAME = []

def eval_genomes_self_play(genomes, config_neat):
    """
    Self-Play Fitness Function.
    Genomes play against other genomes in the population.
    """
    genome_list = list(genomes)
    for _, genome in genome_list:
        genome.fitness = 0
    
    # Update Hall of Fame (Save best from previous generation if available)
    # Note: This function is called every generation.
    # We need a way to know if we should add to HOF.
    # A simple way is to add the best genome of the *current* population to HOF at the END of eval?
    # Or pass it in. 
    # Actually, we can just add the best of the *previous* generation if we had access.
    # But here we are evaluating.
    # Let's just add to HOF periodically based on a global counter or similar?
    # Or better: The training loop handles HOF additions. 
    # But we need HOF *inside* here to play against.
    # Let's assume HALL_OF_FAME is populated externally or we populate it here with a random sample of high fitness?
    # Issue: We don't know fitness yet.
    # Solution: We will rely on the training loop to populate HALL_OF_FAME.
    
    # Randomize list
    random.shuffle(genome_list)
    
    matches_per_genome = 2
    
    for i in range(matches_per_genome):
        # Shuffle for new pairings
        random.shuffle(genome_list)
        
        # Pair (0,1), (2,3)...
        for j in range(0, len(genome_list), 2):
            if j+1 >= len(genome_list):
                break
                
            g1_id, g1 = genome_list[j]
            
            # 20% chance to play against Hall of Fame if available
            use_hof = False
            if HALL_OF_FAME and random.random() < 0.2:
                use_hof = True
                g2 = random.choice(HALL_OF_FAME)
                # g2 is a genome object. We don't update its fitness.
            else:
                g2_id, g2 = genome_list[j+1]
            
            net1 = neat.nn.FeedForwardNetwork.create(g1, config_neat)
            net2 = neat.nn.FeedForwardNetwork.create(g2, config_neat)
            
            game = game_simulator.GameSimulator()
            run = True
            frame_count = 0
            max_frames = 10000 
            target_score = 5 
            
            while run and frame_count < max_frames:
                frame_count += 1
                state = game.get_state()
                
                # Player 1 (Left)
                inputs1 = (
                    state["paddle_left_y"] / config.SCREEN_HEIGHT,
                    state["ball_x"] / config.SCREEN_WIDTH,
                    state["ball_y"] / config.SCREEN_HEIGHT,
                    state["ball_vel_x"] / config.BALL_MAX_SPEED,
                    state["ball_vel_y"] / config.BALL_MAX_SPEED,
                    (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                    1.0 if state["ball_vel_x"] < 0 else 0.0,
                    state["paddle_right_y"] / config.SCREEN_HEIGHT
                )
                out1 = net1.activate(inputs1)
                act1 = out1.index(max(out1))
                move1 = "UP" if act1 == 0 else "DOWN" if act1 == 1 else None
                
                # Player 2 (Right)
                inputs2 = (
                    state["paddle_right_y"] / config.SCREEN_HEIGHT,
                    state["ball_x"] / config.SCREEN_WIDTH,
                    state["ball_y"] / config.SCREEN_HEIGHT,
                    state["ball_vel_x"] / config.BALL_MAX_SPEED,
                    state["ball_vel_y"] / config.BALL_MAX_SPEED,
                    (state["paddle_right_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                    1.0 if state["ball_vel_x"] > 0 else 0.0, # Incoming from right
                    state["paddle_left_y"] / config.SCREEN_HEIGHT
                )
                out2 = net2.activate(inputs2)
                act2 = out2.index(max(out2))
                move2 = "UP" if act2 == 0 else "DOWN" if act2 == 1 else None
                
                score_data = game.update(move1, move2)
                
                # Fitness Rewards
                g1.fitness += 0.01
                if not use_hof:
                    g2.fitness += 0.01
                
                if score_data:
                    if score_data.get("hit_left"):
                        g1.fitness += 1.0
                    if score_data.get("hit_right"):
                        if not use_hof:
                            g2.fitness += 1.0
                        
                    if score_data.get("scored") == "left":
                        g1.fitness += 5.0
                        if not use_hof:
                            g2.fitness -= 2.0
                    elif score_data.get("scored") == "right":
                        if not use_hof:
                            g2.fitness += 5.0
                        g1.fitness -= 2.0
                        
                if game.score_left >= target_score or game.score_right >= target_score:
                    run = False
