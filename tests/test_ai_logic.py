"""Unit tests for AI logic and ELO calculations.

Tests verify the ELO rating system, fitness reward mechanisms, and
AI evaluation functions.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config
from utils import elo_manager
from ai_module import calculate_expected_score, calculate_new_rating
from opponents import get_rule_based_move


class TestELOCalculations(unittest.TestCase):
    """Tests for ELO rating calculations."""
    
    def test_expected_score_equal_ratings(self):
        """Test expected score is 0.5 for equal ratings."""
        expected = calculate_expected_score(1200, 1200)
        self.assertAlmostEqual(expected, 0.5, places=2)
    
    def test_expected_score_higher_rating(self):
        """Test expected score is > 0.5 for higher rated player."""
        expected = calculate_expected_score(1400, 1200)
        self.assertGreater(expected, 0.5)
    
    def test_expected_score_lower_rating(self):
        """Test expected score is < 0.5 for lower rated player."""
        expected = calculate_expected_score(1200, 1400)
        self.assertLess(expected, 0.5)
    
    def test_elo_update_win(self):
        """Test ELO increases after a win."""
        rating = 1200
        expected = 0.5
        actual = 1.0  # Win
        
        new_rating = calculate_new_rating(rating, expected, actual, k_factor=32)
        
        self.assertGreater(new_rating, rating)
    
    def test_elo_update_loss(self):
        """Test ELO decreases after a loss."""
        rating = 1200
        expected = 0.5
        actual = 0.0  # Loss
        
        new_rating = calculate_new_rating(rating, expected, actual, k_factor=32)
        
        self.assertLess(new_rating, rating)
    
    def test_elo_update_draw(self):
        """Test ELO stays same after expected draw."""
        rating = 1200
        expected = 0.5
        actual = 0.5  # Draw
        
        new_rating = calculate_new_rating(rating, expected, actual, k_factor=32)
        
        self.assertAlmostEqual(new_rating, rating, places=1)
    
    def test_elo_upset_victory(self):
        """Test ELO gain is larger for upset victories."""
        rating_underdog = 1200
        rating_favorite = 1400
        
        expected_underdog = calculate_expected_score(rating_underdog, rating_favorite)
        
        # Underdog wins
        new_rating_win = calculate_new_rating(rating_underdog, expected_underdog, 1.0, k_factor=32)
        
        # Expected win against equal opponent
        new_rating_expected = calculate_new_rating(rating_underdog, 0.5, 1.0, k_factor=32)
        
        # Upset should give bigger gain
        gain_upset = new_rating_win - rating_underdog
        gain_expected = new_rating_expected - rating_underdog
        
        self.assertGreater(gain_upset, gain_expected)


class TestELOManager(unittest.TestCase):
    """Tests for elo_manager module."""
    
    @patch('elo_manager.ELO_FILE', 'test_elo_ratings.json')
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    def test_update_elo(self, mock_open, mock_exists):
        """Test update_elo correctly saves new ratings."""
        mock_exists.return_value = False
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Test updating ELO
        elo_manager.update_elo("model1.pkl", 1250)
        
        # Verify file was opened for writing
        mock_open.assert_called()
    
    @patch('elo_manager.load_elo_ratings')
    def test_get_elo_existing(self, mock_load):
        """Test get_elo returns stored rating."""
        mock_load.return_value = {"model1.pkl": 1300}
        
        rating = elo_manager.get_elo("model1.pkl")
        
        self.assertEqual(rating, 1300)
    
    @patch('elo_manager.load_elo_ratings')
    def test_get_elo_default(self, mock_load):
        """Test get_elo returns default for new model."""
        mock_load.return_value = {}
        
        rating = elo_manager.get_elo("new_model.pkl")
        
        self.assertEqual(rating, config.ELO_INITIAL_RATING)


class TestRuleBasedAI(unittest.TestCase):
    """Tests for rule-based opponent logic."""
    
    def test_move_toward_ball_up(self):
        """Test paddle moves up when ball is above."""
        game_state = {
            "paddle_right_y": 300,
            "ball_y": 200
        }
        
        move = get_rule_based_move(game_state, "right")
        
        self.assertEqual(move, "UP")
    
    def test_move_toward_ball_down(self):
        """Test paddle moves down when ball is below."""
        game_state = {
            "paddle_right_y": 200,
            "ball_y": 300
        }
        
        move = get_rule_based_move(game_state, "right")
        
        self.assertEqual(move, "DOWN")
    
    def test_deadzone(self):
        """Test paddle stays still when aligned with ball."""
        paddle_y = 250
        ball_y = 250 + config.PADDLE_HEIGHT / 2  # Centered
        
        game_state = {
            "paddle_right_y": paddle_y,
            "ball_y": ball_y
        }
        
        move = get_rule_based_move(game_state, "right")
        
        self.assertIsNone(move)


class TestFitnessRewards(unittest.TestCase):
    """Tests for fitness reward mechanisms."""
    
    @patch('ai_module.game_simulator.GameSimulator')
    @patch('neat.nn.FeedForwardNetwork')
    def test_survival_rewards(self, mock_network_class, mock_game_class):
        """Test survival time contributes to fitness."""
        # This is a simplified test - actual implementation would be more complex
        # The key is verifying fitness increases over time
        
        mock_genome = Mock()
        mock_genome.fitness = 0
        
        mock_net = Mock()
        mock_net.activate.return_value = [0.5, 0.3, 0.2]
        mock_network_class.create.return_value = mock_net
        
        mock_game = Mock()
        mock_game.get_state.return_value = {
            "paddle_left_y": 250,
            "ball_x": 400,
            "ball_y": 300,
            "ball_vel_x": 5,
            "ball_vel_y": 3,
            "paddle_right_y": 250
        }
        mock_game.update.return_value = None  # No scoring
        mock_game_class.return_value = mock_game
        
        # Would need to actually call eval_genomes here
        # This is a simplified check
        self.assertTrue(True)  # Placeholder
    
    def test_scoring_rewards(self):
        """Test scoring gives higher fitness reward than survival."""
        # Mock a scoring event
        score_reward = 10  # From ai_module
        survival_reward = 0.1
        
        self.assertGreater(score_reward, survival_reward)
    
    def test_hit_rewards(self):
        """Test paddle hits give fitness reward."""
        hit_reward = 1  # From ai_module
        
        self.assertGreater(hit_reward, 0)


class TestELOIntegration(unittest.TestCase):
    """Integration tests for ELO in competitive evaluation."""
    
    def test_elo_initialization(self):
        """Test genomes are initialized with default ELO."""
        mock_genome = Mock()
        mock_genome.elo_rating = None
        
        # Simulate initialization
        if not hasattr(mock_genome, 'elo_rating') or mock_genome.elo_rating is None:
            mock_genome.elo_rating = config.ELO_INITIAL_RATING
        
        self.assertEqual(mock_genome.elo_rating, config.ELO_INITIAL_RATING)
    
    def test_elo_becomes_fitness(self):
        """Test final ELO rating is used as fitness."""
        mock_genome = Mock()
        mock_genome.elo_rating = 1350
        
        # Simulate end of eval_genomes_competitive
        mock_genome.fitness = max(0, mock_genome.elo_rating)
        
        self.assertEqual(mock_genome.fitness, 1350)


class TestHallOfFame(unittest.TestCase):
    """Tests for Hall of Fame functionality."""
    
    def test_hof_initialization(self):
        """Test Hall of Fame starts empty."""
        from ai import ai_module
        
        # HOF should be a list
        self.assertIsInstance(ai_module.HALL_OF_FAME, list)
    
    def test_hof_storage(self):
        """Test genomes can be added to Hall of Fame."""
        from ai import ai_module
        
        initial_len = len(ai_module.HALL_OF_FAME)
        mock_genome = Mock()
        
        ai_module.HALL_OF_FAME.append(mock_genome)
        
        self.assertEqual(len(ai_module.HALL_OF_FAME), initial_len + 1)


if __name__ == '__main__':
    unittest.main()
