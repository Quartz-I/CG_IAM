import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame (use display.init() to avoid lag)
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((1280, 720), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Minecraft PvP Split Screen")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Map dimensions
MAP_SIZE = 60
SPAWN_DISTANCE = 25

# Player 1 variables (spawns at one end)
player1_pos = [-SPAWN_DISTANCE, 0, 0]
player1_rotation = 0
player1_health = 100
player1_score = 0
player1_alive = True

# Player 2 variables (spawns at opposite end)
player2_pos = [SPAWN_DISTANCE, 0, 0]
player2_rotation = 180
player2_health = 100
player2_score = 0
player2_alive = True

# Camera settings
camera_distance = 10
camera_height = 3

# Movement
move_speed = 0.1

# Bullets
bullets = []

# Animation
walk_animation = 0

# Display list IDs for optimization (prevents lag)
ground_display_list = None
cube_display_list = None

class Bullet:
    def __init__(self, pos, rotation, owner):
        self.pos = list(pos)
        self.rotation = rotation
        self.speed = 0.5
        self.lifetime = 300
        self.radius = 0.3
        self.owner = owner
        
    def update(self):
        self.pos[0] += math.sin(math.radians(self.rotation)) * self.speed
        self.pos[2] += math.cos(math.radians(self.rotation)) * self.speed
        self.lifetime -= 1
        
    def is_alive(self):
        return self.lifetime > 0
    
    def check_hit_player(self, player_pos, player_size=1.0):
        """Check if bullet hits a player"""
        dx = self.pos[0] - player_pos[0]
        dy = self.pos[1] - player_pos[1] - 1
        dz = self.pos[2] - player_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < (self.radius + player_size)

def setup_lighting():
    """Setup OpenGL lighting"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 50, 0, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.9, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

def create_cube_display_list():
    """Pre-compile cube geometry to prevent lag"""
    global cube_display_list
    cube_display_list = glGenLists(1)
    glNewList(cube_display_list, GL_COMPILE)
    
    s = 0.5
    vertices = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]
    ]
    
    faces = [
        ([0, 1, 2, 3], (0, 0, -1)),
        ([4, 5, 6, 7], (0, 0, 1)),
        ([0, 1, 5, 4], (0, -1, 0)),
        ([2, 3, 7, 6], (0, 1, 0)),
        ([0, 3, 7, 4], (-1, 0, 0)),
        ([1, 2, 6, 5], (1, 0, 0))
    ]
    
    for face, normal in faces:
        glBegin(GL_QUADS)
        glNormal3fv(normal)
        for vertex_idx in face:
            glVertex3fv(vertices[vertex_idx])
        glEnd()
    
    glEndList()

def draw_minecraft_cube(x, y, z, width, height, depth, color):
    """Draw cube using display list (faster)"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width, height, depth)
    glColor3f(*color)
    glCallList(cube_display_list)
    glPopMatrix()

def draw_minecraft_player(pos, rotation, color, is_moving=False, is_alive=True):
    """Draw Minecraft-style player"""
    if not is_alive:
        return
    
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation, 0, 1, 0)
    
    # Animation
    arm_swing = math.sin(walk_animation) * 30 if is_moving else 0
    leg_swing = math.sin(walk_animation) * 30 if is_moving else 0
    
    # HEAD
    head_color = (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)
    draw_minecraft_cube(0, 1.9, 0, 0.5, 0.5, 0.5, head_color)
    
    # Eyes
    glDisable(GL_LIGHTING)
    draw_minecraft_cube(-0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    draw_minecraft_cube(0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    glEnable(GL_LIGHTING)
    
    # BODY
    draw_minecraft_cube(0, 1.25, 0, 0.5, 0.75, 0.25, color)
    
    # RIGHT ARM
    glPushMatrix()
    glTranslatef(-0.375, 1.5, 0)
    glRotatef(arm_swing, 1, 0, 0)
    glTranslatef(0, -0.25, 0)
    draw_minecraft_cube(0, -0.125, 0, 0.25, 0.75, 0.25, color)
    glPopMatrix()
    
    # LEFT ARM
    glPushMatrix()
    glTranslatef(0.375, 1.5, 0)
    glRotatef(-arm_swing, 1, 0, 0)
    glTranslatef(0, -0.25, 0)
    draw_minecraft_cube(0, -0.125, 0, 0.25, 0.75, 0.25, color)
    glPopMatrix()
    
    # RIGHT LEG
    glPushMatrix()
    glTranslatef(-0.125, 0.875, 0)
    glRotatef(-leg_swing, 1, 0, 0)
    glTranslatef(0, -0.375, 0)
    leg_color = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6)
    draw_minecraft_cube(0, 0, 0, 0.25, 0.75, 0.25, leg_color)
    glPopMatrix()
    
    # LEFT LEG
    glPushMatrix()
    glTranslatef(0.125, 0.875, 0)
    glRotatef(leg_swing, 1, 0, 0)
    glTranslatef(0, -0.375, 0)
    draw_minecraft_cube(0, 0, 0, 0.25, 0.75, 0.25, leg_color)
    glPopMatrix()
    
    glPopMatrix()

def create_ground_display_list():
    """Pre-compile ground to prevent lag"""
    global ground_display_list
    ground_display_list = glGenLists(1)
    glNewList(ground_display_list, GL_COMPILE)
    
    # Main ground
    glColor3f(0.4, 0.7, 0.3)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glEnd()
    
    # Map borders (walls)
    wall_color = (0.5, 0.3, 0.2)
    wall_height = 5
    
    # North wall
    glColor3f(*wall_color)
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, -MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
    # South wall
    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, MAP_SIZE)
    glEnd()
    
    # West wall
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
    # East wall
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
    # Grid lines
    glDisable(GL_LIGHTING)
    glColor3f(0.3, 0.6, 0.2)
    glBegin(GL_LINES)
    for i in range(-MAP_SIZE, MAP_SIZE + 1, 5):
        glVertex3f(i, 0.01, -MAP_SIZE)
        glVertex3f(i, 0.01, MAP_SIZE)
        glVertex3f(-MAP_SIZE, 0.01, i)
        glVertex3f(MAP_SIZE, 0.01, i)
    glEnd()
    glEnable(GL_LIGHTING)
    
    glEndList()

