import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Third Person Shooter - Minecraft Style")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Player 1 variables
player1_pos = [0, 0, -10]
player1_rotation = 0
player1_health = 100

# Player 2 variables
player2_pos = [0, 0, 10]
player2_rotation = 180
player2_health = 100

# Camera settings
camera_distance = 10
camera_height = 3

# Movement
move_speed = 0.1

# Bullets and Enemies
bullets = []
enemies = []

# Animation variables
walk_animation = 0

class Bullet:
    def __init__(self, pos, rotation, owner):
        self.pos = list(pos)
        self.rotation = rotation
        self.speed = 0.5
        self.lifetime = 300
        self.radius = 0.2
        self.owner = owner
        
    def update(self):
        self.pos[0] += math.sin(math.radians(self.rotation)) * self.speed
        self.pos[2] += math.cos(math.radians(self.rotation)) * self.speed
        self.lifetime -= 1
        
    def is_alive(self):
        return self.lifetime > 0
    
    def get_bbox(self):
        return {
            'x': self.pos[0],
            'y': self.pos[1],
            'z': self.pos[2],
            'radius': self.radius
        }

class Enemy:
    def __init__(self, x, z):
        self.pos = [x, 1, z]
        self.health = 100
        self.size = 1
        self.alive = True
        
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            
    def get_bbox(self):
        return {
            'x': self.pos[0],
            'y': self.pos[1],
            'z': self.pos[2],
            'size': self.size
        }

def check_collision_sphere_box(bullet_bbox, enemy_bbox):
    """Check collision between bullet (sphere) and enemy (box)"""
    dx = bullet_bbox['x'] - enemy_bbox['x']
    dy = bullet_bbox['y'] - enemy_bbox['y']
    dz = bullet_bbox['z'] - enemy_bbox['z']
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    return distance < (bullet_bbox['radius'] + enemy_bbox['size'])

