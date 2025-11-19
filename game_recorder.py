import csv
import os
import datetime
import config

class GameRecorder:
    def __init__(self):
        self.frames = []
        self.start_time = datetime.datetime.now()
        self.filename = f"recording_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"
        self.save_path = os.path.join(config.LOGS_HUMAN_DIR, self.filename)
        
    def log_frame(self, state, action_left, action_right):
        """
        Logs a single frame of gameplay.
        state: dict from game.get_state()
        action_left: 'UP', 'DOWN', or None
        action_right: 'UP', 'DOWN', or None (Human usually)
        """
        # We want to record data that helps train a model to mimic the winner (usually human if we are recording human data)
        # But we record everything for now.
        
        row = {
            "timestamp": (datetime.datetime.now() - self.start_time).total_seconds(),
            "ball_x": state["ball_x"],
            "ball_y": state["ball_y"],
            "ball_vel_x": state["ball_vel_x"],
            "ball_vel_y": state["ball_vel_y"],
            "paddle_left_y": state["paddle_left_y"],
            "paddle_right_y": state["paddle_right_y"],
            "action_left": action_left if action_left else "STAY",
            "action_right": action_right if action_right else "STAY",
            "score_left": state["score_left"],
            "score_right": state["score_right"]
        }
        self.frames.append(row)

    def save_recording(self):
        if not self.frames:
            return
            
        try:
            with open(self.save_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.frames[0].keys())
                writer.writeheader()
                writer.writerows(self.frames)
            print(f"Game recording saved to {self.save_path}")
        except Exception as e:
            print(f"Failed to save recording: {e}")
