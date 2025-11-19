import pygame
import math

pygame.init()

# Get screen info for fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Fullscreen setup
#screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soccer Stars - Local Multiplayer")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BLUE = (30, 144, 255)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 100, 0)

# Physics constants
FRICTION = 0.99
BOUNCE = 0.8
MIN_VELOCITY = 0.1

class Disc:
    def __init__(self, x, y, radius, color, is_ball=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = 0
        self.vy = 0
        self.color = color
        self.is_ball = is_ball
        self.mass = 2 if is_ball else 1
        
    def update(self):
        # Apply friction
        self.vx *= FRICTION
        self.vy *= FRICTION
        
        # Stop if velocity is very small
        if abs(self.vx) < MIN_VELOCITY:
            self.vx = 0
        if abs(self.vy) < MIN_VELOCITY:
            self.vy = 0
            
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Wall collisions
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * BOUNCE
        elif self.x + self.radius >= WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -self.vx * BOUNCE
            
        # Top and bottom walls (with goal areas) - ONLY BALL CAN SCORE
        goal_left = WIDTH // 2 - 150
        goal_right = WIDTH // 2 + 150
        
        if self.y - self.radius <= 0:
            if self.is_ball and goal_left <= self.x <= goal_right:
                return "player1_scores"  # Goal! (only if it's the ball)
            else:
                self.y = self.radius
                self.vy = -self.vy * BOUNCE
                
        elif self.y + self.radius >= HEIGHT:
            if self.is_ball and goal_left <= self.x <= goal_right:
                return "player2_scores"  # Goal! (only if it's the ball)
            else:
                self.y = HEIGHT - self.radius
                self.vy = -self.vy * BOUNCE
        
        return None
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        if self.is_ball:
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)
    
    def is_moving(self):
        return abs(self.vx) > MIN_VELOCITY or abs(self.vy) > MIN_VELOCITY

def check_collision(disc1, disc2):
    dx = disc1.x - disc2.x
    dy = disc1.y - disc2.y
    distance = math.sqrt(dx * dx + dy * dy)
    
    return distance <= (disc1.radius + disc2.radius)

def resolve_collision(disc1, disc2):
    # Calculate distance and overlap
    dx = disc1.x - disc2.x
    dy = disc1.y - disc2.y
    distance = math.sqrt(dx * dx + dy * dy)
    
    if distance == 0:
        distance = 0.1
        dx = 0.1
    
    # Separate discs
    overlap = (disc1.radius + disc2.radius) - distance
    if overlap > 0:
        nx = dx / distance
        ny = dy / distance
        
        separation = overlap / 2
        disc1.x += nx * separation
        disc1.y += ny * separation
        disc2.x -= nx * separation
        disc2.y -= ny * separation
    
    # Calculate collision response
    collision_angle = math.atan2(dy, dx)
    
    # Rotate velocities
    v1 = math.sqrt(disc1.vx**2 + disc1.vy**2)
    v2 = math.sqrt(disc2.vx**2 + disc2.vy**2)
    
    if v1 > 0:
        angle1 = math.atan2(disc1.vy, disc1.vx)
    else:
        angle1 = 0
        
    if v2 > 0:
        angle2 = math.atan2(disc2.vy, disc2.vx)
    else:
        angle2 = 0
    
    # New velocities after elastic collision
    m1 = disc1.mass
    m2 = disc2.mass
    
    v1x = v1 * math.cos(angle1 - collision_angle)
    v1y = v1 * math.sin(angle1 - collision_angle)
    v2x = v2 * math.cos(angle2 - collision_angle)
    v2y = v2 * math.sin(angle2 - collision_angle)
    
    final_v1x = ((m1 - m2) * v1x + 2 * m2 * v2x) / (m1 + m2)
    final_v2x = ((m2 - m1) * v2x + 2 * m1 * v1x) / (m1 + m2)
    
    # Rotate back
    disc1.vx = final_v1x * math.cos(collision_angle) - v1y * math.sin(collision_angle)
    disc1.vy = final_v1x * math.sin(collision_angle) + v1y * math.cos(collision_angle)
    disc2.vx = final_v2x * math.cos(collision_angle) - v2y * math.sin(collision_angle)
    disc2.vy = final_v2x * math.sin(collision_angle) + v2y * math.cos(collision_angle)

