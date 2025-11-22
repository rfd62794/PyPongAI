import os
import shutil
import argparse
import config
from utils import elo_manager
import pickle

def get_fitness_from_filename(filename):
    try:
        # Expected format: model_YYYYMMDD_HHMMSS_fitnessXXX.pkl
        # or gen_X_fit_XXX.pkl
        if "fitness" in filename:
            return int(filename.split("fitness")[1].split(".")[0])
        elif "_fit_" in filename:
            return int(filename.split("_fit_")[1].split(".")[0])
        return 0
    except (IndexError, ValueError):
        return 0

def get_best_model():
    """
    Returns the path to the best model based on fitness score.
    Returns None if no models are found.
    """
    models = scan_models()
    if not models:
        return None
    
    # Sort by fitness descending
    models.sort(key=lambda x: get_fitness_from_filename(os.path.basename(x)), reverse=True)
    return models[0]

def get_best_model_by_elo():
    """
    Returns the path to the best model based on ELO rating.
    Falls back to fitness if ELO is not available or equal.
    """
    models = scan_models()
    if not models:
        return None
        
    elo_ratings = elo_manager.load_elo_ratings()
    
    def get_sort_key(model_path):
        filename = os.path.basename(model_path)
        elo = elo_ratings.get(filename, config.ELO_INITIAL_RATING)
        fitness = get_fitness_from_filename(filename)
        return (elo, fitness)
        
    models.sort(key=get_sort_key, reverse=True)
    return models[0]

def convert_models_to_elo_format():
    """
    Scans all models, ensures they have an ELO rating (default 1200),
    and saves them back. Also updates the central ELO registry.
    """
    models = scan_models()
    print(f"Scanning {len(models)} models for ELO conversion...")
    
    elo_ratings = elo_manager.load_elo_ratings()
    updates = 0
    
    for model_path in models:
        try:
            filename = os.path.basename(model_path)
            
            # Load Genome
            with open(model_path, "rb") as f:
                genome = pickle.load(f)
                
            # Check/Set ELO
            if not hasattr(genome, 'elo_rating'):
                # Check if we have it in registry
                if filename in elo_ratings:
                    genome.elo_rating = elo_ratings[filename]
                else:
                    genome.elo_rating = config.ELO_INITIAL_RATING
                    elo_ratings[filename] = config.ELO_INITIAL_RATING
                
                # Save back
                with open(model_path, "wb") as f:
                    pickle.dump(genome, f)
                updates += 1
            else:
                # Ensure registry matches genome
                if filename not in elo_ratings:
                    elo_ratings[filename] = genome.elo_rating
                elif elo_ratings[filename] != genome.elo_rating:
                    # Registry takes precedence or genome? Let's trust registry if available, else genome
                    # Actually, let's trust the registry as the source of truth for ELO
                    genome.elo_rating = elo_ratings[filename]
                    with open(model_path, "wb") as f:
                        pickle.dump(genome, f)
                    updates += 1
                    
        except Exception as e:
            print(f"Error converting {model_path}: {e}")
            
    # Save registry
    elo_manager.save_elo_ratings(elo_ratings)
    print(f"Conversion complete. Updated {updates} models.")

def delete_models(model_paths):
    """
    Safely deletes a list of model files.
    Returns the number of successfully deleted files.
    """
    deleted_count = 0
    for path in model_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                deleted_count += 1
                print(f"Deleted: {os.path.basename(path)}")
                
                # Remove ELO entry
                elo_manager.remove_elo(os.path.basename(path))
        except Exception as e:
            print(f"Error deleting {path}: {e}")
    return deleted_count

def scan_models():
    models = []
    # Scan main model dir
    for f in os.listdir(config.MODEL_DIR):
        if f.endswith(".pkl"):
            models.append(os.path.join(config.MODEL_DIR, f))
    
    # Scan checkpoints
    checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
    if os.path.exists(checkpoint_dir):
        for f in os.listdir(checkpoint_dir):
            if f.endswith(".pkl"):
                models.append(os.path.join(checkpoint_dir, f))
                
    # Scan existing tiers to allow re-organizing
    tiers_root = os.path.join(config.MODEL_DIR, "tiers")
    if os.path.exists(tiers_root):
        for root, dirs, files in os.walk(tiers_root):
            for f in files:
                if f.endswith(".pkl"):
                    models.append(os.path.join(root, f))

    return models

def get_tier_name(fitness):
    if fitness < 500:
        step = 50
        start = (fitness // step) * step
        end = start + step
        return f"Fitness_{start}_{end}"
    elif fitness < 1000:
        step = 100
        start = (fitness // step) * step
        end = start + step
        return f"Fitness_{start}_{end}"
    else:
        step = 200
        start = (fitness // step) * step
        end = start + step
        return f"Fitness_{start}_{end}"

def organize_models(dry_run=False):
    models = scan_models()
    # Deduplicate by filename (if needed) or just process all
    # Sort by fitness descending
    models.sort(key=lambda x: get_fitness_from_filename(os.path.basename(x)), reverse=True)
    
    print(f"Found {len(models)} models.")
    
    tier_counts = {}
    
    for i, model_path in enumerate(models):
        filename = os.path.basename(model_path)
        fitness = get_fitness_from_filename(filename)
        
        target_tier = get_tier_name(fitness)
            
        tier_counts[target_tier] = tier_counts.get(target_tier, 0) + 1
        
        if not dry_run:
            target_dir = os.path.join(config.MODEL_DIR, "tiers", target_tier)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, filename)
            
            # Move if not already there
            if model_path != target_path:
                shutil.move(model_path, target_path)
                print(f"Moved {filename} -> {target_tier}")
        else:
            print(f"[Dry Run] Would move {filename} -> {target_tier} (Fitness: {fitness})")

    if not dry_run:
        print("\nOrganization Complete.")
        print("Summary:")
        for tier in sorted(tier_counts.keys()):
            print(f"  {tier}: {tier_counts[tier]}")

def clean_archive():
    archive_dir = os.path.join(config.MODEL_DIR, "tiers", "Archive")
    if not os.path.exists(archive_dir):
        print("Archive directory not found.")
        return

    files = [f for f in os.listdir(archive_dir) if f.endswith(".pkl")]
    print(f"Found {len(files)} models in Archive.")
    confirm = input("Are you sure you want to DELETE all models in Archive? (y/N): ")
    if confirm.lower() == 'y':
        for f in files:
            os.remove(os.path.join(archive_dir, f))
        print("Archive cleaned.")
    else:
        print("Operation cancelled.")

def main():
    parser = argparse.ArgumentParser(description="Project PaddleMind Model Manager")
    parser.add_argument("--report", action="store_true", help="Show current model rankings")
    parser.add_argument("--organize", action="store_true", help="Organize models into tiers")
    parser.add_argument("--clean", action="store_true", help="Delete models in Archive tier")
    
    args = parser.parse_args()
    
    if args.organize:
        organize_models(dry_run=False)
    elif args.clean:
        clean_archive()
    elif args.report:
        organize_models(dry_run=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Operation interrupted by user.")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
