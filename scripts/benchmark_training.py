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
    
    # Create a larger population of 50 genomes for benchmarking
    pop_size = 50
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
    print("\nRunning PARALLEL Evaluation (Run 1 - Pool Creation Overhead)...")
    os.environ["PYPONGAI_PARALLEL_EVAL"] = "true"
    num_cpus = mp.cpu_count()
    print(f"CPUs Detected: {num_cpus}")
    
    start_parallel1 = time.time()
    ai_module.eval_genomes_competitive(genomes, config_neat)
    end_parallel1 = time.time()
    parallel_time1 = end_parallel1 - start_parallel1
    print(f"Parallel Time (Run 1): {parallel_time1:.2f} seconds")

    print("\nRunning PARALLEL Evaluation (Run 2 - Pooled / Persistent)...")
    start_parallel2 = time.time()
    ai_module.eval_genomes_competitive(genomes, config_neat)
    end_parallel2 = time.time()
    parallel_time2 = end_parallel2 - start_parallel2
    print(f"Parallel Time (Run 2): {parallel_time2:.2f} seconds")
    
    # Comparison using the faster run
    speedup = serial_time / parallel_time2 if parallel_time2 > 0 else 0
    print("-" * 50)
    print(f"BEST SPEEDUP (Persistent): {speedup:.2f}x")
    print("=" * 50)

if __name__ == "__main__":
    benchmark()
