# train.py
import patch_neat
import os
import neat
import pickle
import ai_module
# train.py
import patch_neat
import os
import neat
import pickle
import ai_module
import config
import datetime

def run_training(seed_genomes=None):
    """
    Runs the NEAT training process.
    """
    # Load configuration
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)

    # Create the population
    p = neat.Population(config_neat)
    
    # Seeding Logic
    if seed_genomes:
        print(f"Seeding population with {len(seed_genomes)} genomes...")
        # Replace random genomes with seeded ones
        # We need to ensure IDs are unique if we are merging multiple populations
        # But for simplicity, we can just overwrite the first N genomes
        
        # NEAT population is a dict {id: genome}
        pop_ids = list(p.population.keys())
        
        for i, seed_genome in enumerate(seed_genomes):
            if i >= len(pop_ids):
                break # Population full
            
            target_id = pop_ids[i]
            # Assign the seed genome to this ID
            # We must copy it to avoid reference issues if using same object multiple times
            # But here we just take the object.
            # IMPORTANT: The seed genome might have a different ID. We should probably keep its ID 
            # or reassign it to match the current population structure.
            # Safest is to reassign ID.
            seed_genome.key = target_id
            p.population[target_id] = seed_genome
            
        # Re-speciate to ensure species set references the new genome objects
        p.species.speciate(config_neat, p.population, p.generation)
            
        print("Seeding complete.")

    # Add reporters
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Custom Reporter for Validation
    class ValidationReporter(neat.reporting.BaseReporter):
        def start_generation(self, generation):
            self.generation = generation

        def end_generation(self, config, population, species_set):
            # Find best genome
            best_genome = None
            best_fitness = -float('inf')
            for g in population.values():
                if g.fitness is not None and g.fitness > best_fitness:
                    best_fitness = g.fitness
                    best_genome = g
            
            if best_genome:
                avg_rally, win_rate = ai_module.validate_genome(best_genome, config)
                print(f"   [Validation] Best Genome vs Rule-Based: Avg Rally={avg_rally:.2f}, Win Rate={win_rate:.2f}")
                
                # Update Hall of Fame every 5 generations
                if self.generation % 5 == 0:
                    # We need to clone it to ensure it doesn't get mutated later?
                    # NEAT genomes are usually mutated in place or cloned during reproduction.
                    # But the population object persists.
                    # Safest is to pickle/unpickle or use copy.deepcopy
                    import copy
                    ai_module.HALL_OF_FAME.append(copy.deepcopy(best_genome))
                    print(f"   [HOF] Added Best Genome to Hall of Fame. Size: {len(ai_module.HALL_OF_FAME)}")
                
                # Log to CSV
                with open(os.path.join(config_neat.stats_path_csv), 'a', newline='') as f:
                    writer = csv.writer(f)
                    # We need generation number. BaseReporter doesn't store it easily unless we track it.
                    # But we can append to the file created below.
                    pass

    p.add_reporter(ValidationReporter())
    
    # Run for 50 generations
    # Run for 50 generations
    print("Starting training (Self-Play Mode)...")
    
    # Setup CSV logging first
    import csv
    stats_filename = f"training_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    stats_path = os.path.join(config.LOGS_TRAINING_DIR, stats_filename)
    config_neat.stats_path_csv = stats_path # Hack to pass path to reporter
    
    with open(stats_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["generation", "max_fitness", "avg_fitness", "std_dev", "val_avg_rally", "val_win_rate"])

    # We need to override the reporter to write to this CSV
    class CSVReporter(neat.reporting.BaseReporter):
        def __init__(self, csv_path):
            self.csv_path = csv_path
            self.generation = 0
        
        def start_generation(self, generation):
            self.generation = generation
            
        def end_generation(self, config, population, species_set):
            # Get stats from the stats reporter? 
            # It's easier to just calculate here or grab from stats object if accessible.
            # Let's just calculate simple stats
            fitnesses = [g.fitness for g in population.values() if g.fitness is not None]
            max_f = max(fitnesses) if fitnesses else 0
            avg_f = sum(fitnesses) / len(fitnesses) if fitnesses else 0
            import statistics
            std = statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0
            
            # Validation
            best_genome = None
            best_fitness = -float('inf')
            for g in population.values():
                if g.fitness is not None and g.fitness > best_fitness:
                    best_fitness = g.fitness
                    best_genome = g
            
            val_rally = 0
            val_win = 0
            if best_genome:
                val_rally, val_win = ai_module.validate_genome(best_genome, config)
                print(f"   [Validation] Best Genome vs Rule-Based: Avg Rally={val_rally:.2f}, Win Rate={val_win:.2f}")

            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([self.generation, max_f, avg_f, std, val_rally, val_win])

    p.add_reporter(CSVReporter(stats_path))

    winner = p.run(ai_module.eval_genomes_self_play, 50)

    print(f"Training stats saved to {stats_path}")

    # Save the winner
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fitness_score = int(winner.fitness) if winner.fitness else 0
    model_filename = f"model_{timestamp}_fitness{fitness_score}.pkl"
    
    with open(os.path.join(config.MODEL_DIR, model_filename), "wb") as f:
        pickle.dump(winner, f)
    print(f"Training finished. Best genome saved to {os.path.join(config.MODEL_DIR, model_filename)}")
    
    # Also save as 'best_genome.pkl' for easy access
    with open(os.path.join(config.MODEL_DIR, "best_genome.pkl"), "wb") as f:
        pickle.dump(winner, f)

if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--seed", help="Path to a specific model file to seed with")
        parser.add_argument("--seed_dir", help="Directory containing models to seed with")
        args = parser.parse_args()
        
        seeds = []
        if args.seed:
            if os.path.exists(args.seed):
                with open(args.seed, "rb") as f:
                    seeds.append(pickle.load(f))
        
        if args.seed_dir:
            if os.path.exists(args.seed_dir):
                for f in os.listdir(args.seed_dir):
                    if f.endswith(".pkl"):
                        try:
                            with open(os.path.join(args.seed_dir, f), "rb") as file:
                                seeds.append(pickle.load(file))
                        except:
                            pass

        run_training(seed_genomes=seeds if seeds else None)
    except KeyboardInterrupt:
        print("\n[!] Training interrupted by user.")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
