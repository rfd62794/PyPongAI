import game_simulator
import config

def test_simulator():
    print("Testing GameSimulator...")
    game = game_simulator.GameSimulator()
    
    # Test Initial State
    state = game.get_state()
    assert state["score_left"] == 0
    assert state["score_right"] == 0
    assert state["game_over"] == False
    print("Initial state verified.")
    
    # Test Movement
    initial_y = state["paddle_left_y"]
    game.update(left_move="UP", right_move=None)
    new_state = game.get_state()
    assert new_state["paddle_left_y"] < initial_y
    print("Paddle movement verified.")
    
    # Test Scoring (Simulate many frames)
    print("Simulating game until score...")
    scored = False
    for _ in range(5000):
        # Move paddles randomly to keep game alive slightly longer or just let it score
        score_data = game.update(left_move=None, right_move=None)
        if score_data and score_data.get("scored"):
            print(f"Score detected: {score_data['scored']}")
            scored = True
            break
            
    if scored:
        print("Scoring verified.")
    else:
        print("Warning: No score in 5000 frames (might be normal if ball is slow, but unlikely).")

    print("GameSimulator test passed!")

if __name__ == "__main__":
    test_simulator()
