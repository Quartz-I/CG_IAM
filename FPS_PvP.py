import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame
pygame.display.init()
pygame.font.init()
pygame.joystick.init()
screen = pygame.display.set_mode((1920, 1080), DOUBLEBUF | OPENGL)
pygame.display.set_caption("PvP Split Screen - 1080p")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Font for score numbers
score_font = pygame.font.Font(None, 120)

# Map dimensions
MAP_SIZE = 60
SPAWN_DISTANCE = 25

# Player 1 variables
player1_pos = [-SPAWN_DISTANCE, 0, 0]
player1_rotation = 0
player1_health = 100
player1_score = 0
player1_alive = True

# Player 2 variables
player2_pos = [SPAWN_DISTANCE, 0, 0]
player2_rotation = 180
player2_health = 100
player2_score = 0
player2_alive = True

# Portal cooldowns
portal_cooldown1 = 0
portal_cooldown2 = 0

# Camera settings
camera_distance = 10
camera_height = 3

# Movement
move_speed = 0.1

# Bullets
bullets = []

# Obstacles list
obstacles = []

# Portals list - each portal has position and destination
portals = []

# Animation
walk_animation = 0
portal_animation = 0

# Display lists
ground_display_list = None
cube_display_list = None

# Controllers
controllers = []
controller1_last_shoot = False
controller2_last_shoot = False

class Portal:
    def __init__(self, x, z, dest_x, dest_z, color=(0.5, 0, 1)):
        self.x = x
        self.y = 2.5
        self.z = z
        self.dest_x = dest_x
        self.dest_z = dest_z
        self.color = color
        self.radius = 1.5
        self.height = 5
    
    def check_teleport(self, player_pos):
        """Check if player is in portal"""
        dx = player_pos[0] - self.x
        dz = player_pos[2] - self.z
        distance = math.sqrt(dx*dx + dz*dz)
        return distance < self.radius

def add_portal_pair(x1, z1, x2, z2):
    """Add two linked portals (bidirectional teleport)"""
    portals.append(Portal(x1, z1, x2, z2, (0.5, 0, 1)))
    portals.append(Portal(x2, z2, x1, z1, (1, 0.5, 0)))

def init_controllers():
    global controllers
    controllers.clear()
    
    count = pygame.joystick.get_count()
    print(f"\n=== Controllers detected: {count} ===")
    
    for i in range(count):
        controller = pygame.joystick.Joystick(i)
        controller.init()
        controllers.append(controller)
        print(f"Controller {i}: {controller.get_name()}")
        print(f"  Axes: {controller.get_numaxes()}")
        print(f"  Buttons: {controller.get_numbuttons()}")
    
    return count

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
        dx = self.pos[0] - player_pos[0]
        dy = self.pos[1] - player_pos[1] - 1
        dz = self.pos[2] - player_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < (self.radius + player_size)
    
    def check_hit_obstacle(self, obstacle):
        dx = self.pos[0] - obstacle['x']
        dy = self.pos[1] - obstacle['y']
        dz = self.pos[2] - obstacle['z']
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < (self.radius + obstacle['size'])

class Obstacle:
    def __init__(self, x, y, z, width, height, depth, color):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
        self.color = color
        self.size = max(width, height, depth) / 2
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'color': self.color,
            'size': self.size
        }

def add_obstacle(x, y, z, width, height, depth, color):
    obstacles.append(Obstacle(x, y, z, width, height, depth, color))

def add_wall(x1, z1, x2, z2, height=3, thickness=1):
    center_x = (x1 + x2) / 2
    center_z = (z1 + z2) / 2
    length = math.sqrt((x2-x1)**2 + (z2-z1)**2)
    
    if abs(x2 - x1) > abs(z2 - z1):
        add_obstacle(center_x, height/2, center_z, length, height, thickness, (0.5, 0.3, 0.2))
    else:
        add_obstacle(center_x, height/2, center_z, thickness, height, length, (0.5, 0.3, 0.2))

def add_box_obstacle(x, z, size=3):
    add_obstacle(x, size/2, z, size, size, size, (0.6, 0.4, 0.2))

def add_pillar(x, z, height=5, radius=1.5):
    add_obstacle(x, height/2, z, radius*2, height, radius*2, (0.4, 0.4, 0.4))

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 50, 0, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.9, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

