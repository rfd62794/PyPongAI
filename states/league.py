import pygame
import neat
import os
import pickle
import config
import game_engine
import sys
import math
from states.base import BaseState
from model_manager import get_fitness_from_filename, delete_models
import elo_manager
from match_recorder import MatchRecorder
import match_database

class MatchAnalyzer:
    def __init__(self):
        self.stats = {
            "left": {"hits": 0, "distance": 0, "reaction_frames": [], "last_ball_vel_x": 0, "last_paddle_y": 0, "bounce_frame": None},
            "right": {"hits": 0, "distance": 0, "reaction_frames": [], "last_ball_vel_x": 0, "last_paddle_y": 0, "bounce_frame": None}
        }
        self.rally_length = 0
        self.rallies = []
        self.frame_count = 0
        
    def update(self, game_state):
        self.frame_count += 1
        ball_vel_x = game_state["ball_vel_x"]
        
        # Initialize last_paddle_y on first frame
        if self.frame_count == 1:
             self.stats["left"]["last_paddle_y"] = game_state["paddle_left_y"]
             self.stats["right"]["last_paddle_y"] = game_state["paddle_right_y"]
             
        # Distance Tracking
        dist_left = abs(game_state["paddle_left_y"] - self.stats["left"]["last_paddle_y"])
        self.stats["left"]["distance"] += dist_left
        self.stats["left"]["last_paddle_y"] = game_state["paddle_left_y"]
        
        dist_right = abs(game_state["paddle_right_y"] - self.stats["right"]["last_paddle_y"])
        self.stats["right"]["distance"] += dist_right
        self.stats["right"]["last_paddle_y"] = game_state["paddle_right_y"]

        # Hit Detection & Bounce Recording
        if ball_vel_x > 0 and self.stats["left"]["last_ball_vel_x"] < 0:
            self.stats["left"]["hits"] += 1
            self.stats["right"]["bounce_frame"] = self.frame_count # Ball heading to Right
            
        elif ball_vel_x < 0 and self.stats["right"]["last_ball_vel_x"] > 0:
            self.stats["right"]["hits"] += 1
            self.stats["left"]["bounce_frame"] = self.frame_count # Ball heading to Left
            
        self.stats["left"]["last_ball_vel_x"] = ball_vel_x
        self.stats["right"]["last_ball_vel_x"] = ball_vel_x
        
        # Reaction Time Logic
        if ball_vel_x < 0 and self.stats["left"]["bounce_frame"] is not None:
            if dist_left > 0.5: # Significant movement
                reaction = self.frame_count - self.stats["left"]["bounce_frame"]
                self.stats["left"]["reaction_frames"].append(reaction)
                self.stats["left"]["bounce_frame"] = None 
        
        if ball_vel_x > 0 and self.stats["right"]["bounce_frame"] is not None:
            if dist_right > 0.5:
                reaction = self.frame_count - self.stats["right"]["bounce_frame"]
                self.stats["right"]["reaction_frames"].append(reaction)
                self.stats["right"]["bounce_frame"] = None

    def get_stats(self):
        return {
            "left": {
                "hits": self.stats["left"]["hits"],
                "reaction_sum": sum(self.stats["left"]["reaction_frames"]),
                "reaction_count": len(self.stats["left"]["reaction_frames"]),
                "distance": self.stats["left"]["distance"]
            },
            "right": {
                "hits": self.stats["right"]["hits"],
                "reaction_sum": sum(self.stats["right"]["reaction_frames"]),
                "reaction_count": len(self.stats["right"]["reaction_frames"]),
                "distance": self.stats["right"]["distance"]
            },
            "rallies": self.rallies
        }

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
        
        import random
        random.shuffle(self.match_queue)
        
        self.total_matches = len(self.match_queue)
        
        # Setup NEAT config
        local_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(local_dir, 'neat_config.txt')
        self.config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                  config_path)
                                  
        self.start_next_match()

    def start_next_match(self):
        if not self.match_queue:
            self.finish_tournament()
            return
            
        p1_path, p2_path = self.match_queue.pop(0)
        
        # Check if models still exist (might have been deleted)
        if p1_path in self.deleted_models or p2_path in self.deleted_models:
            self.start_next_match()
            return

        self.current_match = {
            "p1": p1_path,
            "p2": p2_path,
            "game": game_engine.Game(),
            "net1": None,
            "net2": None
        }
        
        # Initialize Match Analyzer
        self.analyzer = MatchAnalyzer()
        
        # Initialize Match Recorder with metadata
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
        
        # Load Genomes
        try:
            with open(p1_path, "rb") as f:
                g1 = pickle.load(f)
            with open(p2_path, "rb") as f:
                g2 = pickle.load(f)
                
            self.current_match["net1"] = neat.nn.FeedForwardNetwork.create(g1, self.config_neat)
            self.current_match["net2"] = neat.nn.FeedForwardNetwork.create(g2, self.config_neat)
            
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

    def finish_match(self):
        match = self.current_match
        score1 = match["game"].score_left
        score2 = match["game"].score_right
        
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
        stats = self.analyzer.get_stats()
        
        self.model_stats[p1]["hits"] += stats["left"]["hits"]
        self.model_stats[p2]["hits"] += stats["right"]["hits"]
        
        self.model_stats[p1]["distance_moved"] += stats["left"]["distance"]
        self.model_stats[p2]["distance_moved"] += stats["right"]["distance"]
        
        self.model_stats[p1]["total_reaction_time"] += stats["left"]["reaction_sum"]
        self.model_stats[p1]["reaction_count"] += stats["left"]["reaction_count"]
        
        self.model_stats[p2]["total_reaction_time"] += stats["right"]["reaction_sum"]
        self.model_stats[p2]["reaction_count"] += stats["right"]["reaction_count"]
        
        # Save Match Recording and index it
        match_metadata = self.recorder.save()
        if match_metadata:
            # Add post-match ELO to metadata
            match_metadata["p1_elo_after"] = self.model_stats[p1]["elo"]
            match_metadata["p2_elo_after"] = self.model_stats[p2]["elo"]
            match_database.index_match(match_metadata)
        
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
            
            # Speed up if visuals off
            if not self.show_visuals:
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
                net1 = self.current_match["net1"]
                net2 = self.current_match["net2"]
                
                state = game.get_state()
                
                # Update Analyzer
                self.analyzer.update(state)
                self.recorder.record_frame(state)
                
                # AI 1 (Left)
                inputs1 = (
                    state["paddle_left_y"] / config.SCREEN_HEIGHT,
                    state["ball_x"] / config.SCREEN_WIDTH,
                    state["ball_y"] / config.SCREEN_HEIGHT,
                    state["ball_vel_x"] / config.BALL_MAX_SPEED,
                    state["ball_vel_y"] / config.BALL_MAX_SPEED,
                    (state["paddle_left_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                    1.0 if state["ball_vel_x"] < 0 else 0.0,
                    state["paddle_right_y"] / config.SCREEN_HEIGHT
                )
                out1 = net1.activate(inputs1)
                act1 = out1.index(max(out1))
                left_move = "UP" if act1 == 0 else "DOWN" if act1 == 1 else None
                
                # AI 2 (Right)
                inputs2 = (
                    state["paddle_right_y"] / config.SCREEN_HEIGHT,
                    state["ball_x"] / config.SCREEN_WIDTH,
                    state["ball_y"] / config.SCREEN_HEIGHT,
                    state["ball_vel_x"] / config.BALL_MAX_SPEED,
                    state["ball_vel_y"] / config.BALL_MAX_SPEED,
                    (state["paddle_right_y"] - state["ball_y"]) / config.SCREEN_HEIGHT,
                    1.0 if state["ball_vel_x"] > 0 else 0.0,
                    state["paddle_left_y"] / config.SCREEN_HEIGHT
                )
                out2 = net2.activate(inputs2)
                act2 = out2.index(max(out2))
                right_move = "UP" if act2 == 0 else "DOWN" if act2 == 1 else None
                
                game.update(left_move, right_move)
                
                if game.score_left >= config.MAX_SCORE or game.score_right >= config.MAX_SCORE:
                    self.finish_match()
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
                self.current_match["game"].draw(screen)
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
