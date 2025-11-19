# ai_module.py
import neat
import pygame
import config
import game_engine

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