def create_cube_display_list():
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
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width, height, depth)
    glColor3f(*color)
    glCallList(cube_display_list)
    glPopMatrix()

def draw_portal(portal):
    """Draw a spinning sphere portal"""
    glPushMatrix()
    glTranslatef(portal.x, portal.y, portal.z)
    
    # Spinning animation
    glRotatef(portal_animation * 2, 0, 1, 0)
    glRotatef(portal_animation, 1, 0, 0)
    
    # Draw sphere with lighting
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Outer glow sphere (transparent)
    pulse = 0.5 + 0.3 * math.sin(portal_animation * 0.1)
    glColor4f(portal.color[0], portal.color[1], portal.color[2], 0.3 * pulse)
    
    radius = portal.radius
    slices = 20
    stacks = 20
    
    # Draw outer transparent sphere
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glNormal3f(x * zr0, y * zr0, z0)
            glVertex3f(x * zr0 * radius * 1.2, y * zr0 * radius * 1.2, z0 * radius * 1.2)
            
            glNormal3f(x * zr1, y * zr1, z1)
            glVertex3f(x * zr1 * radius * 1.2, y * zr1 * radius * 1.2, z1 * radius * 1.2)
        glEnd()
    
    # Inner solid sphere
    glColor4f(portal.color[0] * 0.8, portal.color[1] * 0.8, portal.color[2] * 0.8, 0.8)
    
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glNormal3f(x * zr0, y * zr0, z0)
            glVertex3f(x * zr0 * radius, y * zr0 * radius, z0 * radius)
            
            glNormal3f(x * zr1, y * zr1, z1)
            glVertex3f(x * zr1 * radius, y * zr1 * radius, z1 * radius)
        glEnd()
    
    # Bright core
    glDisable(GL_LIGHTING)
    glColor4f(1, 1, 1, 0.9)
    core_radius = radius * 0.3
    
    for i in range(stacks // 2):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glVertex3f(x * zr0 * core_radius, y * zr0 * core_radius, z0 * core_radius)
            glVertex3f(x * zr1 * core_radius, y * zr1 * core_radius, z1 * core_radius)
        glEnd()
    
    glEnable(GL_LIGHTING)
    glDisable(GL_BLEND)
    
    glPopMatrix()

def draw_minecraft_player(pos, rotation, color, is_moving=False, is_alive=True):
    if not is_alive:
        return
    
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation, 0, 1, 0)
    
    arm_swing = math.sin(walk_animation) * 30 if is_moving else 0
    leg_swing = math.sin(walk_animation) * 30 if is_moving else 0
    
    head_color = (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)
    draw_minecraft_cube(0, 1.9, 0, 0.5, 0.5, 0.5, head_color)
    
    glDisable(GL_LIGHTING)
    draw_minecraft_cube(-0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    draw_minecraft_cube(0.12, 1.95, -0.26, 0.08, 0.08, 0.02, (0, 0, 0))
    glEnable(GL_LIGHTING)
    
    draw_minecraft_cube(0, 1.25, 0, 0.5, 0.75, 0.25, color)
    
    glPushMatrix()
    glTranslatef(-0.375, 1.5, 0)
    glRotatef(arm_swing, 1, 0, 0)
    glTranslatef(0, -0.25, 0)
    draw_minecraft_cube(0, -0.125, 0, 0.25, 0.75, 0.25, color)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0.375, 1.5, 0)
    glRotatef(-arm_swing, 1, 0, 0)
    glTranslatef(0, -0.25, 0)
    draw_minecraft_cube(0, -0.125, 0, 0.25, 0.75, 0.25, color)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.125, 0.875, 0)
    glRotatef(-leg_swing, 1, 0, 0)
    glTranslatef(0, -0.375, 0)
    leg_color = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6)
    draw_minecraft_cube(0, 0, 0, 0.25, 0.75, 0.25, leg_color)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0.125, 0.875, 0)
    glRotatef(leg_swing, 1, 0, 0)
    glTranslatef(0, -0.375, 0)
    draw_minecraft_cube(0, 0, 0, 0.25, 0.75, 0.25, leg_color)
    glPopMatrix()
    
    glPopMatrix()

