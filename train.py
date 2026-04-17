# train.py
import patch_neat
import os
import neat
import pickle
import argparse
import datetime
from ai import ai_module
from core import config

def main():
    parser = argparse.ArgumentParser(description="PyPongAI Training Engine")
    parser.add_argument("--mode", default="research", choices=["research", "baseline"],
                        help="'research' uses ELO+Novelty, 'baseline' uses ELO only")
    parser.add_argument("--generations", type=int, default=50, help="Number of generations to train")
    parser.add_argument("--visual", action="store_true", help="Enable visual training feedback")
    args = parser.parse_args()
    
    # Load NEAT config
    config_path = os.path.join(os.path.dirname(__file__), "neat_config.txt")
    config_obj = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                     neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    # Create population
    pop = neat.Population(config_obj)
    
    # Add reporters
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    
    # Select eval function based on mode
    if args.mode == "research":
        eval_func = ai_module.eval_genomes_competitive
        print("RESEARCH MODE: ELO + Novelty Search")
    else:
        # Assuming eval_genomes is the baseline ELO-only or simple evaluator
        eval_func = ai_module.eval_genomes 
        print("BASELINE MODE: ELO only")
    
    # Run training
    print(f"Starting {args.generations}-generation training run...")
    try:
        winner = pop.run(eval_func, n=args.generations)
    except KeyboardInterrupt:
        print("\n[!] Training interrupted by user.")
        return

    # Save best model
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"best_genome_gen{args.generations}_{timestamp}.pkl"
    save_path = os.path.join(config.MODEL_DIR, output_file)
    
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(winner, f)
    
    # Also save as 'best_genome.pkl' for easy access
    with open(os.path.join(config.MODEL_DIR, "best_genome.pkl"), "wb") as f:
        pickle.dump(winner, f)
        
    print(f"Training complete. Best genome saved to {save_path}")
    print(f"   Final Fitness: {winner.fitness:.2f}")

if __name__ == "__main__":
    main()
