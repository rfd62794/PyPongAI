import multiprocessing
import time
import config
import game_engine
import game_simulator

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
                        # print(f"DEBUG: Processing LEFT {left_move}")
                    elif cmd["paddle"] == "right":
                        right_move = cmd["action"]
            except multiprocessing.queues.Empty:
                break
        
        if not running:
            break

        # Update Game
        score_data = game.update(left_move, right_move)
        # if left_move:
        #    print(f"DEBUG: Paddle Left Y: {game.left_paddle.rect.y}, Speed: {game.left_paddle.speed}")
        
        # Get State
        state = game.get_state()
        
        # Add event data if any
        if score_data:
            state.update(score_data)
            
        # Send state back to main process
        # clear old state to prevent backlog if main process is slow? 
        # For now, just put it. If queue is full, we might want to drop frames or block.
        # Let's assume the main process consumes fast enough.
        if not output_queue.full():
            output_queue.put(state)
            
        # Frame Rate Control
        if visual_mode and target_fps > 0:
            clock.tick(target_fps)
        elif not visual_mode and target_fps > 0:
            # Manual sleep for non-visual if requested
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
        # We want to drain the queue to get the absolute latest state
        new_state = None
        try:
            while not self.output_queue.empty():
                new_state = self.output_queue.get_nowait()
        except multiprocessing.queues.Empty:
            pass
            
        if new_state:
            self.latest_state = new_state
            self.score_left = new_state["score_left"]
            self.score_right = new_state["score_right"]
            
            # Check for events to return
            # The game engine returns a dict if event, None if not.
            # Our state always exists. We need to check if "scored" or "hit" keys are present.
            if "scored" in new_state or "hit_left" in new_state or "hit_right" in new_state:
                return new_state
            return None
            
        return None

    def get_state(self):
        if self.latest_state:
            return self.latest_state
        # Return default state if nothing received yet
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

    def draw(self, screen):
        """
        Draws the game state to the screen.
        """
        if not self.latest_state:
            return

        screen.fill(config.BLACK)
        
        # Draw Net
        game_engine.pygame.draw.line(screen, config.WHITE, (config.SCREEN_WIDTH // 2, 0), (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT), 2)
        
        # Draw Scores
        if game_engine.pygame.font.get_init():
            font = game_engine.pygame.font.Font(None, 74)
            text_left = font.render(str(self.score_left), 1, config.WHITE)
            screen.blit(text_left, (config.SCREEN_WIDTH // 4, 10))
            text_right = font.render(str(self.score_right), 1, config.WHITE)
            screen.blit(text_right, (config.SCREEN_WIDTH * 3 // 4, 10))
        
        # Draw Paddles
        left_rect = game_engine.pygame.Rect(10, self.latest_state["paddle_left_y"], config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
        right_rect = game_engine.pygame.Rect(config.SCREEN_WIDTH - 10 - config.PADDLE_WIDTH, self.latest_state["paddle_right_y"], config.PADDLE_WIDTH, config.PADDLE_HEIGHT)
        
        game_engine.pygame.draw.rect(screen, config.WHITE, left_rect)
        game_engine.pygame.draw.rect(screen, config.WHITE, right_rect)
        
        # Draw Ball
        ball_rect = game_engine.pygame.Rect(self.latest_state["ball_x"], self.latest_state["ball_y"], config.BALL_RADIUS * 2, config.BALL_RADIUS * 2)
        game_engine.pygame.draw.ellipse(screen, config.WHITE, ball_rect)
