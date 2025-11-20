"""Headless game simulation for PyPongAI.

This module provides a lightweight, Pygame-independent implementation of the
Pong game logic. It's optimized for high-speed AI training by eliminating
rendering overhead while maintaining identical game physics to the visual version.
"""

import random
import config


class Rect:
    """A simple rectangle class mimicking pygame.Rect for collision detection.
    
    Provides properties for accessing and manipulating rectangle boundaries,
    enabling collision detection without Pygame dependencies.
    
    Attributes:
        x: X-coordinate of the rectangle's top-left corner.
        y: Y-coordinate of the rectangle's top-left corner.
        width: Width of the rectangle.
        height: Height of the rectangle.
    """
    
    def __init__(self, x, y, width, height):
        """Initializes a rectangle with position and dimensions.
        
        Args:
            x: X-coordinate of top-left corner.
            y: Y-coordinate of top-left corner.
            width: Rectangle width in pixels.
            height: Rectangle height in pixels.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def left(self):
        return self.x
    
    @left.setter
    def left(self, value):
        self.x = value

    @property
    def right(self):
        return self.x + self.width
    
    @right.setter
    def right(self, value):
        self.x = value - self.width

    @property
    def top(self):
        return self.y
    
    @top.setter
    def top(self, value):
        self.y = value

    @property
    def bottom(self):
        return self.y + self.height
    
    @bottom.setter
    def bottom(self, value):
        self.y = value - self.height

    @property
    def centerx(self):
        return self.x + self.width / 2
    
    @centerx.setter
    def centerx(self, value):
        self.x = value - self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2
    
    @centery.setter
    def centery(self, value):
        self.y = value - self.height / 2
    
    @property
    def center(self):
        return (self.centerx, self.centery)
    
    @center.setter
    def center(self, value):
        self.centerx = value[0]
        self.centery = value[1]

    def colliderect(self, other):
        """Checks for collision with another rectangle.
        
        Args:
            other: Another Rect instance to check collision with.
        
        Returns:
            bool: True if rectangles overlap, False otherwise.
        """
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class Paddle:
    """Represents a game paddle with position and movement logic.
    
    Attributes:
        rect: Rect instance defining paddle position and dimensions.
        speed: Current movement speed of the paddle.
    """
    
    def __init__(self, x, y):
        """Initializes a paddle at the specified position.
        
        Args:
            x: X-coordinate of paddle's top-left corner.
            y: Y-coordinate of paddle's top-left corner.
        """
        self.rect = Rect(x, y, config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
        self.speed = config.PADDLE_SPEED

    def move(self, up=True):
        """Moves the paddle vertically within screen bounds.
        
        Args:
            up: If True, moves paddle upward. If False, moves downward.
        """
        if up:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed
        
        # Keep paddle on screen
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > config.SCREEN_HEIGHT:
            self.rect.bottom = config.SCREEN_HEIGHT


class Ball:
    """Represents the game ball with position and velocity.
    
    Attributes:
        rect: Rect instance defining ball position and dimensions.
        vel_x: Horizontal velocity in pixels per frame.
        vel_y: Vertical velocity in pixels per frame.
        initial_speed_x: Initial X speed for resets.
        initial_speed_y: Initial Y speed for resets.
    """
    
    def __init__(self, speed_x=None, speed_y=None):
        """Initializes the ball at screen center with specified or default velocity.
        
        Args:
            speed_x: Initial horizontal speed. If None, uses config.BALL_SPEED_X.
            speed_y: Initial vertical speed. If None, uses config.BALL_SPEED_Y.
        """
        self.rect = Rect(config.SCREEN_WIDTH // 2 - config.BALL_RADIUS,
                         config.SCREEN_HEIGHT // 2 - config.BALL_RADIUS,
                         config.BALL_RADIUS * 2, config.BALL_RADIUS * 2)
        self.initial_speed_x = speed_x if speed_x is not None else config.BALL_SPEED_X
        self.initial_speed_y = speed_y if speed_y is not None else config.BALL_SPEED_Y
        self.vel_x = self.initial_speed_x * random.choice((1, -1))
        self.vel_y = self.initial_speed_y * random.choice((1, -1))

    def move(self):
        """Updates ball position based on current velocity."""
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def reset(self):
        """Resets ball to center with random velocity direction."""
        self.rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        self.vel_x = self.initial_speed_x * random.choice((1, -1))
        self.vel_y = self.initial_speed_y * random.choice((1, -1))


class GameSimulator:
    """Headless Pong game simulator for high-speed AI training.
    
    This class provides the complete game logic without rendering. It handles
    paddle movement, ball physics, collision detection, and scoring while
    maintaining identical behavior to the visual game_engine.Game class.
    
    Attributes:
        left_paddle: Paddle instance for the left player.
        right_paddle: Paddle instance for the right player.
        ball: Ball instance.
        score_left: Current score for left player.
        score_right: Current score for right player.
    """
    
    def __init__(self, ball_speed=None):
        """Initializes a new game with paddles and ball at starting positions.
        
        Args:
            ball_speed: Optional custom ball speed for curriculum learning.
                If None, uses default config values.
        """
        self.left_paddle = Paddle(10, config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH,
                                    config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.ball = Ball(speed_x=ball_speed, speed_y=ball_speed)
        self.score_left = 0
        self.score_right = 0

    def update(self, left_move=None, right_move=None):
        """Updates game state for one frame based on player moves.
        
        Processes paddle movements, ball physics, collisions, and scoring.
        Paddle speed dynamically scales with ball velocity for fair gameplay.
        
        Args:
            left_move: Movement command for left paddle ("UP", "DOWN", or None).
            right_move: Movement command for right paddle ("UP", "DOWN", or None).
        
        Returns:
            dict or None: Dictionary containing game state and event data if an
                event occurred (scoring, paddle hit, game over), None otherwise.
                Event dict may contain keys: "scored", "hit_left", "hit_right",
                "game_over", plus all state keys from get_state().
        """
        # Move paddles
        # Dynamic Paddle Speed
        current_speed_ratio = abs(self.ball.vel_x) / config.BALL_SPEED_X
        new_paddle_speed = config.PADDLE_SPEED * current_speed_ratio
        new_paddle_speed = min(new_paddle_speed, config.PADDLE_MAX_SPEED)
        self.left_paddle.speed = new_paddle_speed
        self.right_paddle.speed = new_paddle_speed

        if left_move == "UP":
            self.left_paddle.move(up=True)
        elif left_move == "DOWN":
            self.left_paddle.move(up=False)
        
        if right_move == "UP":
            self.right_paddle.move(up=True)
        elif right_move == "DOWN":
            self.right_paddle.move(up=False)

        # Move ball
        self.ball.move()

        # Wall Collision (Top/Bottom)
        if self.ball.rect.top <= 0 or self.ball.rect.bottom >= config.SCREEN_HEIGHT:
            self.ball.vel_y *= -1

        # Track paddle hits
        hit_left = False
        hit_right = False
        contact_metrics = {}

        # Paddle Collision - Left Paddle
        if self.ball.rect.colliderect(self.left_paddle.rect):
            # Store contact metrics BEFORE modifying velocities
            contact_metrics["contact_y"] = self.ball.rect.y
            contact_metrics["ball_vel_x_before"] = self.ball.vel_x
            contact_metrics["ball_vel_y_before"] = self.ball.vel_y
            
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.left = self.left_paddle.rect.right  # Prevent sticking
            hit_left = True
        
        # Paddle Collision - Right Paddle
        if self.ball.rect.colliderect(self.right_paddle.rect):
            # Store contact metrics BEFORE modifying velocities
            contact_metrics["contact_y"] = self.ball.rect.y
            contact_metrics["ball_vel_x_before"] = self.ball.vel_x
            contact_metrics["ball_vel_y_before"] = self.ball.vel_y
            
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.right = self.right_paddle.rect.left  # Prevent sticking
            hit_right = True
            
        # Cap Speed
        self.ball.vel_x = max(min(self.ball.vel_x, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
        self.ball.vel_y = max(min(self.ball.vel_y, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)

        # Scoring
        score_data = None
        if self.ball.rect.left <= 0:
            # Right scores
            self.score_right += 1
            score_data = self.get_state()
            score_data["scored"] = "right"
            self.ball.reset()
        elif self.ball.rect.right >= config.SCREEN_WIDTH:
            # Left scores
            self.score_left += 1
            score_data = self.get_state()
            score_data["scored"] = "left"
            self.ball.reset()
            
        # Check for Game Over
        if self.score_left >= config.MAX_SCORE or self.score_right >= config.MAX_SCORE:
            if score_data is None:
                score_data = self.get_state()
            score_data["game_over"] = True
        
        # Return hit events even if no score
        if score_data is None and (hit_left or hit_right):
            score_data = {}
        
        if score_data is not None:
            score_data["hit_left"] = hit_left
            score_data["hit_right"] = hit_right
            # Add advanced contact metrics if a hit occurred
            if hit_left or hit_right:
                score_data.update(contact_metrics)
            
        return score_data

    def get_state(self):
        """Returns the current game state as a dictionary.
        
        Returns:
            dict: Dictionary containing ball position/velocity, paddle positions,
                scores, and game_over flag. Keys: "ball_x", "ball_y", "ball_vel_x",
                "ball_vel_y", "paddle_left_y", "paddle_right_y", "score_left",
                "score_right", "game_over".
        """
        return {
            "ball_x": self.ball.rect.x,
            "ball_y": self.ball.rect.y,
            "ball_vel_x": self.ball.vel_x,
            "ball_vel_y": self.ball.vel_y,
            "paddle_left_y": self.left_paddle.rect.y,
            "paddle_right_y": self.right_paddle.rect.y,
            "score_left": self.score_left,
            "score_right": self.score_right,
            "game_over": False
        }
