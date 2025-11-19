# ai_module.py
import neat
import pygame
import config
import game_engine
import random

def get_rule_based_move(game_state, paddle="right"):
    """
    Returns a simple rule-based move ('UP', 'DOWN', or None).
    Tracks the ball's Y position.
    """
    paddle_y = game_state[f"paddle_{paddle}_y"]
    ball_y = game_state["ball_y"]
    paddle_center = paddle_y + config.PADDLE_HEIGHT / 2
    
    # Deadzone to prevent jitter
    if abs(paddle_center - ball_y) < 10:
        return None
        
    if paddle_center < ball_y:
        return "DOWN"
    elif paddle_center > ball_y:
        return "UP"
    return None

def eval_genomes(genomes, config_neat):
    """
    NEAT fitness function.
    Evaluates each genome by playing a game against a rule-based opponent.
    """
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
        genome.fitness = 0
        
        game = game_engine.Game()
        
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
                1.0 if state["ball_vel_x"] < 0 else 0.0
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

def eval_genomes_competitive(genomes, config_neat):
    """
    Competitive co-evolution fitness function.
    Each genome plays multiple matches against other genomes.
    Both paddles are controlled by evolving AI.
    """
    # Convert to list for easier indexing
    genome_list = list(genomes)
    
    # Initialize fitness to 0
    for _, genome in genome_list:
        genome.fitness = 0
    
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
            game = game_engine.Game()
            run = True
            frame_count = 0
            max_frames = 3000  # Prevent infinite games
            
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
                    1.0 if state["ball_vel_x"] < 0 else 0.0
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
                    1.0 if state["ball_vel_x"] > 0 else 0.0  # Incoming from right perspective
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
                
                # Survival reward
                genome.fitness += 0.1
                opp_genome.fitness += 0.1
                
                # Check for scoring and hit events
                if score_data:
                    # Reward hits
                    if score_data.get("hit_left"):
                        genome.fitness += 1
                    if score_data.get("hit_right"):
                        opp_genome.fitness += 1
                    
                    # Reward/penalize scoring
                    if score_data.get("scored") == "left":
                        genome.fitness += 20  # Win
                        opp_genome.fitness -= 10  # Loss
                        run = False
                    elif score_data.get("scored") == "right":
                        genome.fitness -= 10  # Loss
                        opp_genome.fitness += 20  # Win
                        run = False
    
    # Normalize fitness by number of matches played
    for _, genome in genome_list:
        genome.fitness = genome.fitness / matches_per_genome if matches_per_genome > 0 else 0
