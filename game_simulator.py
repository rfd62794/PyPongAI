import random
import config

class Rect:
    """
    A simple rectangle class to mimic pygame.Rect for headless simulation.
    """
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def left(self): return self.x
    @left.setter
    def left(self, value): self.x = value

    @property
    def right(self): return self.x + self.width
    @right.setter
    def right(self, value): self.x = value - self.width

    @property
    def top(self): return self.y
    @top.setter
    def top(self, value): self.y = value

    @property
    def bottom(self): return self.y + self.height
    @bottom.setter
    def bottom(self, value): self.y = value - self.height

    @property
    def centerx(self): return self.x + self.width / 2
    @centerx.setter
    def centerx(self, value): self.x = value - self.width / 2

    @property
    def centery(self): return self.y + self.height / 2
    @centery.setter
    def centery(self, value): self.y = value - self.height / 2
    
    @property
    def center(self): return (self.centerx, self.centery)
    @center.setter
    def center(self, value): 
        self.centerx = value[0]
        self.centery = value[1]

    def colliderect(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

class Paddle:
    def __init__(self, x, y):
        self.rect = Rect(x, y, config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
        self.speed = config.PADDLE_SPEED

    def move(self, up=True):
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
    def __init__(self):
        self.rect = Rect(config.SCREEN_WIDTH // 2 - config.BALL_RADIUS,
                         config.SCREEN_HEIGHT // 2 - config.BALL_RADIUS,
                         config.BALL_RADIUS * 2, config.BALL_RADIUS * 2)
        self.vel_x = config.BALL_SPEED_X * random.choice((1, -1))
        self.vel_y = config.BALL_SPEED_Y * random.choice((1, -1))

    def move(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def reset(self):
        self.rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        self.vel_x = config.BALL_SPEED_X * random.choice((1, -1))
        self.vel_y = config.BALL_SPEED_Y * random.choice((1, -1))

class GameSimulator:
    """
    Headless version of the Game class.
    """
    def __init__(self):
        self.left_paddle = Paddle(10, config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH, config.SCREEN_HEIGHT // 2 - config.PADDLE_HEIGHT // 2)
        self.ball = Ball()
        self.score_left = 0
        self.score_right = 0

    def update(self, left_move=None, right_move=None):
        """
        Updates the game state.
        left_move, right_move: 'UP', 'DOWN', or None
        Returns: score_data (dict) if a score occurred, else None
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

        # Paddle Collision
        # Left Paddle
        if self.ball.rect.colliderect(self.left_paddle.rect):
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.left = self.left_paddle.rect.right # Prevent sticking
            hit_left = True
        
        # Right Paddle
        if self.ball.rect.colliderect(self.right_paddle.rect):
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.right = self.right_paddle.rect.left # Prevent sticking
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
            
        return score_data

    def get_state(self):
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