def create_ground_display_list():
    global ground_display_list
    ground_display_list = glGenLists(1)
    glNewList(ground_display_list, GL_COMPILE)
    
    glColor3f(0.4, 0.7, 0.3)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glEnd()
    
    wall_color = (0.5, 0.3, 0.2)
    wall_height = 5
    
    glColor3f(*wall_color)
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, -MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, MAP_SIZE)
    glEnd()
    
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f(-MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(-MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(-MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(MAP_SIZE, 0, -MAP_SIZE)
    glVertex3f(MAP_SIZE, 0, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, MAP_SIZE)
    glVertex3f(MAP_SIZE, wall_height, -MAP_SIZE)
    glEnd()
    
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
    glCallList(ground_display_list)

def draw_obstacles():
    for obs in obstacles:
        draw_minecraft_cube(obs.x, obs.y, obs.z, obs.width, obs.height, obs.depth, obs.color)

def draw_bullet(bullet):
    color = (1, 1, 0) if bullet.owner == 1 else (0, 1, 1)
    draw_minecraft_cube(bullet.pos[0], bullet.pos[1] + 1, bullet.pos[2], 0.2, 0.2, 0.2, color)

def draw_text_2d(x, y, text, font, color=(255, 255, 255)):
    text_surface = font.render(str(text), True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glRasterPos2f(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                 GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def draw_minimap(x, y, size, player_pos, player_rotation, other_pos, player_num):
    """Draw rotating minimap that follows player"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + size, y)
    glVertex2f(x + size, y + size)
    glVertex2f(x, y + size)
    glEnd()
    
    # Border
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + size, y)
    glVertex2f(x + size, y + size)
    glVertex2f(x, y + size)
    glEnd()
    
    center_x = x + size / 2
    center_y = y + size / 2
    scale = size / (MAP_SIZE * 2)
    
    rotation = math.radians(player_rotation + 180)
    
    def rotate_point(px, pz, angle):
        """Rotate a point around origin"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return (px * cos_a - pz * sin_a, px * sin_a + pz * cos_a)
    
    # Draw map bounds (rotated)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINE_LOOP)
    corners = [(-MAP_SIZE, -MAP_SIZE), (MAP_SIZE, -MAP_SIZE), 
               (MAP_SIZE, MAP_SIZE), (-MAP_SIZE, MAP_SIZE)]
    for corner_x, corner_z in corners:
        # Relative to player
        rel_x = corner_x - player_pos[0]
        rel_z = corner_z - player_pos[2]
        # Rotate
        rot_x, rot_z = rotate_point(rel_x, rel_z, rotation)
        # Clamp to minimap bounds
        screen_x = center_x + rot_x * scale
        screen_y = center_y - rot_z * scale
        glVertex2f(screen_x, screen_y)
    glEnd()
    
    # Draw obstacles (rotated)
    glColor3f(0.6, 0.4, 0.2)
    for obs in obstacles:
        rel_x = obs.x - player_pos[0]
        rel_z = obs.z - player_pos[2]
        
        # Only draw if in range
        if abs(rel_x) < MAP_SIZE and abs(rel_z) < MAP_SIZE:
            rot_x, rot_z = rotate_point(rel_x, rel_z, rotation)
            
            ox = center_x + rot_x * scale
            oz = center_y - rot_z * scale
            obs_size = obs.width * scale * 0.5
            
            # Check if in minimap bounds
            if (x < ox < x + size) and (y < oz < y + size):
                glBegin(GL_QUADS)
                glVertex2f(ox - obs_size, oz - obs_size)
                glVertex2f(ox + obs_size, oz - obs_size)
                glVertex2f(ox + obs_size, oz + obs_size)
                glVertex2f(ox - obs_size, oz + obs_size)
                glEnd()
    
    # Draw portals (rotated)
    for portal in portals:
        rel_x = portal.x - player_pos[0]
        rel_z = portal.z - player_pos[2]
        
        if abs(rel_x) < MAP_SIZE and abs(rel_z) < MAP_SIZE:
            rot_x, rot_z = rotate_point(rel_x, rel_z, rotation)
            
            px = center_x + rot_x * scale
            pz = center_y - rot_z * scale
            
            if (x < px < x + size) and (y < pz < y + size):
                glColor3f(*portal.color)
                glBegin(GL_TRIANGLE_FAN)
                glVertex2f(px, pz)
                for i in range(9):
                    angle = (i / 8) * 2 * math.pi
                    glVertex2f(px + math.cos(angle) * 3, pz + math.sin(angle) * 3)
                glEnd()
    
    # Draw other player (rotated)
    rel_x = other_pos[0] - player_pos[0]
    rel_z = other_pos[2] - player_pos[2]
    
    if abs(rel_x) < MAP_SIZE and abs(rel_z) < MAP_SIZE:
        rot_x, rot_z = rotate_point(rel_x, rel_z, rotation)
        
        ox = center_x + rot_x * scale
        oz = center_y - rot_z * scale
        
        if (x < ox < x + size) and (y < oz < y + size):
            other_color = (0.9, 0.3, 0.3) if player_num == 1 else (0.3, 0.5, 0.9)
            glColor3f(*other_color)
            glBegin(GL_TRIANGLES)
            glVertex2f(ox, oz - 5)
            glVertex2f(ox - 4, oz + 4)
            glVertex2f(ox + 4, oz + 4)
            glEnd()
    
    # Draw current player (center - always visible)
    player_color = (0.3, 0.5, 0.9) if player_num == 1 else (0.9, 0.3, 0.3)
    glColor3f(*player_color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(center_x, center_y)
    for i in range(9):
        angle = (i / 8) * 2 * math.pi
        glVertex2f(center_x + math.cos(angle) * 4, center_y + math.sin(angle) * 4)
    glEnd()
    
    # Direction arrow (always points up on minimap)
    arrow_len = 8
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(center_x, center_y)
    glVertex2f(center_x, center_y + arrow_len)
    glEnd()
    
    # Arrow head
    glBegin(GL_TRIANGLES)
    glVertex2f(center_x, center_y + arrow_len)
    glVertex2f(center_x - 3, center_y + arrow_len - 5)
    glVertex2f(center_x + 3, center_y + arrow_len - 5)
    glEnd()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def set_camera(player_pos, player_rotation):
    cam_x = player_pos[0] - math.sin(math.radians(player_rotation)) * camera_distance
    cam_y = player_pos[1] + camera_height
    cam_z = player_pos[2] - math.cos(math.radians(player_rotation)) * camera_distance
    
    gluLookAt(
        cam_x, cam_y, cam_z,
        player_pos[0], player_pos[1] + 1.5, player_pos[2],
        0, 1, 0
    )

def draw_scene(player1_moving, player2_moving):
    draw_ground()
    draw_obstacles()
    
    for portal in portals:
        draw_portal(portal)
    
    draw_minecraft_player(player1_pos, player1_rotation, (0.3, 0.5, 0.9), player1_moving, player1_alive)
    draw_minecraft_player(player2_pos, player2_rotation, (0.9, 0.3, 0.3), player2_moving, player2_alive)
    
    for bullet in bullets:
        draw_bullet(bullet)

def handle_controller_input():
    """Handle both controllers"""
    global player1_pos, player1_rotation, player1_alive
    global player2_pos, player2_rotation, player2_alive
    global controller1_last_shoot, controller2_last_shoot
    
    p1_moving = False
    p2_moving = False
    
    # Player 1 Controller
    if len(controllers) >= 1 and player1_alive:
        c = controllers[0]
        speed = move_speed * 3
        
        left_x = c.get_axis(0)
        left_y = c.get_axis(1)
        right_x = c.get_axis(2)
        
        if abs(left_x) < 0.15: left_x = 0
        if abs(left_y) < 0.15: left_y = 0
        if abs(right_x) < 0.15: right_x = 0
        
        player1_rotation -= right_x * 2
        
        if abs(left_x) > 0 or abs(left_y) > 0:
            new_x = player1_pos[0] - math.sin(math.radians(player1_rotation)) * left_y * speed
            new_z = player1_pos[2] - math.cos(math.radians(player1_rotation)) * left_y * speed
            new_x += math.sin(math.radians(player1_rotation - 90)) * left_x * speed
            new_z += math.cos(math.radians(player1_rotation - 90)) * left_x * speed
            
            collision = False
            for obs in obstacles:
                if abs(new_x - obs.x) < obs.width/2 + 0.5 and abs(new_z - obs.z) < obs.depth/2 + 0.5:
                    collision = True
                    break
            
            if not collision:
                player1_pos[0] = max(-MAP_SIZE+1, min(MAP_SIZE-1, new_x))
                player1_pos[2] = max(-MAP_SIZE+1, min(MAP_SIZE-1, new_z))
            
            p1_moving = True
        
        shoot = c.get_button(7)
        if c.get_numaxes() > 5:
            shoot = shoot or c.get_axis(5) > 0.5
        
        if shoot and not controller1_last_shoot:
            shoot_player1()
        controller1_last_shoot = shoot
    
    # Player 2 Controller
    if len(controllers) >= 2 and player2_alive:
        c = controllers[1]
        speed = move_speed * 3
        
        left_x = c.get_axis(0)
        left_y = c.get_axis(1)
        right_x = c.get_axis(2)
        
        if abs(left_x) < 0.15: left_x = 0
        if abs(left_y) < 0.15: left_y = 0
        if abs(right_x) < 0.15: right_x = 0
        
        player2_rotation -= right_x * 2
        
        if abs(left_x) > 0 or abs(left_y) > 0:
            new_x = player2_pos[0] - math.sin(math.radians(player2_rotation)) * left_y * speed
            new_z = player2_pos[2] - math.cos(math.radians(player2_rotation)) * left_y * speed
            new_x += math.sin(math.radians(player2_rotation - 90)) * left_x * speed
            new_z += math.cos(math.radians(player2_rotation - 90)) * left_x * speed
            
            collision = False
            for obs in obstacles:
                if abs(new_x - obs.x) < obs.width/2 + 0.5 and abs(new_z - obs.z) < obs.depth/2 + 0.5:
                    collision = True
                    break
            
            if not collision:
                player2_pos[0] = max(-MAP_SIZE+1, min(MAP_SIZE-1, new_x))
                player2_pos[2] = max(-MAP_SIZE+1, min(MAP_SIZE-1, new_z))
            
            p2_moving = True
        
        shoot = c.get_button(0)
        if c.get_numaxes() > 5:
            shoot = shoot or c.get_axis(5) > 0.5
        
        if shoot and not controller2_last_shoot:
            shoot_player2()
        controller2_last_shoot = shoot
    
    return p1_moving, p2_moving

def handle_player1_movement(keys, dt):
    global player1_pos, player1_rotation
    if not player1_alive:
        return False
    
    speed = move_speed * dt
    is_moving = False
    
    if keys[K_q]:
        player1_rotation += 2
    if keys[K_e]:
        player1_rotation -= 2
    
    new_x, new_z = player1_pos[0], player1_pos[2]
    
    if keys[K_w]:
        new_x += math.sin(math.radians(player1_rotation)) * speed
        new_z += math.cos(math.radians(player1_rotation)) * speed
        is_moving = True
    if keys[K_s]:
        new_x -= math.sin(math.radians(player1_rotation)) * speed
        new_z -= math.cos(math.radians(player1_rotation)) * speed
        is_moving = True
    if keys[K_d]:
        new_x += math.sin(math.radians(player1_rotation - 90)) * speed
        new_z += math.cos(math.radians(player1_rotation - 90)) * speed
        is_moving = True
    if keys[K_a]:
        new_x += math.sin(math.radians(player1_rotation + 90)) * speed
        new_z += math.cos(math.radians(player1_rotation + 90)) * speed
        is_moving = True
    
    collision = False
    for obs in obstacles:
        dx = new_x - obs.x
        dz = new_z - obs.z
        if (abs(dx) < obs.width / 2 + 0.5 and abs(dz) < obs.depth / 2 + 0.5):
            collision = True
            break
    
    if not collision:
        player1_pos[0] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, new_x))
        player1_pos[2] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, new_z))
    
    return is_moving

def handle_player2_movement(keys, dt):
    global player2_pos, player2_rotation
    if not player2_alive:
        return False
    
    speed = move_speed * dt
    is_moving = False
    
    if keys[K_u]:
        player2_rotation += 2
    if keys[K_o]:
        player2_rotation -= 2
    
    new_x, new_z = player2_pos[0], player2_pos[2]
    
    if keys[K_i]:
        new_x += math.sin(math.radians(player2_rotation)) * speed
        new_z += math.cos(math.radians(player2_rotation)) * speed
        is_moving = True
    if keys[K_k]:
        new_x -= math.sin(math.radians(player2_rotation)) * speed
        new_z -= math.cos(math.radians(player2_rotation)) * speed
        is_moving = True
    if keys[K_j]:
        new_x += math.sin(math.radians(player2_rotation - 90)) * speed
        new_z += math.cos(math.radians(player2_rotation - 90)) * speed
        is_moving = True
    if keys[K_l]:
        new_x += math.sin(math.radians(player2_rotation + 90)) * speed
        new_z += math.cos(math.radians(player2_rotation + 90)) * speed
        is_moving = True
    
    collision = False
    for obs in obstacles:
        dx = new_x - obs.x
        dz = new_z - obs.z
        if (abs(dx) < obs.width / 2 + 0.5 and abs(dz) < obs.depth / 2 + 0.5):
            collision = True
            break
    
    if not collision:
        player2_pos[0] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, new_x))
        player2_pos[2] = max(-MAP_SIZE + 1, min(MAP_SIZE - 1, new_z))
    
    return is_moving

