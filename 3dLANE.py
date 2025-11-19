import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Lane Sphere Game")
clock = pygame.time.Clock()

# Colors
SKY_BLUE = (135, 206, 235)
ROAD_GRAY = (80, 80, 80)
LINE_WHITE = (255, 255, 255)
SPHERE_RED = (255, 50, 50)
TREE_GREEN = (34, 139, 34)
TREE_BROWN = (101, 67, 33)
GOLD = (255, 215, 0)
BLACK = (0, 0, 0)

# Game settings
FPS = 60
lane_count = 3
current_lane = 1  # Middle lane (0=left, 1=middle, 2=right)

# 3D perspective settings
horizon = HEIGHT // 3
road_width_far = 100
road_width_near = 600
perspective_segments = 100

class Tree:
    def __init__(self, lane, distance):
        self.lane = lane
        self.distance = distance
        self.width = 40
        self.height = 60
        
    def update(self, speed):
        self.distance -= speed
        
    def draw(self, screen):
        if self.distance > 0:
            # Calculate perspective scale
            scale = 1 - (self.distance / 1000)
            scale = max(0.1, min(scale, 1))
            
            # Calculate screen position
            screen_y = horizon + (HEIGHT - horizon) * (1 - self.distance / 1000)
            
            # Calculate lane position
            road_width = road_width_far + (road_width_near - road_width_far) * scale
            lane_width = road_width / lane_count
            lane_x = WIDTH // 2 - road_width // 2 + self.lane * lane_width + lane_width // 2
            
            # Draw tree trunk
            trunk_width = int(15 * scale)
            trunk_height = int(30 * scale)
            pygame.draw.rect(screen, TREE_BROWN,
                           (lane_x - trunk_width // 2, 
                            int(screen_y) - trunk_height,
                            trunk_width, trunk_height))
            
            # Draw tree foliage (circle)
            foliage_radius = int(25 * scale)
            pygame.draw.circle(screen, TREE_GREEN,
                             (int(lane_x), int(screen_y) - trunk_height),
                             foliage_radius)
            
            # Add darker outline
            pygame.draw.circle(screen, (20, 100, 20),
                             (int(lane_x), int(screen_y) - trunk_height),
                             foliage_radius, 2)

