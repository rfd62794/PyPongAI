import patch_neat
import pygame
import neat
import os
import pickle
import config
from game_engine import Game
from human_rival import HumanRival
import sys

def play_game():
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
    
    # Rival System
    rival_sys = HumanRival()
    rival_path = rival_sys.get_rival_model()
    
    while menu_running:
        screen.fill(config.BLACK)
        
        title = font.render("Select Opponent", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mx, my = pygame.mouse.get_pos()
        
        btn_challenge = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 150, 300, 50)
        btn_select = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 220, 300, 50)
        btn_rival = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 290, 300, 50)
        btn_quit = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 360, 300, 50)
        
        # Draw Buttons
        # Challenge Best
        color = (100, 100, 100) if btn_challenge.collidepoint((mx, my)) else (50, 50, 50)
        pygame.draw.rect(screen, color, btn_challenge)
        pygame.draw.rect(screen, config.WHITE, btn_challenge, 2)
        text = small_font.render("Challenge Best AI", True, config.WHITE)
        screen.blit(text, (btn_challenge.centerx - text.get_width()//2, btn_challenge.centery - text.get_height()//2))
        
        # Select File
        color = (100, 100, 100) if btn_select.collidepoint((mx, my)) else (50, 50, 50)
        pygame.draw.rect(screen, color, btn_select)
        pygame.draw.rect(screen, config.WHITE, btn_select, 2)
        text = small_font.render("Select Model File", True, config.WHITE)
        screen.blit(text, (btn_select.centerx - text.get_width()//2, btn_select.centery - text.get_height()//2))

        # Challenge Rival
        if rival_path:
            color = (100, 80, 50) if btn_rival.collidepoint((mx, my)) else (80, 50, 20)
            pygame.draw.rect(screen, color, btn_rival)
            pygame.draw.rect(screen, config.WHITE, btn_rival, 2)
            rival_fit = rival_sys.stats.get('rival_fitness', '?')
            text = small_font.render(f"Challenge Rival (Fit: {rival_fit})", True, config.WHITE)
            screen.blit(text, (btn_rival.centerx - text.get_width()//2, btn_rival.centery - text.get_height()//2))
        
        # Quit
        color = (100, 100, 100) if btn_quit.collidepoint((mx, my)) else (50, 50, 50)
        pygame.draw.rect(screen, color, btn_quit)
        pygame.draw.rect(screen, config.WHITE, btn_quit, 2)
        text = small_font.render("Back", True, config.WHITE)
        screen.blit(text, (btn_quit.centerx - text.get_width()//2, btn_quit.centery - text.get_height()//2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                sys.exit(100)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if btn_challenge.collidepoint((mx, my)):
                        # Find best model
                        models = []
                        for root, dirs, files in os.walk(config.MODEL_DIR):
                            for file in files:
                                if file.endswith(".pkl"):
                                    models.append(os.path.join(root, file))
                        if models:
                            # Sort by fitness in filename
                            def get_fit(p):
                                try:
                                    return int(p.split("fitness")[1].split(".")[0])
                                except:
                                    return 0
                            models.sort(key=get_fit, reverse=True)
                            selected_model_path = models[0]
                            menu_running = False
                            
                    elif btn_select.collidepoint((mx, my)):
                        # Simple file dialog simulation or just list
                        # For now, let's just pick the best one to save time or implement a list later
                        pass 
                        
                    elif btn_rival.collidepoint((mx, my)) and rival_path:
                        selected_model_path = rival_path
                        menu_running = False

                    elif btn_quit.collidepoint((mx, my)):
                        pygame.quit()
                        sys.exit(100)

    if not selected_model_path:
        pygame.quit()
        return

    # Load genome
    with open(selected_model_path, "rb") as f:
        genome = pickle.load(f)

    # Load config
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat_config.txt")
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)

    net = neat.nn.FeedForwardNetwork.create(genome, neat_config)
    
    # Run Game
    game = Game()
    clock = pygame.time.Clock()
    running = True
    
    print("\n[!] Starting Match vs AI...")
    print("Controls: UP/DOWN Arrows")
    
    final_score_human = 0
    
    try:
        while running:
            dt = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    sys.exit(100)

            # Human Input (Right Paddle)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                game.right_paddle.move(up=True)
            if keys[pygame.K_DOWN]:
                game.right_paddle.move(up=False)

            # AI Input (Left Paddle)
            # Inputs: Ball Y, Ball X, Paddle Y, Ball VY, Ball VX
            inputs = (game.ball.rect.y, game.ball.rect.x, game.left_paddle.rect.y, game.ball.vel_y, game.ball.vel_x)
            output = net.activate(inputs)
            
            # Output is usually a list of floats. 
            # Decision: > 0.5 move down, < -0.5 move up, else stay
            # Or 3 outputs: Up, Down, Stay
            
            # Assuming 3 outputs from config
            decision = output.index(max(output))
            
            if decision == 0: # Up
                game.left_paddle.move(up=True)
            elif decision == 1: # Down
                game.left_paddle.move(up=False)
            # 2 is Stay
            
            game.update(dt)
            game.draw(screen)
            
            pygame.display.flip()
            
            if game.game_over:
                final_score_human = game.score_r
                
                # Update Rival Stats
                if rival_sys.update_score(final_score_human):
                    print(f"New Personal Best! {final_score_human}")
                
                pygame.time.wait(2000)
                running = False
                
    except KeyboardInterrupt:
        print("\n[!] Game interrupted by user.")
        sys.exit(100)
    except SystemExit as e:
        if e.code == 100:
            sys.exit(100)
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
        pygame.quit()
        
    pygame.quit()

if __name__ == "__main__":
    play_game()
