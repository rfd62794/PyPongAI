import pygame

class BaseState:
    def __init__(self, manager):
        self.manager = manager

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_input(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass
