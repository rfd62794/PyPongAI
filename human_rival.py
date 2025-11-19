import os
import json
import config
import model_manager

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
            self.find_new_rival()
            self.save_stats()
            return True
        return False
        
    def find_new_rival(self):
        # Heuristic: Find model with fitness roughly 50x the human score?
        # Or just find the best available model?
        # Let's try to find a model that is slightly better than the human's "implied fitness"
        # Implied fitness = score * 100 (Rough guess, max score 10 -> 1000 fitness)
        
        target_fitness = self.stats["best_score"] * 50 
        if target_fitness < 100: target_fitness = 100 # Minimum challenge
        
        models = model_manager.scan_models()
        best_match = None
        min_diff = float('inf')
        
        for m in models:
            fit = model_manager.get_fitness_from_filename(os.path.basename(m))
            # We want a rival that is at least this good, but closest to it
            if fit >= target_fitness:
                diff = fit - target_fitness
                if diff < min_diff:
                    min_diff = diff
                    best_match = m
                    
        # If no model is better, take the absolute best one
        if not best_match and models:
             models.sort(key=lambda x: model_manager.get_fitness_from_filename(os.path.basename(x)), reverse=True)
             best_match = models[0]
             
        if best_match:
            self.stats["rival_model"] = best_match
            self.stats["rival_fitness"] = model_manager.get_fitness_from_filename(os.path.basename(best_match))
            print(f"New Rival Selected: {os.path.basename(best_match)} (Fitness: {self.stats['rival_fitness']})")
            
    def get_rival_model(self):
        if self.stats["rival_model"] and os.path.exists(self.stats["rival_model"]):
            return self.stats["rival_model"]
        
        # If missing, try to find one
        self.find_new_rival()
        self.save_stats()
        return self.stats["rival_model"]
