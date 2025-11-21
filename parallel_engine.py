import multiprocessing
import time
import config
import game_engine
import game_simulator
import neat
import pickle
import os
from match_analyzer import MatchAnalyzer
from match_recorder import MatchRecorder
def _run_fast_match(match_config, record_match=False):
    """
    Runs a complete match in the background process at maximum speed.
    """
    p1_path = match_config["p1_path"]
    p2_path = match_config["p2_path"]
    neat_config_path = match_config["neat_config_path"]
    metadata = match_config["metadata"]
    
    # Load Genomes and Config
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              neat_config_path)
                              
    with open(p1_path, "rb") as f:
        g1 = pickle.load(f)
    with open(p2_path, "rb") as f:
        g2 = pickle.load(f)
        
    net1 = neat.nn.FeedForwardNetwork.create(g1, config_neat)
    net2 = neat.nn.FeedForwardNetwork.create(g2, config_neat)
    
    # Initialize Game Components
    game = game_simulator.GameSimulator()
    analyzer = MatchAnalyzer()
    recorder = None
    if record_match:
        recorder = MatchRecorder(
            os.path.basename(p1_path), 
            os.path.basename(p2_path),
            match_type="tournament",
            metadata=metadata
        )
    
    # Run Match Loop
    target_score = config.MAX_SCORE
    running = True
    
    while running:
        state = game.get_state()
        
        # Update Analyzer & Recorder
        analyzer.update(state)
        if recorder:
            recorder.record_frame(state)
        
        # AI 1 (Left)
        inputs1 = (
            state["paddle_left_y"] / config.SCREEN_HEIGHT,
            state["ball_x"] / config.SCREEN_WIDTH,
            state["ball_y"] / config.SCREEN_HEIGHT,
            state["ball_vel_x"] / config.BALL_MAX_SPEED,
            state["ball_vel_y"] / config.BALL_MAX_SPEED,
            (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
            1.0 if state["ball_vel_x"] < 0 else 0.0,
            state["paddle_right_y"] / config.SCREEN_HEIGHT
        )
        out1 = net1.activate(inputs1)
        act1 = out1.index(max(out1))
        left_move = "UP" if act1 == 0 else "DOWN" if act1 == 1 else None
        
        # AI 2 (Right)
        inputs2 = (
            state["paddle_right_y"] / config.SCREEN_HEIGHT,
            state["ball_x"] / config.SCREEN_WIDTH,
            state["ball_y"] / config.SCREEN_HEIGHT,
            state["ball_vel_x"] / config.BALL_MAX_SPEED,
            state["ball_vel_y"] / config.BALL_MAX_SPEED,
            (state["paddle_right_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
            1.0 if state["ball_vel_x"] > 0 else 0.0,
            state["paddle_left_y"] / config.SCREEN_HEIGHT
        )
        out2 = net2.activate(inputs2)
        act2 = out2.index(max(out2))
        right_move = "UP" if act2 == 0 else "DOWN" if act2 == 1 else None
        
        # Update Game
        game.update(left_move, right_move)
        
        # Check End Condition
        if game.score_left >= target_score or game.score_right >= target_score:
            running = False
            
    # Compile Results
    stats = analyzer.get_stats()
    match_metadata = None
    if recorder:
        match_metadata = recorder.save()
    
    # We don't index here because the main process handles ELO updates and then re-indexes if needed.
    # Actually, the main process expects to handle ELO updates.
    # But we can return the match_metadata so the main process can index it properly after ELO updates.
    
    return {
        "score_left": game.score_left,
        "score_right": game.score_right,
        "stats": stats,
        "match_metadata": match_metadata
    }

def _game_loop(input_queue, output_queue, visual_mode, target_fps):
    """
    The main loop for the separate game process.
    """
    # Initialize the appropriate game engine
    if visual_mode:
        game = game_engine.Game()
        clock = game_engine.pygame.time.Clock()
    else:
        game = game_simulator.GameSimulator()
        clock = None

    # Signal that we are ready
    output_queue.put({"type": "READY"})

    running = True
    while running:
        # Process all available commands
        left_move = None
        right_move = None
        
        while not input_queue.empty():
            try:
                cmd = input_queue.get_nowait()
                if cmd["type"] == "STOP":
                    running = False
                    break
                elif cmd["type"] == "MOVE":
                    if cmd["paddle"] == "left":
                        left_move = cmd["action"]
                    elif cmd["paddle"] == "right":
                        right_move = cmd["action"]
                elif cmd["type"] == "PLAY_MATCH":
                    # Run a full match and return result
                    result = _run_fast_match(cmd["config"], record_match=cmd.get("record_match", False))
                    output_queue.put({"type": "MATCH_RESULT", "data": result})
                    # We continue the loop, but effectively we just waited for the match to finish
                    
            except multiprocessing.queues.Empty:
                break
        
        if not running:
            break

        # Only update the continuous game loop if NOT in a blocking match command (which we just handled synchronously above)
        # But wait, if we handled PLAY_MATCH, we already finished it.
        # The standard update loop below is for the "interactive" mode (visual or frame-by-frame).
        # If we are just a worker for PLAY_MATCH, we might not need this loop to run constantly.
        # But for backward compatibility with visual mode, we keep it.
        
        # Update Game
        score_data = game.update(left_move, right_move)
        
        # Get State
        state = game.get_state()
        
        # Add event data if any
        if score_data:
            state.update(score_data)
            
        # Send state back to main process
        if not output_queue.full():
            output_queue.put(state)
            
        # Frame Rate Control
        if visual_mode and target_fps > 0:
            clock.tick(target_fps)
        elif not visual_mode and target_fps > 0:
            time.sleep(1.0 / target_fps)

class ParallelGameEngine:
    def __init__(self, visual_mode=True, target_fps=60):
        self.visual_mode = visual_mode
        self.target_fps = target_fps
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue(maxsize=1) # Keep only latest state
        self.process = None
        self.latest_state = None
        
        # Mimic Game attributes for compatibility where possible
        self.score_left = 0
        self.score_right = 0
        
    def start(self):
        if self.process is None:
            self.process = multiprocessing.Process(
                target=_game_loop,
                args=(self.input_queue, self.output_queue, self.visual_mode, self.target_fps)
            )
            self.process.start()
            
            # Wait for ready signal
            print("Waiting for engine to start...")
            while True:
                try:
                    msg = self.output_queue.get(timeout=5.0)
                    if msg.get("type") == "READY":
                        print("Engine started.")
                        break
                except multiprocessing.queues.Empty:
                    print("Engine start timed out.")
                    self.stop()
                    break

    def stop(self):
        if self.process:
            self.input_queue.put({"type": "STOP"})
            self.process.join(timeout=1.0)
            if self.process.is_alive():
                self.process.terminate()
            self.process = None

    def update(self, left_move=None, right_move=None):
        """
        Sends moves and retrieves the latest state.
        Returns score_data (dict) if an event occurred, else None (for compatibility).
        """
        # Send moves
        if left_move:
            self.input_queue.put({"type": "MOVE", "paddle": "left", "action": left_move})
        if right_move:
            self.input_queue.put({"type": "MOVE", "paddle": "right", "action": right_move})
            
        # Get latest state
        new_state = None
        try:
            while not self.output_queue.empty():
                item = self.output_queue.get_nowait()
                if item.get("type") == "READY":
                    continue
                if item.get("type") == "MATCH_RESULT":
                    # This shouldn't happen in normal update loop, but just in case
                    continue 
                new_state = item
        except multiprocessing.queues.Empty:
            pass
            
        if new_state:
            self.latest_state = new_state
            self.score_left = new_state["score_left"]
            self.score_right = new_state["score_right"]
            
            if "scored" in new_state or "hit_left" in new_state or "hit_right" in new_state:
                return new_state
            return None
            
        return None

    def get_state(self):
        if self.latest_state:
            return self.latest_state
        return {
            "ball_x": config.SCREEN_WIDTH // 2,
            "ball_y": config.SCREEN_HEIGHT // 2,
            "ball_vel_x": 0,
            "ball_vel_y": 0,
            "paddle_left_y": config.SCREEN_HEIGHT // 2,
            "paddle_right_y": config.SCREEN_HEIGHT // 2,
            "score_left": 0,
            "score_right": 0,
            "game_over": False
        }
        
    def play_match(self, match_config, record_match=False):
        """
        Sends a command to play a full match and waits for the result.
        """
        self.input_queue.put({"type": "PLAY_MATCH", "config": match_config, "record_match": record_match})
        
        # Wait for result
        while True:
            try:
                msg = self.output_queue.get(timeout=30.0) # 30s timeout for a match
                if msg.get("type") == "MATCH_RESULT":
                    return msg["data"]
            except multiprocessing.queues.Empty:
                print("Match timed out!")
                return None