class Collectible:
    def __init__(self, lane, distance):
        self.lane = lane
        self.distance = distance
        self.radius = 15
        self.collected = False
        
    def update(self, speed):
        self.distance -= speed
        
    def draw(self, screen):
        if self.distance > 0 and not self.collected:
            # Calculate perspective scale
            scale = 1 - (self.distance / 1000)
            scale = max(0.1, min(scale, 1))
            
            # Calculate screen position
            screen_y = horizon + (HEIGHT - horizon) * (1 - self.distance / 1000)
            
            # Calculate lane position
            road_width = road_width_far + (road_width_near - road_width_far) * scale
            lane_width = road_width / lane_count
            lane_x = WIDTH // 2 - road_width // 2 + self.lane * lane_width + lane_width // 2
            
            # Draw coin (gold circle)
            coin_radius = int(self.radius * scale)
            pygame.draw.circle(screen, GOLD,
                             (int(lane_x), int(screen_y) - coin_radius),
                             coin_radius)
            
            # Add shine effect
            pygame.draw.circle(screen, (255, 255, 200),
                             (int(lane_x) - coin_radius // 3, 
                              int(screen_y) - coin_radius - coin_radius // 3),
                             coin_radius // 3)
            
            # Add outline
            pygame.draw.circle(screen, (200, 170, 0),
                             (int(lane_x), int(screen_y) - coin_radius),
                             coin_radius, 2)

def draw_road(screen):
    # Draw sky
    screen.fill(SKY_BLUE)
    
    # Draw road with perspective
    for i in range(perspective_segments):
        progress = i / perspective_segments
        
        # Calculate width at this segment
        segment_width = road_width_far + (road_width_near - road_width_far) * progress
        y_pos = horizon + (HEIGHT - horizon) * progress
        
        # Draw road segment
        left_x = WIDTH // 2 - segment_width // 2
        right_x = WIDTH // 2 + segment_width // 2
        
        # Alternate road colors for depth effect
        color_offset = int(progress * 20)
        road_color = (ROAD_GRAY[0] - color_offset, 
                     ROAD_GRAY[1] - color_offset, 
                     ROAD_GRAY[2] - color_offset)
        
        if i < perspective_segments - 1:
            next_progress = (i + 1) / perspective_segments
            next_width = road_width_far + (road_width_near - road_width_far) * next_progress
            next_y = horizon + (HEIGHT - horizon) * next_progress
            next_left = WIDTH // 2 - next_width // 2
            next_right = WIDTH // 2 + next_width // 2
            
            # Draw road polygon
            points = [(left_x, y_pos), (right_x, y_pos), 
                     (next_right, next_y), (next_left, next_y)]
            pygame.draw.polygon(screen, road_color, points)
            
            # Draw lane dividers
            if i % 10 == 0:
                for lane in range(1, lane_count):
                    lane_pos = left_x + (segment_width / lane_count) * lane
                    next_lane_pos = next_left + (next_width / lane_count) * lane
                    pygame.draw.line(screen, LINE_WHITE,
                                   (lane_pos, y_pos),
                                   (next_lane_pos, next_y), 2)

def draw_sphere(screen, lane):
    # Calculate sphere position (always at bottom of screen)
    sphere_y = HEIGHT - 80
    road_width = road_width_near
    lane_width = road_width / lane_count
    sphere_x = WIDTH // 2 - road_width // 2 + lane * lane_width + lane_width // 2
    
    # Draw sphere with shading
    radius = 30
    pygame.draw.circle(screen, SPHERE_RED, (int(sphere_x), sphere_y), radius)
    
    # Add highlight for 3D effect
    highlight_offset = radius // 3
    pygame.draw.circle(screen, (255, 150, 150),
                      (int(sphere_x) - highlight_offset, 
                       sphere_y - highlight_offset),
                      radius // 3)
    
    # Add shadow
    shadow_y = HEIGHT - 40
    pygame.draw.ellipse(screen, (50, 50, 50),
                       (int(sphere_x) - radius, shadow_y - 5, radius * 2, 10))

def check_tree_collision(player_lane, trees):
    for tree in trees:
        # Check if tree is at player position and in same lane
        if 10 < tree.distance < 50 and tree.lane == player_lane:
            return True
    return False

def check_collectible_collision(player_lane, collectibles):
    for collectible in collectibles:
        # Check if collectible is at player position and in same lane
        if 10 < collectible.distance < 80 and collectible.lane == player_lane and not collectible.collected:
            collectible.collected = True
            return True
    return False

# Main game loop
def main():
    global current_lane
    
    running = True
    game_over = False
    score = 0
    coins_collected = 0
    speed = 5
    
    trees = []
    collectibles = []
    tree_spawn_timer = 0
    tree_spawn_delay = 60
    collectible_spawn_timer = 0
    collectible_spawn_delay = 40
    
    # Font for score
    font = pygame.font.Font(None, 36)
    
    while running:
        clock.tick(FPS)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and current_lane > 0:
                        current_lane -= 1
                    elif event.key == pygame.K_RIGHT and current_lane < lane_count - 1:
                        current_lane += 1
        
        if not game_over:
            # Spawn trees
            tree_spawn_timer += 1
            if tree_spawn_timer >= tree_spawn_delay:
                tree_spawn_timer = 0
                lane = random.randint(0, lane_count - 1)
                trees.append(Tree(lane, 1000))
                
                # Increase difficulty
                if score % 10 == 0 and score > 0:
                    speed += 0.05
                    tree_spawn_delay = max(30, tree_spawn_delay - 1)
            
            # Spawn collectibles
            collectible_spawn_timer += 1
            if collectible_spawn_timer >= collectible_spawn_delay:
                collectible_spawn_timer = 0
                lane = random.randint(0, lane_count - 1)
                collectibles.append(Collectible(lane, 1000))
            
            # Update trees
            for tree in trees:
                tree.update(speed)
            
            # Update collectibles
            for collectible in collectibles:
                collectible.update(speed)
            
            # Remove off-screen objects and update score
            trees = [tree for tree in trees if tree.distance > -50]
            collectibles = [col for col in collectibles if col.distance > -50]
            
            for tree in trees:
                if tree.distance < -10 and tree.distance > -15:
                    score += 1
            
            # Check collectible collision
            if check_collectible_collision(current_lane, collectibles):
                coins_collected += 1
                score += 5  # Bonus points for collecting coins
            
            # Check tree collision
            if check_tree_collision(current_lane, trees):
                game_over = True
        
        # Drawing
        draw_road(screen)
        
        # Draw collectibles first (behind trees)
        for collectible in collectibles:
            collectible.draw(screen)
        
        # Draw trees
        for tree in trees:
            tree.draw(screen)
        
        # Draw player sphere
        draw_sphere(screen, current_lane)
        
        # Draw score and coins
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        coins_text = font.render(f"Coins: {coins_collected}", True, GOLD)
        screen.blit(coins_text, (10, 50))
        
        # Draw game over
        if game_over:
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("GAME OVER!", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(game_over_text, text_rect)
            
            final_score_text = font.render(f"Final Score: {score} | Coins: {coins_collected}", True, BLACK)
            final_rect = final_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(final_score_text, final_rect)
            
            restart_text = font.render("Press R to Restart", True, BLACK)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90))
            screen.blit(restart_text, restart_rect)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                # Reset game
                game_over = False
                score = 0
                coins_collected = 0
                speed = 5
                trees = []
                collectibles = []
                current_lane = 1
                tree_spawn_delay = 60
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