def shoot_player1():
    if player1_alive:
        bullet = Bullet([player1_pos[0], player1_pos[1] + 1, player1_pos[2]], player1_rotation, 1)
        bullets.append(bullet)

def shoot_player2():
    if player2_alive:
        bullet = Bullet([player2_pos[0], player2_pos[1] + 1, player2_pos[2]], player2_rotation, 2)
        bullets.append(bullet)

def respawn_player(player_num):
    global player1_pos, player1_health, player1_alive, player1_rotation
    global player2_pos, player2_health, player2_alive, player2_rotation
    
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
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1920, 0, 1080, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # SCOREBOARD
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(10, 1080 - 220)
    glVertex2f(250, 1080 - 220)
    glVertex2f(250, 1080 - 10)
    glVertex2f(10, 1080 - 10)
    glEnd()
    
    glColor3f(1, 1, 1)
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glVertex2f(10, 1080 - 220)
    glVertex2f(250, 1080 - 220)
    glVertex2f(250, 1080 - 10)
    glVertex2f(10, 1080 - 10)
    glEnd()
    
    glColor3f(0.3, 0.5, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(20, 1080 - 50)
    glVertex2f(60, 1080 - 50)
    glVertex2f(60, 1080 - 20)
    glVertex2f(20, 1080 - 20)
    glEnd()
    
    glColor3f(0.9, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(20, 1080 - 200)
    glVertex2f(60, 1080 - 200)
    glVertex2f(60, 1080 - 170)
    glVertex2f(20, 1080 - 170)
    glEnd()
    
    # Health bars
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(1920 - 310, 1080 - 40)
    glVertex2f(1920 - 10, 1080 - 40)
    glVertex2f(1920 - 10, 1080 - 10)
    glVertex2f(1920 - 310, 1080 - 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player1_health / 100.0) * 300
    glBegin(GL_QUADS)
    glVertex2f(1920 - 310, 1080 - 40)
    glVertex2f(1920 - 310 + health_width, 1080 - 40)
    glVertex2f(1920 - 310 + health_width, 1080 - 10)
    glVertex2f(1920 - 310, 1080 - 10)
    glEnd()
    
    glColor3f(0.5, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(1920 - 310, 40)
    glVertex2f(1920 - 10, 40)
    glVertex2f(1920 - 10, 10)
    glVertex2f(1920 - 310, 10)
    glEnd()
    
    glColor3f(0, 1, 0)
    health_width = (player2_health / 100.0) * 300
    glBegin(GL_QUADS)
    glVertex2f(1920 - 310, 40)
    glVertex2f(1920 - 310 + health_width, 40)
    glVertex2f(1920 - 310 + health_width, 10)
    glVertex2f(1920 - 310, 10)
    glEnd()
    
    # Divider
    glColor3f(1, 1, 1)
    glLineWidth(3)
    glBegin(GL_LINES)
    glVertex2f(0, 540)
    glVertex2f(1920, 540)
    glEnd()
    
    # Crosshairs
    glLineWidth(3)
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    glVertex2f(960 - 20, 810)
    glVertex2f(960 + 20, 810)
    glVertex2f(960, 810 - 20)
    glVertex2f(960, 810 + 20)
    glEnd()
    
    glBegin(GL_LINES)
    glVertex2f(960 - 20, 270)
    glVertex2f(960 + 20, 270)
    glVertex2f(960, 270 - 20)
    glVertex2f(960, 270 + 20)
    glEnd()
    
    # Minimaps
    draw_minimap(1920 - 210, 1080 - 260, 200, player1_pos, player1_rotation, player2_pos, 1)
    draw_minimap(1920 - 210, 50, 200, player2_pos, player2_rotation, player1_pos, 2)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    draw_text_2d(80, 1080 - 70, player1_score, score_font, (100, 150, 255))
    draw_text_2d(80, 1080 - 220, player2_score, score_font, (255, 100, 100))
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# Initialize
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
setup_lighting()

create_cube_display_list()
create_ground_display_list()

# Add obstacles
add_box_obstacle(0, 0, 4)
add_pillar(-10, -10, 6, 1.5)
add_pillar(10, 10, 6, 1.5)
add_pillar(-10, 10, 6, 1.5)
add_pillar(10, -10, 6, 1.5)

add_wall(-20, -15, -10, -15, 3, 1)
add_wall(10, 15, 20, 15, 3, 1)
add_wall(-15, -20, -15, -10, 3, 1)
add_wall(15, 10, 15, 20, 3, 1)

add_box_obstacle(-15, 0, 3)
add_box_obstacle(15, 0, 3)
add_box_obstacle(0, -15, 3)
add_box_obstacle(0, 15, 3)

add_portal_pair(-40, 0, 40, 0)
add_portal_pair(40, 0, -40, 0)   

init_controllers()

# Main loop
running = True
last_time = pygame.time.get_ticks()
respawn_delay = 0

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 10.0
    last_time = current_time
    
    walk_animation += 0.1
    portal_animation += 1
    
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                shoot_player1()
            if event.key == K_SEMICOLON:
                shoot_player2()
    
    keys = pygame.key.get_pressed()
    
    controller1_moving, controller2_moving = handle_controller_input()
    
    if len(controllers) < 1:
        player1_moving = handle_player1_movement(keys, dt)
    else:
        player1_moving = controller1_moving
    
    if len(controllers) < 2:
        player2_moving = handle_player2_movement(keys, dt)
    else:
        player2_moving = controller2_moving
    
    # Check portal teleportation with cooldown
    if portal_cooldown1 > 0:
        portal_cooldown1 -= 1
    if portal_cooldown2 > 0:
        portal_cooldown2 -= 1

    for portal in portals:
        if player1_alive and portal.check_teleport(player1_pos) and portal_cooldown1 == 0:
            player1_pos[0] = portal.dest_x
            player1_pos[2] = portal.dest_z
            portal_cooldown1 = 60  # 1 second cooldown at 60fps
        if player2_alive and portal.check_teleport(player2_pos) and portal_cooldown2 == 0:
            player2_pos[0] = portal.dest_x
            player2_pos[2] = portal.dest_z
            portal_cooldown2 = 60

    
    # Update bullets
    bullets = [b for b in bullets if b.is_alive()]
    for bullet in bullets:
        bullet.update()
    
    # Collision detection
    for bullet in bullets[:]:
        for obs in obstacles:
            if bullet.check_hit_obstacle(obs.to_dict()):
                if bullet in bullets:
                    bullets.remove(bullet)
                break
        
        if bullet not in bullets:
            continue
        
        if bullet.owner == 2 and player1_alive:
            if bullet.check_hit_player(player1_pos):
                player1_health -= 34
                if bullet in bullets:
                    bullets.remove(bullet)
                if player1_health <= 0:
                    player1_alive = False
                    player2_score += 1
                    respawn_delay = 180
                    
        if bullet.owner == 1 and player2_alive:
            if bullet.check_hit_player(player2_pos):
                player2_health -= 34
                if bullet in bullets:
                    bullets.remove(bullet)
                if player2_health <= 0:
                    player2_alive = False
                    player1_score += 1
                    respawn_delay = 180
    
    if respawn_delay > 0:
        respawn_delay -= 1
        if respawn_delay == 0:
            if not player1_alive:
                respawn_player(1)
            if not player2_alive:
                respawn_player(2)
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # PLAYER 1 VIEW
    glViewport(0, 540, 1920, 540)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, (1920/540), 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player1_pos, player1_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # PLAYER 2 VIEW
    glViewport(0, 0, 1920, 540)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, (1920/540), 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    set_camera(player2_pos, player2_rotation)
    draw_scene(player1_moving, player2_moving)
    
    # HUD
    glViewport(0, 0, 1920, 1080)
    draw_split_screen_hud()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
