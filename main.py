import pygame
import sys
import os
import random
import math

pygame.init()

# --- Screen setup ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brain Bucket")
clock = pygame.time.Clock()

# --- Modern Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CARD_BACK = (25, 35, 60)  # Dark blue to match background
CARD_BORDER = (70, 180, 255)  # Bright blue border
CARD_REVEALED = (240, 248, 255)  # Light blue/white for revealed cards
CARD_MATCHED = (200, 255, 200)  # Light green for matched cards
PLAYER_COLOR = (100, 150, 255)  # Same color for both human and AI
PLAYER_HIGHLIGHT = (0, 128, 0)  # Highlighting color for active player
BUTTON_COLOR = (50, 150, 250)
BUTTON_HOVER = (80, 180, 255)
BUTTON_TEXT = WHITE
SHADOW_COLOR = (0, 0, 0, 50)  # Semi-transparent black

# --- Grid Config ---
ROWS, COLS = 4, 4
BLOCK_SIZE = 90  # Slightly larger
BLOCK_GAP = 12  # More spacing
BORDER_RADIUS = 12  # More rounded corners
BORDER_WIDTH = 3  # Thinner border for modern look

GRID_WIDTH = COLS * BLOCK_SIZE + (COLS - 1) * BLOCK_GAP
GRID_HEIGHT = ROWS * BLOCK_SIZE + (ROWS - 1) * BLOCK_GAP

grid_x = (WIDTH - GRID_WIDTH) // 2
grid_y = 130  # Reduced space for simplified header

# --- Modern Fonts ---
title_font = pygame.font.SysFont("Arial", 48, bold=True)
score_font = pygame.font.SysFont("Arial", 24, bold=True)
button_font = pygame.font.SysFont("Arial", 24, bold=True)

# --- Background ---
def create_cover_background():
    """Create a background image that covers the screen (like CSS background-size: cover)"""
    original_bg = pygame.image.load(os.path.join("img", "bg.jpg"))
    original_width, original_height = original_bg.get_size()
    
    # Calculate scale to cover the entire screen
    scale_x = WIDTH / original_width
    scale_y = HEIGHT / original_height
    scale = max(scale_x, scale_y)  # Use the larger scale to ensure full coverage
    
    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # Scale the image
    scaled_bg = pygame.transform.smoothscale(original_bg, (new_width, new_height))
    
    # Create a surface for the final background
    bg_surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Center the scaled image on the screen
    offset_x = (WIDTH - new_width) // 2
    offset_y = (HEIGHT - new_height) // 2
    
    bg_surface.blit(scaled_bg, (offset_x, offset_y))
    
    return bg_surface

bg_image = create_cover_background()

def draw_shadow(surface, rect, offset=3):
    """Draw a subtle shadow behind elements"""
    shadow_surface = pygame.Surface((rect.width + offset * 2, rect.height + offset * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, SHADOW_COLOR, 
                     (0, 0, rect.width + offset * 2, rect.height + offset * 2), 
                     border_radius=BORDER_RADIUS)
    surface.blit(shadow_surface, (rect.x - offset, rect.y - offset))

def initialize_game():
    """Initialize or reset the game state"""
    global blocks, selected_blocks, current_turn, human_score, ai_score, ai_memory, ai_last_move, last_reveal_time, waiting_to_switch
    
    # --- Load 8 images (2 of each) ---
    image_paths = [os.path.join("img", f"{i}.png") for i in range(1, 9)] * 2
    random.shuffle(image_paths)

    # Load and scale images
    def load_scaled_image(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, (BLOCK_SIZE - 20, BLOCK_SIZE - 20))

    # Load images and assign IDs (1 to 8)
    loaded_images = {}
    for i in range(1, 9):
        path = os.path.join("img", f"{i}.png")
        loaded_images[i] = load_scaled_image(path)

    # Create shuffled ID pairs (2 of each)
    image_ids = list(loaded_images.keys()) * 2
    random.shuffle(image_ids)

    # --- Block structure ---
    blocks = []
    for i in range(ROWS * COLS):
        row = i // COLS
        col = i % COLS
        x = grid_x + col * (BLOCK_SIZE + BLOCK_GAP)
        y = grid_y + row * (BLOCK_SIZE + BLOCK_GAP)
        rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        
        image_id = image_ids[i]
        blocks.append({
            "rect": rect,
            "image": loaded_images[image_id],
            "image_id": image_id,
            "revealed": False,
            "matched": False,
            "id": i
        })

    # --- Game State ---
    selected_blocks = []
    current_turn = "HUMAN"
    human_score = 0
    ai_score = 0
    ai_memory = {}
    ai_last_move = 0
    last_reveal_time = 0
    waiting_to_switch = False

# Initialize the game
initialize_game()

ai_thinking_delay = 800
reveal_delay = 1000

# --- Timer events ---
SWITCH_TURN_EVENT = pygame.USEREVENT + 1

def switch_turn():
    global current_turn
    current_turn = "AI" if current_turn == "HUMAN" else "HUMAN"

def create_restart_button():
    """Create modern restart button"""
    button_width, button_height = 180, 50
    button_x = (WIDTH - button_width) // 2
    button_y = (HEIGHT // 2) + 100
    return pygame.Rect(button_x, button_y, button_width, button_height)

def draw_modern_header():
    """Draw simplified header with title and flexible score panels"""
    # Title with shadow
    title_text = title_font.render("Brain Bucket", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 50))
    
    # Shadow for title
    shadow_text = title_font.render("Brain Bucket", True, (0, 0, 0, 100))
    screen.blit(shadow_text, (title_rect.x + 2, title_rect.y + 2))
    screen.blit(title_text, title_rect)
    
    # Flexible score panels
    panel_width, panel_height = 140, 50
    
    # Human score panel
    human_panel = pygame.Rect(50, 80, panel_width, panel_height)
    draw_shadow(screen, human_panel, 2)
    
    # Panel color - same color for both, highlighted when active
    human_panel_color = PLAYER_HIGHLIGHT if current_turn == "HUMAN" else PLAYER_COLOR
    pygame.draw.rect(screen, human_panel_color, human_panel, border_radius=10)
    pygame.draw.rect(screen, WHITE, human_panel, width=2, border_radius=10)
    
    # Human text - side by side format
    human_text = score_font.render(f"Human: {human_score}", True, WHITE)
    text_rect = human_text.get_rect(center=human_panel.center)
    screen.blit(human_text, text_rect)
    
    # AI score panel
    ai_panel = pygame.Rect(WIDTH - 190, 80, panel_width, panel_height)
    draw_shadow(screen, ai_panel, 2)
    
    ai_panel_color = PLAYER_HIGHLIGHT if current_turn == "AI" else PLAYER_COLOR
    pygame.draw.rect(screen, ai_panel_color, ai_panel, border_radius=10)
    pygame.draw.rect(screen, WHITE, ai_panel, width=2, border_radius=10)
    
    # AI text - side by side format
    ai_text = score_font.render(f"AI: {ai_score}", True, WHITE)
    text_rect = ai_text.get_rect(center=ai_panel.center)
    screen.blit(ai_text, text_rect)

def draw_modern_card(block):
    """Draw a modern-styled card with enhanced visuals"""
    rect = block["rect"]
    flip_progress = block.get("flip_progress", 0)
    
    # Determine card state
    is_revealed = block.get("revealed", False)
    is_matched = block.get("matched", False)
    is_flipping = block.get("flipping", False)
    
    show_image = (
        is_revealed or is_matched or 
        (is_flipping and block.get("flip_target") == "reveal" and flip_progress > 0.5)
    )
    
    # Calculate flip animation
    if is_flipping:
        scale = 1 - abs(flip_progress - 0.5) * 2
        scaled_width = max(1, int(BLOCK_SIZE * scale))
        draw_rect = pygame.Rect(rect.centerx - scaled_width // 2, rect.y, scaled_width, BLOCK_SIZE)
    else:
        draw_rect = rect
    
    # Draw shadow
    draw_shadow(screen, draw_rect, 3)
    
    # Choose card color
    if is_matched:
        card_color = CARD_MATCHED
        border_color = (100, 255, 100)
    elif show_image:
        card_color = CARD_REVEALED
        border_color = CARD_BORDER
    else:
        card_color = CARD_BACK
        border_color = CARD_BORDER
    
    # Draw card
    pygame.draw.rect(screen, card_color, draw_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, border_color, draw_rect, width=BORDER_WIDTH, border_radius=BORDER_RADIUS)
    
    # Draw image or back pattern
    if show_image and draw_rect.width > 20:
        image = pygame.transform.smoothscale(block["image"], (draw_rect.width - 20, draw_rect.height - 20))
        screen.blit(image, image.get_rect(center=draw_rect.center))
    elif not show_image:
        # Draw a subtle pattern on card back
        center_x, center_y = draw_rect.center
        for i in range(3):
            radius = 8 + i * 6
            alpha = 30 - i * 8
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (255, 255, 255, alpha), (radius, radius), radius)
            screen.blit(circle_surface, (center_x - radius, center_y - radius))

# --- Main loop ---
running = True
while running:
    screen.blit(bg_image, (0, 0))
    
    # Draw simplified header
    draw_modern_header()
    
    now = pygame.time.get_ticks()
    
    # --- Draw Cards ---
    for block in blocks:
        draw_modern_card(block)
    
    # Update flip animations
    for block in blocks:
        if block.get("flipping", False):
            block["flip_progress"] += 0.1 * block["flip_direction"]
            
            if block["flip_progress"] >= 0.5 and block["flip_direction"] == 1:
                if block["flip_target"] == "reveal":
                    block["revealed"] = True
                elif block["flip_target"] == "hide":
                    block["revealed"] = False
                block["flip_direction"] = -1
            
            if block["flip_progress"] <= 0:
                block["flipping"] = False
                block["flip_progress"] = 0
    
    # Game over screen
    game_over = human_score + ai_score == 8
    if game_over:
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        
        # Win message
        win_font = pygame.font.SysFont("Arial", 54, bold=True)
        
        if human_score > ai_score:
            win_text = win_font.render("Victory!", True, (100, 255, 100))
            subtitle = score_font.render("Congratulations! You won!", True, WHITE)
        elif ai_score > human_score:
            win_text = win_font.render("Game Over", True, (255, 100, 100))
            subtitle = score_font.render("Better luck next time!", True, WHITE)
        else:
            win_text = win_font.render("Draw!", True, (100, 150, 255))
            subtitle = score_font.render("Great match! It's a tie!", True, WHITE)
        
        # Center the messages
        win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        
        # Draw shadows
        shadow_win = win_font.render(win_text.get_text() if hasattr(win_text, 'get_text') else 
                                   ("Victory!" if human_score > ai_score else 
                                    "Game Over" if ai_score > human_score else "Draw!"), True, (0, 0, 0))
        screen.blit(shadow_win, (win_rect.x + 2, win_rect.y + 2))
        screen.blit(win_text, win_rect)
        screen.blit(subtitle, subtitle_rect)
        
        # Modern restart button
        restart_button = create_restart_button()
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = restart_button.collidepoint(mouse_pos)
        
        draw_shadow(screen, restart_button, 3)
        
        button_color = BUTTON_HOVER if is_hovering else BUTTON_COLOR
        pygame.draw.rect(screen, button_color, restart_button, border_radius=12)
        pygame.draw.rect(screen, WHITE, restart_button, width=2, border_radius=12)
        
        button_text = button_font.render("Play Again", True, BUTTON_TEXT)
        text_rect = button_text.get_rect(center=restart_button.center)
        screen.blit(button_text, text_rect)
    
    pygame.display.flip()
    clock.tick(60)
    
    # Game logic
    if len(selected_blocks) == 2 and not waiting_to_switch and now - last_reveal_time > reveal_delay:
        b1, b2 = selected_blocks
        
        if b1["image_id"] == b2["image_id"]:
            b1["matched"] = b2["matched"] = True
            if current_turn == "HUMAN":
                human_score += 1
            else:
                ai_score += 1
        else:
            for b in [b1, b2]:
                b["flipping"] = True
                b["flip_progress"] = 0
                b["flip_direction"] = 1
                b["flip_target"] = "hide"
        
        waiting_to_switch = True
        pygame.time.set_timer(SWITCH_TURN_EVENT, 500)
    
    # AI Turn
    if current_turn == "AI" and not waiting_to_switch and len(selected_blocks) < 2 and now - ai_last_move > ai_thinking_delay and not game_over:
        unrevealed = [b for b in blocks if not b["revealed"] and not b["matched"]]
        match_found = False
        
        for img_id, ids in ai_memory.items():
            matching_ids = [bid for bid in ids if not blocks[bid]["matched"]]
            if len(matching_ids) >= 2:
                b1 = blocks[matching_ids[0]]
                b2 = blocks[matching_ids[1]]
                for b in [b1, b2]:
                    b["flipping"] = True
                    b["flip_progress"] = 0
                    b["flip_direction"] = 1
                    b["flip_target"] = "reveal"
                selected_blocks = [b1, b2]
                match_found = True
                break
        
        if not match_found and len(unrevealed) >= 2:
            choices = random.sample(unrevealed, 2)
            for b in choices:
                b["flipping"] = True
                b["flip_progress"] = 0
                b["flip_direction"] = 1
                b["flip_target"] = "reveal"
                img_id = b["image_id"]
                if img_id not in ai_memory:
                    ai_memory[img_id] = []
                if b["id"] not in ai_memory[img_id]:
                    ai_memory[img_id].append(b["id"])
            selected_blocks = choices
        
        ai_last_move = pygame.time.get_ticks()
        last_reveal_time = pygame.time.get_ticks()
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_over:
                restart_button = create_restart_button()
                if restart_button.collidepoint(event.pos):
                    initialize_game()
            elif current_turn == "HUMAN" and not waiting_to_switch:
                if len(selected_blocks) < 2:
                    pos = pygame.mouse.get_pos()
                    for block in blocks:
                        if block["rect"].collidepoint(pos) and not block["revealed"] and not block["matched"]:
                            block["flipping"] = True
                            block["flip_progress"] = 0
                            block["flip_direction"] = 1
                            block["flip_target"] = "reveal"
                            selected_blocks.append(block)
                            
                            img_id = block["image_id"]
                            if img_id not in ai_memory:
                                ai_memory[img_id] = []
                            if block["id"] not in ai_memory[img_id]:
                                ai_memory[img_id].append(block["id"])
                            
                            if len(selected_blocks) == 2:
                                last_reveal_time = pygame.time.get_ticks()
                            break
        
        elif event.type == SWITCH_TURN_EVENT:
            pygame.time.set_timer(SWITCH_TURN_EVENT, 0)
            selected_blocks = []
            waiting_to_switch = False
            switch_turn()

pygame.quit()
sys.exit()