"""Tests for TrainState orchestration and reporter wiring."""

import types

import pygame
import pytest

from ai import ai_module
from states.train import TrainState
from training import reporters


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


class DummyManager:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.changed_to = None

    def change_state(self, key):
        self.changed_to = key


def make_population():
    genome = types.SimpleNamespace(fitness=10, elo_rating=1200)
    return {1: genome}


def test_train_state_uses_visual_reporter(monkeypatch):
    manager = DummyManager()
    state = TrainState(manager)
    state.visual_mode = True
    state.use_best_seed = False

    added_reporters = []

    def fake_add_reporter(reporter):
        added_reporters.append(reporter)

    class DummyPopulation:
        def __init__(self):
            self.reporters = types.SimpleNamespace(reporters=[])

        def add_reporter(self, reporter):
            fake_add_reporter(reporter)

        def run(self, fn, generations):
            return types.SimpleNamespace(fitness=42)

    monkeypatch.setattr("neat.Population", lambda cfg: DummyPopulation())
    monkeypatch.setattr(reporters, "UIProgressReporter", type("FakeUI", (), {}))
    monkeypatch.setattr(reporters, "VisualReporter", type("FakeVisual", (), {}))

    state.start_training()

    reporter_types = {rep.__class__.__name__ for rep in added_reporters}
    assert "FakeVisual" in reporter_types


def test_train_state_turns_off_visual(monkeypatch):
    manager = DummyManager()
    state = TrainState(manager)
    state.visual_mode = False
    state.use_best_seed = False

    added_reporters = []

    class DummyPopulation:
        def add_reporter(self, reporter):
            added_reporters.append(reporter)

        def run(self, fn, generations):
            return types.SimpleNamespace(fitness=1)

    monkeypatch.setattr("neat.Population", lambda cfg: DummyPopulation())
    monkeypatch.setattr(reporters, "UIProgressReporter", type("FakeUI", (), {}))
    monkeypatch.setattr(reporters, "VisualReporter", type("FakeVisual", (), {}))

    state.start_training()

    reporter_names = {rep.__class__.__name__ for rep in added_reporters}
    assert "FakeVisual" not in reporter_names
    assert "FakeUI" in reporter_names


def test_train_state_returns_to_menu(monkeypatch):
    manager = DummyManager()
    state = TrainState(manager)
    state.visual_mode = False
    state.use_best_seed = False

    class DummyPopulation:
        def add_reporter(self, reporter):
            pass

        def run(self, fn, generations):
            return types.SimpleNamespace(fitness=1)

    monkeypatch.setattr("neat.Population", lambda cfg: DummyPopulation())

    state.start_training()

    assert manager.changed_to == "menu"
