"""Rule-based AI opponents for PyPongAI.

This module provides simple rule-based opponent implementations that can be used
for training and testing NEAT-evolved AI agents.
"""

from core import config


def get_rule_based_move(game_state, paddle="right"):
    """Returns a simple rule-based paddle move based on ball position.
    
    This function implements a basic AI that tracks the ball's Y position
    and moves the paddle to intercept it. It includes a deadzone to prevent
    jittering when the paddle is already aligned with the ball.
    
    Args:
        game_state: A dictionary containing the current game state with keys:
            - paddle_{paddle}_y: Y position of the specified paddle
            - ball_y: Y position of the ball
        paddle: Which paddle to control ("left" or "right"). Defaults to "right".
    
    Returns:
        str or None: "UP" to move paddle up, "DOWN" to move paddle down, 
            or None to stay in place.
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
