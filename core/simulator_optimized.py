"""Optimized headless game simulation with SRP refactoring.

This module provides a faster, more maintainable implementation by:
- Separating physics, collision, and scoring concerns
- Caching state to reduce allocations
- Early termination for obvious outcomes
"""

import random
from . import config


class Rect:
    """A simple rectangle class mimicking pygame.Rect for collision detection."""
    
    __slots__ = ('x', 'y', 'width', 'height')
    
    def __init__(self, x, y, width, height):
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
        """Fast collision detection using AABB."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class Paddle:
    """Represents a game paddle with position and movement logic."""
    
    __slots__ = ('rect', 'speed')
    
    def __init__(self, x, y):
        self.rect = Rect(x, y, config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
        self.speed = config.PADDLE_SPEED

    def move(self, up=True):
        """Moves the paddle vertically within screen bounds."""
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
    """Represents the game ball with position and velocity."""
    
    __slots__ = ('rect', 'vel_x', 'vel_y', 'initial_speed_x', 'initial_speed_y')
    
    def __init__(self, speed_x=None, speed_y=None):
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


class CollisionDetector:
    """Handles collision detection logic (SRP: single responsibility)."""
    
    @staticmethod
    def check_wall_collision(ball):
        """Check and handle wall collisions. Returns True if collision occurred."""
        if ball.rect.top <= 0:
            ball.vel_y *= -1  # Bounce down
            return True
        elif ball.rect.bottom >= config.SCREEN_HEIGHT:
            ball.vel_y *= -1  # Bounce up
            return True
        return False
    
    @staticmethod
    def check_paddle_collision(ball, paddle, is_left=True):
        """Check paddle collision. Returns True if collision occurred."""
        if ball.rect.colliderect(paddle.rect):
            ball.vel_x *= -config.BALL_SPEED_INCREMENT
            ball.vel_y *= config.BALL_SPEED_INCREMENT
            if is_left:
                ball.rect.left = paddle.rect.right
            else:
                ball.rect.right = paddle.rect.left
            # Cap speed
            ball.vel_x = max(min(ball.vel_x, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
            ball.vel_y = max(min(ball.vel_y, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
            return True
        return False


class ScoreManager:
    """Handles scoring logic (SRP: single responsibility)."""
    
    @staticmethod
    def check_scoring(ball, score_left, score_right):
        """Check if a point was scored. Returns (left_scored, right_scored)."""
        if ball.rect.left <= 0:
            return (False, True)  # Right scores
        elif ball.rect.right >= config.SCREEN_WIDTH:
            return (True, False)  # Left scores
        return (False, False)


class GameSimulator:
    """Optimized headless Pong game simulator with SRP refactoring.
    
    Responsibilities separated:
    - Physics: ball/paddle movement
    - Collision: CollisionDetector
    - Scoring: ScoreManager
    """
    
    __slots__ = ('left_paddle', 'right_paddle', 'ball', 'score_left', 'score_right', 
                 '_cached_state', '_state_dirty')
    
    def __init__(self, ball_speed=None):
        self.left_paddle = Paddle(10, config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH,
                                    config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.ball = Ball(speed_x=ball_speed, speed_y=ball_speed)
        self.score_left = 0
        self.score_right = 0
        self._cached_state = None
        self._state_dirty = True

    def update(self, left_move=None, right_move=None):
        """Updates game state for one frame. Returns event dict or None."""
        # Update paddle speeds based on ball velocity
        speed_ratio = abs(self.ball.vel_x) / config.BALL_SPEED_X
        paddle_speed = min(config.PADDLE_SPEED * speed_ratio, config.PADDLE_MAX_SPEED)
        self.left_paddle.speed = paddle_speed
        self.right_paddle.speed = paddle_speed

        # Move paddles
        if left_move == "UP":
            self.left_paddle.move(up=True)
            self._state_dirty = True
        elif left_move == "DOWN":
            self.left_paddle.move(up=False)
            self._state_dirty = True
        
        if right_move == "UP":
            self.right_paddle.move(up=True)
            self._state_dirty = True
        elif right_move == "DOWN":
            self.right_paddle.move(up=False)
            self._state_dirty = True

        # Move ball
        self.ball.move()
        self._state_dirty = True

        # Check collisions
        hit_left = CollisionDetector.check_paddle_collision(self.ball, self.left_paddle, is_left=True)
        hit_right = CollisionDetector.check_paddle_collision(self.ball, self.right_paddle, is_left=False)
        CollisionDetector.check_wall_collision(self.ball)

        # Check scoring
        left_scored, right_scored = ScoreManager.check_scoring(self.ball, self.score_left, self.score_right)
        
        score_data = None
        if left_scored:
            self.score_left += 1
            self.ball.reset()
            self._state_dirty = True
            score_data = self.get_state()
            score_data["scored"] = "left"
        elif right_scored:
            self.score_right += 1
            self.ball.reset()
            self._state_dirty = True
            score_data = self.get_state()
            score_data["scored"] = "right"
        
        # Check for game over
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
            
        return score_data

    def get_state(self):
        """Returns cached state or creates new one if dirty."""
        if self._cached_state is None or self._state_dirty:
            self._cached_state = {
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
            self._state_dirty = False
        return self._cached_state.copy()  # Return copy to prevent mutation

