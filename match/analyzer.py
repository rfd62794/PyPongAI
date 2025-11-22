class MatchAnalyzer:
    def __init__(self):
        self.stats = {
            "left": {"hits": 0, "distance": 0, "reaction_frames": [], "last_ball_vel_x": 0, "last_paddle_y": 0, "bounce_frame": None},
            "right": {"hits": 0, "distance": 0, "reaction_frames": [], "last_ball_vel_x": 0, "last_paddle_y": 0, "bounce_frame": None}
        }
        self.rally_length = 0
        self.rallies = []
        self.frame_count = 0
        
    def update(self, game_state):
        self.frame_count += 1
        ball_vel_x = game_state["ball_vel_x"]
        
        # Initialize last_paddle_y on first frame
        if self.frame_count == 1:
             self.stats["left"]["last_paddle_y"] = game_state["paddle_left_y"]
             self.stats["right"]["last_paddle_y"] = game_state["paddle_right_y"]
             
        # Distance Tracking
        dist_left = abs(game_state["paddle_left_y"] - self.stats["left"]["last_paddle_y"])
        self.stats["left"]["distance"] += dist_left
        self.stats["left"]["last_paddle_y"] = game_state["paddle_left_y"]
        
        dist_right = abs(game_state["paddle_right_y"] - self.stats["right"]["last_paddle_y"])
        self.stats["right"]["distance"] += dist_right
        self.stats["right"]["last_paddle_y"] = game_state["paddle_right_y"]

        # Hit Detection & Bounce Recording
        if ball_vel_x > 0 and self.stats["left"]["last_ball_vel_x"] < 0:
            self.stats["left"]["hits"] += 1
            self.stats["right"]["bounce_frame"] = self.frame_count # Ball heading to Right
            
        elif ball_vel_x < 0 and self.stats["right"]["last_ball_vel_x"] > 0:
            self.stats["right"]["hits"] += 1
            self.stats["left"]["bounce_frame"] = self.frame_count # Ball heading to Left
            
        self.stats["left"]["last_ball_vel_x"] = ball_vel_x
        self.stats["right"]["last_ball_vel_x"] = ball_vel_x
        
        # Reaction Time Logic
        if ball_vel_x < 0 and self.stats["left"]["bounce_frame"] is not None:
            if dist_left > 0.5: # Significant movement
                reaction = self.frame_count - self.stats["left"]["bounce_frame"]
                self.stats["left"]["reaction_frames"].append(reaction)
                self.stats["left"]["bounce_frame"] = None 
        
        if ball_vel_x > 0 and self.stats["right"]["bounce_frame"] is not None:
            if dist_right > 0.5:
                reaction = self.frame_count - self.stats["right"]["bounce_frame"]
                self.stats["right"]["reaction_frames"].append(reaction)
                self.stats["right"]["bounce_frame"] = None

    def get_stats(self):
        return {
            "left": {
                "hits": self.stats["left"]["hits"],
                "reaction_sum": sum(self.stats["left"]["reaction_frames"]),
                "reaction_count": len(self.stats["left"]["reaction_frames"]),
                "distance": self.stats["left"]["distance"]
            },
            "right": {
                "hits": self.stats["right"]["hits"],
                "reaction_sum": sum(self.stats["right"]["reaction_frames"]),
                "reaction_count": len(self.stats["right"]["reaction_frames"]),
                "distance": self.stats["right"]["distance"]
            },
            "rallies": self.rallies
        }
