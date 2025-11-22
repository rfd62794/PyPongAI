import unittest
from unittest.mock import MagicMock, patch
from ai import ai_module
from core import config

class MockGenome:
    def __init__(self, key):
        self.key = key
        self.fitness = None

class TestELOIntegration(unittest.TestCase):
    @patch('ai_module.neat.nn.FeedForwardNetwork.create')
    @patch('ai_module.game_engine.Game')
    def test_eval_genomes_competitive_elo(self, mock_game_class, mock_net_create):
        # Setup Mocks
        mock_net = MagicMock()
        # Mock activate to return a valid output (e.g., [1, 0, 0] for UP)
        mock_net.activate.return_value = [1.0, 0.0, 0.0] 
        mock_net_create.return_value = mock_net
        
        # Mock Game
        mock_game = MagicMock()
        mock_game_class.return_value = mock_game
        
        # Mock Game State
        mock_game.get_state.return_value = {
            "paddle_left_y": 100, "paddle_right_y": 100,
            "ball_x": 400, "ball_y": 300,
            "ball_vel_x": 5, "ball_vel_y": 5
        }
        
        # Scenario: Left wins immediately
        # Match 1: G1 (Left) vs G2 (Right). G1 wins -> "left"
        # Match 2: G2 (Left) vs G1 (Right). G1 wins -> "right"
        mock_game.update.side_effect = [
            {"scored": "left", "hit_left": True},  # Match 1: G1 wins
            {"scored": "right", "hit_left": True}, # Match 2: G2 loses (G1 wins)
            {"scored": "left", "hit_left": True}, 
            {"scored": "left", "hit_left": True}
        ]
        
        # Create Genomes
        genomes = [(1, MockGenome(1)), (2, MockGenome(2))]
        
        # Run Evaluation
        ai_module.eval_genomes_competitive(genomes, config_neat=None)
        
        g1 = genomes[0][1]
        g2 = genomes[1][1]
        
        # Verify ELO attributes were added
        self.assertTrue(hasattr(g1, 'elo_rating'))
        self.assertTrue(hasattr(g2, 'elo_rating'))
        
        # Verify Ratings Changed
        # G1 won, so should be > 1200
        self.assertGreater(g1.elo_rating, 1200)
        # G2 lost, so should be < 1200
        self.assertLess(g2.elo_rating, 1200)
        
        # Verify Fitness is set to ELO
        self.assertEqual(g1.fitness, g1.elo_rating)
        self.assertEqual(g2.fitness, g2.elo_rating)
        
        print(f"G1 Rating: {g1.elo_rating}, Fitness: {g1.fitness}")
        print(f"G2 Rating: {g2.elo_rating}, Fitness: {g2.fitness}")

if __name__ == '__main__':
    unittest.main()
