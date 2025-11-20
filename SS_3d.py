import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Create fullscreen OpenGL context
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN)
pygame.display.set_caption("Soccer Stars 3D")
clock = pygame.time.Clock()

# Field dimensions: 22:15 ratio (similar to 110m x 75m)
FIELD_LENGTH = 11.0  # Half-length (22 units total)
FIELD_WIDTH = 7.5    # Half-width (15 units total)

# Setup orthographic top-down view with 22:15 ratio
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(-FIELD_LENGTH - 1, FIELD_LENGTH + 1, -FIELD_WIDTH - 1, FIELD_WIDTH + 1, -10, 10)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
gluLookAt(0, 10, 0,      # Camera above
          0, 0, 0,        # Looking at center
          0, 0, -1)       # Up vector
#glRotatef(90, 0, 1, 0)    # Rotate 90 degrees

# Set background color
glClearColor(0.1, 0.5, 0.2, 1.0)

# Enable features
glEnable(GL_DEPTH_TEST)
glEnable(GL_LIGHTING)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Multiple lights
glEnable(GL_LIGHT0)
glEnable(GL_LIGHT1)
glEnable(GL_LIGHT2)

glLight(GL_LIGHT0, GL_POSITION, (0, 10, 0, 1))
glLight(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1))
glLight(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1))
glLight(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1))

