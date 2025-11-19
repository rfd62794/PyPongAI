import pygame
import sys
import os
import subprocess
import config

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("Project PaddleMind - Hub")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 36)

def draw_button(rect, text, hover=False):
    color = (100, 100, 100) if hover else (50, 50, 50)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, config.WHITE, rect, 2) # Border
    
    text_surf = small_font.render(text, True, config.WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

def main_menu():
    global screen
    running = True
    while running:
        screen.fill(config.BLACK)
        
        # Title
        title = font.render("Project PaddleMind", True, config.WHITE)
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mx, my = pygame.mouse.get_pos()
        
        # Buttons
        btn_play = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 150, 300, 50)
        btn_train = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 220, 300, 50)
        btn_manage = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 290, 300, 50)
        btn_dash = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 360, 300, 50)
        btn_quit = pygame.Rect(config.SCREEN_WIDTH//2 - 150, 430, 300, 50)
        
        draw_button(btn_play, "Play Game", btn_play.collidepoint((mx, my)))
        draw_button(btn_train, "Visual Training", btn_train.collidepoint((mx, my)))
        draw_button(btn_manage, "Manage Models", btn_manage.collidepoint((mx, my)))
        draw_button(btn_dash, "Analytics Dashboard", btn_dash.collidepoint((mx, my)))
        draw_button(btn_quit, "Quit", btn_quit.collidepoint((mx, my)))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if btn_play.collidepoint((mx, my)):
                        pygame.quit()
                        try:
                            subprocess.check_call([sys.executable, "play.py"])
                        except subprocess.CalledProcessError as e:
                            if e.returncode == 100:
                                print("Exiting application...")
                                sys.exit()
                        pygame.init()
                        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                        pygame.display.set_caption("Project PaddleMind - Hub")
                        
                    elif btn_train.collidepoint((mx, my)):
                        pygame.quit()
                        try:
                            subprocess.check_call([sys.executable, "visual_train.py"])
                        except subprocess.CalledProcessError as e:
                            if e.returncode == 100:
                                print("Exiting application...")
                                sys.exit()
                        pygame.init()
                        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                        pygame.display.set_caption("Project PaddleMind - Hub")
                        
                    elif btn_manage.collidepoint((mx, my)):
                        pygame.quit()
                        try:
                            subprocess.check_call([sys.executable, "visual_model_manager.py"])
                        except subprocess.CalledProcessError as e:
                            if e.returncode == 100:
                                print("Exiting application...")
                                sys.exit()
                        pygame.init()
                        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                        pygame.display.set_caption("Project PaddleMind - Hub")
                        
                    elif btn_dash.collidepoint((mx, my)):
                        pygame.quit()
                        try:
                            subprocess.check_call([sys.executable, "dashboard.py"])
                        except subprocess.CalledProcessError as e:
                            if e.returncode == 100:
                                print("Exiting application...")
                                sys.exit()
                        pygame.init()
                        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                        pygame.display.set_caption("Project PaddleMind - Hub")
                        
                    elif btn_quit.collidepoint((mx, my)):
                        running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n[!] Exiting Hub...")
        pygame.quit()
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
        pygame.quit()
