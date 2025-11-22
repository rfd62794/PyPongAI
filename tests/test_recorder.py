import human_recorder
import os
import shutil

def test_recorder():
    print("Testing HumanRecorder...")
    recorder = human_recorder.HumanRecorder()
    
    # Mock data
    state = {
        "ball_x": 100, "ball_y": 100,
        "ball_vel_x": 5, "ball_vel_y": 5,
        "paddle_left_y": 50, "paddle_right_y": 50
    }
    
    recorder.record_frame(state, "UP")
    recorder.record_frame(state, "DOWN")
    recorder.record_frame(state, None)
    
    filepath = recorder.filepath
    recorder.close()
    
    if os.path.exists(filepath):
        print(f"Recorder created file: {filepath}")
        with open(filepath, 'r') as f:
            lines = f.readlines()
            print(f"Lines written: {len(lines)}")
            if len(lines) == 4: # Header + 3 rows
                print("SUCCESS: Recorder wrote correct number of lines.")
            else:
                print("FAILURE: Incorrect line count.")
        
        # Cleanup
        os.remove(filepath)
        # Remove dir if empty
        try:
            os.rmdir("human_data")
        except:
            pass
    else:
        print("FAILURE: File not created.")

if __name__ == "__main__":
    test_recorder()
