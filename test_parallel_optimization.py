import unittest
import multiprocessing
import time
import os
import neat
import pickle
import config
from parallel_engine import ParallelGameEngine

class TestParallelOptimization(unittest.TestCase):
    def setUp(self):
        # Setup paths
        self.config_path = os.path.join(os.path.dirname(__file__), 'neat_config.txt')
        self.p1_path = "test_p1.pkl"
        self.p2_path = "test_p2.pkl"
        
        # Load real config
        self.neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  self.config_path)
        
        # Create dummy genomes using Population to handle innovation tracking
        pop = neat.Population(self.neat_config)
        
        # Create new genomes
        reproduction = neat.DefaultReproduction(self.neat_config.reproduction_config,
                                                pop.reporters,
                                                self.neat_config.stagnation_config)
        
        genomes = reproduction.create_new(self.neat_config.genome_type, 
                                          self.neat_config.genome_config, 
                                          2)
        
        genome_list = list(genomes.values())
        self.g1 = genome_list[0]
        self.g2 = genome_list[1]
        
        # Save genomes
        with open(self.p1_path, "wb") as f:
            pickle.dump(self.g1, f)
        with open(self.p2_path, "wb") as f:
            pickle.dump(self.g2, f)
            
        self.engine = ParallelGameEngine(visual_mode=False, target_fps=0)
        self.engine.start()

    def tearDown(self):
        self.engine.stop()
        if os.path.exists(self.p1_path):
            os.remove(self.p1_path)
        if os.path.exists(self.p2_path):
            os.remove(self.p2_path)
            
        # Clean up any created match recordings
        for f in os.listdir(config.LOGS_MATCHES_DIR):
            if f.startswith("match_") and "test_p1" in f:
                os.remove(os.path.join(config.LOGS_MATCHES_DIR, f))

    def test_play_match_recording_on(self):
        print("\nTesting Fast Match Execution (Recording ON)...")
        
        match_config = {
            "p1_path": os.path.abspath(self.p1_path),
            "p2_path": os.path.abspath(self.p2_path),
            "neat_config_path": os.path.abspath(self.config_path),
            "metadata": {"test": True}
        }
        
        print(f"Checking file existence (ON): {match_config['p1_path']}")
        print(f"Exists: {os.path.exists(match_config['p1_path'])}")
        
        start_time = time.time()
        result = self.engine.play_match(match_config, record_match=True)
        end_time = time.time()
        
        self.assertIsNotNone(result)
        self.assertIn("score_left", result)
        self.assertIn("score_right", result)
        self.assertIn("stats", result)
        self.assertIn("match_metadata", result)
        self.assertIsNotNone(result["match_metadata"]) # Should have metadata
        
        print(f"Match finished in {end_time - start_time:.4f}s")
        print(f"Result: {result['score_left']} - {result['score_right']}")
        
    def test_play_match_recording_off(self):
        print("\nTesting Fast Match Execution (Recording OFF)...")
        
        match_config = {
            "p1_path": os.path.abspath(self.p1_path),
            "p2_path": os.path.abspath(self.p2_path),
            "neat_config_path": os.path.abspath(self.config_path),
            "metadata": {"test": True}
        }
        
        start_time = time.time()
        result = self.engine.play_match(match_config, record_match=False)
        end_time = time.time()
        
        self.assertIsNotNone(result)
        self.assertIn("score_left", result)
        self.assertIn("score_right", result)
        self.assertIn("stats", result)
        self.assertIn("match_metadata", result)
        self.assertIsNone(result["match_metadata"]) # Should be None
        
        print(f"Match finished in {end_time - start_time:.4f}s")
        print(f"Result: {result['score_left']} - {result['score_right']}")

if __name__ == '__main__':
    unittest.main()
