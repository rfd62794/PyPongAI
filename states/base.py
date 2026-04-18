import pygame

class BaseState:
    def __init__(self, manager):
        self.manager = manager

    # Keyboard command mappings (override per state if needed)
    KEYBOARD_COMMANDS = {
        "escape": "back_to_menu",
        "p": "go_play",
        "t": "go_train",
        "l": "go_league",
        "m": "go_models",
        "a": "go_analytics",
        "s": "start_action",
        "c": "compare_mode",
        "q": "quit",
    }
    
    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_input(self, event):
        """Default input handling with keyboard command routing."""
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key).lower()
            self.handle_keyboard_command(key_name)

    def handle_keyboard_command(self, key_name: str):
        """Route keyboard commands to state transitions."""
        cmd = self.KEYBOARD_COMMANDS.get(key_name)
        
        if cmd == "back_to_menu":
            self.manager.change_state("menu")
        elif cmd == "go_play":
            self.manager.change_state("game")
        elif cmd == "go_train":
            self.manager.change_state("train")
        elif cmd == "go_league":
            self.manager.change_state("league")
        elif cmd == "go_models":
            self.manager.change_state("models")
        elif cmd == "go_analytics":
            self.manager.change_state("analytics")
        elif cmd == "compare_mode":
            self.manager.change_state("compare")
        elif cmd == "start_action":
            self.on_start_action()
        elif cmd == "quit":
            pygame.quit()
            import sys
            sys.exit(0)

    def on_start_action(self):
        """Override in subclasses for 'S' key handling."""
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass
