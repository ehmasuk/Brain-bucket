import pygame
import sys
import os
import random

pygame.init()

# --- Screen setup ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match - Brain Bucket")
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLOCK_BORDER = (200, 200, 200)
BG_COLOR = (20, 20, 40)
RED = (255, 60, 60)
BLUE = (60, 160, 255)

# --- Grid Config ---
ROWS, COLS = 4, 4
BLOCK_SIZE = 85
BLOCK_GAP = 10
BORDER_RADIUS = 6
BORDER_WIDTH = 5

GRID_WIDTH = COLS * BLOCK_SIZE + (COLS - 1) * BLOCK_GAP
GRID_HEIGHT = ROWS * BLOCK_SIZE + (ROWS - 1) * BLOCK_GAP

grid_x = (WIDTH - GRID_WIDTH) // 2
grid_y = 130

# --- Fonts ---
title_font = pygame.font.SysFont("Arial", 36, bold=True)
small_font = pygame.font.SysFont("Arial", 24)

# --- Background ---
bg_image = pygame.image.load(os.path.join("img", "bg.jpg"))
bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

# --- Load 8 images (2 of each) ---
image_paths = [os.path.join("img", f"{i}.png") for i in range(1, 9)] * 2
random.shuffle(image_paths)

# Load and scale images
def load_scaled_image(path):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (BLOCK_SIZE - 10, BLOCK_SIZE - 10))

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
current_turn = "HUMAN"  # or "AI"
human_score = 0
ai_score = 0
ai_memory = {}  # image_id -> list of block ids
ai_last_move = 0
ai_thinking_delay = 800  # ms delay before AI acts
last_reveal_time = 0
reveal_delay = 1000  # 1 second after reveal
waiting_to_switch = False  # 2-second wait before switch


# --- Timer events ---
SWITCH_TURN_EVENT = pygame.USEREVENT + 1

def switch_turn():
    global current_turn
    current_turn = "AI" if current_turn == "HUMAN" else "HUMAN"

# --- Main loop ---
running = True
while running:
    screen.blit(bg_image, (0, 0))

    # --- Title ---
    title = title_font.render("Brain Bucket", True, WHITE)
    screen.blit(title, ((WIDTH - title.get_width()) // 2, 40))

    # --- Turn and Score ---
    turn_text = small_font.render(f"Turn: {current_turn}", True, RED if current_turn == "HUMAN" else BLUE)
    screen.blit(turn_text, (30, 20))

    score_text = small_font.render(f"Human: {human_score}    AI: {ai_score}", True, WHITE)
    screen.blit(score_text, (WIDTH - score_text.get_width() - 30, 20))

    now = pygame.time.get_ticks()

    # --- Draw Blocks ---
    for block in blocks:
        rect = block["rect"]
        flip_progress = block.get("flip_progress", 0)

        # Proper show condition during flip
        show_image = (
            block.get("revealed", False) or 
            block.get("matched", False) or 
            (block.get("flipping") and block.get("flip_target") == "reveal" and flip_progress > 0.5)
        )

        if block.get("flipping", False):
            scale = 1 - abs(flip_progress - 0.5) * 2  # 1 → 0 → 1
            scaled_width = max(1, int(BLOCK_SIZE * scale))
            draw_rect = pygame.Rect(rect.centerx - scaled_width // 2, rect.y, scaled_width, BLOCK_SIZE)
        else:
            draw_rect = rect

        pygame.draw.rect(screen, BLOCK_BORDER, draw_rect, border_radius=BORDER_RADIUS)

        if show_image:
            pygame.draw.rect(screen, WHITE, draw_rect.inflate(-BORDER_WIDTH * 2, -BORDER_WIDTH * 2), border_radius=BORDER_RADIUS)
            if draw_rect.width > 10:
                image = pygame.transform.smoothscale(block["image"], (draw_rect.width - 10, draw_rect.height - 10))
                screen.blit(image, image.get_rect(center=draw_rect.center))
        else:
            pygame.draw.rect(screen, BG_COLOR, draw_rect.inflate(-BORDER_WIDTH * 2, -BORDER_WIDTH * 2), border_radius=BORDER_RADIUS)



    for block in blocks:
        if block.get("flipping", False):
            block["flip_progress"] += 0.1 * block["flip_direction"]
            
            # Reached midpoint — toggle reveal/hide
            if block["flip_progress"] >= 0.5 and block["flip_direction"] == 1:
                if block["flip_target"] == "reveal":
                    block["revealed"] = True
                elif block["flip_target"] == "hide":
                    block["revealed"] = False
                block["flip_direction"] = -1  # start expanding

            # Finish flip
            if block["flip_progress"] <= 0:
                block["flipping"] = False
                block["flip_progress"] = 0



    pygame.display.flip()
    clock.tick(60)

    # --- Hide and schedule switch after 2 cards are revealed and delay passed ---
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

        # Start 2-second wait before switching turn
        waiting_to_switch = True
        pygame.time.set_timer(SWITCH_TURN_EVENT, 2000)

    # --- AI Turn ---
    if current_turn == "AI" and not waiting_to_switch and len(selected_blocks) < 2 and now - ai_last_move > ai_thinking_delay:
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

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and current_turn == "HUMAN" and not waiting_to_switch:
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
