import pygame
import neat
import os
import pickle
import config
import game_engine
import game_simulator
import sys
import math
from states.base import BaseState
from model_manager import get_fitness_from_filename, delete_models
from utils import elo_manager
from match.recorder import MatchRecorder
from match import database as match_database
from match.parallel_engine import ParallelGameEngine
from match.analyzer import MatchAnalyzer
from agent_factory import AgentFactory

class LeagueState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        
        self.mode = "SETUP"  # SETUP, RUNNING, RESULTS, DASHBOARD
        self.models = []
        self.model_stats = {}  # {path: {"wins": 0, "losses": 0, "fitness": 0, "elo": 1200, ...}}
        self.current_match = None
        self.match_queue = []
        self.completed_matches = 0
        self.total_matches = 0
        
        # New Settings
        self.show_visuals = config.TOURNAMENT_VISUAL_DEFAULT
        self.min_fitness_threshold = config.TOURNAMENT_MIN_FITNESS_DEFAULT
        self.similarity_threshold = config.TOURNAMENT_SIMILARITY_THRESHOLD
        self.record_matches = False # Default to OFF
        
        # Deletion Tracking
        self.deleted_models = []
        self.deletion_reasons = {} # {path: reason}
        self.shutout_deletions = 0
        
        # Dashboard Button
        self.dashboard_button = pygame.Rect(config.SCREEN_WIDTH - 220, config.SCREEN_HEIGHT - 60, 200, 40)

        # UI
        self.start_button = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 400, 300, 50)
        self.back_button = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
        
        # Sliders
        self.fitness_slider = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 200, 300, 20)
        self.similarity_slider = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 300, 300, 20)
        self.dragging_fitness = False
        self.dragging_similarity = False
        
        # Dashboard State
        self.dashboard_view = "OVERVIEW"  # OVERVIEW, MODEL_DETAIL, MATCH_HISTORY, REPLAY
        self.selected_model = None  # For MODEL_DETAIL view
        self.selected_match = None  # For REPLAY view
        self.model_list_scroll = 0  # For scrolling through models
        self.match_history_scroll = 0  # For scrolling through matches

    def enter(self, **kwargs):
        self.mode = "SETUP"
        self.scan_models_for_league()
        
    def scan_models_for_league(self):
        self.models = []
        self.model_stats = {}
        
        # Load ELOs
        elo_ratings = elo_manager.load_elo_ratings()
        
        for root, dirs, files in os.walk(config.MODEL_DIR):
            for file in files:
                if file.endswith(".pkl"):
                    full_path = os.path.join(root, file)
                    fitness = get_fitness_from_filename(file)
                    self.models.append(full_path)
                    
                    # Get stored ELO or default
                    stored_elo = elo_ratings.get(file, config.ELO_INITIAL_RATING)
                    
                    self.model_stats[full_path] = {
                        "wins": 0,
                        "losses": 0,
                        "fitness": fitness,
                        "points_scored": 0,
                        "points_conceded": 0,
                        "elo": stored_elo,
                        "hits": 0,
                        "misses": 0,
                        "rallies": [],
                        "distance_moved": 0,
                        "total_reaction_time": 0,
                        "reaction_count": 0
                    }
        
        # Sort by fitness initially for display
        self.models.sort(key=lambda x: self.model_stats[x]["fitness"], reverse=True)

    def pre_filter_models(self):
        """Filter models based on minimum fitness threshold."""
        filtered_models = []
        for model_path in self.models:
            fitness = self.model_stats[model_path]["fitness"]
            if fitness >= self.min_fitness_threshold:
                filtered_models.append(model_path)
            else:
                self.deleted_models.append(model_path)
                self.deletion_reasons[model_path] = f"Low Fitness (< {self.min_fitness_threshold})"
        
        self.models = filtered_models
        print(f"Pre-filtered: {len(self.models)} models remaining.")

    def start_tournament(self):
        self.pre_filter_models()
        
        if len(self.models) < 2:
            print("Not enough models for a tournament!")
            return

        self.mode = "RUNNING"
        self.completed_matches = 0
        self.match_queue = []
        
        # Create Round Robin Schedule
        for i in range(len(self.models)):
            for j in range(i + 1, len(self.models)):
                self.match_queue.append((self.models[i], self.models[j]))
        if p1_path in self.deleted_models or p2_path in self.deleted_models:
            self.start_next_match()
            return

        # Choose engine based on visuals setting
        target_fps = 60 if self.show_visuals else 0
        game_instance = ParallelGameEngine(visual_mode=self.show_visuals, target_fps=target_fps)
        game_instance.start()

        self.current_match = {
            "p1": p1_path,
            "p2": p2_path,
            "game": game_instance,
            "net1": None,
            "net2": None,
            "is_visual": self.show_visuals,
            "waiting_for_result": not self.show_visuals
        }
        
        # Initialize Match Analyzer
        self.analyzer = MatchAnalyzer()
        
        # Initialize Match Recorder with metadata
        self.recorder = None
        if self.record_matches:
            metadata = {
                "p1_fitness": self.model_stats[p1_path]["fitness"],
                "p2_fitness": self.model_stats[p2_path]["fitness"],
                "p1_elo_before": self.model_stats[p1_path]["elo"],
                "p2_elo_before": self.model_stats[p2_path]["elo"]
            }
            self.recorder = MatchRecorder(
                os.path.basename(p1_path), 
                os.path.basename(p2_path),
                match_type="tournament",
                metadata=metadata
            )
        
        if not self.show_visuals:
            # FAST MODE: Send command to run full match in background
            local_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(local_dir, 'neat_config.txt')
            
            match_config = {
                "p1_path": p1_path,
                "p2_path": p2_path,
                "neat_config_path": config_path,
                "metadata": metadata
            }
            game_instance.input_queue.put({"type": "PLAY_MATCH", "config": match_config, "record_match": self.record_matches})
            return

        # VISUAL MODE: Load Genomes locally
        try:
            # We need the neat_config path. It's usually in the root.
            neat_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "neat_config.txt")
            
            agent1 = AgentFactory.create_agent(p1_path, neat_config_path)
            agent2 = AgentFactory.create_agent(p2_path, neat_config_path)
            
            self.current_match["agent1"] = agent1
            self.current_match["agent2"] = agent2
            
        except Exception as e:
            print(f"Error loading models: {e}")
            self.start_next_match()

    def calculate_elo_change(self, rating_a, rating_b, score_a, score_b):
        """Calculates ELO change based on match outcome."""
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        
        if score_a > score_b:
            actual_a = 1
        else:
            actual_a = 0
            
        change = config.ELO_K_FACTOR * (actual_a - expected_a)
        return change

    def check_for_shutout(self, loser_path, loser_score, winner_score):
        """Checks if the loss was a shutout (0 points) and deletes if enabled."""
        if config.TOURNAMENT_DELETE_SHUTOUTS and loser_score == 0 and winner_score >= 5:
            print(f"Shutout detected! Deleting {os.path.basename(loser_path)}")
            self.deleted_models.append(loser_path)
            self.deletion_reasons[loser_path] = "Shutout Loss (0 points)"
            self.shutout_deletions += 1
            
            if loser_path in self.models:
                self.models.remove(loser_path)
                
            delete_models([loser_path])
            elo_manager.remove_elo(os.path.basename(loser_path))

    def finish_match(self, score1, score2, stats, match_metadata):
        match = self.current_match
        p1 = match["p1"]
        p2 = match["p2"]
        
        # Update Stats
        self.model_stats[p1]["points_scored"] += score1
        self.model_stats[p1]["points_conceded"] += score2
        self.model_stats[p2]["points_scored"] += score2
        self.model_stats[p2]["points_conceded"] += score1
        
        # ELO Update
        elo1 = self.model_stats[p1]["elo"]
        elo2 = self.model_stats[p2]["elo"]
        
        change = self.calculate_elo_change(elo1, elo2, score1, score2)
        
        self.model_stats[p1]["elo"] += change
        self.model_stats[p2]["elo"] -= change
        
        # Save ELOs immediately
        elo_updates = {
            os.path.basename(p1): self.model_stats[p1]["elo"],
            os.path.basename(p2): self.model_stats[p2]["elo"]
        }
        elo_manager.update_bulk_elo(elo_updates)
        
        # Record Win/Loss
        if score1 > score2:
            self.model_stats[p1]["wins"] += 1
            self.model_stats[p2]["losses"] += 1
            self.check_for_shutout(p2, score2, score1)
        else:
            self.model_stats[p2]["wins"] += 1
            self.model_stats[p1]["losses"] += 1
            self.check_for_shutout(p1, score1, score2)
            
        # Consolidate Analyzer Stats
        self.model_stats[p1]["hits"] += stats["left"]["hits"]
        self.model_stats[p2]["hits"] += stats["right"]["hits"]
        
        self.model_stats[p1]["distance_moved"] += stats["left"]["distance"]
        self.model_stats[p2]["distance_moved"] += stats["right"]["distance"]
        
        self.model_stats[p1]["total_reaction_time"] += stats["left"]["reaction_sum"]
        self.model_stats[p1]["reaction_count"] += stats["left"]["reaction_count"]
        
        self.model_stats[p2]["total_reaction_time"] += stats["right"]["reaction_sum"]
        self.model_stats[p2]["reaction_count"] += stats["right"]["reaction_count"]
        
        # Save Match Recording and index it
        if match_metadata:
            # Add post-match ELO to metadata
            match_metadata["p1_elo_after"] = self.model_stats[p1]["elo"]
            match_metadata["p2_elo_after"] = self.model_stats[p2]["elo"]
            match_database.index_match(match_metadata)
        
        # Clean up engine
        if match["game"]:
            match["game"].stop()
        
        self.completed_matches += 1
        self.start_next_match()

    def prune_similar_models(self):
        """Prunes models that are too similar in fitness."""
        fitness_groups = {}
        for model in self.models:
            fit = self.model_stats[model]["fitness"]
            key = round(fit / self.similarity_threshold) * self.similarity_threshold
            if key not in fitness_groups:
                fitness_groups[key] = []
            fitness_groups[key].append(model)
            
        for key, group in fitness_groups.items():
            if len(group) > 1:
                group.sort(key=lambda x: self.model_stats[x]["elo"], reverse=True)
                keep = group[0]
                remove = group[1:]
                
                for m in remove:
                    self.deleted_models.append(m)
                    self.deletion_reasons[m] = f"Similarity Pruning (Group {key})"
                    if m in self.models:
                        self.models.remove(m)
                    delete_models([m])
                    elo_manager.remove_elo(os.path.basename(m))

    def finish_tournament(self):
        self.mode = "RESULTS"
        self.prune_similar_models()
        
        # Final Ranking
        self.models.sort(key=lambda x: self.model_stats[x]["elo"], reverse=True)
        
        # Keep top 10
        top_10 = self.models[:10]
        
        for m in self.models[10:]:
            self.deleted_models.append(m)
            self.deletion_reasons[m] = "Not in Top 10"
            delete_models([m])
            elo_manager.remove_elo(os.path.basename(m))
            
        self.models = top_10

    def handle_input(self, event):
        if self.mode == "SETUP":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.start_button.collidepoint(event.pos):
                    self.start_tournament()
                elif self.back_button.collidepoint(event.pos):
                    self.manager.change_state("menu")
                
                # Sliders
                if self.fitness_slider.collidepoint(event.pos):
                    self.dragging_fitness = True
                if self.similarity_slider.collidepoint(event.pos):
                    self.dragging_similarity = True
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_fitness = False
                self.dragging_similarity = False
                
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_fitness:
                    rel_x = event.pos[0] - self.fitness_slider.x
                    pct = max(0, min(1, rel_x / self.fitness_slider.width))
                    self.min_fitness_threshold = int(100 + pct * 400) # 100-500
                if self.dragging_similarity:
                    rel_x = event.pos[0] - self.similarity_slider.x
                    pct = max(0, min(1, rel_x / self.similarity_slider.width))
                    self.similarity_threshold = int(5 + pct * 45) # 5-50
            
            # Visual Toggle
            if event.type == pygame.MOUSEBUTTONDOWN:
                toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 150, 200, 40)
                if toggle_rect.collidepoint(event.pos):
                    self.show_visuals = not self.show_visuals

        elif self.mode == "RUNNING":
            # Visual Toggle
            if event.type == pygame.MOUSEBUTTONDOWN:
                toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 150, 10, 140, 40)
                if toggle_rect.collidepoint(event.pos):
                    self.show_visuals = not self.show_visuals
            
            # Toggle Recording
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.record_matches = not self.record_matches

            # Speed up if visuals off
            if not self.show_visuals:
                # Parallel engine handles speed, but we can call update multiple times per frame if we want even faster?
                # Actually, the parallel engine loop runs as fast as possible if target_fps=0.
                # But we need to pump events here.
                # Let's just call update once per frame here, and let the parallel engine handle the physics loop?
                # Wait, if we only call update once here, we only get one state update per frame.
                # If the parallel engine is running freely, it might be producing states faster than we consume.
                # But our update() logic sends commands. If we don't send commands, the AI doesn't move.
                # So we need to run this loop fast.
                for _ in range(10):
                    if self.current_match:
                        self.update(0)

        elif self.mode == "RESULTS":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.collidepoint(event.pos):
                    self.manager.change_state("menu")
                elif self.dashboard_button.collidepoint(event.pos):
                    self.manager.change_state("analytics")

    def update(self, dt):
        if self.mode == "RUNNING":
            if self.current_match:
                game = self.current_match["game"]
                
                # Check for fast match result
                if self.current_match.get("waiting_for_result"):
                    try:
                        while not game.output_queue.empty():
                            msg = game.output_queue.get_nowait()
                            if msg.get("type") == "MATCH_RESULT":
                                data = msg["data"]
                                self.finish_match(
                                    data["score_left"], 
                                    data["score_right"], 
                                    data["stats"], 
                                    data["match_metadata"]
                                )
                                return
                    except Exception:
                        pass
                    return

                # VISUAL MODE UPDATE
                agent1 = self.current_match["agent1"]
                agent2 = self.current_match["agent2"]
                
                state = game.get_state()
                
                # Update Analyzer
                self.analyzer.update(state)
                if self.recorder:
                    self.recorder.record_frame(state)
                
                # AI 1 (Left)
                left_move = agent1.get_move(state, "left")
                
                # AI 2 (Right)
                right_move = agent2.get_move(state, "right")
                
                game.update(left_move, right_move)
                
                target_score = config.VISUAL_MAX_SCORE if self.show_visuals else config.MAX_SCORE
                if game.score_left >= target_score or game.score_right >= target_score:
                    self.finish_match(
                        game.score_left, 
                        game.score_right, 
                        self.analyzer.get_stats(), 
                        self.recorder.save() if self.recorder else None
                    )
            else:
                self.start_next_match()

    def draw_setup(self, screen):
        screen.fill(config.BLACK)
        title = self.font.render("Tournament Setup", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Sliders
        pygame.draw.rect(screen, config.GRAY, self.fitness_slider)
        pygame.draw.rect(screen, config.WHITE, (self.fitness_slider.x + (self.min_fitness_threshold - 100)/400 * self.fitness_slider.width - 5, self.fitness_slider.y - 5, 10, 30))
        fit_text = self.small_font.render(f"Min Fitness: {self.min_fitness_threshold}", True, config.WHITE)
        screen.blit(fit_text, (self.fitness_slider.x, self.fitness_slider.y - 30))
        
        pygame.draw.rect(screen, config.GRAY, self.similarity_slider)
        pygame.draw.rect(screen, config.WHITE, (self.similarity_slider.x + (self.similarity_threshold - 5)/45 * self.similarity_slider.width - 5, self.similarity_slider.y - 5, 10, 30))
        sim_text = self.small_font.render(f"Similarity Threshold: {self.similarity_threshold}", True, config.WHITE)
        screen.blit(sim_text, (self.similarity_slider.x, self.similarity_slider.y - 30))
        
        # Visual Toggle
        toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 250, 150, 200, 40)
        color = (0, 100, 0) if self.show_visuals else (100, 0, 0)
        pygame.draw.rect(screen, color, toggle_rect)
        pygame.draw.rect(screen, config.WHITE, toggle_rect, 2)
        toggle_text = self.small_font.render("Visuals: " + ("ON" if self.show_visuals else "OFF"), True, config.WHITE)
        screen.blit(toggle_text, (toggle_rect.centerx - toggle_text.get_width()//2, toggle_rect.centery - toggle_text.get_height()//2))

        # Warning
        count = 0
        for m in self.models:
            if self.model_stats[m]["fitness"] >= self.min_fitness_threshold:
                count += 1
        warn_text = self.small_font.render(f"Models Qualified: {count} / {len(self.models)}", True, config.YELLOW if count > 0 else config.RED)
        screen.blit(warn_text, (config.SCREEN_WIDTH//2 - warn_text.get_width()//2, 350))

        # Start Button
        pygame.draw.rect(screen, (0, 100, 0), self.start_button)
        start_text = self.font.render("Start Tournament", True, config.WHITE)
        screen.blit(start_text, (self.start_button.centerx - start_text.get_width()//2, self.start_button.centery - start_text.get_height()//2))
        
        # Back Button
        pygame.draw.rect(screen, (100, 0, 0), self.back_button)
        back_text = self.small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))

    def draw_running(self, screen):
        if self.show_visuals:
            if self.current_match:
                # Only draw if it's a visual game instance
                if self.current_match.get("is_visual", True):
                    self.current_match["game"].draw(screen)
                else:
                    screen.fill(config.BLACK)
                    text = self.font.render("Fast Mode (Visuals Disabled for this Match)", True, config.WHITE)
                    screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
        else:
            screen.fill(config.BLACK)
            text = self.font.render("Tournament Running (Fast Mode)...", True, config.WHITE)
            screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, config.SCREEN_HEIGHT//2))
        
        # Overlay Info
        info = f"Match {self.completed_matches + 1} / {self.total_matches}"
        info_surf = self.small_font.render(info, True, config.WHITE)
        screen.blit(info_surf, (10, 10))
        
        # Deletion Counter
        del_text = f"Deleted: {len(self.deleted_models)}"
        del_surf = self.small_font.render(del_text, True, config.RED)
        screen.blit(del_surf, (10, 40))
        
        # Visual Toggle Button
        toggle_rect = pygame.Rect(config.SCREEN_WIDTH - 150, 10, 140, 40)
        color = (0, 100, 0) if self.show_visuals else (100, 0, 0)
        pygame.draw.rect(screen, color, toggle_rect)
        toggle_text = self.small_font.render("Visuals: " + ("ON" if self.show_visuals else "OFF"), True, config.WHITE)
        screen.blit(toggle_text, (toggle_rect.centerx - toggle_text.get_width()//2, toggle_rect.centery - toggle_text.get_height()//2))

        # Recording Status
        rec_text = f"Recording: {'ON' if self.record_matches else 'OFF'} (Press R)"
        rec_surf = self.small_font.render(rec_text, True, config.RED if self.record_matches else config.GRAY)
        screen.blit(rec_surf, (config.SCREEN_WIDTH - 250, 60))

    def draw_results(self, screen):
        screen.fill(config.BLACK)
        title = self.font.render("Tournament Results", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Survivor Stats
        y = 100
        header = self.small_font.render("Rank | Model | ELO | W-L | Fit", True, config.GRAY)
        screen.blit(header, (50, y))
        y += 30
        
        for i, model in enumerate(self.models[:10]): # Top 10
            stats = self.model_stats[model]
            name = os.path.basename(model)
            text = f"{i+1}. {name[:15]}... | {int(stats['elo'])} | {stats['wins']}-{stats['losses']} | {stats['fitness']}"
            surf = self.small_font.render(text, True, config.WHITE)
            screen.blit(surf, (50, y))
            y += 30
            
        # Deletion Stats
        y = 100
        x = config.SCREEN_WIDTH // 2 + 50
        header2 = self.small_font.render("Deletion Statistics", True, config.GRAY)
        screen.blit(header2, (x, y))
        y += 30
        
        stats_text = [
            f"Total Deleted: {len(self.deleted_models)}",
            f"Shutouts (5-0): {self.shutout_deletions}",
            f"Low Fitness: {list(self.deletion_reasons.values()).count(f'Low Fitness (< {self.min_fitness_threshold})')}"
        ]
        
        for line in stats_text:
            surf = self.small_font.render(line, True, config.RED)
            screen.blit(surf, (x, y))
            y += 30

        # Dashboard Button
        pygame.draw.rect(screen, (0, 0, 150), self.dashboard_button)
        dash_text = self.small_font.render("Analytics Dashboard", True, config.WHITE)
        screen.blit(dash_text, (self.dashboard_button.centerx - dash_text.get_width()//2, self.dashboard_button.centery - dash_text.get_height()//2))

        # Back Button
        pygame.draw.rect(screen, (100, 0, 0), self.back_button)
        back_text = self.small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))
        back_text = self.small_font.render("< Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))
    
    def draw_dashboard_replay(self, screen):
        """Replay viewer (placeholder for now)."""
        screen.fill(config.BLACK)
        title = self.font.render("Replay Viewer - Coming Soon", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, config.SCREEN_HEIGHT//2))
        
        # Back Button
        pygame.draw.rect(screen, (100, 0, 0), self.back_button)
        back_text = self.small_font.render("< Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))

    def draw(self, screen):
        if self.mode == "SETUP":
            self.draw_setup(screen)
        elif self.mode == "RUNNING":
            self.draw_running(screen)
        elif self.mode == "RESULTS":
            self.draw_results(screen)
        elif self.mode == "DASHBOARD":
            self.draw_dashboard(screen)
