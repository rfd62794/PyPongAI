"""
Automation Bridge: Receives commands via stdin, converts to pygame events.

Enables ContentEngine to control PyPongAI without synthetic keyboard input.
Works in background thread, doesn't block game loop.
"""

import json
import sys
import threading
import logging
from typing import Optional
import pygame

logger = logging.getLogger(__name__)


class AutomationBridge:
    """
    Listens on stdin for JSON commands and posts pygame events.
    
    Runs in background thread to avoid blocking game loop.
    """
    
    # Map command to pygame key constant
    KEY_MAP = {
        "p": pygame.K_p,
        "s": pygame.K_s,
        "t": pygame.K_t,
        "l": pygame.K_l,
        "m": pygame.K_m,
        "a": pygame.K_a,
        "c": pygame.K_c,
        "n": pygame.K_n,
        "r": pygame.K_r,
        "escape": pygame.K_ESCAPE,
        "q": pygame.K_q,
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "space": pygame.K_SPACE,
        "enter": pygame.K_RETURN,
        "return": pygame.K_RETURN,
    }
    
    def __init__(self, enabled: bool = True):
        """
        Initialize automation bridge.
        """
        self.enabled = enabled
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the automation bridge listener thread."""
        if not self.enabled:
            logger.debug("Automation bridge disabled")
            return
        
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info("Automation bridge started (listening on stdin)")
    
    def stop(self):
        """Stop the automation bridge."""
        if not self.running:
            return
        
        self.running = False
        # Thread is daemon, so we don't strictly need to join if process is exiting
    
    def _listen_loop(self):
        """Main listening loop: read JSON from stdin, post pygame events."""
        try:
            # We don't use 'for line in sys.stdin' because it's heavily buffered.
            # Reading line by line manually.
            while self.running:
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    self._handle_command(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {line}")
                except Exception as e:
                    logger.error(f"Error handling command: {e}")
        
        except Exception as e:
            logger.debug(f"Automation bridge loop exit: {e}")
        finally:
            self.running = False
    
    def _handle_command(self, data: dict):
        """Handle a command dict."""
        command = data.get("command")
        
        if command == "press":
            key = data.get("key", "").lower()
            duration_ms = data.get("duration_ms", 100)
            self._post_keypress(key, duration_ms)
        
        elif command == "ping":
            # Test command
            print(json.dumps({"pong": True, "status": "active"}), flush=True)
        
        elif command == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            
        else:
            logger.warning(f"Unknown command: {command}")
    
    def _post_keypress(self, key: str, duration_ms: int = 50):
        """Post a keypress event to pygame."""
        if key not in self.KEY_MAP:
            logger.warning(f"Unknown key: {key}")
            return
        
        key_code = self.KEY_MAP[key]
        
        try:
            # Post KEYDOWN event
            # Use a dummy scancode if needed, but 'key' is what BaseState uses
            keydown_event = pygame.event.Event(
                pygame.KEYDOWN,
                key=key_code,
                mod=pygame.KMOD_NONE,
                unicode=key if len(key) == 1 else ""
            )
            pygame.event.post(keydown_event)
            
            # If duration is requested, we'd need a sub-thread or timer.
            # For navigation, a KEYDOWN is usually enough if the state manager 
            # consumes it immediately. 
            # We'll post a KEYUP shortly after to be safe.
            def release():
                threading.Event().wait(duration_ms / 1000.0)
                keyup_event = pygame.event.Event(
                    pygame.KEYUP,
                    key=key_code,
                    mod=pygame.KMOD_NONE
                )
                pygame.event.post(keyup_event)
                
            threading.Thread(target=release, daemon=True).start()
            logger.debug(f"Injected keypress: {key}")
        
        except Exception as e:
            logger.error(f"Failed to post keypress {key}: {e}")
