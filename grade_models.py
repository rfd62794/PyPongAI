import os
import pickle
import neat
import config
from game_engine import Game
import sys

def load_genome(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def get_fitness_from_name(filename):
    try:
        if "fitness" in filename:
            return int(filename.split("fitness")[1].split(".")[0])
        elif "_fit_" in filename:
            return int(filename.split("_fit_")[1].split(".")[0])
        return 0
    except:
        return 0

def find_master_model():
    models = []
    for root, dirs, files in os.walk(config.MODEL_DIR):
        for file in files:
            if file.endswith(".pkl") and "Grade" not in file: # Don't use already graded models as master? Or do?
                # Actually, the master should be the absolute best, graded or not.
                models.append(os.path.join(root, file))
    
    if not models:
        return None
        
    models.sort(key=lambda x: get_fitness_from_name(os.path.basename(x)), reverse=True)
    return models[0]

def simulate_match(genome1, genome2, config_neat):
    # Returns score1, score2
    net1 = neat.nn.FeedForwardNetwork.create(genome1, config_neat)
    net2 = neat.nn.FeedForwardNetwork.create(genome2, config_neat)
    
    game = Game()
    # Headless simulation
    # We need a loop
    max_frames = 3600 # 1 minute at 60fps cap
    
    for _ in range(max_frames):
        # AI 1 (Left)
        inputs1 = (
            game.left_paddle.rect.y,
            game.ball.rect.x,
            game.ball.rect.y,
            game.ball.vel_x,
            game.ball.vel_y,
            game.left_paddle.rect.y - game.ball.rect.y,
            1.0 if game.ball.vel_x < 0 else 0.0
        )
        out1 = net1.activate(inputs1)
        dec1 = out1.index(max(out1))
        move1 = "UP" if dec1 == 0 else "DOWN" if dec1 == 1 else None
        
        # AI 2 (Right)
        # We need to flip inputs for the right side AI?
        # Usually we train them as Left paddle.
        # If we put it on the Right, we need to mirror the inputs.
        # Mirror X, Mirror Velocity X.
        # Ball X is 0..Width. For Right AI, relative X is Width - Ball X?
        # Let's assume the model is trained to play on the LEFT.
        # To play on RIGHT, we must flip the board perspective.
        
        inputs2 = (
            game.right_paddle.rect.y,
            config.SCREEN_WIDTH - game.ball.rect.x, # Mirror X
            game.ball.rect.y,
            -game.ball.vel_x, # Mirror VX
            game.ball.vel_y,
            game.right_paddle.rect.y - game.ball.rect.y,
            1.0 if game.ball.vel_x > 0 else 0.0 # Incoming if moving Right (>0)
        )
        out2 = net2.activate(inputs2)
        dec2 = out2.index(max(out2))
        move2 = "UP" if dec2 == 0 else "DOWN" if dec2 == 1 else None
        
        game_state = game.update(move1, move2)
        
        if game.score_left >= 5 or game.score_right >= 5:
            break
            
    return game.score_left, game.score_right

def grade_models():
    print("--- Starting Model Grading ---")
    
    # Load NEAT Config
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat_config.txt")
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)

    master_path = find_master_model()
    if not master_path:
        print("No models found.")
        return
        
    print(f"Master Model: {os.path.basename(master_path)}")
    master_genome = load_genome(master_path)
    
    # Scan all models
    for root, dirs, files in os.walk(config.MODEL_DIR):
        for file in files:
            if file.endswith(".pkl") and file != os.path.basename(master_path):
                full_path = os.path.join(root, file)
                
                # Skip if already graded?
                if "Grade" in file:
                    continue
                    
                print(f"Grading {file}...", end="", flush=True)
                
                try:
                    candidate_genome = load_genome(full_path)
                    
                    # Play Candidate (Left) vs Master (Right)
                    # Actually, let's play Candidate vs Master.
                    # If Candidate wins, it's S tier.
                    
                    s1, s2 = simulate_match(candidate_genome, master_genome, neat_config)
                    
                    grade = "D"
                    if s1 > s2: # Won
                        grade = "S"
                    elif s1 >= 3: # Close loss
                        grade = "A"
                    elif s1 >= 1: # Scored something
                        grade = "B"
                    else: # 0 points
                        grade = "C"
                        
                    print(f" Score: {s1}-{s2} -> Grade {grade}")
                    
                    # Rename
                    new_name = file.replace(".pkl", f"_Grade{grade}.pkl")
                    new_path = os.path.join(root, new_name)
                    os.rename(full_path, new_path)
                    
                except Exception as e:
                    print(f" Error: {e}")

if __name__ == "__main__":
    grade_models()