def draw_ground():
    """Draw ground using display list"""
    glCallList(ground_display_list)

def draw_bullet(bullet):
    """Draw bullet"""
    color = (1, 1, 0) if bullet.owner == 1 else (0, 1, 1)
    draw_minecraft_cube(bullet.pos[0], bullet.pos[1] + 1, bullet.pos[2], 0.2, 0.2, 0.2, color)

def set_camera(player_pos, player_rotation):
    """Set camera behind player"""
    cam_x = player_pos[0] - math.sin(math.radians(player_rotation)) * camera_distance
    cam_y = player_pos[1] + camera_height
    cam_z = player_pos[2] - math.cos(math.radians(player_rotation)) * camera_distance
    
    gluLookAt(
        cam_x, cam_y, cam_z,
        player_pos[0], player_pos[1] + 1.5, player_pos[2],
        0, 1, 0
    )

def draw_scene(player1_moving, player2_moving):
    """Draw the entire game scene"""
    draw_ground()
    
    # Draw both players
    draw_minecraft_player(player1_pos, player1_rotation, (0.3, 0.5, 0.9), player1_moving, player1_alive)
    draw_minecraft_player(player2_pos, player2_rotation, (0.9, 0.3, 0.3), player2_moving, player2_alive)
    
    # Draw bullets
    for bullet in bullets:
        draw_bullet(bullet)

def handle_player1_movement(keys, dt):
    """Handle Player 1 movement"""
    global player1_pos, player1_rotation
    if not player1_alive:
        return False
    
    speed = move_speed * dt
    is_moving = False
    
    if keys[K_q]:
        player1_rotation += 2
    if keys[K_e]:
        player1_rotation -= 2
    
    if keys[K_w]:
        player1_pos[0] += math.sin(math.radians(player1_rotation)) * speed
        player1_pos[2] += math.cos(math.radians(player1_rotation)) * speed
        is_moving = True
    if keys[K_s]:
        player1_pos[0] -= math.sin(math.radians(player1_rotation)) * speed
        player1_pos[2] -= math.cos(math.radians(player1_rotation)) * speed
        is_moving = True
    if keys[K_d]:
        player1_pos[0] += math.sin(math.radians(player1_rotation - 90)) * speed
        player1_pos[2] += math.cos(math.radians(player1_rotation - 90)) * speed
        is_moving = True
    if keys[K_a]:
        player1_pos[0] += math.sin(math.radians(player1_rotation + 90)) * speed
        player1_pos[2] += math.cos(math.radians(player1_rotation + 90)) * speed
        is_moving = True
    
    # Keep player in bounds
    player1_pos[0] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, player1_pos[0]))
    player1_pos[2] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, player1_pos[2]))
    
    return is_moving

