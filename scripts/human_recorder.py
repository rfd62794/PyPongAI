# human_recorder.py
import csv
import os
import datetime
from core import config

class HumanRecorder:
    def __init__(self):
        self.log_dir = "human_data"
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(self.log_dir, f"human_play_{timestamp}.csv")
        self.buffer = []
        
        # Define headers
        # State: ball_x, ball_y, ball_vel_x, ball_vel_y, paddle_left_y, paddle_right_y
        # Action: Human move (UP, DOWN, STAY)
        self.headers = ["ball_x", "ball_y", "ball_vel_x", "ball_vel_y", 
                        "paddle_left_y", "paddle_right_y", "human_action"]
        
        with open(self.filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def record_frame(self, game_state, human_action):
        """
        Records a single frame of data.
        human_action: 'UP', 'DOWN', or None (STAY)
        """
        action_str = "STAY"
        if human_action == "UP":
            action_str = "UP"
        elif human_action == "DOWN":
            action_str = "DOWN"
            
        row = [
            game_state["ball_x"],
            game_state["ball_y"],
            game_state["ball_vel_x"],
            game_state["ball_vel_y"],
            game_state["paddle_left_y"],
            game_state["paddle_right_y"],
            action_str
        ]
        self.buffer.append(row)
        
        # Flush periodically
        if len(self.buffer) >= 100:
            self.flush()
            
    def flush(self):
        if not self.buffer:
            return
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.buffer)
        self.buffer = []

    def close(self):
        self.flush()
