import os
import csv
import datetime
import config

class TrainingLogger:
    def __init__(self):
        self.log_dir = os.path.join(config.BASE_DIR, "logs", "training")
        os.makedirs(self.log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"training_run_{timestamp}.csv")
        
        self.headers = ["Generation", "Best_Fitness", "Avg_Fitness", "Best_ELO", "Species_Count", "Timestamp"]
        self._initialize_log()

    def _initialize_log(self):
        with open(self.log_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
            
    def log_generation(self, generation, best_fitness, avg_fitness, best_elo, species_count):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [generation, best_fitness, avg_fitness, best_elo, species_count, timestamp]
        
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        print(f"Logged generation {generation} to {self.log_file}")
