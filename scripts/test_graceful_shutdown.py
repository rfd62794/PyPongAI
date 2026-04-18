"""Test graceful shutdown behavior for PyPongAI."""

import subprocess
import time
import os
import signal
import sys
from pathlib import Path

def test_shutdown_in_menu():
    """Test CTRL+C in menu state."""
    print("Test 1: CTRL+C in Menu")
    print("-" * 50)
    
    # Run from root
    root_dir = Path(__file__).parent.parent
    
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=str(root_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    
    # Wait for app to start
    time.sleep(3)
    
    # Send CTRL+C
    if os.name == 'nt':
        proc.send_signal(signal.CTRL_C_EVENT)
    else:
        proc.send_signal(signal.SIGINT)
    
    # Wait for exit
    try:
        stdout, stderr = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        print("Error: Process did not exit in time")
        proc.kill()
        stdout, stderr = proc.communicate()
    
    # Check results
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr}")
    
    assert "PyPongAI exited cleanly" in stdout or "PyPongAI exited cleanly" in stderr, "Should log clean exit"
    assert "Traceback" not in stderr, "Should not have tracebacks"
    
    print(f"[OK] Process exited cleanly")
    print()


def test_multiple_restarts():
    """Test multiple start/stop cycles."""
    print("Test 2: Multiple Shutdown Cycles")
    print("-" * 50)
    
    root_dir = Path(__file__).parent.parent
    
    for i in range(3):
        proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(root_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        time.sleep(2)
        if os.name == 'nt':
            proc.send_signal(signal.CTRL_C_EVENT)
        else:
            proc.send_signal(signal.SIGINT)
        
        stdout, stderr = proc.communicate(timeout=10)
        
        assert "PyPongAI exited cleanly" in stdout or "PyPongAI exited cleanly" in stderr
        assert "Traceback" not in stderr
        print(f"  Cycle {i+1}: [OK]")
    
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("PyPongAI Graceful Shutdown Tests")
    print("=" * 50)
    print()
    
    try:
        test_shutdown_in_menu()
        test_multiple_restarts()
        
        print("=" * 50)
        print("All tests passed! [OK]")
        print("=" * 50)
    
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Unexpected error: {e}")
        sys.exit(1)
