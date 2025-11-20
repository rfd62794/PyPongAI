import training_logger
import os
import shutil

def test_logger():
    print("Testing TrainingLogger...")
    
    # Initialize Logger
    logger = training_logger.TrainingLogger()
    log_file = logger.log_file
    print(f"Log file created at: {log_file}")
    
    assert os.path.exists(log_file)
    
    # Log a generation
    logger.log_generation(1, 100.5, 50.2, 1200, 5)
    
    # Read back
    with open(log_file, "r") as f:
        lines = f.readlines()
        
    assert len(lines) >= 2 # Header + 1 row
    header = lines[0].strip().split(",")
    assert header == ["Generation", "Best_Fitness", "Avg_Fitness", "Best_ELO", "Species_Count", "Timestamp"]
    
    data = lines[1].strip().split(",")
    assert data[0] == "1"
    assert data[1] == "100.5"
    assert data[2] == "50.2"
    assert data[3] == "1200"
    assert data[4] == "5"
    
    print("Logging verified.")
    
    # Cleanup (Optional, maybe keep for user to see)
    # os.remove(log_file)

if __name__ == "__main__":
    test_logger()
