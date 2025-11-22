import multiprocessing
import time
import pygame
from core import config
from core import engine as game_engine
from core import simulator as game_simulator
import neat
import pickle
import os
import sys

# Add root directory to path so we can import modules from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .analyzer import MatchAnalyzer
from .recorder import MatchRecorder
from ai.agent_factory import AgentFactory
from .simulator import MatchSimulator

# Agent cache for parallel process (avoids reloading same models)
_agent_cache = {}
_cache_max_size = 50  # Limit cache size

def _run_fast_match(match_config, record_match=False):
    """
    Runs a complete match in the background process at maximum speed.
    Uses agent caching to avoid reloading the same models.
    """
    p1_path = match_config["p1_path"]
    p2_path = match_config["p2_path"]
    neat_config_path = match_config["neat_config_path"]
    metadata = match_config.get("metadata")
    
    try:
        # Check if files exist before trying to load
        if not os.path.exists(p1_path):
            raise FileNotFoundError(f"Model file not found: {p1_path}")
        if not os.path.exists(p2_path):
            raise FileNotFoundError(f"Model file not found: {p2_path}")
        
        # Load Agents using Factory with caching
        cache_key1 = (p1_path, neat_config_path)
        cache_key2 = (p2_path, neat_config_path)
        
        if cache_key1 in _agent_cache:
            agent1 = _agent_cache[cache_key1]
        else:
            agent1 = AgentFactory.create_agent(p1_path, neat_config_path)
            # Add to cache (with size limit)
            if len(_agent_cache) >= _cache_max_size:
                # Remove oldest entry (simple FIFO)
                _agent_cache.pop(next(iter(_agent_cache)))
            _agent_cache[cache_key1] = agent1
        
        if cache_key2 in _agent_cache:
            agent2 = _agent_cache[cache_key2]
        else:
            agent2 = AgentFactory.create_agent(p2_path, neat_config_path)
            if len(_agent_cache) >= _cache_max_size:
                _agent_cache.pop(next(iter(_agent_cache)))
            _agent_cache[cache_key2] = agent2
        
        # Run Match using Simulator
        simulator = MatchSimulator(
            agent1, 
            agent2, 
            p1_name=os.path.basename(p1_path), 
            p2_name=os.path.basename(p2_path),
            record_match=record_match,
            metadata=metadata
        )
        
        return simulator.run()
    except FileNotFoundError as e:
        # Return a result indicating the match couldn't be run due to missing file
        print(f"Error in _run_fast_match: {e}")
        return {
            "score_left": 0,
            "score_right": 0,
            "stats": {
                "left": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0},
                "right": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0}
            },
            "match_metadata": metadata,
            "error": str(e)
        }
    except Exception as e:
        # Catch any other errors and return a safe result
        print(f"Error in _run_fast_match: {e}")
        import traceback
        traceback.print_exc()
        return {
            "score_left": 0,
            "score_right": 0,
            "stats": {
                "left": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0},
                "right": {"hits": 0, "distance": 0, "reaction_sum": 0, "reaction_count": 0}
            },
            "match_metadata": metadata,
            "error": str(e)
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
    just_finished_match = False
    
    while running:
        # Process all available commands
        left_move = None
        right_move = None
        just_finished_match = False
        
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
                    just_finished_match = True
                    # Skip regular update loop after match to preserve MATCH_RESULT in queue
                    break
                    
            except multiprocessing.queues.Empty:
                break
        
        if not running:
            break

        # Skip regular game loop if we just finished a match (to preserve MATCH_RESULT in queue)
        if just_finished_match:
            continue

        # Only update the continuous game loop if in visual mode or if we have moves to process
        # In fast mode (non-visual), we only process PLAY_MATCH commands, no regular game loop
        if not visual_mode and not left_move and not right_move:
            # In fast mode with no moves, just wait a bit to avoid busy-waiting
            time.sleep(0.001)
            continue

        # Update Game (only in visual mode or when processing moves)
        score_data = game.update(left_move, right_move)
        
        # Get State
        state = game.get_state()
        
        # Add event data if any
        if score_data:
            state.update(score_data)
            
        # Send state back to main process (only in visual mode)
        # In fast mode, we don't send regular state updates - only MATCH_RESULT
        if visual_mode and not output_queue.full():
            try:
                output_queue.put(state)
            except:
                pass
            
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
        self.pending_match_result = None  # Store MATCH_RESULT separately
        
        # Mimic Game attributes for compatibility where possible
        self.score_left = 0
        self.score_right = 0
        self._score_font = None
        
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
                    # Store MATCH_RESULT separately so it doesn't get lost
                    self.pending_match_result = item
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
    
    def check_match_result(self):
        """
        Check if there's a pending MATCH_RESULT message.
        Returns the result data if available, None otherwise.
        This consumes the message (removes it after reading).
        """
        if self.pending_match_result:
            result = self.pending_match_result
            self.pending_match_result = None
            return result
        return None
        
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

    def draw(self, screen):
        """Renders the latest state to the provided Pygame surface."""
        if not self.visual_mode:
            return
        state = self.get_state()
        if not state:
            return

        screen.fill(config.BLACK)
        pygame.draw.line(screen, config.WHITE,
                         (config.SCREEN_WIDTH // 2, 0),
                         (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT), 2)

        # Draw paddles
        pygame.draw.rect(screen, config.WHITE,
                         (10, int(state["paddle_left_y"]), config.PADDLE_WIDTH, config.PADDLE_HEIGHT))
        pygame.draw.rect(screen, config.WHITE,
                         (config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH,
                          int(state["paddle_right_y"]),
                          config.PADDLE_WIDTH, config.PADDLE_HEIGHT))

        # Draw ball (state provides top-left corner)
        ball_center = (int(state["ball_x"]) + config.BALL_RADIUS,
                       int(state["ball_y"]) + config.BALL_RADIUS)
        pygame.draw.circle(screen, config.WHITE, ball_center, config.BALL_RADIUS)

        # Draw scores
        if pygame.font.get_init():
            if self._score_font is None:
                self._score_font = pygame.font.Font(None, 74)
            text_left = self._score_font.render(str(state["score_left"]), True, config.WHITE)
            text_right = self._score_font.render(str(state["score_right"]), True, config.WHITE)
            screen.blit(text_left, (config.SCREEN_WIDTH // 4 - text_left.get_width() // 2, 10))
            screen.blit(text_right, (config.SCREEN_WIDTH * 3 // 4 - text_right.get_width() // 2, 10))
