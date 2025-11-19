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
            
        print("Seeding complete.")

    # Add reporters
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Run for 50 generations
    print("Starting training...")
    winner = p.run(ai_module.eval_genomes, 50)

    # Save the winner
    import datetime
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
