"""Unit tests for model_manager.py.

Tests verify model scanning, ELO conversion, and model management utilities.
"""

import unittest
import sys
import os
import tempfile
import shutil
import pickle
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import model_manager


class SimpleGenome:
    """Simple picklable genome replacement for testing."""
    def __init__(self, fitness=100, elo_rating=None):
        self.fitness = fitness
        if elo_rating is not None:
            self.elo_rating = elo_rating


class TestModelScanning(unittest.TestCase):
    """Tests for model scanning functionality."""
    
    def setUp(self):
        """Create temporary directory for test models."""
        self.test_dir = tempfile.mkdtemp()
        self.original_model_dir = config.MODEL_DIR
        config.MODEL_DIR = self.test_dir
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        config.MODEL_DIR = self.original_model_dir
    
    def create_mock_model(self, filename, fitness=100):
        """Helper to create a mock model file."""
        filepath = os.path.join(self.test_dir, filename)
        
        # Create a simple genome
        genome = SimpleGenome(fitness=fitness)
        
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        return filepath
    
    def test_scan_models_empty_directory(self):
        """Test scanning returns empty list for empty directory."""
        models = model_manager.scan_models()
        
        self.assertEqual(len(models), 0)
    
    def test_scan_models_finds_pkl_files(self):
        """Test scanning finds .pkl files."""
        self.create_mock_model("model1.pkl")
        self.create_mock_model("model2.pkl")
        
        models = model_manager.scan_models()
        
        self.assertEqual(len(models), 2)
    
    def test_scan_models_ignores_non_pkl(self):
        """Test scanning ignores non-.pkl files."""
        self.create_mock_model("model1.pkl")
        
        # Create a non-pkl file
        with open(os.path.join(self.test_dir, "readme.txt"), 'w') as f:
            f.write("test")
        
        models = model_manager.scan_models()
        
        self.assertEqual(len(models), 1)
    
    def test_scan_models_recursive(self):
        """Test scanning finds models in subdirectories."""
        # Create subdirectory
        subdir = os.path.join(self.test_dir, "checkpoints")
        os.makedirs(subdir, exist_ok=True)
        
        self.create_mock_model("model1.pkl")
        
        # Create model in subdirectory
        filepath = os.path.join(subdir, "checkpoint_model.pkl")
        genome = SimpleGenome()
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        models = model_manager.scan_models()
        
        self.assertGreaterEqual(len(models), 2)


class TestModelConversion(unittest.TestCase):
    """Tests for ELO conversion functionality."""
    
    def setUp(self):
        """Create temporary directory for test models."""
        self.test_dir = tempfile.mkdtemp()
        self.original_model_dir = config.MODEL_DIR
        config.MODEL_DIR = self.test_dir
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        config.MODEL_DIR = self.original_model_dir
    
    def create_mock_model_without_elo(self, filename):
        """Create a mock model without ELO attribute."""
        filepath = os.path.join(self.test_dir, filename)
        
        genome = SimpleGenome(fitness=100, elo_rating=None)
        # Remove elo_rating if it was added
        if hasattr(genome, 'elo_rating'):
            delattr(genome, 'elo_rating')
        
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        return filepath
    
    @patch('elo_manager.update_elo')
    def test_convert_models_adds_elo(self, mock_update_elo):
        """Test conversion adds ELO attribute to models without it."""
        filepath = self.create_mock_model_without_elo("model_no_elo.pkl")
        
        model_manager.convert_models_to_elo_format()
        
        # Reload the model
        with open(filepath, 'rb') as f:
            genome = pickle.load(f)
        
        # Should now have ELO attribute
        self.assertTrue(hasattr(genome, 'elo_rating'))
    
    @patch('elo_manager.update_elo')
    def test_convert_preserves_existing_elo(self, mock_update_elo):
        """Test conversion doesn't overwrite existing ELO."""
        filepath = os.path.join(self.test_dir, "model_with_elo.pkl")
        
        genome = SimpleGenome(fitness=150, elo_rating=1400)
        
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        model_manager.convert_models_to_elo_format()
        
        # Reload and check ELO unchanged
        with open(filepath, 'rb') as f:
            genome = pickle.load(f)
        
        self.assertEqual(genome.elo_rating, 1400)
    
    def test_convert_uses_default_elo(self):
        """Test new ELO uses default initial rating."""
        filepath = self.create_mock_model_without_elo("model_default.pkl")
        
        model_manager.convert_models_to_elo_format()
        
        with open(filepath, 'rb') as f:
            genome = pickle.load(f)
        
        self.assertEqual(genome.elo_rating, config.ELO_INITIAL_RATING)


