"""Training reporters providing UI feedback during NEAT evolution."""

import datetime
import os
import pickle
import sys
from typing import Optional

import neat
import pygame

from core import config
from ai.opponents import get_rule_based_move
from match.parallel_engine import ParallelGameEngine


class UIProgressReporter(neat.reporting.BaseReporter):
    """Reporter that renders lightweight textual progress updates."""

    def __init__(self, screen: pygame.Surface, logger: Optional[object] = None):
        self.screen = screen
        self.logger = logger
        self.generation = 0
        self.font = pygame.font.Font(None, 36)
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def start_generation(self, generation: int) -> None:
        self.generation = generation
        print(f"--- Starting Generation {generation} ---")

        self.screen.fill(config.BLACK)
        text = self.font.render(
            f"Training Generation {generation} (Fast Mode)...", True, config.WHITE
        )
        self.screen.blit(
            text,
            (
                config.SCREEN_WIDTH // 2 - text.get_width() // 2,
                config.SCREEN_HEIGHT // 2,
            ),
        )

        sub = self.font.render("Check console for details.", True, config.GRAY)
        self.screen.blit(
            sub,
            (
                config.SCREEN_WIDTH // 2 - sub.get_width() // 2,
                config.SCREEN_HEIGHT // 2 + 40,
            ),
        )

        pygame.display.flip()
        pygame.event.pump()

    def end_generation(self, config_neat, population, species_set) -> None:
        best_genome = None
        best_fitness = -float("inf")
        total_fitness = 0
        count = 0
        best_elo = 0

        for genome in population.values():
            if genome.fitness is None:
                continue
            total_fitness += genome.fitness
            count += 1
            if genome.fitness > best_fitness:
                best_fitness = genome.fitness
                best_genome = genome
                if hasattr(genome, "elo_rating"):
                    best_elo = genome.elo_rating

        avg_fitness = total_fitness / count if count > 0 else 0

        if best_genome:
            print(f"Generation {self.generation} Best Fitness: {best_fitness}")
            self._save_checkpoint(best_genome)

        if self.logger:
            self.logger.log_generation(
                self.generation,
                best_fitness,
                avg_fitness,
                best_elo,
                len(species_set.species),
            )

        pygame.event.pump()

    def _save_checkpoint(self, genome) -> None:
        filename = f"gen_{self.generation}_fit_{int(genome.fitness)}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        with open(filepath, "wb") as fh:
            pickle.dump(genome, fh)


class VisualReporter(neat.reporting.BaseReporter):
    """Reporter that pauses training to visually showcase best genomes."""

    def __init__(self, config_neat, screen: pygame.Surface, logger: Optional[object] = None):
        self.config_neat = config_neat
        self.screen = screen
        self.logger = logger
        self.generation = 0
        self.checkpoint_dir = os.path.join(config.MODEL_DIR, "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.font = pygame.font.Font(None, 36)

    def start_generation(self, generation: int) -> None:
        self.generation = generation
        print(f"--- Starting Generation {generation} ---")

        self.screen.fill(config.BLACK)
        text = self.font.render(f"Training Generation {generation}...", True, config.WHITE)
        self.screen.blit(
            text,
            (
                config.SCREEN_WIDTH // 2 - text.get_width() // 2,
                config.SCREEN_HEIGHT // 2,
            ),
        )
        pygame.display.flip()
        pygame.event.pump()

    def end_generation(self, config_neat, population, species_set) -> None:
        best_genome = None
        best_fitness = -float("inf")
        total_fitness = 0
        count = 0
        best_elo = 0

        for genome in population.values():
            if genome.fitness is None:
                continue
            total_fitness += genome.fitness
            count += 1
            if genome.fitness > best_fitness:
                best_fitness = genome.fitness
                best_genome = genome
                if hasattr(genome, "elo_rating"):
                    best_elo = genome.elo_rating

        avg_fitness = total_fitness / count if count > 0 else 0

        if best_genome:
            print(f"Generation {self.generation} Best Fitness: {best_fitness}")
            self._save_checkpoint(best_genome)
            self._visualize_best(best_genome)

        if self.logger:
            self.logger.log_generation(
                self.generation,
                best_fitness,
                avg_fitness,
                best_elo,
                len(species_set.species),
            )

    def _save_checkpoint(self, genome) -> None:
        filename = f"gen_{self.generation}_fit_{int(genome.fitness)}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        with open(filepath, "wb") as fh:
            pickle.dump(genome, fh)
        print(f"Saved checkpoint: {filename}")

    def _visualize_best(self, genome) -> None:
        print("Visualizing best genome... (Press SPACE to skip)")

        clock = pygame.time.Clock()
        game = ParallelGameEngine(visual_mode=True, target_fps=config.FPS)
        game.start()

        net = neat.nn.FeedForwardNetwork.create(genome, self.config_neat)

        running = True
        while running:
            clock.tick(config.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    running = False

            state = game.get_state()
            inputs = (
                state["paddle_left_y"] / config.SCREEN_HEIGHT,
                state["ball_x"] / config.SCREEN_WIDTH,
                state["ball_y"] / config.SCREEN_HEIGHT,
                state["ball_vel_x"] / config.BALL_MAX_SPEED,
                state["ball_vel_y"] / config.BALL_MAX_SPEED,
                (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                1.0 if state["ball_vel_x"] < 0 else 0.0,
                state["paddle_right_y"] / config.SCREEN_HEIGHT,
            )
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = "UP" if action_idx == 0 else "DOWN" if action_idx == 1 else None

            right_move = get_rule_based_move(state, "right")
            game.update(left_move, right_move)

            game.draw(self.screen)

            info_text = self.font.render(
                f"Gen {self.generation} Best - Press SPACE to Resume", True, config.WHITE
            )
            self.screen.blit(info_text, (10, config.SCREEN_HEIGHT - 40))

            pygame.display.flip()

            if (
                game.score_left >= config.VISUAL_MAX_SCORE
                or game.score_right >= config.VISUAL_MAX_SCORE
            ):
                running = False

        game.stop()
