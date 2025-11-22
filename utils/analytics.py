    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"game_log_{timestamp}.csv"
    filepath = os.path.join(log_dir, filename)
    
    headers = ["timestamp", "ball_x", "ball_y", "ball_vel_x", "ball_vel_y", 
               "paddle_left_y", "paddle_right_y", "score_left", "score_right"]
    
    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
    return filepath

def log_score(log_filepath, score_data):
    """
    Appends a row of score data to the log file.
    """
    # Add timestamp to the data if not present (though we usually add it here)
    current_time = datetime.datetime.now().isoformat()
    
    row = [
        current_time,
        score_data["ball_x"],
        score_data["ball_y"],
        score_data["ball_vel_x"],
        score_data["ball_vel_y"],
        score_data["paddle_left_y"],
        score_data["paddle_right_y"],
        score_data["score_left"],
        score_data["score_right"]
    ]
    
    with open(log_filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

def log_game(game_data):
    """
    Logs game data to a CSV file in the matches directory.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"game_log_{timestamp}.csv"
    filepath = os.path.join(config.LOGS_MATCHES_DIR, filename)
    
    df = pd.DataFrame(game_data)
    df.to_csv(filepath, index=False)
    # print(f"Game logged to {filepath}")

def log_human_game(game_data):
    """
    Logs human gameplay data for imitation learning.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"human_log_{timestamp}.csv"
    filepath = os.path.join(config.LOGS_HUMAN_DIR, filename)
    
    df = pd.DataFrame(game_data)
    df.to_csv(filepath, index=False)
    print(f"Human game logged to {filepath}")
