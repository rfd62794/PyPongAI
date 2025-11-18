# play.py
import pygame
import pickle
import neat
import os
import config
import game_engine

def play_game():
    """
    Runs the game in Human vs AI mode.
    """
    # List models
    models = [f for f in os.listdir(config.MODEL_DIR) if f.endswith(".pkl")]
    if not models:
        print("No models found in models/ directory. Please train an AI first.")
        return

    print("Available models:")
    for i, m in enumerate(models):
        print(f"{i + 1}. {m}")
    
    try:
        choice = int(input("Select a model number: ")) - 1
        model_filename = models[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    # Load model
    model_path = os.path.join(config.MODEL_DIR, model_filename)
    with open(model_path, "rb") as f:
        genome = pickle.load(f)

    # Load NEAT config to create network
    config_path = os.path.join(os.path.dirname(__file__), config.NEAT_CONFIG_PATH)
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              config_path)
    
    net = neat.nn.FeedForwardNetwork.create(genome, neat_config)

    # Initialize Game
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Project PaddleMind - Human vs AI")
    clock = pygame.time.Clock()
    
    game = game_engine.Game()
    
    running = True
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

        # Update Game
        game.update(left_move, right_move)
        
        # Draw
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    play_game()