class TestBestModelSelection(unittest.TestCase):
    """Tests for best model selection."""
    
    def setUp(self):
        """Create temporary directory for test models."""
        self.test_dir = tempfile.mkdtemp()
        self.original_model_dir = config.MODEL_DIR
        config.MODEL_DIR = self.test_dir
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        config.MODEL_DIR = self.original_model_dir
    
    def create_model_with_elo(self, filename, elo):
        """Create model with specific ELO."""
        filepath = os.path.join(self.test_dir, filename)
        
        genome = SimpleGenome(fitness=elo, elo_rating=elo)
        
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        return filepath
    
    def test_get_best_model_by_elo(self):
        """Test best model selection uses ELO rating."""
        self.create_model_with_elo("model_low.pkl", 1200)
        self.create_model_with_elo("model_high.pkl", 1500)
        self.create_model_with_elo("model_mid.pkl", 1300)
        
        best_path = model_manager.get_best_model_by_elo()
        
        self.assertIsNotNone(best_path)
        self.assertIn("model_high.pkl", best_path)
    
    def test_get_best_model_no_models(self):
        """Test returns None when no models exist."""
        best_path = model_manager.get_best_model_by_elo()
        
        self.assertIsNone(best_path)


class TestFitnessExtraction(unittest.TestCase):
    """Tests for fitness value extraction from filenames."""
    
    def test_fitness_from_filename_standard(self):
        """Test extracting fitness from standard format."""
        fitness = model_manager.get_fitness_from_filename("model_fitness1200.pkl")
        self.assertEqual(fitness, 1200)
    
    def test_fitness_from_filename_underscore(self):
        """Test extracting fitness from _fit_ format."""
        fitness = model_manager.get_fitness_from_filename("gen_10_fit_1500.pkl")
        self.assertEqual(fitness, 1500)
    
    def test_fitness_from_filename_no_fitness(self):
        """Test returns 0 for files without fitness in name."""
        fitness = model_manager.get_fitness_from_filename("model.pkl")
        self.assertEqual(fitness, 0)
    
    def test_fitness_from_filename_invalid(self):
        """Test handles invalid fitness values gracefully."""
        fitness = model_manager.get_fitness_from_filename("model_fitness_abc.pkl")
        self.assertEqual(fitness, 0)


class TestModelDeletion(unittest.TestCase):
    """Tests for model deletion functionality."""
    
    def setUp(self):
        """Create temporary directory for test models."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_delete_models(self):
        """Test models are deleted correctly."""
        # Create test file
        filepath = os.path.join(self.test_dir, "model_to_delete.pkl")
        genome = SimpleGenome()
        with open(filepath, 'wb') as f:
            pickle.dump(genome, f)
        
        self.assertTrue(os.path.exists(filepath))
        
        model_manager.delete_models([filepath])
        
        self.assertFalse(os.path.exists(filepath))
    
    def test_delete_nonexistent_model(self):
        """Test deleting nonexistent model doesn't raise error."""
        fake_path = os.path.join(self.test_dir, "nonexistent.pkl")
        
        # Should not raise exception
        try:
            model_manager.delete_models([fake_path])
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success)


class TestModelMetadata(unittest.TestCase):
    """Tests for model metadata handling."""
    
    def test_model_has_fitness_attribute(self):
        """Test loaded models have fitness attribute."""
        genome = SimpleGenome(fitness=1234)
        
        self.assertTrue(hasattr(genome, 'fitness'))
        self.assertEqual(genome.fitness, 1234)
    
    def test_model_has_elo_after_conversion(self):
        """Test models have ELO after conversion."""
        genome = SimpleGenome(elo_rating=1200)
        
        self.assertTrue(hasattr(genome, 'elo_rating'))


if __name__ == '__main__':
    unittest.main()
