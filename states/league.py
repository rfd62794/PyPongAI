import pygame
import neat
import os
import pickle
import config
import game_engine
import sys
from states.base import BaseState
from model_manager import scan_models, get_fitness_from_filename, delete_models

class LeagueState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        
        self.mode = "SETUP"  # SETUP, RUNNING, RESULTS
        self.models = []
        self.model_stats = {}  # {path: {"wins": 0, "losses": 0, "fitness": 0}}
        self.current_match = None
        self.match_queue = []
        self.completed_matches = 0
        self.total_matches = 0
        
        # Tournament Enhancement Settings
        self.show_visuals = config.TOURNAMENT_VISUAL_DEFAULT
        self.min_fitness_threshold = config.TOURNAMENT_MIN_FITNESS_DEFAULT
        self.similarity_threshold = config.TOURNAMENT_SIMILARITY_THRESHOLD
        self.delete_shutouts = config.TOURNAMENT_DELETE_SHUTOUTS
        
        # Deletion Tracking
        self.deleted_models = []
        self.deletion_reasons = {}
        self.prefilter_deletions = 0
        self.shutout_deletions = 0
        self.similarity_deletions = 0
        
        # UI
        self.start_button = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 400, 300, 50)
        self.back_button = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)
        self.cancel_button = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 500, 300, 50)
        self.visual_toggle_button = pygame.Rect(config.SCREEN_WIDTH - 220, 10, 100, 40)
        
        # Sliders for setup
        self.min_fitness_slider_rect = pygame.Rect(150, 300, 500, 20)
        self.similarity_slider_rect = pygame.Rect(150, 360, 500, 20)
        self.dragging_min_fitness = False
        self.dragging_similarity = False
        
    def enter(self, **kwargs):
        self.mode = "SETUP"
        self.scan_models_for_league()
        
    def scan_models_for_league(self):
        """Scan all models and prepare for tournament"""
        all_models = scan_models()
        
        # Filter out any models we don't want (could add exclusions here)
        self.models = all_models
        
        # Initialize stats
        self.model_stats = {}
        for model_path in self.models:
            fitness = get_fitness_from_filename(os.path.basename(model_path))
            self.model_stats[model_path] = {
                "wins": 0,
                "losses": 0,
                "fitness": fitness,
                "score": 0,  # Will be calculated as wins - losses
                "points_scored": 0,
                "points_conceded": 0,
                "matches_played": 0
            }
    
    def pre_filter_models(self):
        """Filter out models below the minimum fitness threshold"""
        if self.min_fitness_threshold <= 0:
            return
            
        to_delete = []
        survivors = []
        
        for model_path in self.models:
            stats = self.model_stats.get(model_path)
            if stats and stats["fitness"] < self.min_fitness_threshold:
                to_delete.append(model_path)
            else:
                survivors.append(model_path)
                
        if to_delete:
            count = delete_models(to_delete)
            self.prefilter_deletions = count
            self.deleted_models.extend(to_delete)
            for path in to_delete:
                self.deletion_reasons[path] = f"Pre-filter: Fitness {self.model_stats[path]['fitness']} < {self.min_fitness_threshold}"
                if path in self.model_stats:
                    del self.model_stats[path]
            
            print(f"Pre-filtered {count} models below fitness {self.min_fitness_threshold}")
            self.models = survivors

    def start_tournament(self):
        """Initialize and start the round-robin tournament"""
        # Pre-filter models based on fitness
        self.pre_filter_models()
        
        if len(self.models) < 2:
            print("Not enough models for a tournament!")
            return
            
        self.mode = "RUNNING"
        
        # Create match queue (round-robin: each model plays every other model once)
        self.match_queue = []
        for i in range(len(self.models)):
            for j in range(i + 1, len(self.models)):
                self.match_queue.append((self.models[i], self.models[j]))
        
        self.total_matches = len(self.match_queue)
        self.completed_matches = 0
        self.current_match = None
        
        # Load NEAT config
        local_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(local_dir, 'neat_config.txt')
        self.config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                       neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                       config_path)
    
    def start_next_match(self):
        """Initialize the next match"""
        if not self.match_queue:
            self.finish_tournament()
            return
        
        # Get next match
        model1_path, model2_path = self.match_queue.pop(0)
        
        # Load models
        with open(model1_path, "rb") as f:
            genome1 = pickle.load(f)
        with open(model2_path, "rb") as f:
            genome2 = pickle.load(f)
        
        # Create networks
        net1 = neat.nn.FeedForwardNetwork.create(genome1, self.config_neat)
        net2 = neat.nn.FeedForwardNetwork.create(genome2, self.config_neat)
        
        # Initialize match state
        self.current_match = {
            "model1_path": model1_path,
            "model2_path": model2_path,
            "model1": os.path.basename(model1_path),
            "model2": os.path.basename(model2_path),
            "net1": net1,
            "net2": net2,
            "game": game_engine.Game(),
            "frame_count": 0,
            "max_frames": 10000,
            "target_score": 5,
            "finished": False
        }
    
    def update_match(self):
        """Update the current match by one frame"""
        if not self.current_match or self.current_match["finished"]:
            return
        
        match = self.current_match
        match["frame_count"] += 1
        
        state = match["game"].get_state()
        
        # Player 1 (Left)
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
        out1 = match["net1"].activate(inputs1)
        act1 = out1.index(max(out1))
        move1 = "UP" if act1 == 0 else "DOWN" if act1 == 1 else None
        
        # Player 2 (Right)
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
        out2 = match["net2"].activate(inputs2)
        act2 = out2.index(max(out2))
        move2 = "UP" if act2 == 0 else "DOWN" if act2 == 1 else None
        
        # Update game
        match["game"].update(move1, move2)
        
        # Check for winner
        if (match["game"].score_left >= match["target_score"] or 
            match["game"].score_right >= match["target_score"] or
            match["frame_count"] >= match["max_frames"]):
            self.finish_match()
    
    def check_for_shutout(self, match):
        """Check if the match was a shutout (5-0) and delete the loser if enabled"""
        if not self.delete_shutouts:
            return
            
        loser_path = None
        score_diff = abs(match["score1"] - match["score2"])
        
        # Check for 5-0 (assuming target score is 5)
        if score_diff >= 5 and (match["score1"] == 0 or match["score2"] == 0):
            if match["score1"] == 0:
                loser_path = match["model1_path"]
            elif match["score2"] == 0:
                loser_path = match["model2_path"]
                
        if loser_path and loser_path not in self.deleted_models:
            # Verify it's not already deleted
            if os.path.exists(loser_path):
                delete_models([loser_path])
                self.deleted_models.append(loser_path)
                self.shutout_deletions += 1
                self.deletion_reasons[loser_path] = "Shutout (5-0 loss)"
                print(f"Deleted {os.path.basename(loser_path)} due to shutout")
                
                # Remove from future matches in queue
                self.match_queue = [m for m in self.match_queue if m[0] != loser_path and m[1] != loser_path]

    def finish_match(self):
        """Finish the current match and record results"""
        if not self.current_match:
            return
        
        match = self.current_match
        model1_path = match["model1_path"]
        model2_path = match["model2_path"]
        
        match["finished"] = True
        match["score1"] = match["game"].score_left
        match["score2"] = match["game"].score_right
        
        # Record results
        if match["game"].score_left > match["game"].score_right:
            self.model_stats[model1_path]["wins"] += 1
            self.model_stats[model2_path]["losses"] += 1
            match["winner"] = 1
        else:
            self.model_stats[model2_path]["wins"] += 1
            self.model_stats[model1_path]["losses"] += 1
            match["winner"] = 2
            
        # Update detailed stats
        self.model_stats[model1_path]["matches_played"] += 1
        self.model_stats[model1_path]["points_scored"] += match["score1"]
        self.model_stats[model1_path]["points_conceded"] += match["score2"]
        
        self.model_stats[model2_path]["matches_played"] += 1
        self.model_stats[model2_path]["points_scored"] += match["score2"]
        self.model_stats[model2_path]["points_conceded"] += match["score1"]
        
        # Update scores
        for model_path in self.models:
            if model_path in self.model_stats:
                stats = self.model_stats[model_path]
                stats["score"] = stats["wins"] - stats["losses"]
        
        self.completed_matches += 1
        
        # Check for shutout deletion
        self.check_for_shutout(match)
    
    def prune_similar_models(self):
        """Prune models that have very similar fitness scores"""
        if self.similarity_threshold <= 0:
            return
            
        # Sort by fitness to easily find clusters
        sorted_models = sorted(
            self.models,
            key=lambda x: self.model_stats[x]["fitness"],
            reverse=True
        )
        
        to_delete = []
        processed = set()
        
        for i in range(len(sorted_models)):
            if sorted_models[i] in processed:
                continue
                
            current = sorted_models[i]
            cluster = [current]
            processed.add(current)
            
            # Find all similar models
            for j in range(i + 1, len(sorted_models)):
                candidate = sorted_models[j]
                if candidate in processed:
                    continue
                    
                diff = abs(self.model_stats[current]["fitness"] - self.model_stats[candidate]["fitness"])
                if diff <= self.similarity_threshold:
                    cluster.append(candidate)
                    processed.add(candidate)
                else:
                    # Since sorted by fitness, if diff exceeds threshold, all subsequent will too
                    break
            
            # If cluster has more than 1, keep only the best tournament performer
            if len(cluster) > 1:
                # Sort cluster by tournament score (descending)
                cluster.sort(key=lambda x: self.model_stats[x]["score"], reverse=True)
                
                # Keep the first one (best score), delete the rest
                survivor = cluster[0]
                victims = cluster[1:]
                
                to_delete.extend(victims)
                
        if to_delete:
            count = delete_models(to_delete)
            self.similarity_deletions = count
            self.deleted_models.extend(to_delete)
            for path in to_delete:
                self.deletion_reasons[path] = f"Similarity Pruning (Threshold {self.similarity_threshold})"
            
            print(f"Pruned {count} similar models")
            
            # Update survivors
            self.models = [m for m in self.models if m not in to_delete]

    def finish_tournament(self):
        """Process tournament results and delete underperforming models"""
        self.mode = "RESULTS"
        
        # First, prune similar models
        self.prune_similar_models()
        
        # Rank models by score (wins - losses), then by fitness
        ranked_models = sorted(
            self.models,
            key=lambda x: (self.model_stats[x]["score"], self.model_stats[x]["fitness"]),
            reverse=True
        )
        
        # Keep top 10
        top_10 = ranked_models[:10]
        to_delete = ranked_models[10:]
        
        # Delete underperforming models
        if to_delete:
            deleted_count = delete_models(to_delete)
            print(f"Deleted {deleted_count} underperforming models")
            self.deleted_models.extend(to_delete)
            for path in to_delete:
                self.deletion_reasons[path] = "Not in Top 10"
        
        # Update models list to only include survivors
        self.models = top_10
    
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.back_button.collidepoint((mx, my)):
                self.manager.change_state("menu")
                return
                
            # Visual toggle (always available)
            if self.visual_toggle_button.collidepoint((mx, my)):
                self.show_visuals = not self.show_visuals
            
            if self.mode == "SETUP":
                if self.start_button.collidepoint((mx, my)):
                    self.start_tournament()
                    
                # Sliders
                if self.min_fitness_slider_rect.collidepoint((mx, my)):
                    self.dragging_min_fitness = True
                if self.similarity_slider_rect.collidepoint((mx, my)):
                    self.dragging_similarity = True
            
            elif self.mode == "RUNNING":
                if self.cancel_button.collidepoint((mx, my)):
                    self.mode = "SETUP"
                    self.match_queue = []
            
            elif self.mode == "RESULTS":
                # Any click returns to menu
                pass
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_min_fitness = False
            self.dragging_similarity = False
            
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.mode == "SETUP":
                if self.dragging_min_fitness:
                    # 0 to 1000 range
                    val = (mx - self.min_fitness_slider_rect.x) / self.min_fitness_slider_rect.width
                    val = max(0, min(1, val))
                    self.min_fitness_threshold = int(val * 1000)
                    
                if self.dragging_similarity:
                    # 0 to 100 range
                    val = (mx - self.similarity_slider_rect.x) / self.similarity_slider_rect.width
                    val = max(0, min(1, val))
                    self.similarity_threshold = int(val * 100)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.change_state("menu")
    
    def update(self, dt):
        """Called every frame"""
        if self.mode == "RUNNING":
            if self.current_match and not self.current_match["finished"]:
                # Update current match
                if self.show_visuals:
                    self.update_match()
                else:
                    # Speed up! Run multiple updates per frame
                    for _ in range(100):  # Run 100 steps per frame
                        if self.current_match["finished"]:
                            break
                        self.update_match()
                        
            elif self.match_queue:
                # Start next match
                self.start_next_match()
            elif self.current_match and self.current_match["finished"]:
                # Wait a moment before next match (so user can see result)
                # If visuals are off, skip the wait
                if not self.show_visuals:
                    self.current_match = None  # Clear it so next update loop picks up next match immediately
    
    def draw(self, screen):
        screen.fill(config.BLACK)
        
        # Back button (always visible)
        pygame.draw.rect(screen, (150, 50, 50), self.back_button)
        pygame.draw.rect(screen, config.WHITE, self.back_button, 2)
        back_text = self.small_font.render("Back", True, config.WHITE)
        back_rect = back_text.get_rect(center=self.back_button.center)
        screen.blit(back_text, back_rect)
        
        if self.mode == "SETUP":
            self.draw_setup(screen)
        elif self.mode == "RUNNING":
            self.draw_running(screen)
        elif self.mode == "RESULTS":
            self.draw_results(screen)
    
    def draw_setup(self, screen):
        """Draw setup screen"""
        title = self.font.render("League Mode", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        info = self.small_font.render(f"Found {len(self.models)} models", True, config.WHITE)
        screen.blit(info, (config.SCREEN_WIDTH//2 - info.get_width()//2, 120))
        
        if len(self.models) < 2:
            warning = self.small_font.render("Need at least 2 models to run tournament!", True, (255, 100, 100))
            screen.blit(warning, (config.SCREEN_WIDTH//2 - warning.get_width()//2, 180))
        else:
            desc1 = self.tiny_font.render("All models will compete in a round-robin tournament.", True, config.GRAY)
            desc2 = self.tiny_font.render("Only the top 10 performers will be kept.", True, config.GRAY)
            desc3 = self.tiny_font.render(f"This will DELETE {max(0, len(self.models) - 10)} models!", True, (255, 150, 150))
            
            screen.blit(desc1, (config.SCREEN_WIDTH//2 - desc1.get_width()//2, 180))
            screen.blit(desc2, (config.SCREEN_WIDTH//2 - desc2.get_width()//2, 210))
            screen.blit(desc3, (config.SCREEN_WIDTH//2 - desc3.get_width()//2, 240))
            
            # Start button
            mx, my = pygame.mouse.get_pos()
            color = (100, 100, 100) if self.start_button.collidepoint((mx, my)) else (50, 50, 50)
            pygame.draw.rect(screen, color, self.start_button)
            pygame.draw.rect(screen, config.WHITE, self.start_button, 2)
            
            start_text = self.small_font.render("Start Tournament", True, config.WHITE)
            start_rect = start_text.get_rect(center=self.start_button.center)
            screen.blit(start_text, start_rect)
    
    def draw_running(self, screen):
        """Draw tournament progress with visual match"""
        screen.fill(config.BLACK)
        
        # Draw the actual game if a match is active
        if self.current_match and not self.current_match["finished"]:
            # Draw the game
            self.current_match["game"].draw(screen)
            
            # Overlay match info at top
            info_bg = pygame.Rect(0, 0, config.SCREEN_WIDTH, 80)
            pygame.draw.rect(screen, (0, 0, 0, 180), info_bg)
            
            # Model names
            model1_text = self.tiny_font.render(self.current_match["model1"][:30], True, config.WHITE)
            model2_text = self.tiny_font.render(self.current_match["model2"][:30], True, config.WHITE)
            screen.blit(model1_text, (10, 10))
            screen.blit(model2_text, (config.SCREEN_WIDTH - model2_text.get_width() - 10, 10))
            
            # Progress
            progress_text = self.tiny_font.render(
                f"Match {self.completed_matches + 1} / {self.total_matches}",
                True, config.WHITE
            )
            screen.blit(progress_text, (config.SCREEN_WIDTH//2 - progress_text.get_width()//2, 10))
            
            # Score display (larger)
            score_text = self.small_font.render(
                f"{self.current_match['game'].score_left} - {self.current_match['game'].score_right}",
                True, config.WHITE
            )
            screen.blit(score_text, (config.SCREEN_WIDTH//2 - score_text.get_width()//2, 40))
            
        elif self.current_match and self.current_match["finished"]:
            # Show result screen briefly
            result_text = self.font.render("Match Complete!", True, config.WHITE)
            screen.blit(result_text, (config.SCREEN_WIDTH//2 - result_text.get_width()//2, 200))
            
            winner_name = self.current_match["model1"] if self.current_match["winner"] == 1 else self.current_match["model2"]
            winner_text = self.small_font.render(f"Winner: {winner_name[:40]}", True, (100, 255, 100))
            screen.blit(winner_text, (config.SCREEN_WIDTH//2 - winner_text.get_width()//2, 270))
            
            score_text = self.small_font.render(
                f"{self.current_match['score1']} - {self.current_match['score2']}",
                True, config.WHITE
            )
            screen.blit(score_text, (config.SCREEN_WIDTH//2 - score_text.get_width()//2, 320))
        
        # Progress bar at bottom
        bar_width = config.SCREEN_WIDTH - 40
        bar_height = 20
        bar_x = 20
        bar_y = config.SCREEN_HEIGHT - 60
        
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        if self.total_matches > 0:
            progress_width = int((self.completed_matches / self.total_matches) * bar_width)
            pygame.draw.rect(screen, (50, 150, 50), (bar_x, bar_y, progress_width, bar_height))
        pygame.draw.rect(screen, config.WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        progress_pct = self.tiny_font.render(
            f"{int((self.completed_matches / self.total_matches) * 100)}%" if self.total_matches > 0 else "0%",
            True, config.WHITE
        )
        screen.blit(progress_pct, (config.SCREEN_WIDTH//2 - progress_pct.get_width()//2, bar_y - 25))
    
    def draw_results(self, screen):
        """Draw tournament results"""
        title = self.font.render("Tournament Complete!", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        subtitle = self.small_font.render("Top 10 Models (Survivors)", True, (100, 255, 100))
        screen.blit(subtitle, (config.SCREEN_WIDTH//2 - subtitle.get_width()//2, 90))
        
        # Display top 10
        y_offset = 140
        for i, model_path in enumerate(self.models[:10]):
            stats = self.model_stats[model_path]
            rank_text = f"{i+1}. {os.path.basename(model_path)[:40]}"
            stats_text = f"W:{stats['wins']} L:{stats['losses']} Fit:{stats['fitness']}"
            
            rank_surf = self.tiny_font.render(rank_text, True, config.WHITE)
            stats_surf = self.tiny_font.render(stats_text, True, config.GRAY)
            
            screen.blit(rank_surf, (50, y_offset))
            screen.blit(stats_surf, (config.SCREEN_WIDTH - 250, y_offset))
            
            y_offset += 30
        
        # Instructions
        instruction = self.small_font.render("Press ESC or click Back to return to menu", True, config.GRAY)
        screen.blit(instruction, (config.SCREEN_WIDTH//2 - instruction.get_width()//2, config.SCREEN_HEIGHT - 50))
