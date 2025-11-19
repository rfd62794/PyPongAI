# play.py
import patch_neat
import pygame
import pickle
import neat
import os
import config
import game_engine
import human_recorder

def play_game():
    """
    Runs the game in Human vs AI mode with a graphical start menu.
    """
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Project PaddleMind")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 50)
    small_font = pygame.font.Font(None, 36)

    # List models (Recursively scan models/ and models/tiers/)
    models = []
    for root, dirs, files in os.walk(config.MODEL_DIR):
        for file in files:
            if file.endswith(".pkl"):
                # Store relative path for display, or full path?
                # Storing full path is safer, but display needs to be clean
                full_path = os.path.join(root, file)
                models.append(full_path)

    if not models:
        print("No models found. Please train first.")
        pygame.quit()
        return

    def get_fitness(filepath):
        filename = os.path.basename(filepath)
        try:
            if "fitness" in filename:
                return int(filename.split("fitness")[1].split(".")[0])
            elif "_fit_" in filename:
                return int(filename.split("_fit_")[1].split(".")[0])
            return 0
        except (IndexError, ValueError):
            return 0
    models.sort(key=get_fitness)

    # Helper to get display name
    def get_display_name(filepath):
        filename = os.path.basename(filepath)
        # Check if it's in a tier
        parent = os.path.basename(os.path.dirname(filepath))
        if parent in ["God", "Master", "Challenger", "Archive"]:
            return f"[{parent}] {filename}"
        return filename

    # Menu Loop
    selected_model_path = None
    menu_running = True
    
    while menu_running:
        screen.fill(config.BLACK)
        
        # Title
        title = font.render("Project PaddleMind", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mx, my = pygame.mouse.get_pos()
        
        # Buttons
        btn_challenge = pygame.Rect(config.SCREEN_WIDTH//2 - 100, 150, 200, 50)
        btn_master = pygame.Rect(config.SCREEN_WIDTH//2 - 100, 220, 200, 50)
        btn_quit = pygame.Rect(config.SCREEN_WIDTH//2 - 100, 290, 200, 50)
        
        pygame.draw.rect(screen, (50, 50, 50), btn_challenge)
        pygame.draw.rect(screen, (50, 50, 50), btn_master)
        pygame.draw.rect(screen, (50, 50, 50), btn_quit)
        
        # Hover effect
        if btn_challenge.collidepoint((mx, my)):
            pygame.draw.rect(screen, (100, 100, 100), btn_challenge)
        if btn_master.collidepoint((mx, my)):
            pygame.draw.rect(screen, (100, 100, 100), btn_master)
        if btn_quit.collidepoint((mx, my)):
            pygame.draw.rect(screen, (100, 100, 100), btn_quit)

        # Text
        txt_chal = small_font.render("Challenge Mode", True, config.WHITE)
        txt_mast = small_font.render("Master Mode", True, config.WHITE)
        txt_quit = small_font.render("Quit", True, config.WHITE)
        
        screen.blit(txt_chal, (btn_challenge.centerx - txt_chal.get_width()//2, btn_challenge.centery - txt_chal.get_height()//2))
        screen.blit(txt_mast, (btn_master.centerx - txt_mast.get_width()//2, btn_master.centery - txt_mast.get_height()//2))
        screen.blit(txt_quit, (btn_quit.centerx - txt_quit.get_width()//2, btn_quit.centery - txt_quit.get_height()//2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if btn_challenge.collidepoint((mx, my)):
                        # Median model
                        selected_model_path = models[len(models) // 2] if len(models) > 1 else models[0]
                        print(f"Selected: {selected_model_path}")
                        menu_running = False
                    elif btn_master.collidepoint((mx, my)):
                        # Best model
                        selected_model_path = models[-1]
                        print(f"Selected: {selected_model_path}")
                        menu_running = False
                    elif btn_quit.collidepoint((mx, my)):
                        pygame.quit()
                        return

    if not selected_model_path:
        pygame.quit()
        return

    # Load model
    with open(selected_model_path, "rb") as f:
        genome = pickle.load(f)
    
    # Load NEAT config
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
                              
    net = neat.nn.FeedForwardNetwork.create(genome, config_neat)
    
    game = game_engine.Game()
    recorder = human_recorder.HumanRecorder()
    
    running = True
    try:
        while running:
            clock.tick(config.FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Human Input (Right Paddle)
            keys = pygame.key.get_pressed()
            right_move = None
            if keys[pygame.K_UP]:
                right_move = "UP"
            elif keys[pygame.K_DOWN]:
                right_move = "DOWN"

            # AI Input (Left Paddle)
            state = game.get_state()
            inputs = (
                state["paddle_left_y"],
                state["ball_x"],
                state["ball_y"],
                state["ball_vel_x"],
                state["ball_vel_y"]
            )
            output = net.activate(inputs)
            action_idx = output.index(max(output))
            left_move = None
            if action_idx == 0:
                left_move = "UP"
            elif action_idx == 1:
                left_move = "DOWN"

            # Record Human Data
            recorder.record_frame(state, right_move)

            # Update Game
            score_data = game.update(left_move, right_move)
            
            if score_data and score_data.get("game_over"):
                # Show Game Over Screen briefly
                font_go = pygame.font.Font(None, 74)
                text_go = font_go.render("GAME OVER", True, config.WHITE)
                screen.blit(text_go, (config.SCREEN_WIDTH//2 - text_go.get_width()//2, config.SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False

            # Draw
            game.draw(screen)
            pygame.display.flip()
    finally:
        recorder.close()

    pygame.quit()

if __name__ == "__main__":
    play_game()
