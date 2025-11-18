# main.py
import train
import play
import pygame
import config
import game_engine

def play_pvp():
    """
    Runs the game in Player vs Player mode.
    """
    print("Starting Player vs Player...")
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Project PaddleMind - PvP")
    clock = pygame.time.Clock()
    
    game = game_engine.Game()
    
    running = True
    while running:
        clock.tick(config.FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        # Left Paddle (W/S)
        left_move = None
        if keys[pygame.K_w]:
            left_move = "UP"
        elif keys[pygame.K_s]:
            left_move = "DOWN"
            
        # Right Paddle (Up/Down)
        right_move = None
        if keys[pygame.K_UP]:
            right_move = "UP"
        elif keys[pygame.K_DOWN]:
            right_move = "DOWN"

        game.update(left_move, right_move)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()

def main():
    print("Welcome to Project PaddleMind")
    print("1. Train a new AI")
    print("2. Play against an AI")
    print("3. Play Player vs Player")
    
    try:
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            train.run_training()
        elif choice == '2':
            play.play_game()
        elif choice == '3':
            play_pvp()
        else:
            print("Invalid choice.")
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