glLight(GL_LIGHT1, GL_POSITION, (12, 5, 0, 1))
glLight(GL_LIGHT1, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
glLight(GL_LIGHT1, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
glLight(GL_LIGHT1, GL_SPECULAR, (0.3, 0.3, 0.3, 1))

glLight(GL_LIGHT2, GL_POSITION, (-12, 5, 0, 1))
glLight(GL_LIGHT2, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
glLight(GL_LIGHT2, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
glLight(GL_LIGHT2, GL_SPECULAR, (0.3, 0.3, 0.3, 1))

glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (1, 1, 1, 1))
glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50)

# Physics constants
FRICTION = 0.96
BOUNCE = 0.8
MIN_VELOCITY = 0.05

# Scaled measurements (based on standard pitch proportions)
GOAL_WIDTH = 2.4  # Goal width (scaled from 7.32m)
PENALTY_AREA_WIDTH = 5.5  # Penalty area width (scaled from 40.3m)
PENALTY_AREA_LENGTH = 5.5  # Penalty area length (scaled from 16.5m)
GOAL_AREA_WIDTH = 3.0  # Goal area width (scaled from 18.32m)
GOAL_AREA_LENGTH = 1.8  # Goal area length (scaled from 5.5m)
CENTER_CIRCLE_RADIUS = 3.0  # Center circle radius (scaled from 9.15m)
CORNER_RADIUS = 0.3  # Corner arc radius

class Disc3D:
    def __init__(self, x, z, radius, color, is_ball=False):
        self.x = x
        self.y = 0.3 if is_ball else 0.4
        self.z = z
        self.radius = radius
        self.vx = 0
        self.vz = 0
        self.color = color
        self.is_ball = is_ball
        self.mass = 2 if is_ball else 1
        
    def update(self):
        self.vx *= FRICTION
        self.vz *= FRICTION
        
        if abs(self.vx) < MIN_VELOCITY:
            self.vx = 0
        if abs(self.vz) < MIN_VELOCITY:
            self.vz = 0
            
        self.x += self.vx
        self.z += self.vz
        
        # Wall collisions (touchlines - sides)
        if self.z - self.radius <= -FIELD_WIDTH:
            self.z = -FIELD_WIDTH + self.radius
            self.vz = -self.vz * BOUNCE
        elif self.z + self.radius >= FIELD_WIDTH:
            self.z = FIELD_WIDTH - self.radius
            self.vz = -self.vz * BOUNCE
            
        # Goal lines (ends)
        goal_left = -GOAL_WIDTH / 2
        goal_right = GOAL_WIDTH / 2
        
        if self.x - self.radius <= -FIELD_LENGTH:
            if self.is_ball and goal_left <= self.z <= goal_right:
                return "player2_scores"
            else:
                self.x = -FIELD_LENGTH + self.radius
                self.vx = -self.vx * BOUNCE
                
        elif self.x + self.radius >= FIELD_LENGTH:
            if self.is_ball and goal_left <= self.z <= goal_right:
                return "player1_scores"
            else:
                self.x = FIELD_LENGTH - self.radius
                self.vx = -self.vx * BOUNCE
        
        return None
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(*self.color)
        
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluSphere(quadric, self.radius, 32, 32)
        gluDeleteQuadric(quadric)
        
        glPopMatrix()
    
    def is_moving(self):
        return abs(self.vx) > MIN_VELOCITY or abs(self.vz) > MIN_VELOCITY

def check_collision(disc1, disc2):
    dx = disc1.x - disc2.x
    dz = disc1.z - disc2.z
    distance = math.sqrt(dx * dx + dz * dz)
    return distance <= (disc1.radius + disc2.radius)

def resolve_collision(disc1, disc2):
    dx = disc1.x - disc2.x
    dz = disc1.z - disc2.z
    distance = math.sqrt(dx * dx + dz * dz)
    
    if distance == 0:
        distance = 0.1
        dx = 0.1
    
    overlap = (disc1.radius + disc2.radius) - distance
    if overlap > 0:
        nx = dx / distance
        nz = dz / distance
        
        separation = overlap / 2
        disc1.x += nx * separation
        disc1.z += nz * separation
        disc2.x -= nx * separation
        disc2.z -= nz * separation
    
    collision_angle = math.atan2(dz, dx)
    
    v1 = math.sqrt(disc1.vx**2 + disc1.vz**2)
    v2 = math.sqrt(disc2.vx**2 + disc2.vz**2)
    
    angle1 = math.atan2(disc1.vz, disc1.vx) if v1 > 0 else 0
    angle2 = math.atan2(disc2.vz, disc2.vx) if v2 > 0 else 0
    
    m1 = disc1.mass
    m2 = disc2.mass
    
    v1x = v1 * math.cos(angle1 - collision_angle)
    v1z = v1 * math.sin(angle1 - collision_angle)
    v2x = v2 * math.cos(angle2 - collision_angle)
    v2z = v2 * math.sin(angle2 - collision_angle)
    
    final_v1x = ((m1 - m2) * v1x + 2 * m2 * v2x) / (m1 + m2)
    final_v2x = ((m2 - m1) * v2x + 2 * m1 * v1x) / (m1 + m2)
    
    disc1.vx = final_v1x * math.cos(collision_angle) - v1z * math.sin(collision_angle)
    disc1.vz = final_v1x * math.sin(collision_angle) + v1z * math.cos(collision_angle)
    disc2.vx = final_v2x * math.cos(collision_angle) - v2z * math.sin(collision_angle)
    disc2.vz = final_v2x * math.sin(collision_angle) + v2z * math.cos(collision_angle)

def draw_arrow(x1, z1, x2, z2, color):
    glDisable(GL_LIGHTING)
    glColor3f(*color)
    glLineWidth(6)
    
    glBegin(GL_LINES)
    glVertex3f(x1, 0.5, z1)
    glVertex3f(x2, 0.5, z2)
    glEnd()
    
    dx = x2 - x1
    dz = z2 - z1
    length = math.sqrt(dx*dx + dz*dz)
    
    if length > 0.1:
        dx /= length
        dz /= length
        
        px = -dz
        pz = dx
        
        arrow_size = 0.5
        glBegin(GL_TRIANGLES)
        glVertex3f(x2, 0.5, z2)
        glVertex3f(x2 - dx * arrow_size + px * arrow_size/2, 0.5, 
                   z2 - dz * arrow_size + pz * arrow_size/2)
        glVertex3f(x2 - dx * arrow_size - px * arrow_size/2, 0.5, 
                   z2 - dz * arrow_size - pz * arrow_size/2)
        glEnd()
    
    glEnable(GL_LIGHTING)

def draw_power_meter(x, y, power, max_power):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    bar_width = 300
    bar_height = 30
    fill_width = int((power / max_power) * bar_width)
    
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()
    
    if power < max_power * 0.3:
        glColor3f(0, 1, 0)
    elif power < max_power * 0.7:
        glColor3f(1, 1, 0)
    else:
        glColor3f(1, 0, 0)
    
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + fill_width, y)
    glVertex2f(x + fill_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()
    
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_field():
    # Draw bright green football field (22:15 ratio)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.8, 0.2)
    glVertex3f(-FIELD_LENGTH, 0, -FIELD_WIDTH)
    glVertex3f(FIELD_LENGTH, 0, -FIELD_WIDTH)
    glColor3f(0.25, 0.85, 0.25)
    glVertex3f(FIELD_LENGTH, 0, FIELD_WIDTH)
    glVertex3f(-FIELD_LENGTH, 0, FIELD_WIDTH)
    glEnd()
    
    glDisable(GL_LIGHTING)
    glColor3f(1, 1, 1)
    glLineWidth(4)
    
    # Outer boundary (touchlines and goal lines)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-FIELD_LENGTH, 0.01, -FIELD_WIDTH)
    glVertex3f(FIELD_LENGTH, 0.01, -FIELD_WIDTH)
    glVertex3f(FIELD_LENGTH, 0.01, FIELD_WIDTH)
    glVertex3f(-FIELD_LENGTH, 0.01, FIELD_WIDTH)
    glEnd()
    
    # Halfway line
    glLineWidth(3)
    glBegin(GL_LINES)
    glVertex3f(0, 0.01, -FIELD_WIDTH)
    glVertex3f(0, 0.01, FIELD_WIDTH)
    glEnd()
    
    # Center circle
    glBegin(GL_LINE_LOOP)
    for i in range(64):
        angle = i * 2 * math.pi / 64
        glVertex3f(math.cos(angle) * CENTER_CIRCLE_RADIUS, 0.01, 
                   math.sin(angle) * CENTER_CIRCLE_RADIUS)
    glEnd()
    
    # Center spot
    glPointSize(10)
    glBegin(GL_POINTS)
    glVertex3f(0, 0.01, 0)
    glEnd()
    
    # Penalty areas - Player 1 side (right)
    glBegin(GL_LINE_STRIP)
    glVertex3f(FIELD_LENGTH, 0.01, -PENALTY_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH - PENALTY_AREA_LENGTH, 0.01, -PENALTY_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH - PENALTY_AREA_LENGTH, 0.01, PENALTY_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH, 0.01, PENALTY_AREA_WIDTH / 2)
    glEnd()
    
    # Penalty areas - Player 2 side (left)
    glBegin(GL_LINE_STRIP)
    glVertex3f(-FIELD_LENGTH, 0.01, -PENALTY_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH + PENALTY_AREA_LENGTH, 0.01, -PENALTY_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH + PENALTY_AREA_LENGTH, 0.01, PENALTY_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH, 0.01, PENALTY_AREA_WIDTH / 2)
    glEnd()
    
    # Goal areas - Player 1 side
    glBegin(GL_LINE_STRIP)
    glVertex3f(FIELD_LENGTH, 0.01, -GOAL_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH - GOAL_AREA_LENGTH, 0.01, -GOAL_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH - GOAL_AREA_LENGTH, 0.01, GOAL_AREA_WIDTH / 2)
    glVertex3f(FIELD_LENGTH, 0.01, GOAL_AREA_WIDTH / 2)
    glEnd()
    
    # Goal areas - Player 2 side
    glBegin(GL_LINE_STRIP)
    glVertex3f(-FIELD_LENGTH, 0.01, -GOAL_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH + GOAL_AREA_LENGTH, 0.01, -GOAL_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH + GOAL_AREA_LENGTH, 0.01, GOAL_AREA_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH, 0.01, GOAL_AREA_WIDTH / 2)
    glEnd()
    
    # Penalty spots
    penalty_spot_dist = FIELD_LENGTH - 3.6  # Scaled from 11m
    glPointSize(8)
    glBegin(GL_POINTS)
    glVertex3f(penalty_spot_dist, 0.01, 0)
    glVertex3f(-penalty_spot_dist, 0.01, 0)
    glEnd()
    
    # Corner arcs
    glLineWidth(3)
    for corner_x in [-FIELD_LENGTH, FIELD_LENGTH]:
        for corner_z in [-FIELD_WIDTH, FIELD_WIDTH]:
            glBegin(GL_LINE_STRIP)
            sign_x = 1 if corner_x > 0 else -1
            sign_z = 1 if corner_z > 0 else -1
            for i in range(16):
                angle = i * (math.pi / 2) / 15
                x = corner_x - sign_x * CORNER_RADIUS * math.cos(angle)
                z = corner_z - sign_z * CORNER_RADIUS * math.sin(angle)
                glVertex3f(x, 0.01, z)
            glEnd()
    
    glEnable(GL_LIGHTING)
    
    # Goals
    glColor3f(0, 0.4, 0)
    # Player 1 goal
    glBegin(GL_QUADS)
    glVertex3f(FIELD_LENGTH, 0, -GOAL_WIDTH / 2)
    glVertex3f(FIELD_LENGTH, 0, GOAL_WIDTH / 2)
    glVertex3f(FIELD_LENGTH + 0.5, 0, GOAL_WIDTH / 2)
    glVertex3f(FIELD_LENGTH + 0.5, 0, -GOAL_WIDTH / 2)
    glEnd()
    
    # Player 2 goal
    glBegin(GL_QUADS)
    glVertex3f(-FIELD_LENGTH, 0, -GOAL_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH, 0, GOAL_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH - 0.5, 0, GOAL_WIDTH / 2)
    glVertex3f(-FIELD_LENGTH - 0.5, 0, -GOAL_WIDTH / 2)
    glEnd()

def draw_text(x, y, text, color=(255, 255, 255)):
    font = pygame.font.Font(None, 72)
    text_surface = font.render(text, True, color).convert_alpha()
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    
    glWindowPos2d(int(x), int(y))
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                 GL_RGBA, GL_UNSIGNED_BYTE, text_data)

# Initialize game objects
ball = Disc3D(0, 0, 0.35, (1, 0.84, 0), is_ball=True)

player1_discs = [
    Disc3D(6, -2, 0.45, (0.12, 0.56, 1)),
    Disc3D(6, 0, 0.45, (0.12, 0.56, 1)),
    Disc3D(6, 2, 0.45, (0.12, 0.56, 1)),
]

player2_discs = [
    Disc3D(-6, -2, 0.45, (0.86, 0.08, 0.24)),
    Disc3D(-6, 0, 0.45, (0.86, 0.08, 0.24)),
    Disc3D(-6, 2, 0.45, (0.86, 0.08, 0.24)),
]

all_discs = player1_discs + player2_discs + [ball]

current_player = 1
selected_disc = None
aiming = False
aim_start = None
MAX_POWER = 2.5
MIN_DRAG = 0.5

score_p1 = 0
score_p2 = 0
turn_taken = False

def reset_positions():
    ball.x, ball.z = 0, 0
    ball.vx, ball.vz = 0, 0
    
    positions_p1 = [(6, -2), (6, 0), (6, 2)]
    positions_p2 = [(-6, -2), (-6, 0), (-6, 2)]
    
    for i, disc in enumerate(player1_discs):
        disc.x, disc.z = positions_p1[i]
        disc.vx, disc.vz = 0, 0
    
    for i, disc in enumerate(player2_discs):
        disc.x, disc.z = positions_p2[i]
        disc.vx, disc.vz = 0, 0

def all_stopped():
    return all(not disc.is_moving() for disc in all_discs)

def screen_to_field(screen_x, screen_y):
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    
    win_x = float(screen_x)
    win_y = float(viewport[3] - screen_y)
    
    pos = gluUnProject(win_x, win_y, 0.5, modelview, projection, viewport)
    return pos[0], pos[2]

running = True

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        
        if event.type == MOUSEBUTTONDOWN and all_stopped() and not turn_taken:
            mouse_x, mouse_y = event.pos
            field_x, field_z = screen_to_field(mouse_x, mouse_y)
            
            current_discs = player1_discs if current_player == 1 else player2_discs
            for disc in current_discs:
                dx = field_x - disc.x
                dz = field_z - disc.z
                if math.sqrt(dx*dx + dz*dz) <= disc.radius:
                    selected_disc = disc
                    aiming = True
                    aim_start = (field_x, field_z)
                    break
                    
        if event.type == MOUSEBUTTONUP and aiming and selected_disc:
            mouse_x, mouse_y = event.pos
            field_x, field_z = screen_to_field(mouse_x, mouse_y)
            
            dx = aim_start[0] - field_x
            dz = aim_start[1] - field_z
            distance = math.sqrt(dx*dx + dz*dz)
            
            if distance > MIN_DRAG:
                power = min(distance * 0.8, MAX_POWER)
                selected_disc.vx = (dx / distance) * power
                selected_disc.vz = (dz / distance) * power
                turn_taken = True
            
            aiming = False
            selected_disc = None
            aim_start = None
    
    goal_scored = None
    for disc in all_discs:
        result = disc.update()
        if result:
            goal_scored = result
    
    for i in range(len(all_discs)):
        for j in range(i + 1, len(all_discs)):
            if check_collision(all_discs[i], all_discs[j]):
                resolve_collision(all_discs[i], all_discs[j])
    
    if goal_scored:
        if goal_scored == "player1_scores":
            score_p1 += 1
        elif goal_scored == "player2_scores":
            score_p2 += 1
        reset_positions()
        turn_taken = False
    
    if all_stopped() and turn_taken and not aiming:
        current_player = 2 if current_player == 1 else 1
        turn_taken = False
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    draw_field()
    
    current_power = 0
    if aiming and aim_start and selected_disc:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        field_x, field_z = screen_to_field(mouse_x, mouse_y)
        
        dx = aim_start[0] - field_x
        dz = aim_start[1] - field_z
        distance = math.sqrt(dx*dx + dz*dz)
        
        if distance > 0.1:
            current_power = min(distance * 0.8, MAX_POWER)
            arrow_length = min(distance * 2, 5)
            end_x = selected_disc.x + (dx / distance) * arrow_length
            end_z = selected_disc.z + (dz / distance) * arrow_length
            
            draw_arrow(selected_disc.x, selected_disc.z, end_x, end_z, (1, 0.2, 0.2))
    
    for disc in all_discs:
        disc.draw()
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    if aiming:
        draw_power_meter(WIDTH // 2 - 150, HEIGHT - 100, current_power, MAX_POWER)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    draw_text(20, HEIGHT - 80, f"Player 1: {score_p1}", (30, 144, 255))
    draw_text(20, HEIGHT - 150, f"Player 2: {score_p2}", (220, 20, 60))
    
    turn_color = (30, 144, 255) if current_player == 1 else (220, 20, 60)
    status = "WAIT..." if turn_taken else "YOUR TURN"
    draw_text(WIDTH - 550, HEIGHT - 80, f"Player {current_player}: {status}", turn_color)
    
    draw_text(20, 40, "Press ESC to exit", (255, 255, 255))
    
    if not all_stopped():
        draw_text(WIDTH // 2 - 200, HEIGHT // 2, "Wait for discs to stop...", (255, 255, 100))
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
