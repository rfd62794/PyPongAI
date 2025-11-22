import os
import json
from core import config
from ai import model_manager

STATS_FILE = os.path.join(config.DATA_DIR, "human_stats.json")

class HumanRival:
    def __init__(self):
        self.stats = self.load_stats()
        
    def load_stats(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"best_score": 0, "rival_model": None, "rival_fitness": 0}
        
    def save_stats(self):
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=4)
            
    def update_score(self, score):
        if score > self.stats["best_score"]:
            print(f"New Human High Score: {score}!")
            self.stats["best_score"] = score
            # We don't auto-find rival here anymore, we let the match result handle it
            # But if it's a new high score, we might want to bump the target slightly?
            # Let's leave it to update_match_result for consistency
            self.save_stats()
            return True
        return False

    def update_match_result(self, human_score, ai_score, won):
        """
        Adjusts the rival fitness target based on the match outcome.
        """
        current_target = self.stats.get("rival_fitness", 100)
        
        # Initialize if missing
        if current_target == 0:
            current_target = max(100, self.stats["best_score"] * 50)
            
        if won:
            # Increase difficulty
            # If it was a close game, small increase. If domination, large increase.
            diff = human_score - ai_score
            increase = 10 + (diff * 2) # Base 10 + 2 per point diff
            current_target += increase
            print(f"Victory! Increasing Rival Fitness Target to {current_target}")
        else:
            # Decrease difficulty
            diff = ai_score - human_score
            decrease = 10 + (diff * 2)
            current_target -= decrease
            if current_target < 0: current_target = 0
            print(f"Defeat. Decreasing Rival Fitness Target to {current_target}")
            
        self.stats["rival_fitness"] = int(current_target)
        self.find_new_rival() # Find a model matching the new target
        self.save_stats()

    def find_new_rival(self):
        target_fitness = self.stats.get("rival_fitness", 100)
        if target_fitness == 0:
             target_fitness = max(100, self.stats["best_score"] * 50)
             self.stats["rival_fitness"] = target_fitness

        models = model_manager.scan_models()
        best_match = None
        min_diff = float('inf')
        
        for m in models:
            fit = model_manager.get_fitness_from_filename(os.path.basename(m))
            # Find closest model, preferring slightly higher if possible?
            # Just closest absolute difference for now
            diff = abs(fit - target_fitness)
            if diff < min_diff:
                min_diff = diff
                best_match = m
                    
        # If no model found (empty list), do nothing
        if not best_match and models:
             models.sort(key=lambda x: model_manager.get_fitness_from_filename(os.path.basename(x)), reverse=True)
             best_match = models[0]
             
        if best_match:
            self.stats["rival_model"] = best_match
            # We don't overwrite 'rival_fitness' here because that's our TARGET.
            # We just store the model path.
            # Actually, let's store the model's actual fitness for display?
            # No, keep 'rival_fitness' as the TARGET (Elo rating)
            # And maybe add 'actual_model_fitness' for display if needed.
            # For simplicity, let's assume 'rival_fitness' IS the target.
            print(f"Selected Rival Model: {os.path.basename(best_match)} (Target: {target_fitness})")
            
    def get_rival_model(self):
        if self.stats["rival_model"] and os.path.exists(self.stats["rival_model"]):
            return self.stats["rival_model"]
        
        # If missing, try to find one
        self.find_new_rival()
        self.save_stats()
        return self.stats["rival_model"]
