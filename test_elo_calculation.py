import unittest
import math

# Replicating the logic I plan to put in ai_module.py
def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def calculate_new_rating(rating, expected_score, actual_score, k_factor=32):
    return rating + k_factor * (actual_score - expected_score)

class TestELOCalculation(unittest.TestCase):
    def test_expected_score_equal_ratings(self):
        # If ratings are equal, expected score should be 0.5
        expected = calculate_expected_score(1200, 1200)
        self.assertAlmostEqual(expected, 0.5)

    def test_expected_score_higher_rating(self):
        # Higher rating should have higher expected score
        expected = calculate_expected_score(1600, 1200)
        self.assertGreater(expected, 0.5)
        
        # Specific value check: 1/(1+10^(-1)) = 1/(1+0.1) = 1/1.1 ~= 0.909
        self.assertAlmostEqual(expected, 1 / (1 + 10 ** ((1200 - 1600) / 400)), places=3)

    def test_rating_update_win(self):
        # Player A (1200) wins against Player B (1200)
        # Expected score = 0.5
        # Actual score = 1
        # New Rating = 1200 + 32 * (1 - 0.5) = 1200 + 16 = 1216
        new_rating = calculate_new_rating(1200, 0.5, 1, k_factor=32)
        self.assertEqual(new_rating, 1216)

    def test_rating_update_loss(self):
        # Player A (1200) loses against Player B (1200)
        # Expected score = 0.5
        # Actual score = 0
        # New Rating = 1200 + 32 * (0 - 0.5) = 1200 - 16 = 1184
        new_rating = calculate_new_rating(1200, 0.5, 0, k_factor=32)
        self.assertEqual(new_rating, 1184)

    def test_rating_update_draw(self):
        # Player A (1200) draws against Player B (1200)
        # Expected score = 0.5
        # Actual score = 0.5
        # New Rating = 1200 + 32 * (0.5 - 0.5) = 1200
        new_rating = calculate_new_rating(1200, 0.5, 0.5, k_factor=32)
        self.assertEqual(new_rating, 1200)

if __name__ == '__main__':
    unittest.main()
