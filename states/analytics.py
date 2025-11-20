import pygame
import os
import config
from states.base import BaseState
import elo_manager
from model_manager import get_fitness_from_filename
import match_database

class AnalyticsState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        
        self.models = []
        self.model_stats = {}
        
        # View State
        self.view = "OVERVIEW"  # OVERVIEW, MODEL_DETAIL, MATCH_HISTORY
        self.selected_model = None
        self.scroll_y = 0
        
        # UI Elements
        self.back_button = pygame.Rect(config.SCREEN_WIDTH - 110, 10, 100, 40)

    def enter(self, **kwargs):
        self.view = "OVERVIEW"
        self.selected_model = None
        self.scan_models()
        
    def scan_models(self):
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
                    
                    # Initialize stats (we might want to load persistent stats if we had them, 
                    # but for now we rely on ELO and filename fitness, plus maybe match DB aggregation?)
                    # The original LeagueState calculated stats on the fly during the tournament.
                    # For a persistent dashboard, we should ideally aggregate from the match database.
                    # However, to keep it simple and consistent with the request to "move logic",
                    # I will implement basic stats loading from ELO and DB.
                    
                    self.model_stats[full_path] = {
                        "fitness": fitness,
                        "elo": stored_elo,
                        # These will be populated from DB aggregation if possible, or left 0
                        "wins": 0,
                        "losses": 0,
                        "points_scored": 0,
                        "points_conceded": 0,
                        "total_reaction_time": 0,
                        "reaction_count": 0,
                        "distance_moved": 0,
                        "hits": 0
                    }
                    
                    # Aggregate stats from Match Database
                    matches = match_database.get_matches_for_model(file)
                    for m in matches:
                        # Simple aggregation
                        p1 = m.get("p1")
                        p2 = m.get("p2")
                        winner = m.get("winner")
                        score = m.get("final_score", [0, 0])
                        
                        is_p1 = (p1 == file)
                        
                        if is_p1:
                            my_score = score[0]
                            opp_score = score[1]
                            if winner == "p1": self.model_stats[full_path]["wins"] += 1
                            else: self.model_stats[full_path]["losses"] += 1
                        else:
                            my_score = score[1]
                            opp_score = score[0]
                            if winner == "p2": self.model_stats[full_path]["wins"] += 1
                            else: self.model_stats[full_path]["losses"] += 1
                            
                        self.model_stats[full_path]["points_scored"] += my_score
                        self.model_stats[full_path]["points_conceded"] += opp_score

        # Sort by ELO
        self.models.sort(key=lambda x: self.model_stats[x]["elo"], reverse=True)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Back button
            if self.back_button.collidepoint(event.pos):
                if self.view == "OVERVIEW":
                    self.manager.change_state("menu")
                else:
                    self.view = "OVERVIEW"
                    self.selected_model = None
                return
            
            # View-specific handling
            if self.view == "OVERVIEW":
                # Check if clicked on a model in the list
                y_start = 110
                for i, model in enumerate(self.models[:15]):
                    row_rect = pygame.Rect(50, y_start + i * 30, config.SCREEN_WIDTH - 100, 28)
                    if row_rect.collidepoint((mx, my)):
                        self.selected_model = model
                        self.view = "MODEL_DETAIL"
                        return
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.view == "OVERVIEW":
                    self.manager.change_state("menu")
                else:
                    self.view = "OVERVIEW"
                    self.selected_model = None

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.view == "OVERVIEW":
            self.draw_overview(screen)
        elif self.view == "MODEL_DETAIL":
            self.draw_model_detail(screen)
        elif self.view == "MATCH_HISTORY":
            self.draw_match_history(screen)

    def draw_overview(self, screen):
        screen.fill(config.BLACK)
        title = self.font.render("Analytics Dashboard", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        subtitle = self.tiny_font.render("Click on a model to view details", True, config.GRAY)
        screen.blit(subtitle, (config.SCREEN_WIDTH//2 - subtitle.get_width()//2, 60))
        
        # Headers
        headers = ["Rank", "Model", "ELO", "Win %", "Points (Avg)", "Matches"]
        x_offsets = [50, 120, 350, 450, 550, 700]
        
        for i, h in enumerate(headers):
            surf = self.small_font.render(h, True, config.GRAY)
            screen.blit(surf, (x_offsets[i], 80))
            
        # Data (clickable rows)
        y = 110
        mx, my = pygame.mouse.get_pos()
        
        for i, model in enumerate(self.models[:15]): # Show top 15
            stats = self.model_stats[model]
            name = os.path.basename(model)
            
            total_games = stats["wins"] + stats["losses"]
            win_pct = f"{stats['wins']/total_games*100:.1f}%" if total_games > 0 else "0%"
            avg_pts = f"{stats['points_scored']/total_games:.1f}" if total_games > 0 else "-"
            
            row_data = [
                str(i+1),
                name[:20],
                str(int(stats["elo"])),
                win_pct,
                avg_pts,
                str(total_games)
            ]
            
            # Highlight row on hover
            row_rect = pygame.Rect(50, y, config.SCREEN_WIDTH - 100, 28)
            if row_rect.collidepoint((mx, my)):
                pygame.draw.rect(screen, (30, 30, 60), row_rect)
            
            for j, data in enumerate(row_data):
                surf = self.small_font.render(data, True, config.WHITE)
                screen.blit(surf, (x_offsets[j], y))
            
            y += 30

        # Back Button
        pygame.draw.rect(screen, (100, 0, 0), self.back_button)
        back_text = self.small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))

    def draw_model_detail(self, screen):
        screen.fill(config.BLACK)
        
        if not self.selected_model:
            return
        
        stats = self.model_stats[self.selected_model]
        name = os.path.basename(self.selected_model)
        
        # Title
        title = self.font.render(f"Model: {name[:30]}", True, config.WHITE)
        screen.blit(title, (20, 20))
        
        # Stats Card
        y = 80
        total_games = stats['wins'] + stats['losses']
        win_rate = stats['wins']/total_games*100 if total_games > 0 else 0
        
        info_lines = [
            f"Fitness: {stats['fitness']}",
            f"ELO Rating: {int(stats['elo'])}",
            f"Record: {stats['wins']}W - {stats['losses']}L ({win_rate:.1f}% win rate)",
            f"Points: {stats['points_scored']} scored, {stats['points_conceded']} conceded",
            "",
            f"Total Matches: {total_games}"
        ]
        
        for line in info_lines:
            surf = self.small_font.render(line, True, config.WHITE)
            screen.blit(surf, (20, y))
            y += 35
        
        # Match History
        y += 20
        history_title = self.small_font.render("Recent Matches:", True, config.YELLOW)
        screen.blit(history_title, (20, y))
        y += 40
        
        # Get matches from database
        matches = match_database.get_matches_for_model(name)
        
        if not matches:
            no_matches = self.tiny_font.render("No matches recorded yet", True, config.GRAY)
            screen.blit(no_matches, (40, y))
        else:
            # Show last 10 matches
            for i, match in enumerate(matches[:10]):
                p1, p2 = match.get("p1"), match.get("p2")
                winner = match.get("winner")
                score = match.get("final_score", [0, 0])
                match_type = match.get("match_type", "unknown")
                
                # Determine if this model won
                if p1 == name:
                    opponent = p2
                    result = "W" if winner == "p1" else "L"
                    score_display = f"{score[0]}-{score[1]}"
                else:
                    opponent = p1
                    result = "W" if winner == "p2" else "L"
                    score_display = f"{score[1]}-{score[0]}"
                
                result_color = config.GREEN if result == "W" else config.RED
                
                # Draw match
                result_text = self.tiny_font.render(f"[{result}]", True, result_color)
                screen.blit(result_text, (40, y))
                
                match_text = self.tiny_font.render(f"vs {opponent[:25]} | {score_display} | {match_type}", True, config.WHITE)
                screen.blit(match_text, (80, y))
                
                y += 25
                
                if y > config.SCREEN_HEIGHT - 80:
                    break
        
        # Back Button
        pygame.draw.rect(screen, (100, 0, 0), self.back_button)
        back_text = self.small_font.render("< Back", True, config.WHITE)
        screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2, self.back_button.centery - back_text.get_height()//2))

    def draw_match_history(self, screen):
        pass
