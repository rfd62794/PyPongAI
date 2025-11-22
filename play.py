import patch_neat
import pygame
import neat
import os
import pickle
from core import config
from core.engine import Game
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
    game_over = False
    
    # Initialize Recorder
    from core.recorder import GameRecorder
    recorder = GameRecorder()
    
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
                
                # Game Over Menu Events
                if game_over:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            # Rematch - RELOAD RIVAL
                            # Fetch the new rival path (it was updated in update_match_result)
                            new_rival_path = rival_sys.get_rival_model()
                            if new_rival_path and os.path.exists(new_rival_path):
                                print(f"Rematch: Loading new rival {os.path.basename(new_rival_path)}")
                                with open(new_rival_path, "rb") as f:
                                    genome = pickle.load(f)
                                net = neat.nn.FeedForwardNetwork.create(genome, neat_config)
                            
                            game = Game()
                            recorder = GameRecorder() # New recording
                            game_over = False
                        elif event.key == pygame.K_m:
                            # Menu
                            running = False
                        elif event.key == pygame.K_q:
                            # Quit
                            running = False
                            sys.exit(100)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                         # Check clicks if we add buttons later
                         pass

            if not game_over:
                # Human Input (Right Paddle)
                keys = pygame.key.get_pressed()
                action_right = None
                if keys[pygame.K_UP]:
                    game.right_paddle.move(up=True)
                    action_right = "UP"
                if keys[pygame.K_DOWN]:
                    game.right_paddle.move(up=False)
                    action_right = "DOWN"

                # AI Input (Left Paddle)
                # Inputs: Paddle Y, Ball X, Ball Y, Ball VX, Ball VY, Relative Y, Incoming
                inputs = (
                    game.left_paddle.rect.y,
                    game.ball.rect.x,
                    game.ball.rect.y,
                    game.ball.vel_x,
                    game.ball.vel_y,
                    game.left_paddle.rect.y - game.ball.rect.y,
                    1.0 if game.ball.vel_x < 0 else 0.0,
                    game.right_paddle.rect.y
                )
                output = net.activate(inputs)
                
                decision = output.index(max(output))
                action_left = None
                
                if decision == 0: # Up
                    game.left_paddle.move(up=True)
                    action_left = "UP"
                elif decision == 1: # Down
                    game.left_paddle.move(up=False)
                    action_left = "DOWN"
                # 2 is Stay
                
                # Update Game
                game_state = game.update(dt)
                
                # Log Frame
                # We need to get state dict manually or use game.get_state() if available
                # game_engine.py has get_state()
                state = game.get_state()
                recorder.log_frame(state, action_left, action_right)
                
                game.draw(screen)
                
                if game_state and game_state.get("game_over"):
                    final_score_human = game.score_right
                    final_score_ai = game.score_left
                    won = final_score_human > final_score_ai
                    
                    # Update Best Score
                    if rival_sys.update_score(final_score_human):
                        print(f"New Personal Best! {final_score_human}")
                        
                    # Update Rival Difficulty (DDA)
                    # Only if we are playing against a Rival (check selected_model_path vs rival_path)
                    # Or we can just always update if we want the "Rival" system to track general performance
                    # Let's update if we launched via "Challenge Rival" OR if we want to track it generally.
                    # For now, let's always update the "Rival Fitness" based on performance, 
                    # so the "Challenge Rival" button is always accurate to current form.
                    rival_sys.update_match_result(final_score_human, final_score_ai, won)
                    
                    # Save Recording
                    recorder.save_recording()
                    
                    game_over = True
                    # Don't exit loop, just switch to game_over state
            
            else:
                # Draw Game Over Screen
                # Darken background
                s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                s.set_alpha(128)
                s.fill((0,0,0))
                screen.blit(s, (0,0))
                
                # Text
                res_text = "YOU WON!" if game.score_right > game.score_left else "YOU LOST!"
                color = (50, 255, 50) if game.score_right > game.score_left else (255, 50, 50)
                
                title_surf = font.render(res_text, True, color)
                screen.blit(title_surf, (config.SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))
                
                score_surf = font.render(f"{game.score_left} - {game.score_right}", True, config.WHITE)
                screen.blit(score_surf, (config.SCREEN_WIDTH//2 - score_surf.get_width()//2, 220))
                
                # Show new rival fitness
                new_fit = rival_sys.stats.get("rival_fitness", "?")
                fit_surf = small_font.render(f"New Rival Rating: {new_fit}", True, config.WHITE)
                screen.blit(fit_surf, (config.SCREEN_WIDTH//2 - fit_surf.get_width()//2, 280))
                
                info_surf = small_font.render("Press R to Rematch (New Rival), M for Menu, Q to Quit", True, config.GRAY)
                screen.blit(info_surf, (config.SCREEN_WIDTH//2 - info_surf.get_width()//2, 400))
            
            pygame.display.flip()
                
    except KeyboardInterrupt:
        print("\n[!] Game interrupted by user.")
        sys.exit(100)
    except SystemExit as e:
        if e.code == 100:
            sys.exit(100)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[!] An error occurred: {e}")
        pygame.quit()
        
    pygame.quit()

if __name__ == "__main__":
    play_game()
