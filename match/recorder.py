import json
import os
import time
import config
import uuid

class MatchRecorder:
    def __init__(self, p1_name, p2_name, match_type="tournament", metadata=None):
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.match_type = match_type  # "tournament", "training_validation", "checkpoint_viz", "human_vs_ai"
        self.metadata = metadata or {}  # Extra context: fitness, ELO, generation
        self.frames = []
        self.start_time = time.time()
        self.frame_count = 0
        self.match_id = str(uuid.uuid4())[:8]  # Short unique ID
        
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
        Saves the recorded match to a JSON file and returns metadata for indexing.
        """
        if not self.frames:
            return None

        timestamp = int(self.start_time)
        # Sanitize filenames
        safe_p1 = "".join([c for c in self.p1_name if c.isalnum() or c in (' ', '_', '-')]).strip()[:30]
        safe_p2 = "".join([c for c in self.p2_name if c.isalnum() or c in (' ', '_', '-')]).strip()[:30]
        
        filename = f"match_{timestamp}_{self.match_id}_{safe_p1}_vs_{safe_p2}.json"
        filepath = os.path.join(config.LOGS_MATCHES_DIR, filename)
        
        final_score_left = self.frames[-1]["sl"]
        final_score_right = self.frames[-1]["sr"]
        
        data = {
            "match_id": self.match_id,
            "p1": self.p1_name,
            "p2": self.p2_name,
            "match_type": self.match_type,
            "timestamp": self.start_time,
            "total_frames": self.frame_count,
            "winner": "p1" if final_score_left > final_score_right else "p2",
            "final_score": [final_score_left, final_score_right],
            "metadata": self.metadata,  # Store extra context
            "frames": self.frames
        }
        
        try:
            with open(filepath, "w") as f:
                json.dump(data, f)
            print(f"Match recording saved: {filename}")
            
            # Return metadata for database indexing
            return {
                "match_id": self.match_id,
                "timestamp": self.start_time,
                "p1": self.p1_name,
                "p2": self.p2_name,
                "match_type": self.match_type,
                "winner": "p1" if final_score_left > final_score_right else "p2",
                "final_score": [final_score_left, final_score_right],
                "duration_frames": self.frame_count,
                "file_path": filepath,
                **self.metadata  # Include metadata fields
            }
        except Exception as e:
            print(f"Error saving match recording: {e}")
            return None
