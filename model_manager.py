import os
import shutil
import argparse
import config

TIERS = {
    "God": 20,         # Top 20
    "Master": 50,      # Top 21-50
    "Challenger": 100, # Top 51-100
    "Archive": None    # The rest
}

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
    for tier in TIERS.keys():
        tier_dir = os.path.join(config.MODEL_DIR, "tiers", tier)
        if os.path.exists(tier_dir):
            for f in os.listdir(tier_dir):
                if f.endswith(".pkl"):
                    models.append(os.path.join(tier_dir, f))

    return models

def organize_models(dry_run=False):
    models = scan_models()
    # Deduplicate by filename (if needed) or just process all
    # Sort by fitness descending
    models.sort(key=lambda x: get_fitness_from_filename(os.path.basename(x)), reverse=True)
    
    print(f"Found {len(models)} models.")
    
    tier_counts = {k: 0 for k in TIERS.keys()}
    
    for i, model_path in enumerate(models):
        filename = os.path.basename(model_path)
        rank = i + 1
        
        target_tier = "Archive"
        if rank <= TIERS["God"]:
            target_tier = "God"
        elif rank <= TIERS["Master"]:
            target_tier = "Master"
        elif rank <= TIERS["Challenger"]:
            target_tier = "Challenger"
            
        tier_counts[target_tier] += 1
        
        if not dry_run:
            target_dir = os.path.join(config.MODEL_DIR, "tiers", target_tier)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, filename)
            
            # Move if not already there
            if model_path != target_path:
                shutil.move(model_path, target_path)
                print(f"Moved {filename} -> {target_tier}")
        else:
            print(f"[Dry Run] Would move {filename} -> {target_tier} (Fitness: {get_fitness_from_filename(filename)})")

    if not dry_run:
        print("\nOrganization Complete.")
        print("Summary:")
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count}")

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