def handle_player2_movement(keys, dt):
    """Handle Player 2 movement"""
    global player2_pos, player2_rotation
    if not player2_alive:
        return False
    
    speed = move_speed * dt
    is_moving = False
    
    if keys[K_u]:
        player2_rotation += 2
    if keys[K_o]:
        player2_rotation -= 2
    
# Movement
    if keys[K_i]:
        player2_pos[0] += math.sin(math.radians(player2_rotation)) * speed
        player2_pos[2] += math.cos(math.radians(player2_rotation)) * speed
    if keys[K_k]:
        player2_pos[0] -= math.sin(math.radians(player2_rotation)) * speed
        player2_pos[2] -= math.cos(math.radians(player2_rotation)) * speed
    if keys[K_l]:
        player2_pos[0] += math.sin(math.radians(player2_rotation - 90)) * speed
        player2_pos[2] += math.cos(math.radians(player2_rotation - 90)) * speed
    if keys[K_j]:
        player2_pos[0] += math.sin(math.radians(player2_rotation + 90)) * speed
        player2_pos[2] += math.cos(math.radians(player2_rotation + 90)) * speed
        is_moving = True
    
    # Keep player in bounds
    player2_pos[0] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, player2_pos[0]))
    player2_pos[2] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, player2_pos[2]))
    
    return is_moving

def shoot_player1():
    """Player 1 shoots"""
    if player1_alive:
        bullet = Bullet([player1_pos[0], player1_pos[1] + 1, player1_pos[2]], player1_rotation, 1)
        bullets.append(bullet)

def shoot_player2():
    """Player 2 shoots"""
    if player2_alive:
        bullet = Bullet([player2_pos[0], player2_pos[1] + 1, player2_pos[2]], player2_rotation, 2)
        bullets.append(bullet)

def respawn_player(player_num):
    """Respawn player at their spawn point"""
    global player1_pos, player1_health, player1_alive, player2_pos, player2_health, player2_alive
    
    if player_num == 1:
        player1_pos = [-SPAWN_DISTANCE, 0, 0]
        player1_rotation = 0
        player1_health = 100
        player1_alive = True
    else:
        player2_pos = [SPAWN_DISTANCE, 0, 0]
        player2_rotation = 180
        player2_health = 100
        player2_alive = True

