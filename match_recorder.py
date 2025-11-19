import json
import os
import time
import config

class MatchRecorder:
    def __init__(self, p1_name, p2_name):
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.frames = []
        self.start_time = time.time()
        self.frame_count = 0
        
    def record_frame(self, game_state):
        """
        Records a single frame of the game state.
        """
        self.frame_count += 1
        
        # Optimize: Round floats to reduce file size
        frame_data = {
            "f": self.frame_count,
            "bx": round(game_state["ball_x"], 1),
            "by": round(game_state["ball_y"], 1),
            "bvx": round(game_state["ball_vel_x"], 2),
            "bvy": round(game_state["ball_vel_y"], 2),
            "ply": round(game_state["paddle_left_y"], 1),
            "pry": round(game_state["paddle_right_y"], 1),
            "sl": game_state["score_left"],
            "sr": game_state["score_right"]
        }
        self.frames.append(frame_data)
        
    def save(self):
        """
        Saves the recorded match to a JSON file.
        """
        if not self.frames:
            return

        timestamp = int(self.start_time)
        # Sanitize filenames
        safe_p1 = "".join([c for c in self.p1_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        safe_p2 = "".join([c for c in self.p2_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        
        filename = f"match_{timestamp}_{safe_p1}_vs_{safe_p2}.json"
        filepath = os.path.join(config.LOGS_MATCHES_DIR, filename)
        
        data = {
            "p1": self.p1_name,
            "p2": self.p2_name,
            "timestamp": self.start_time,
            "total_frames": self.frame_count,
            "winner": "p1" if self.frames[-1]["sl"] > self.frames[-1]["sr"] else "p2",
            "final_score": [self.frames[-1]["sl"], self.frames[-1]["sr"]],
            "frames": self.frames
        }
        
        try:
            with open(filepath, "w") as f:
                json.dump(data, f)
            print(f"Match recording saved: {filename}")
        except Exception as e:
            print(f"Error saving match recording: {e}")
