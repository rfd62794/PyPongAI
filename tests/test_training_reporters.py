"""Tests for training reporters module."""

import types

import pytest

from ai import ai_module
from training import reporters
from training.reporters import CSVReporter, ValidationReporter


class DummyGenome:
    """Simple genome stand-in for reporter tests."""

    def __init__(self, fitness):
        self.fitness = fitness


@pytest.fixture
def restore_hof():
    original = list(ai_module.HALL_OF_FAME)
    ai_module.HALL_OF_FAME = []
    try:
        yield
    finally:
        ai_module.HALL_OF_FAME = original


def test_validation_reporter_records_hof(monkeypatch, restore_hof):
    reporter = ValidationReporter()
    reporter.start_generation(5)

    captured = {}

    def fake_validate(genome, config_neat, generation):
        captured["args"] = (genome, config_neat, generation)
        return 2.5, 0.75

    monkeypatch.setattr(reporters, "validate_genome", fake_validate)

    population = {
        1: DummyGenome(1.0),
        2: DummyGenome(5.0),
    }

    reporter.end_generation(object(), population, types.SimpleNamespace())

    assert captured["args"][0] is population[2]
    assert captured["args"][2] == 5
    assert len(ai_module.HALL_OF_FAME) == 1


def test_validation_reporter_skips_hof_when_not_interval(monkeypatch, restore_hof):
    reporter = ValidationReporter()
    reporter.start_generation(4)

    monkeypatch.setattr(reporters, "validate_genome", lambda genome, cfg, gen: (1.0, 0.5))

    population = {1: DummyGenome(3.0)}

    reporter.end_generation(object(), population, types.SimpleNamespace())

    assert ai_module.HALL_OF_FAME == []


def test_csv_reporter_writes_row(tmp_path, monkeypatch):
    csv_path = tmp_path / "stats.csv"
    reporter = CSVReporter(str(csv_path))
    reporter.start_generation(3)

    monkeypatch.setattr(reporters, "validate_genome", lambda genome, cfg, gen: (1.0, 0.5))

    population = {
        1: DummyGenome(2.0),
        2: DummyGenome(4.0),
    }

    reporter.end_generation(object(), population, types.SimpleNamespace())

    contents = csv_path.read_text().strip().splitlines()
    assert contents, "CSV reporter should append a row"
    last_row = contents[-1].split(",")
    assert last_row[0] == "3"
    assert last_row[-2:] == ["1.0", "0.5"]