def draw_split_screen_hud():
    """Draw HUD with scoreboard"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1280, 0, 720, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # SCOREBOARD (Left side)
    # Background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(10, 720 - 150)
    glVertex2f(160, 720 - 150)
    glVertex2f(160, 720 - 10)
    glVertex2f(10, 720 - 10)
    glEnd()
    
    # Border
    glColor3f(1, 1, 1)
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glVertex2f(10, 720 - 150)
    glVertex2f(160, 720 - 150)
    glVertex2f(160, 720 - 10)
    glVertex2f(10, 720 - 10)
    glEnd()
    
    # Player 1 score indicator
    glColor3f(0.3, 0.5, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(20, 720 - 40)
    glVertex2f(40, 720 - 40)
    glVertex2f(40, 720 - 20)
    glVertex2f(20, 720 - 20)
    glEnd()
    
    # Player 1 score bars
    for i in range(player1_score):
        glColor3f(0.3, 0.5, 0.9)
        glBegin(GL_QUADS)
        y_offset = 60 + i * 15
        glVertex2f(50, 720 - y_offset)
        glVertex2f(150, 720 - y_offset)
        glVertex2f(150, 720 - y_offset + 10)
        glVertex2f(50, 720 - y_offset + 10)
        glEnd()
    
    # Player 2 score indicator
    glColor3f(0.9, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(20, 720 - 130)
    glVertex2f(40, 720 - 130)
    glVertex2f(40, 720 - 110)
    glVertex2f(20, 720 - 110)
    glEnd()
    
    # Player 2 score bars
    for i in range(player2_score):
        glColor3f(0.9, 0.3, 0.3)
        glBegin(GL_QUADS)
        y_offset = 150 + i * 15
        if y_offset < 250:  # Don't overflow
            glVertex2f(50, 720 - y_offset)
            glVertex2f(150, 720 - y_offset)
            glVertex2f(150, 720 - y_offset + 10)
            glVertex2f(50, 720 - y_offset + 10)
            glEnd()
    
    # Player 1 health bar (top right)
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(1280 - 210, 720 - 30)
    glVertex2f(1280 - 10, 720 - 30)
    glVertex2f(1280 - 10, 720 - 10)
    glVertex2f(1280 - 210, 720 - 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player1_health / 100.0) * 200
    glBegin(GL_QUADS)
    glVertex2f(1280 - 210, 720 - 30)
    glVertex2f(1280 - 210 + health_width, 720 - 30)
    glVertex2f(1280 - 210 + health_width, 720 - 10)
    glVertex2f(1280 - 210, 720 - 10)
    glEnd()
    
    # Player 2 health bar (bottom right)
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(1280 - 210, 30)
    glVertex2f(1280 - 10, 30)
    glVertex2f(1280 - 10, 10)
    glVertex2f(1280 - 210, 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player2_health / 100.0) * 200
    glBegin(GL_QUADS)
    glVertex2f(1280 - 210, 30)
    glVertex2f(1280 - 210 + health_width, 30)
    glVertex2f(1280 - 210 + health_width, 10)
    glVertex2f(1280 - 210, 10)
    glEnd()
    
    # Divider line
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(0, 360)
    glVertex2f(1280, 360)
    glEnd()
    
    # Crosshairs
    glLineWidth(3)
    # Player 1 crosshair
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    glVertex2f(640 - 15, 540)
    glVertex2f(640 + 15, 540)
    glVertex2f(640, 540 - 15)
    glVertex2f(640, 540 + 15)
    glEnd()
    
    # Player 2 crosshair
    glBegin(GL_LINES)
    glVertex2f(640 - 15, 180)
    glVertex2f(640 + 15, 180)
    glVertex2f(640, 180 - 15)
    glVertex2f(640, 180 + 15)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# Initialize OpenGL
glEnable(GL_DEPTH_TEST)
setup_lighting()

# Create display lists BEFORE main loop (prevents lag)
create_cube_display_list()
create_ground_display_list()

# Main loop
running = True
last_time = pygame.time.get_ticks()
respawn_delay = 0

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 10.0
    last_time = current_time
    
    walk_animation += 0.1
    
    # Events
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                shoot_player1()
            if event.key == K_SEMICOLON:
                shoot_player2()
    
    # Input
    keys = pygame.key.get_pressed()
    player1_moving = handle_player1_movement(keys, dt)
    player2_moving = handle_player2_movement(keys, dt)
    
    # Update bullets
    bullets = [b for b in bullets if b.is_alive()]
    for bullet in bullets:
        bullet.update()
    
    # Check bullet collisions with players
    for bullet in bullets[:]:
        # Check if player 1 is hit by player 2's bullet
        if bullet.owner == 2 and player1_alive:
            if bullet.check_hit_player(player1_pos):
                player1_health -= 34
                if bullet in bullets:
                    bullets.remove(bullet)
                if player1_health <= 0:
                    player1_alive = False
                    player2_score += 1
                    respawn_delay = 180  # 3 seconds at 60fps
                    
        # Check if player 2 is hit by player 1's bullet
        if bullet.owner == 1 and player2_alive:
            if bullet.check_hit_player(player2_pos):
                player2_health -= 34
                if bullet in bullets:
                    bullets.remove(bullet)
                if player2_health <= 0:
                    player2_alive = False
                    player1_score += 1
                    respawn_delay = 180
    
    # Handle respawn
    if respawn_delay > 0:
        respawn_delay -= 1
        if respawn_delay == 0:
            if not player1_alive:
                respawn_player(1)
            if not player2_alive:
                respawn_player(2)
    
    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # PLAYER 1 VIEW (Top Half)
    glViewport(0, 360, 1280, 360)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (1280/360), 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player1_pos, player1_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # PLAYER 2 VIEW (Bottom Half)
    glViewport(0, 0, 1280, 360)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (1280/360), 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player2_pos, player2_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # Draw HUD
    glViewport(0, 0, 1280, 720)
    draw_split_screen_hud()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
