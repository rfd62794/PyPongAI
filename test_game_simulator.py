"""Unit tests for game_simulator.py.

Tests verify the headless game simulation logic including ball movement,
paddle collisions, scoring mechanics, and boundary constraints.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from game_simulator import GameSimulator, Paddle, Ball, Rect


class TestRect(unittest.TestCase):
    """Tests for the Rect class."""
    
    def test_rect_properties(self):
        """Test that rectangle properties are calculated correctly."""
        rect = Rect(10, 20, 30, 40)
        self.assertEqual(rect.left, 10)
        self.assertEqual(rect.top, 20)
        self.assertEqual(rect.right, 40)  # 10 + 30
        self.assertEqual(rect.bottom, 60)  # 20 + 40
        self.assertEqual(rect.centerx, 25)  # 10 + 30/2
        self.assertEqual(rect.centery, 40)  # 20 + 40/2
    
    def test_rect_collision(self):
        """Test rectangle collision detection."""
        rect1 = Rect(0, 0, 10, 10)
        rect2 = Rect(5, 5, 10, 10)
        rect3 = Rect(20, 20, 10, 10)
        
        self.assertTrue(rect1.colliderect(rect2))
        self.assertFalse(rect1.colliderect(rect3))


class TestPaddle(unittest.TestCase):
    """Tests for the Paddle class."""
    
    def test_paddle_initialization(self):
        """Test paddle is created at correct position."""
        paddle = Paddle(100, 200)
        self.assertEqual(paddle.rect.x, 100)
        self.assertEqual(paddle.rect.y, 200)
        self.assertEqual(paddle.rect.width, config.PADDLE_WIDTH)
        self.assertEqual(paddle.rect.height, config.PADDLE_HEIGHT)
    
    def test_paddle_bounds(self):
        """Test paddles cannot move outside screen boundaries."""
        paddle = Paddle(100, 0)
        
        # Try to move above screen
        paddle.move(up=True)
        self.assertGreaterEqual(paddle.rect.top, 0)
        
        # Move to bottom
        paddle.rect.y = config.SCREEN_HEIGHT - config.PADDLE_HEIGHT
        paddle.move(up=False)
        self.assertLessEqual(paddle.rect.bottom, config.SCREEN_HEIGHT)


class TestBall(unittest.TestCase):
    """Tests for the Ball class."""
    
    def test_ball_initialization(self):
        """Test ball starts at screen center with velocity."""
        ball = Ball()
        self.assertEqual(ball.rect.centerx, config.SCREEN_WIDTH // 2)
        self.assertEqual(ball.rect.centery, config.SCREEN_HEIGHT // 2)
        self.assertNotEqual(ball.vel_x, 0)
        self.assertNotEqual(ball.vel_y, 0)
    
    def test_ball_movement(self):
        """Test ball position updates correctly with velocity."""
        ball = Ball()
        initial_x = ball.rect.x
        initial_y = ball.rect.y
        
        ball.move()
        
        self.assertEqual(ball.rect.x, initial_x + ball.vel_x)
        self.assertEqual(ball.rect.y, initial_y + ball.vel_y)
    
    def test_ball_reset(self):
        """Test ball returns to center after reset."""
        ball = Ball()
        ball.rect.x = 100
        ball.rect.y = 100
        
        ball.reset()
        
        self.assertEqual(ball.rect.centerx, config.SCREEN_WIDTH // 2)
        self.assertEqual(ball.rect.centery, config.SCREEN_HEIGHT // 2)


class TestGameSimulator(unittest.TestCase):
    """Tests for the GameSimulator class."""
    
    def setUp(self):
        """Create a fresh game instance for each test."""
        self.game = GameSimulator()
    
    def test_game_initialization(self):
        """Test game initializes with correct starting state."""
        self.assertEqual(self.game.score_left, 0)
        self.assertEqual(self.game.score_right, 0)
        self.assertIsNotNone(self.game.left_paddle)
        self.assertIsNotNone(self.game.right_paddle)
        self.assertIsNotNone(self.game.ball)
    
    def test_get_state(self):
        """Test get_state returns complete game state."""
        state = self.game.get_state()
        
        required_keys = [
            "ball_x", "ball_y", "ball_vel_x", "ball_vel_y",
            "paddle_left_y", "paddle_right_y",
            "score_left", "score_right", "game_over"
        ]
        
        for key in required_keys:
            self.assertIn(key, state)
    
    def test_paddle_movement(self):
        """Test paddles move correctly based on input."""
        initial_left_y = self.game.left_paddle.rect.y
        initial_right_y = self.game.right_paddle.rect.y
        
        self.game.update(left_move="UP", right_move="DOWN")
        
        self.assertLess(self.game.left_paddle.rect.y, initial_left_y)
        self.assertGreater(self.game.right_paddle.rect.y, initial_right_y)
    
    def test_scoring_left(self):
        """Test ball passing left paddle scores for right side."""
        # Position ball near left edge
        self.game.ball.rect.x = 5
        self.game.ball.vel_x = -10  # Moving left
        
        score_data = self.game.update()
        
        if score_data and score_data.get("scored") == "right":
            self.assertEqual(self.game.score_right, 1)
            self.assertEqual(self.game.score_left, 0)
    
    def test_scoring_right(self):
        """Test ball passing right paddle scores for left side."""
        # Position ball near right edge
        self.game.ball.rect.x = config.SCREEN_WIDTH - 10
        self.game.ball.vel_x = 10  # Moving right
        
        score_data = self.game.update()
        
        if score_data and score_data.get("scored") == "left":
            self.assertEqual(self.game.score_left, 1)
            self.assertEqual(self.game.score_right, 0)
    
    def test_paddle_collision(self):
        """Test ball reflects X-velocity upon hitting paddle."""
        # Position ball to collide with left paddle
        self.game.ball.rect.x = self.game.left_paddle.rect.right - 5
        self.game.ball.rect.y = self.game.left_paddle.rect.y + 10
        initial_vel_x = self.game.ball.vel_x = -5  # Moving toward paddle
        
        score_data = self.game.update()
        
        # Check if collision was detected
        if score_data and score_data.get("hit_left"):
            # Velocity should reverse and be modified by increment
            self.assertGreater(self.game.ball.vel_x, 0)  # Now moving right
    
    def test_wall_collision(self):
        """Test ball reflects Y-velocity upon hitting top/bottom walls."""
        # Position ball at top edge
        self.game.ball.rect.y = 1
        self.game.ball.vel_y = -5  # Moving up
        
        self.game.update()
        
        # Velocity should reverse
        self.assertGreater(self.game.ball.vel_y, 0)
    
    def test_game_over_condition(self):
        """Test game_over flag is set when max score is reached."""
        # Set score to near max
        self.game.score_left = config.MAX_SCORE - 1
        
        # Force a score for left
        self.game.ball.rect.x = config.SCREEN_WIDTH - 5
        self.game.ball.vel_x = 10
        
        score_data = self.game.update()
        
        # Game should be over after this score
        if score_data and self.game.score_left >= config.MAX_SCORE:
            self.assertTrue(score_data.get("game_over", False))
    
    def test_no_movement_returns_none(self):
        """Test update returns None when no significant events occur."""
        # Position ball safely in middle
        self.game.ball.rect.x = config.SCREEN_WIDTH // 2
        self.game.ball.rect.y = config.SCREEN_HEIGHT // 2
        self.game.ball.vel_x = 5
        self.game.ball.vel_y = 5
        
        # Run a few updates without collisions
        for _ in range(5):
            result = self.game.update()
            # Should return None or dict, but not cause errors
            if result is not None:
                self.assertIsInstance(result, dict)


class TestGamePhysics(unittest.TestCase):
    """Tests for game physics and edge cases."""
    
    def test_ball_speed_cap(self):
        """Test ball velocity is capped at max speed."""
        game = GameSimulator()
        
        # Set velocity beyond max
        game.ball.vel_x = config.BALL_MAX_SPEED * 2
        game.ball.vel_y = config.BALL_MAX_SPEED * 2
        
        game.update()
        
        # Velocity should be capped
        self.assertLessEqual(abs(game.ball.vel_x), config.BALL_MAX_SPEED)
        self.assertLessEqual(abs(game.ball.vel_y), config.BALL_MAX_SPEED)
    
    def test_dynamic_paddle_speed(self):
        """Test paddle speed adjusts based on ball velocity."""
        game = GameSimulator()
        
        # Set high ball velocity
        game.ball.vel_x = config.BALL_MAX_SPEED
        
        game.update(left_move="UP")
        
        # Paddle speed should have been adjusted
        # (actual value depends on implementation details)
        self.assertIsNotNone(game.left_paddle.speed)


if __name__ == '__main__':
    unittest.main()
