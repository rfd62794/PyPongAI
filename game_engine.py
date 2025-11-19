# game_engine.py
import pygame
import random
import config

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
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

    def draw(self, screen):
        pygame.draw.rect(screen, config.WHITE, self.rect)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(config.SCREEN_WIDTH // 2 - config.BALL_RADIUS,
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

    def draw(self, screen):
        pygame.draw.ellipse(screen, config.WHITE, self.rect)

class Game:
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

        # Paddle Collision
        # Left Paddle
        # Paddle Collision
        # Left Paddle
        if self.ball.rect.colliderect(self.left_paddle.rect):
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.left = self.left_paddle.rect.right # Prevent sticking
        
        # Right Paddle
        if self.ball.rect.colliderect(self.right_paddle.rect):
            self.ball.vel_x *= -config.BALL_SPEED_INCREMENT
            self.ball.vel_y *= config.BALL_SPEED_INCREMENT
            self.ball.rect.right = self.right_paddle.rect.left # Prevent sticking
            
        # Cap Speed
        self.ball.vel_x = max(min(self.ball.vel_x, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
        self.ball.vel_y = max(min(self.ball.vel_y, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)

        # Scoring
        score_data = None
        if self.ball.rect.left <= 0:
            # Right scores
            self.score_right += 1
            score_data = self.get_state()
            self.ball.reset()
        elif self.ball.rect.right >= config.SCREEN_WIDTH:
            # Left scores
            self.score_left += 1
            score_data = self.get_state()
            self.ball.reset()
            
        # Check for Game Over
        if self.score_left >= config.MAX_SCORE or self.score_right >= config.MAX_SCORE:
            if score_data is None:
                 score_data = self.get_state()
            score_data["game_over"] = True
            
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

    def draw(self, screen):
        screen.fill(config.BLACK)
        
        # Draw Net
        pygame.draw.line(screen, config.WHITE, (config.SCREEN_WIDTH // 2, 0), (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT), 2)
        
        # Draw Scores
        if pygame.font.get_init():
            font = pygame.font.Font(None, 74)
            if str(self.score_left):
                text_left = font.render(str(self.score_left), 1, config.WHITE)
                screen.blit(text_left, (config.SCREEN_WIDTH // 4, 10))
            if str(self.score_right):
                text_right = font.render(str(self.score_right), 1, config.WHITE)
                screen.blit(text_right, (config.SCREEN_WIDTH * 3 // 4, 10))
        
        self.left_paddle.draw(screen)
        self.right_paddle.draw(screen)
        self.ball.draw(screen)