def setup_lighting():
    """Setup OpenGL lighting"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 20, 0, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

def draw_minecraft_cube(x, y, z, width, height, depth, color):
    """Draw a Minecraft-style cube (block)"""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    
    w, h, d = width/2, height/2, depth/2
    
    # Define vertices
    vertices = [
        [-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d],  # Back
        [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]        # Front
    ]
    
    faces = [
        ([0, 1, 2, 3], (0, 0, -1)),  # Back
        ([4, 5, 6, 7], (0, 0, 1)),   # Front
        ([0, 1, 5, 4], (0, -1, 0)),  # Bottom
        ([2, 3, 7, 6], (0, 1, 0)),   # Top
        ([0, 3, 7, 4], (-1, 0, 0)),  # Left
        ([1, 2, 6, 5], (1, 0, 0))    # Right
    ]
    
    for face, normal in faces:
        glBegin(GL_QUADS)
        glNormal3fv(normal)
        for vertex_idx in face:
            glVertex3fv(vertices[vertex_idx])
        glEnd()
        
        # Draw black outline (Minecraft style)
        glDisable(GL_LIGHTING)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for vertex_idx in face:
            glVertex3fv(vertices[vertex_idx])
        glEnd()
        glEnable(GL_LIGHTING)
        glColor3f(*color)
    
    glPopMatrix()

def draw_minecraft_player(pos, rotation, color, is_moving=False):
    """Draw a Minecraft-style player with head, body, arms, and legs"""
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation, 0, 1, 0)
    
    # Calculate arm/leg swing for walking animation
    arm_swing = math.sin(walk_animation) * 30 if is_moving else 0
    leg_swing = math.sin(walk_animation) * 30 if is_moving else 0
    
    # HEAD (8x8x8 pixels in Minecraft = 0.5x0.5x0.5 units)
    head_color = (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)
    draw_minecraft_cube(0, 1.9, 0, 0.5, 0.5, 0.5, head_color)
    
    # Eyes (simple black cubes)
    glDisable(GL_LIGHTING)
    draw_minecraft_cube(-0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    draw_minecraft_cube(0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    glEnable(GL_LIGHTING)
    
    # BODY (8x12x4 pixels = 0.5x0.75x0.25 units)
    draw_minecraft_cube(0, 1.25, 0, 0.5, 0.75, 0.25, color)
    
    # RIGHT ARM (4x12x4 pixels = 0.25x0.75x0.25 units)
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
    
    # RIGHT LEG (4x12x4 pixels = 0.25x0.75x0.25 units)
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

def draw_ground():
    """Draw ground with Minecraft-style grass blocks"""
    # Main ground (grass color)
    glColor3f(0.4, 0.7, 0.3)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-100, 0, -100)
    glVertex3f(100, 0, -100)
    glVertex3f(100, 0, 100)
    glVertex3f(-100, 0, 100)
    glEnd()
    
    # Draw some grass blocks as decoration
    glDisable(GL_LIGHTING)
    for x in range(-50, 51, 10):
        for z in range(-50, 51, 10):
            if (x + z) % 20 == 0:
                glColor3f(0.3, 0.6, 0.2)
                glBegin(GL_LINE_LOOP)
                glVertex3f(x - 0.5, 0.01, z - 0.5)
                glVertex3f(x + 0.5, 0.01, z - 0.5)
                glVertex3f(x + 0.5, 0.01, z + 0.5)
                glVertex3f(x - 0.5, 0.01, z + 0.5)
                glEnd()
    glEnable(GL_LIGHTING)

def draw_bullet(bullet):
    """Draw bullet as small glowing cube"""
    color = (1, 1, 0) if bullet.owner == 1 else (0, 1, 1)
    draw_minecraft_cube(bullet.pos[0], bullet.pos[1] + 1, bullet.pos[2], 0.2, 0.2, 0.2, color)

def draw_enemy(enemy):
    """Draw enemy as Minecraft zombie/hostile mob"""
    if not enemy.alive:
        return
    
    # Enemy body (darker/hostile colors)
    health_ratio = enemy.health / 100.0
    color = (0.3, 0.6 * health_ratio, 0.3)
    
    glPushMatrix()
    glTranslatef(enemy.pos[0], enemy.pos[1] - 0.5, enemy.pos[2])
    
    # Head
    draw_minecraft_cube(0, 1.4, 0, 0.5, 0.5, 0.5, (0.4, 0.8 * health_ratio, 0.4))
    
    # Body
    draw_minecraft_cube(0, 0.75, 0, 0.5, 0.75, 0.25, color)
    
    # Arms
    draw_minecraft_cube(-0.375, 0.75, 0, 0.25, 0.75, 0.25, color)
    draw_minecraft_cube(0.375, 0.75, 0, 0.25, 0.75, 0.25, color)
    
    # Legs
    draw_minecraft_cube(-0.125, 0.25, 0, 0.25, 0.5, 0.25, (0.2, 0.4 * health_ratio, 0.2))
    draw_minecraft_cube(0.125, 0.25, 0, 0.25, 0.5, 0.25, (0.2, 0.4 * health_ratio, 0.2))
    
    glPopMatrix()
    
    # Health bar above enemy
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(enemy.pos[0], enemy.pos[1] + 1.5, enemy.pos[2])
    
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(0.5, 0, 0)
    glVertex3f(0.5, 0.1, 0)
    glVertex3f(-0.5, 0.1, 0)
    glEnd()
    
    glColor3f(0, 1, 0)
    glBegin(GL_QUADS)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(-0.5 + health_ratio, 0, 0)
    glVertex3f(-0.5 + health_ratio, 0.1, 0)
    glVertex3f(-0.5, 0.1, 0)
    glEnd()
    
    glPopMatrix()
    glEnable(GL_LIGHTING)

def set_camera(player_pos, player_rotation):
    """Set camera behind a specific player"""
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
    
    # Draw both Minecraft-style players
    draw_minecraft_player(player1_pos, player1_rotation, (0.3, 0.5, 0.9), player1_moving)
    draw_minecraft_player(player2_pos, player2_rotation, (0.9, 0.3, 0.3), player2_moving)
    
    # Draw bullets
    for bullet in bullets:
        draw_bullet(bullet)
    
    # Draw enemies
    for enemy in enemies:
        draw_enemy(enemy)

def handle_player1_movement(keys, dt):
    """Handle Player 1 movement (WASD)"""
    global player1_pos, player1_rotation
    speed = move_speed * dt
    is_moving = False
    
    # Rotation
    if keys[K_q]:
        player1_rotation += 2
    if keys[K_e]:
        player1_rotation -= 2
    
    # Movement
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
    
    return is_moving

def handle_player2_movement(keys, dt):
    """Handle Player 2 movement (Arrow keys)"""
    global player2_pos, player2_rotation
    speed = move_speed * dt
    is_moving = False
    
    # Rotation
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
    
    return is_moving

def shoot_player1():
    """Player 1 shoots"""
    bullet = Bullet([player1_pos[0], player1_pos[1], player1_pos[2]], player1_rotation, 1)
    bullets.append(bullet)

def shoot_player2():
    """Player 2 shoots"""
    bullet = Bullet([player2_pos[0], player2_pos[1], player2_pos[2]], player2_rotation, 2)
    bullets.append(bullet)

def spawn_enemies():
    """Spawn enemies around the map"""
    for i in range(8):
        angle = i * 45
        x = math.sin(math.radians(angle)) * 20
        z = math.cos(math.radians(angle)) * 20
        enemies.append(Enemy(x, z))

def draw_split_screen_hud():
    """Draw HUD for split screen"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1280, 0, 720, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Player 1 health bar (top screen)
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(10, 720 - 30)
    glVertex2f(210, 720 - 30)
    glVertex2f(210, 720 - 10)
    glVertex2f(10, 720 - 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player1_health / 100.0) * 200
    glBegin(GL_QUADS)
    glVertex2f(10, 720 - 30)
    glVertex2f(10 + health_width, 720 - 30)
    glVertex2f(10 + health_width, 720 - 10)
    glVertex2f(10, 720 - 10)
    glEnd()
    
    # Player 2 health bar (bottom screen)
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(10, 30)
    glVertex2f(210, 30)
    glVertex2f(210, 10)
    glVertex2f(10, 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player2_health / 100.0) * 200
    glBegin(GL_QUADS)
    glVertex2f(10, 30)
    glVertex2f(10 + health_width, 30)
    glVertex2f(10 + health_width, 10)
    glVertex2f(10, 10)
    glEnd()
    
    # Divider line
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(0, 360)
    glVertex2f(1280, 360)
    glEnd()
    
    # Crosshairs (Minecraft style - simple +)
    glLineWidth(3)
    # Player 1 crosshair (top)
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    glVertex2f(640 - 15, 540)
    glVertex2f(640 + 15, 540)
    glVertex2f(640, 540 - 15)
    glVertex2f(640, 540 + 15)
    glEnd()
    
    # Player 2 crosshair (bottom)
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

# Initialize
glEnable(GL_DEPTH_TEST)
setup_lighting()
spawn_enemies()

# Main loop
running = True
last_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 10.0
    last_time = current_time
    
    # Update walk animation
    walk_animation += 0.2
    
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
    
    # Collision detection
    for bullet in bullets[:]:
        for enemy in enemies:
            if enemy.alive and check_collision_sphere_box(bullet.get_bbox(), enemy.get_bbox()):
                enemy.take_damage(34)
                if bullet in bullets:
                    bullets.remove(bullet)
                break
    
    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # ===== PLAYER 1 VIEW (Top Half) =====
    glViewport(0, 360, 1280, 360)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, (1280/360), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player1_pos, player1_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # ===== PLAYER 2 VIEW (Bottom Half) =====
    glViewport(0, 0, 1280, 360)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, (1280/360), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player2_pos, player2_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # Draw HUD (full screen)
    glViewport(0, 0, 1280, 720)
    draw_split_screen_hud()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
