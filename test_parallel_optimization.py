import unittest
import os
import pickle
import neat
import config
from parallel_engine import ParallelGameEngine

class TestParallelOptimization(unittest.TestCase):
    def setUp(self):
        # Create dummy config
        self.config_path = "test_neat_config.txt"
        with open(self.config_path, "w") as f:
            f.write("""
[NEAT]
fitness_criterion     = max
fitness_threshold     = 10000
pop_size              = 50
reset_on_extinction   = False
no_fitness_termination = False

[DefaultGenome]
single_structural_mutation = False
structural_mutation_surer = default

# activation options
activation_default      = random
activation_mutate_rate  = 0.0
activation_options      = sigmoid tanh relu

# node aggregation options
aggregation_default     = sum
aggregation_mutate_rate = 0.0
aggregation_options     = sum

# node bias options
bias_init_mean          = 0.0
bias_init_stdev         = 1.0
bias_init_type          = gaussian
bias_max_value          = 30.0
bias_min_value          = -30.0
bias_mutate_power       = 0.5
bias_mutate_rate        = 0.7
bias_replace_rate       = 0.1

# genome compatibility options
compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5

# connection add/remove rates
conn_add_prob           = 0.5
conn_delete_prob        = 0.5

# connection enable options
enabled_default         = True
enabled_mutate_rate     = 0.01
enabled_rate_to_true_add = 0.0
enabled_rate_to_false_add = 0.0
enabled_rate_to_true_delete = 0.0
enabled_rate_to_false_delete = 0.0

# RECURRENT NETWORK ENABLED
feed_forward            = False
initial_connection      = full

# node add/remove rates
node_add_prob           = 0.2
node_delete_prob        = 0.2

# network parameters
num_hidden              = 1
num_inputs              = 8
num_outputs             = 3

# node response options
response_init_mean      = 1.0
response_init_stdev     = 0.0
response_init_type      = gaussian
response_max_value      = 30.0
response_min_value      = -30.0
response_mutate_power   = 0.0
response_mutate_rate    = 0.0
response_replace_rate   = 0.0

# weight options
weight_init_mean        = 0.0
weight_init_stdev       = 1.0
weight_init_type        = gaussian
weight_max_value        = 30
weight_min_value        = -30
weight_mutate_power     = 0.5
weight_mutate_rate      = 0.8
weight_replace_rate     = 0.1

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = max
max_stagnation       = 20
species_elitism      = 2

[DefaultReproduction]
elitism            = 2
survival_threshold = 0.2
min_species_size   = 1
""")
        
        # Create dummy genomes using Population to handle innovation tracking
        self.neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  self.config_path)
        
        pop = neat.Population(self.neat_config)
        # Run for 0 generations just to initialize
        # Actually, we just need to access the population
        # But Population doesn't expose genomes directly until run?
        # We can just create a reproduction object and create_new
        
        reproduction = neat.DefaultReproduction(self.neat_config.reproduction_config,
                                                self.neat_config.reproduction_reporters,
                                                self.neat_config.stagnation_config)
        
        # Create a dictionary of genomes
        genomes = reproduction.create_new(self.neat_config.genome_type, 
                                          self.neat_config.genome_config, 
                                          2)
        
        genome_list = list(genomes.values())
        self.g1 = genome_list[0]
        self.g2 = genome_list[1]
        
        self.p1_path = "test_p1.pkl"
        self.p2_path = "test_p2.pkl"
        
        with open(self.p1_path, "wb") as f:
            pickle.dump(self.g1, f)
        with open(self.p2_path, "wb") as f:
            pickle.dump(self.g2, f)
            
    def tearDown(self):
        # Cleanup
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.p1_path):
            os.remove(self.p1_path)
        if os.path.exists(self.p2_path):
            os.remove(self.p2_path)

    def test_play_match(self):
        print("Testing Fast Match Execution...")
        engine = ParallelGameEngine(visual_mode=False, target_fps=0)
        engine.start()
        
        match_config = {
            "p1_path": os.path.abspath(self.p1_path),
            "p2_path": os.path.abspath(self.p2_path),
            "neat_config_path": os.path.abspath(self.config_path),
            "metadata": {"test": True}
        }
        
        import time
        start = time.time()
        result = engine.play_match(match_config)
        duration = time.time() - start
        
        engine.stop()
        
        print(f"Match finished in {duration:.4f}s")
        print(f"Result: {result['score_left']} - {result['score_right']}")
        
        self.assertIsNotNone(result)
        self.assertIn("score_left", result)
        self.assertIn("score_right", result)
        self.assertIn("stats", result)
        self.assertIn("match_metadata", result)
        
        # Ensure match actually ran (scores might be 0-0 if AI is dumb, but stats should exist)
        self.assertIsNotNone(result["stats"]["left"])
        
        # Verify speed (should be very fast, definitely under 1s for a simple match, 
        # but max score is 11, so it might take a bit if they rally. 
        # But with random weights they probably miss instantly.)
        self.assertLess(duration, 5.0) 

if __name__ == '__main__':
    unittest.main()
