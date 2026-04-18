import os
import sys

# Add parent dir to path BEFORE importing patch_neat
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import patch_neat
import time
import neat
import multiprocessing as mp

from ai import ai_module
from core import config

def benchmark():
    print("PyPongAI TRAINING BENCHMARK")
    print("=" * 50)
    
    # Load NEAT config
    local_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(local_dir, 'neat_config.txt')
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
    
    # Create a small population of 10 genomes for benchmarking
    # (Matches current training defaults for quick tests)
    pop_size = 10
    p = neat.Population(config_neat)
    genomes = list(p.population.items())[:pop_size]
    
    print(f"Population Size: {pop_size}")
    print(f"Matches to simulate: {pop_size * 5} (5 opponents each)") # Approximate
    print("-" * 50)
    
    # Test 1: Serial Evaluation
    print("Running SERIAL Evaluation...")
    os.environ["PYPONGAI_PARALLEL_EVAL"] = "false"
    start_serial = time.time()
    ai_module.eval_genomes_competitive(genomes, config_neat)
    end_serial = time.time()
    serial_time = end_serial - start_serial
    print(f"Serial Time: {serial_time:.2f} seconds")
    
    # Test 2: Parallel Evaluation
    print("\nRunning PARALLEL Evaluation...")
    os.environ["PYPONGAI_PARALLEL_EVAL"] = "true"
    num_cpus = mp.cpu_count()
    print(f"CPUs Detected: {num_cpus}")
    
    start_parallel = time.time()
    ai_module.eval_genomes_competitive(genomes, config_neat)
    end_parallel = time.time()
    parallel_time = end_parallel - start_parallel
    
    print(f"Parallel Time: {parallel_time:.2f} seconds")
    
    # Comparison
    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print("-" * 50)
    print(f"TOTAL SPEEDUP: {speedup:.2f}x")
    print("=" * 50)

if __name__ == "__main__":
    benchmark()
