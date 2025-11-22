import time
from match.parallel_engine import ParallelGameEngine

def test():
    print("Starting Engine...")
    engine = ParallelGameEngine(visual_mode=False, target_fps=0)
    engine.start()
    
    time.sleep(0.5)
    state = engine.get_state()
    print(f"Initial Y: {state['paddle_left_y']}")
    
    print("Sending UP commands...")
    for _ in range(10):
        engine.update(left_move="UP")
        time.sleep(0.02)
        
    print("Fetching final state...")
    engine.update() # Fetch
    state = engine.get_state()
    print(f"Final Y: {state['paddle_left_y']}")
    
    if state['paddle_left_y'] < 300:
        print("SUCCESS: Paddle moved up.")
    else:
        print("FAILURE: Paddle did not move.")
        
    engine.stop()
    print("Engine stopped.")

if __name__ == "__main__":
    test()
