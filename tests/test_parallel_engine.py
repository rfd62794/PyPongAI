import unittest
import time
from match.parallel_engine import ParallelGameEngine
from core import config

class TestParallelEngine(unittest.TestCase):
    def test_engine_starts_and_stops(self):
        print("Testing Start/Stop...")
        engine = ParallelGameEngine(visual_mode=False, target_fps=0)
        engine.start()
        self.assertIsNotNone(engine.process)
        self.assertTrue(engine.process.is_alive())
        engine.stop()
        self.assertIsNone(engine.process)
        print("Start/Stop Passed.")

    def test_state_updates(self):
        print("Testing State Updates...")
        engine = ParallelGameEngine(visual_mode=False, target_fps=0)
        engine.start()
        
        # Wait for initial state
        time.sleep(0.1)
        state = engine.get_state()
        self.assertIsNotNone(state)
        self.assertIn("ball_x", state)
        
        # Send move multiple times to ensure movement
        for _ in range(10):
            engine.update(left_move="UP")
            time.sleep(0.01)
        
        # Fetch new state
        engine.update()
        
        new_state = engine.get_state()
        print(f"DEBUG: Old Y: {state['paddle_left_y']}, New Y: {new_state['paddle_left_y']}")
        self.assertNotEqual(state["paddle_left_y"], new_state["paddle_left_y"])
        
        engine.stop()
        print("State Updates Passed.")

    def test_performance_non_visual(self):
        print("Testing Non-Visual Performance...")
        engine = ParallelGameEngine(visual_mode=False, target_fps=0)
        engine.start()
        
        start_time = time.time()
        frames = 0
        while time.time() - start_time < 1.0:
            engine.update()
            frames += 1
            
        engine.stop()
        print(f"Non-Visual Frames per Second: {frames}")
        self.assertGreater(frames, 100) # Should be very fast
        print("Non-Visual Performance Passed.")

    def test_performance_visual_capped(self):
        print("Testing Visual FPS Cap...")
        target = 30
        engine = ParallelGameEngine(visual_mode=True, target_fps=target)
        engine.start()
        
        # We can't easily measure the internal FPS of the subprocess from here without more IPC.
        # But we can check if it runs without crashing.
        # And we can check if update() returns reasonably fast (it shouldn't block).
        
        start_time = time.time()
        for _ in range(10):
            engine.update()
            time.sleep(1/30) # Simulate main loop
            
        engine.stop()
        print("Visual FPS Cap Test Ran (Visual verification needed for exact FPS).")

if __name__ == '__main__':
    unittest.main()
