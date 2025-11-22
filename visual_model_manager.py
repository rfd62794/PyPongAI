import pygame
import sys
import os
import config
from ai import model_manager

def show_model_manager():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Project PaddleMind - Model Manager")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Load models
    models = model_manager.scan_models()
    models.sort(key=lambda x: model_manager.get_fitness_from_filename(os.path.basename(x)), reverse=True)
    
    # Pagination
    page = 0
    per_page = 8
    
    selected_index = -1
    
    # Buttons
    btn_organize = pygame.Rect(50, config.SCREEN_HEIGHT - 80, 200, 50)
    # btn_delete = pygame.Rect(270, config.SCREEN_HEIGHT - 80, 200, 50) # TODO: Implement delete
    btn_back = pygame.Rect(config.SCREEN_WIDTH - 150, 20, 100, 40)
    
    running = True
    while running:
        screen.fill(config.BLACK)
        
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos # Use event position for accuracy
                
                if btn_back.collidepoint((mx, my)):
                    running = False
                    sys.exit(0) # Return to main menu logic

                if btn_organize.collidepoint((mx, my)):
                    print("Organizing models...")
                    model_manager.organize_models()
                    # Reload models
                    models = model_manager.scan_models()
                    models.sort(key=lambda x: model_manager.get_fitness_from_filename(os.path.basename(x)), reverse=True)
                
                # Pagination clicks (simple zones)
                # Left side of pagination text
                if config.SCREEN_HEIGHT - 150 < my < config.SCREEN_HEIGHT - 100:
                     if mx < config.SCREEN_WIDTH // 2:
                         page = max(0, page - 1)
                     else:
                         max_page = (len(models) - 1) // per_page
                         page = min(max_page, page + 1)

        # Header
        title = font.render("Model Manager", True, config.WHITE)
        screen.blit(title, (50, 30))
        
        stats = f"Total Models: {len(models)}"
        stats_surf = small_font.render(stats, True, config.GRAY)
        screen.blit(stats_surf, (50, 70))
        
        # Model List
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(models))
        
        list_y = 120
        for i in range(start_idx, end_idx):
            model_path = models[i]
            filename = os.path.basename(model_path)
            fitness = model_manager.get_fitness_from_filename(filename)
            parent_dir = os.path.basename(os.path.dirname(model_path))
            
            # Highlight selected
            rect = pygame.Rect(50, list_y, config.SCREEN_WIDTH - 100, 40)
            color = (70, 70, 100) if i == selected_index else (40, 40, 40)
            
            # Hover effect
            mx, my = pygame.mouse.get_pos()
            if rect.collidepoint((mx, my)):
                color = (60, 60, 80) if i != selected_index else (80, 80, 120)
                if pygame.mouse.get_pressed()[0]:
                    selected_index = i
                
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, config.WHITE, rect, 1)
            
            text = f"{i+1}. {filename} | Fit: {fitness} | Loc: {parent_dir}"
            text_surf = small_font.render(text, True, config.WHITE)
            screen.blit(text_surf, (60, list_y + 10))
            
            list_y += 50
            
        # Pagination Controls
        if len(models) > per_page:
            page_text = f"Page {page + 1} / {(len(models) - 1) // per_page + 1}"
            page_surf = small_font.render(page_text, True, config.WHITE)
            screen.blit(page_surf, (config.SCREEN_WIDTH // 2 - page_surf.get_width() // 2, list_y + 10))
            
            hint = small_font.render("Click Left/Right side to Navigate", True, config.GRAY)
            screen.blit(hint, (config.SCREEN_WIDTH // 2 - hint.get_width() // 2, list_y + 30))

        # Action Buttons
        # Organize
        pygame.draw.rect(screen, (50, 100, 50), btn_organize)
        pygame.draw.rect(screen, config.WHITE, btn_organize, 2)
        org_text = font.render("Auto-Organize", True, config.WHITE)
        screen.blit(org_text, (btn_organize.centerx - org_text.get_width()//2, btn_organize.centery - org_text.get_height()//2))
        
        # Back
        pygame.draw.rect(screen, (100, 50, 50), btn_back)
        pygame.draw.rect(screen, config.WHITE, btn_back, 2)
        back_text = small_font.render("Back", True, config.WHITE)
        screen.blit(back_text, (btn_back.centerx - back_text.get_width()//2, btn_back.centery - back_text.get_height()//2))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    try:
        show_model_manager()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()