# Initialize game objects
ball = Disc(WIDTH // 2, HEIGHT // 2, 20, YELLOW, is_ball=True)

player1_discs = [
    Disc(WIDTH // 2 - 100, HEIGHT - 200, 30, BLUE),
    Disc(WIDTH // 2, HEIGHT - 200, 30, BLUE),
    Disc(WIDTH // 2 + 100, HEIGHT - 200, 30, BLUE),
]

player2_discs = [
    Disc(WIDTH // 2 - 100, 200, 30, RED),
    Disc(WIDTH // 2, 200, 30, RED),
    Disc(WIDTH // 2 + 100, 200, 30, RED),
]

all_discs = player1_discs + player2_discs + [ball]

# Game state
current_player = 1
selected_disc = None
aiming = False
aim_start = None
power = 0
MAX_POWER = 200

score_p1 = 0
score_p2 = 0

def reset_positions():
    ball.x, ball.y = WIDTH // 2, HEIGHT // 2
    ball.vx, ball.vy = 0, 0
    
    positions_p1 = [(WIDTH // 2 - 100, HEIGHT - 200), (WIDTH // 2, HEIGHT - 200), (WIDTH // 2 + 100, HEIGHT - 200)]
    positions_p2 = [(WIDTH // 2 - 100, 200), (WIDTH // 2, 200), (WIDTH // 2 + 100, 200)]
    
    for i, disc in enumerate(player1_discs):
        disc.x, disc.y = positions_p1[i]
        disc.vx, disc.vy = 0, 0
    
    for i, disc in enumerate(player2_discs):
        disc.x, disc.y = positions_p2[i]
        disc.vx, disc.vy = 0, 0

def all_stopped():
    return all(not disc.is_moving() for disc in all_discs)

# Game loop
running = True
font = pygame.font.Font(None, 72)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Press ESC to exit fullscreen
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and all_stopped():
            mouse_x, mouse_y = event.pos
            
            # Select disc to shoot
            current_discs = player1_discs if current_player == 1 else player2_discs
            for disc in current_discs:
                dx = mouse_x - disc.x
                dy = mouse_y - disc.y
                if math.sqrt(dx*dx + dy*dy) <= disc.radius:
                    selected_disc = disc
                    aiming = True
                    aim_start = (mouse_x, mouse_y)
                    break
                    
        if event.type == pygame.MOUSEBUTTONUP and aiming:
            mouse_x, mouse_y = event.pos
            
            # Calculate shot power and direction
            dx = aim_start[0] - mouse_x
            dy = aim_start[1] - mouse_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            power = min(distance / 10, MAX_POWER)
            
            if distance > 5:
                selected_disc.vx = (dx / distance) * power
                selected_disc.vy = (dy / distance) * power
            
            aiming = False
            selected_disc = None
            aim_start = None
    
    # Update physics
    goal_scored = None
    for disc in all_discs:
        result = disc.update()
        if result:
            goal_scored = result
    
    # Check collisions between all discs
    for i in range(len(all_discs)):
        for j in range(i + 1, len(all_discs)):
            if check_collision(all_discs[i], all_discs[j]):
                resolve_collision(all_discs[i], all_discs[j])
    
    # Handle goals
    if goal_scored:
        if goal_scored == "player1_scores":
            score_p1 += 1
        elif goal_scored == "player2_scores":
            score_p2 += 1
        reset_positions()
    
    # Switch turns
    if all_stopped() and not aiming and selected_disc is None:
        if current_player == 1:
            current_player = 2
        else:
            current_player = 1
    
    # Draw everything
    screen.fill(GREEN)
    
    # Draw goals
    goal_width = 300
    pygame.draw.rect(screen, DARK_GREEN, (WIDTH // 2 - goal_width // 2, 0, goal_width, 15))
    pygame.draw.rect(screen, DARK_GREEN, (WIDTH // 2 - goal_width // 2, HEIGHT - 15, goal_width, 15))
    
    # Draw goal posts
    pygame.draw.rect(screen, WHITE, (WIDTH // 2 - goal_width // 2, 0, 10, 60))
    pygame.draw.rect(screen, WHITE, (WIDTH // 2 + goal_width // 2 - 10, 0, 10, 60))
    pygame.draw.rect(screen, WHITE, (WIDTH // 2 - goal_width // 2, HEIGHT - 60, 10, 60))
    pygame.draw.rect(screen, WHITE, (WIDTH // 2 + goal_width // 2 - 10, HEIGHT - 60, 10, 60))
    
    # Draw center line
    pygame.draw.line(screen, WHITE, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 3)
    pygame.draw.circle(screen, WHITE, (WIDTH // 2, HEIGHT // 2), 80, 3)
    
    # Draw discs
    for disc in all_discs:
        disc.draw(screen)
    
    # Draw aiming line
    if aiming and aim_start:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.line(screen, WHITE, (selected_disc.x, selected_disc.y), (mouse_x, mouse_y), 3)
        
        # Draw power indicator
        dx = aim_start[0] - mouse_x
        dy = aim_start[1] - mouse_y
        distance = math.sqrt(dx*dx + dy*dy)
        power_display = min(distance / 10, MAX_POWER)
        
        end_x = selected_disc.x - (dx / distance) * power_display * 5 if distance > 0 else selected_disc.x
        end_y = selected_disc.y - (dy / distance) * power_display * 5 if distance > 0 else selected_disc.y
        pygame.draw.line(screen, RED, (selected_disc.x, selected_disc.y), (end_x, end_y), 6)
    
    # Draw scores and turn indicator
    score_text = font.render(f"P1: {score_p1}  P2: {score_p2}", True, WHITE)
    screen.blit(score_text, (20, 20))
    
    turn_text = font.render(f"Player {current_player}'s Turn", True, BLUE if current_player == 1 else RED)
    screen.blit(turn_text, (WIDTH - 450, 20))
    
    # Exit instruction
    exit_text = pygame.font.Font(None, 36).render("Press ESC to exit", True, WHITE)
    screen.blit(exit_text, (WIDTH // 2 - 100, HEIGHT - 40))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
