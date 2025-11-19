pygame.display.set_caption("Project PaddleMind - Analytics Dashboard")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 24)

# Colors
BG_COLOR = (30, 30, 30)
TAB_COLOR = (50, 50, 50)
TAB_ACTIVE_COLOR = (80, 80, 80)
TEXT_COLOR = config.WHITE
HIGHLIGHT_COLOR = (100, 100, 255)

class Dashboard:
    def __init__(self):
        self.active_tab = "Overview"
        self.tabs = ["Overview", "Models", "Matches"]
        self.running = True
        self.scroll_y = 0
        
        # Load Data
        self.models = self.load_models()
        self.matches = self.load_matches()
        self.human_stats = self.load_human_stats()
        
    def load_models(self):
        models = []
        for root, dirs, files in os.walk(config.MODEL_DIR):
            for file in files:
                if file.endswith(".pkl"):
                    full_path = os.path.join(root, file)
                    fitness = 0
                    try:
                        if "fitness" in file:
                            fitness = int(file.split("fitness")[1].split(".")[0])
                        elif "_fit_" in file:
                            fitness = int(file.split("_fit_")[1].split(".")[0])
                    except:
                        pass
                    
                    tier = os.path.basename(os.path.dirname(full_path))
                    if tier == "models": tier = "Unsorted"
                    
                    models.append({
                        "name": file,
                        "path": full_path,
                        "fitness": fitness,
                        "tier": tier
                    })
        models.sort(key=lambda x: x["fitness"], reverse=True)
        return models

    def load_matches(self):
        matches = []
        files = glob.glob(os.path.join(config.LOGS_MATCHES_DIR, "*.csv"))
        for f in files:
            try:
                df = pd.read_csv(f)
                if not df.empty:
                    matches.append({
                        "file": os.path.basename(f),
                        "frames": len(df),
                        "max_score_left": df['score_left'].max(),
                        "max_score_right": df['score_right'].max(),
                        "avg_ball_speed": df['ball_vel_x'].abs().mean()
                    })
            except:
                pass
        matches.sort(key=lambda x: x["file"], reverse=True) # Newest first
        return matches

    def draw_overview(self):
        y = 80
        
        # Title
        title = font.render("System Overview", True, HIGHLIGHT_COLOR)
        screen.blit(title, (50, y))
        y += 50
        
        # Stats
        stats = [
            f"Total Models: {len(self.models)}",
            f"Total Matches Recorded: {len(self.matches)}",
            f"Human Training Data: {self.human_stats['total_frames']} frames",
            f"Top Fitness: {self.models[0]['fitness'] if self.models else 0}"
        ]
        
        for stat in stats:
            surf = small_font.render(stat, True, TEXT_COLOR)
            screen.blit(surf, (50, y))
            y += 30
            
        # Human Actions
        y += 30
        h_title = font.render("Human Play Style", True, HIGHLIGHT_COLOR)
        screen.blit(h_title, (50, y))
        y += 40
        
        for action, count in self.human_stats['actions'].items():
            surf = small_font.render(f"{action}: {count}", True, TEXT_COLOR)
            screen.blit(surf, (50, y))
            y += 30

    def draw_models(self):
        y = 80 - self.scroll_y
        
        header = small_font.render(f"{'Name':<40} {'Tier':<15} {'Fitness':<10}", True, HIGHLIGHT_COLOR)
        screen.blit(header, (50, y))
        y += 30
        
        for model in self.models:
            if y > 50 and y < config.SCREEN_HEIGHT - 50:
                text = f"{model['name'][:35]:<40} {model['tier']:<15} {model['fitness']:<10}"
                surf = small_font.render(text, True, TEXT_COLOR)
                screen.blit(surf, (50, y))
            y += 30

    def draw_matches(self):
        y = 80 - self.scroll_y
        
        header = small_font.render(f"{'File':<30} {'Frames':<10} {'Score (L-R)':<15} {'Avg Speed':<10}", True, HIGHLIGHT_COLOR)
        screen.blit(header, (50, y))
        y += 30
        
        for match in self.matches:
            if y > 50 and y < config.SCREEN_HEIGHT - 50:
                score = f"{match['max_score_left']}-{match['max_score_right']}"
                text = f"{match['file'][:25]:<30} {match['frames']:<10} {score:<15} {match['avg_ball_speed']:.2f}"
                surf = small_font.render(text, True, TEXT_COLOR)
                screen.blit(surf, (50, y))
            y += 30

    def draw_back_button(self):
        rect = pygame.Rect(config.SCREEN_WIDTH - 120, config.SCREEN_HEIGHT - 50, 100, 40)
        pygame.draw.rect(screen, (150, 50, 50), rect)
        pygame.draw.rect(screen, config.WHITE, rect, 2)
        text = small_font.render("Back", True, config.WHITE)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        return rect

    def run(self):
        while self.running:
            screen.fill(BG_COLOR)
            
            self.draw_tabs()
            
            if self.active_tab == "Overview":
                self.draw_overview()
            elif self.active_tab == "Models":
                self.draw_models()
            elif self.active_tab == "Matches":
                self.draw_matches()
                
            back_btn = self.draw_back_button()
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    sys.exit(100)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos # Use event position for accuracy
                    
                    # Tab Click
                    if my < 50:
                        tab_width = config.SCREEN_WIDTH // len(self.tabs)
                        idx = mx // tab_width
                        if 0 <= idx < len(self.tabs):
                            self.active_tab = self.tabs[idx]
                            self.scroll_y = 0
                            
                    # Back Button
                    if back_btn.collidepoint((mx, my)):
                        self.running = False
                        sys.exit(0) # Return to main menu logic
                        
                    # Scroll
                    if event.button == 4: # Up
                        self.scroll_y = max(0, self.scroll_y - 20)
                    elif event.button == 5: # Down
                        self.scroll_y += 20

        pygame.quit()

if __name__ == "__main__":
    try:
        dash = Dashboard()
        dash.run()
    except KeyboardInterrupt:
        print("\n[!] Dashboard interrupted.")
        sys.exit(100)
    except SystemExit as e:
        if e.code == 100:
            sys.exit(100)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        pygame.quit()
