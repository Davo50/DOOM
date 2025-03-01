import pygame
import math
import sys
import random
import numpy as np
from pygame import mixer

# Initialize pygame and mixer
pygame.init()
mixer.init()

# Constants
WIDTH, HEIGHT = 800, 600
HALF_HEIGHT = HEIGHT // 2
FOV = 60  # Field of view
HALF_FOV = FOV / 2
RAY_COUNT = 120  # Number of rays to cast
MAX_DEPTH = 800  # Maximum ray casting distance
TILE_SIZE = 64
PLAYER_SIZE = 10
SCALE = WIDTH / RAY_COUNT

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (150, 75, 0)
YELLOW = (255, 255, 0)

# Game map (1 = wall, 0 = empty space, 2 = door, 3 = health pack, 4 = ammo)
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, 0, 0, 3, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 4, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

MAP_WIDTH = len(MAP[0]) * TILE_SIZE
MAP_HEIGHT = len(MAP) * TILE_SIZE

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DOOM Clone")
clock = pygame.time.Clock()

# Load and create textures
def create_texture(color, pattern=True):
    texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
    texture.fill(color)
    if pattern:
        for i in range(TILE_SIZE):
            for j in range(TILE_SIZE):
                if (i + j) % 8 == 0 or i % 8 == 0 or j % 8 == 0:
                    texture.set_at((i, j), (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50)))
    return texture

wall_texture = create_texture(BROWN)
door_texture = create_texture((100, 50, 0))
health_texture = create_texture((200, 0, 0), False)
ammo_texture = create_texture((200, 200, 0), False)

# Create enemy sprite
enemy_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
enemy_texture.fill((0, 0, 0, 0))
pygame.draw.circle(enemy_texture, (200, 20, 20), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)
pygame.draw.circle(enemy_texture, (50, 50, 50), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 4)

# Create weapon images
shotgun_image = pygame.Surface((300, 200), pygame.SRCALPHA)
pygame.draw.rect(shotgun_image, (60, 60, 60), (80, 100, 180, 20))  # barrel
pygame.draw.rect(shotgun_image, (80, 80, 80), (70, 120, 60, 60))   # handle
shotgun_image = pygame.transform.scale(shotgun_image, (WIDTH // 2, HEIGHT // 2))

pistol_image = pygame.Surface((200, 150), pygame.SRCALPHA)
pygame.draw.rect(pistol_image, (50, 50, 50), (80, 80, 100, 15))  # barrel
pygame.draw.rect(pistol_image, (70, 70, 70), (70, 95, 40, 50))   # handle
pistol_image = pygame.transform.scale(pistol_image, (WIDTH // 3, HEIGHT // 3))

bfg_image = pygame.Surface((400, 250), pygame.SRCALPHA)
pygame.draw.rect(bfg_image, (20, 100, 20), (100, 100, 200, 40))  # barrel
pygame.draw.rect(bfg_image, (50, 150, 50), (80, 140, 80, 70))    # handle
pygame.draw.circle(bfg_image, (0, 255, 0, 128), (300, 120), 30)  # energy orb
bfg_image = pygame.transform.scale(bfg_image, (WIDTH // 2, HEIGHT // 2))

# Create muzzle flash
muzzle_flash = pygame.Surface((100, 100), pygame.SRCALPHA)
pygame.draw.circle(muzzle_flash, (255, 255, 0, 200), (50, 50), 40)
pygame.draw.circle(muzzle_flash, (255, 150, 0, 150), (50, 50), 30)
pygame.draw.circle(muzzle_flash, (255, 255, 255, 100), (50, 50), 20)

# Create HUD elements
hud_font = pygame.font.SysFont('Arial', 24)

# Load sounds
try:
    shotgun_sound = mixer.Sound("shotgun.wav")
    pistol_sound = mixer.Sound("pistol.wav") 
    bfg_sound = mixer.Sound("bfg.wav")
    pain_sound = mixer.Sound("pain.wav")
    death_sound = mixer.Sound("death.wav")
    pickup_sound = mixer.Sound("pickup.wav")
    door_sound = mixer.Sound("door.wav")
except:
    # Create placeholder sounds if files not found
    shotgun_sound = mixer.Sound(buffer=bytes([128] * 2048))
    pistol_sound = mixer.Sound(buffer=bytes([128] * 1024))
    bfg_sound = mixer.Sound(buffer=bytes([128] * 4096))
    pain_sound = mixer.Sound(buffer=bytes([128] * 1024))
    death_sound = mixer.Sound(buffer=bytes([128] * 2048))
    pickup_sound = mixer.Sound(buffer=bytes([128] * 512))
    door_sound = mixer.Sound(buffer=bytes([128] * 1024))

# Player setup
player_x = TILE_SIZE * 1.5
player_y = TILE_SIZE * 1.5
player_angle = 0
player_speed = 3
rotation_speed = 3
player_health = 100
player_max_health = 100
pistol_ammo = 50
shotgun_ammo = 20
bfg_ammo = 5
current_weapon = "pistol"
is_firing = False
firing_frame = 0
door_opening = {}  # Track doors that are opening/closing

# Enemy setup
class Enemy:
    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.angle = 0
        self.speed = 1
        self.state = "idle"  # idle, chase, attack
        self.attack_cooldown = 0
        self.hit_cooldown = 0
        self.dead = False
        
    def update(self, player_x, player_y):
        if self.dead:
            return
            
        # Calculate distance to player
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Calculate angle to player
        self.angle = math.degrees(math.atan2(dy, dx))
        
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
            return
            
        # State machine
        if distance < TILE_SIZE * 1.5:
            self.state = "attack"
            if self.attack_cooldown <= 0:
                # Attack player
                self.attack_cooldown = 60  # Attack once per second
                return True
            else:
                self.attack_cooldown -= 1
        elif distance < TILE_SIZE * 8:
            self.state = "chase"
            # Move towards player if not blocked by wall
            move_x = self.x + math.cos(math.radians(self.angle)) * self.speed
            move_y = self.y + math.sin(math.radians(self.angle)) * self.speed
            if not is_wall(move_x, move_y):
                self.x = move_x
                self.y = move_y
        else:
            self.state = "idle"
            
        return False
        
    def take_damage(self, damage):
        if self.dead:
            return False
            
        self.health -= damage
        self.hit_cooldown = 5  # Short invulnerability
        
        if self.health <= 0:
            self.dead = True
            try:
                death_sound.play()
            except:
                pass
            return True
        else:
            try:
                pain_sound.play()
            except:
                pass
            return False

# Create enemies
enemies = [
    Enemy(TILE_SIZE * 8.5, TILE_SIZE * 2.5),
    Enemy(TILE_SIZE * 14.5, TILE_SIZE * 8.5),
    Enemy(TILE_SIZE * 12.5, TILE_SIZE * 13.5),
    Enemy(TILE_SIZE * 3.5, TILE_SIZE * 9.5),
    Enemy(TILE_SIZE * 9.5, TILE_SIZE * 14.5)
]

# Convert angle to radians
def to_radians(degrees):
    return degrees * math.pi / 180

# Check if a point is inside a wall
def is_wall(x, y):
    map_x = int(x // TILE_SIZE)
    map_y = int(y // TILE_SIZE)
    if 0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP):
        return MAP[map_y][map_x] in [1, 2]  # Wall or closed door
    return True  # Assume out of bounds is a wall

# Check what's at a specific map position
def get_map_item(x, y):
    map_x = int(x // TILE_SIZE)
    map_y = int(y // TILE_SIZE)
    if 0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP):
        return MAP[map_y][map_x]
    return 1  # Wall by default if out of bounds

# Set map item at a position
def set_map_item(x, y, item):
    map_x = int(x // TILE_SIZE)
    map_y = int(y // TILE_SIZE)
    if 0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP):
        MAP[map_y][map_x] = item

# Raycasting function
def cast_ray(angle):
    # Ensure angle is between 0 and 360
    angle %= 360
    
    # Convert angle to radians
    angle_rad = to_radians(angle)
    
    # Get direction vectors
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Initialize variables for the smallest distance
    min_distance = float('inf')
    hit_type = None
    texture_offset = 0
    map_coords = (0, 0)
    
    # Handle horizontal intersections (east-west walls)
    if abs(sin_a) > 0.0001:
        # Determine the first horizontal grid intersection
        if sin_a > 0:  # Looking down
            y_hor = math.floor(player_y / TILE_SIZE) * TILE_SIZE + TILE_SIZE
            dy = TILE_SIZE
        else:  # Looking up
            y_hor = math.floor(player_y / TILE_SIZE) * TILE_SIZE
            dy = -TILE_SIZE
        
        # Calculate the x-component step size
        dx = dy / math.tan(angle_rad)
        
        # Calculate the first intersection point
        x_hor = player_x + (y_hor - player_y) / sin_a * cos_a
        
        # Step through the grid and check for wall hits
        for _ in range(100):  # Limit iterations to prevent infinite loop
            map_x, map_y = int(x_hor // TILE_SIZE), int(y_hor // TILE_SIZE)
            
            # Check if we're out of bounds or hit a wall
            if not (0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP)):
                break
            
            map_item = MAP[map_y][map_x]
            if map_item in [1, 2]:  # Wall or door
                # Calculate distance to intersection
                dist = math.sqrt((x_hor - player_x) ** 2 + (y_hor - player_y) ** 2)
                if dist < min_distance:
                    min_distance = dist
                    hit_type = 'h'
                    texture_offset = int(x_hor % TILE_SIZE)
                    map_coords = (map_x, map_y)
                break
            
            # Move to next intersection
            x_hor += dx
            y_hor += dy
    
    # Handle vertical intersections (north-south walls)
    if abs(cos_a) > 0.0001:
        # Determine the first vertical grid intersection
        if cos_a > 0:  # Looking right
            x_vert = math.floor(player_x / TILE_SIZE) * TILE_SIZE + TILE_SIZE
            dx = TILE_SIZE
        else:  # Looking left
            x_vert = math.floor(player_x / TILE_SIZE) * TILE_SIZE
            dx = -TILE_SIZE
        
        # Calculate the y-component step size
        dy = dx * math.tan(angle_rad)
        
        # Calculate the first intersection point
        y_vert = player_y + (x_vert - player_x) * math.tan(angle_rad)
        
        # Step through the grid and check for wall hits
        for _ in range(100):  # Limit iterations to prevent infinite loop
            map_x, map_y = int(x_vert // TILE_SIZE), int(y_vert // TILE_SIZE)
            
            # Check if we're out of bounds or hit a wall
            if not (0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP)):
                break
            
            map_item = MAP[map_y][map_x]
            if map_item in [1, 2]:  # Wall or door
                # Calculate distance to intersection
                dist = math.sqrt((x_vert - player_x) ** 2 + (y_vert - player_y) ** 2)
                if dist < min_distance:
                    min_distance = dist
                    hit_type = 'v'
                    texture_offset = int(y_vert % TILE_SIZE)
                    map_coords = (map_x, map_y)
                break
            
            # Move to next intersection
            x_vert += dx
            y_vert += dy
    
    # Return the closest intersection
    if min_distance == float('inf'):
        # No wall was hit, return a default value
        return MAX_DEPTH, 'v', 0, (0, 0)
    
    return min_distance, hit_type, texture_offset, map_coords

# Find visible enemies
def find_visible_enemies(fov_start, fov_end):
    visible = []
    
    for i, enemy in enumerate(enemies):
        if enemy.dead:
            continue
            
        # Calculate angle and distance to enemy
        dx = enemy.x - player_x
        dy = enemy.y - player_y
        angle = math.degrees(math.atan2(dy, dx)) % 360
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if enemy is in player's FOV
        rel_angle = (angle - player_angle) % 360
        if rel_angle > 180:
            rel_angle -= 360
            
        if abs(rel_angle) <= HALF_FOV:
            # Check if enemy is not behind a wall
            ray_dist, _, _, _ = cast_ray(angle)
            if distance < ray_dist:
                sprite_size = min(int(HEIGHT / distance * TILE_SIZE), HEIGHT * 2)
                # Calculate position on screen
                sprite_x = int(rel_angle / FOV * WIDTH + WIDTH / 2 - sprite_size / 2)
                visible.append((distance, sprite_size, sprite_x, i))
    
    # Sort by distance (farther sprites drawn first)
    visible.sort(reverse=True)
    return visible

# Handle player firing weapon
def player_fire():
    global is_firing, firing_frame, pistol_ammo, shotgun_ammo, bfg_ammo
    
    # Check ammo
    if current_weapon == "pistol" and pistol_ammo <= 0:
        return False
    elif current_weapon == "shotgun" and shotgun_ammo <= 0:
        return False
    elif current_weapon == "bfg" and bfg_ammo <= 0:
        return False
    
    # Set firing animation
    is_firing = True
    firing_frame = 5
    
    # Play sound
    if current_weapon == "pistol":
        pistol_ammo -= 1
        try:
            pistol_sound.play()
        except:
            pass
    elif current_weapon == "shotgun":
        shotgun_ammo -= 1
        try:
            shotgun_sound.play()
        except:
            pass
    elif current_weapon == "bfg":
        bfg_ammo -= 1
        try:
            bfg_sound.play()
        except:
            pass
    
    # Calculate damage
    if current_weapon == "pistol":
        damage = 20
        spread = 5  # Degrees
    elif current_weapon == "shotgun":
        damage = 15  # per pellet
        spread = 15  # Degrees
    else:  # BFG
        damage = 100
        spread = 30  # Degrees
    
    # Fire weapon
    hit_enemy = False
    if current_weapon == "shotgun":
        # Shotgun fires multiple pellets
        for _ in range(8):
            spray_angle = player_angle + random.uniform(-spread, spread)
            hit_enemy = hit_enemy or fire_projectile(spray_angle, damage // 2)
    elif current_weapon == "bfg":
        # BFG hits all enemies in cone
        for enemy in enemies:
            if enemy.dead:
                continue
                
            dx = enemy.x - player_x
            dy = enemy.y - player_y
            angle = math.degrees(math.atan2(dy, dx))
            rel_angle = (angle - player_angle) % 360
            if rel_angle > 180:
                rel_angle -= 360
                
            if abs(rel_angle) <= spread:
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < TILE_SIZE * 10:  # BFG range
                    killed = enemy.take_damage(damage)
                    if killed:
                        hit_enemy = True
    else:
        # Pistol fires single shot
        spray_angle = player_angle + random.uniform(-spread, spread)
        hit_enemy = fire_projectile(spray_angle, damage)
    
    return hit_enemy

# Fire a single projectile
def fire_projectile(angle, damage):
    ray_dist, _, _, coords = cast_ray(angle)
    
    for i, enemy in enumerate(enemies):
        if enemy.dead:
            continue
            
        # Calculate distance to enemy
        dx = enemy.x - player_x
        dy = enemy.y - player_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if enemy is hit
        enemy_angle = math.degrees(math.atan2(dy, dx))
        rel_angle = (enemy_angle - angle) % 360
        if rel_angle > 180:
            rel_angle -= 360
            
        if abs(rel_angle) < 5 and distance < ray_dist:
            # Hit! Calculate damage falloff with distance
            damage_dealt = max(damage * (1 - distance / (TILE_SIZE * 10)), damage / 2)
            killed = enemy.take_damage(int(damage_dealt))
            return killed
    
    return False

# Draw the 3D scene
def draw_scene():
    # Fill background with a sky and floor
    pygame.draw.rect(screen, (50, 50, 100), (0, 0, WIDTH, HALF_HEIGHT))
    pygame.draw.rect(screen, (50, 50, 50), (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

    # Prepare z-buffer for sprite rendering
    z_buffer = [float('inf')] * WIDTH

    # Cast rays and draw walls
    for i in range(RAY_COUNT):
        # Calculate ray angle
        ray_angle = player_angle - HALF_FOV + FOV * i / RAY_COUNT
        
        # Cast ray
        distance, hit_type, texture_offset, map_coords = cast_ray(ray_angle)
        
        # Store distance in z-buffer
        z_buffer[i] = distance
        
        # Fix fisheye effect
        correct_angle = to_radians(ray_angle - player_angle)
        distance = distance * math.cos(correct_angle)
        
        # Calculate wall height
        wall_height = min(int(HEIGHT / distance * TILE_SIZE), HEIGHT * 2) if distance > 0 else HEIGHT
        
        # Determine wall texture based on map item
        if map_coords[0] >= 0 and map_coords[1] >= 0:
            map_item = MAP[map_coords[1]][map_coords[0]]
            if map_item == 1:  # Wall
                texture = wall_texture
            elif map_item == 2:  # Door
                texture = door_texture
            else:
                texture = wall_texture
        else:
            texture = wall_texture
        
        # Get texture column
        if 0 <= texture_offset < TILE_SIZE:
            wall_column = texture.subsurface((texture_offset, 0, 1, TILE_SIZE))
            wall_column = pygame.transform.scale(wall_column, (int(SCALE), wall_height))
            
            if hit_type == 'v':
                # Apply shadow for vertical hits
                shadow = pygame.Surface(wall_column.get_size(), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 50))
                wall_column.blit(shadow, (0, 0))
        else:
            # Fallback color if texture_offset is out of range
            wall_column = pygame.Surface((int(SCALE), wall_height))
            wall_column.fill(BROWN if hit_type == 'h' else DARK_GRAY)
        
        # Draw the wall strip
        wall_pos = (int(i * SCALE), HALF_HEIGHT - wall_height // 2)
        screen.blit(wall_column, wall_pos)
    
    # Draw visible enemies
    visible_enemies = find_visible_enemies(player_angle - HALF_FOV, player_angle + HALF_FOV)
    for distance, size, x_pos, enemy_idx in visible_enemies:
        # Calculate sprite height based on distance
        enemy = enemies[enemy_idx]
        sprite = pygame.transform.scale(enemy_texture, (size, size))
        
        # Draw the sprite
        y_pos = HALF_HEIGHT - size // 2
        screen.blit(sprite, (x_pos, y_pos))
    
    # Draw items (health packs, ammo)
    for y, row in enumerate(MAP):
        for x, cell in enumerate(row):
            if cell in [3, 4]:  # Health pack or ammo
                # Calculate distance and angle to item
                item_x = (x + 0.5) * TILE_SIZE
                item_y = (y + 0.5) * TILE_SIZE
                dx = item_x - player_x
                dy = item_y - player_y
                item_dist = math.sqrt(dx*dx + dy*dy)
                item_angle = math.degrees(math.atan2(dy, dx)) % 360
                
                # Check if item is in player's FOV
                rel_angle = (item_angle - player_angle) % 360
                if rel_angle > 180:
                    rel_angle -= 360
                    
                if abs(rel_angle) <= HALF_FOV:
                    # Check if item is not behind a wall
                    ray_dist = z_buffer[int((rel_angle + HALF_FOV) / FOV * RAY_COUNT)]
                    if item_dist < ray_dist:
                        # Calculate item size based on distance
                        item_size = min(int(HEIGHT / item_dist * TILE_SIZE / 2), HEIGHT)
                        texture = health_texture if cell == 3 else ammo_texture
                        item_sprite = pygame.transform.scale(texture, (item_size, item_size))
                        
                        # Calculate position on screen
                        item_x_screen = int(WIDTH / 2 + rel_angle / FOV * WIDTH - item_size / 2)
                        item_y_screen = HALF_HEIGHT - item_size // 2
                        
                        # Draw the item
                        screen.blit(item_sprite, (item_x_screen, item_y_screen))

# Draw weapon
def draw_weapon():
    global is_firing, firing_frame
    
    if current_weapon == "pistol":
        weapon_img = pistol_image
        weapon_x = WIDTH // 2 - pistol_image.get_width() // 2
        weapon_y = HEIGHT - pistol_image.get_height() + 20
    elif current_weapon == "shotgun":
        weapon_img = shotgun_image
        weapon_x = WIDTH // 2 - shotgun_image.get_width() // 2
        weapon_y = HEIGHT - shotgun_image.get_height() + 20
    else:  # BFG
        weapon_img = bfg_image
        weapon_x = WIDTH // 2 - bfg_image.get_width() // 2
        weapon_y = HEIGHT - bfg_image.get_height() + 20
    
    # Apply firing animation
    if is_firing:
        weapon_y -= 10
        firing_frame -= 1
        if firing_frame <= 0:
            is_firing = False
        
        # Draw muzzle flash
        if firing_frame > 3:
            flash_x = WIDTH // 2
            flash_y = HEIGHT - weapon_img.get_height() // 2
            screen.blit(muzzle_flash, (flash_x - muzzle_flash.get_width() // 2, flash_y - muzzle_flash.get_height() // 2))
    
    # Draw weapon
    screen.blit(weapon_img, (weapon_x, weapon_y))

# Draw HUD
def draw_hud():
    # Health
    health_text = hud_font.render(f"Health: {player_health}", True, RED if player_health < 25 else WHITE)
    screen.blit(health_text, (10, HEIGHT - 70))
    
    # Ammo
    if current_weapon == "pistol":
        ammo_text = hud_font.render(f"Pistol: {pistol_ammo}", True, YELLOW if pistol_ammo < 10 else WHITE)
    elif current_weapon == "shotgun":
        ammo_text = hud_font.render(f"Shotgun: {shotgun_ammo}", True, YELLOW if shotgun_ammo < 5 else WHITE)
    else:
        ammo_text = hud_font.render(f"BFG: {bfg_ammo}", True, YELLOW if bfg_ammo < 2 else WHITE)
    screen.blit(ammo_text, (10, HEIGHT - 40))
    
    # Weapon selector
    weapons_text = hud_font.render("1:Pistol 2:Shotgun 3:BFG", True, WHITE)
    screen.blit(weapons_text, (WIDTH - 250, HEIGHT - 40))

def draw_minimap(player_x, player_y, player_angle):
    # Set minimap size and position
    map_size = 120
    tile_size = map_size / max(len(MAP[0]), len(MAP))
    map_pos = (WIDTH - map_size - 10, 10)
    
    # Create minimap surface
    minimap = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
    minimap.fill((0, 0, 0, 128))  # Semi-transparent background
    
    # Draw map tiles
    for y, row in enumerate(MAP):
        for x, tile in enumerate(row):
            if tile == 1:  # Wall
                color = BROWN
            elif tile == 2:  # Door
                color = (100, 50, 0)
            elif tile == 3:  # Health
                color = RED
            elif tile == 4:  # Ammo
                color = YELLOW
            else:  # Empty space
                color = DARK_GRAY
            
            rect = (x * tile_size, y * tile_size, tile_size, tile_size)
            pygame.draw.rect(minimap, color, rect)
    
    # Draw enemies on minimap
    for enemy in enemies:
        if not enemy.dead:
            ex = enemy.x / TILE_SIZE * tile_size
            ey = enemy.y / TILE_SIZE * tile_size
            pygame.draw.circle(minimap, RED, (int(ex), int(ey)), int(tile_size / 3))
    
    # Draw player on minimap
    px = player_x / TILE_SIZE * tile_size
    py = player_y / TILE_SIZE * tile_size
    pygame.draw.circle(minimap, GREEN, (int(px), int(py)), int(tile_size / 2))
    
    # Draw player direction
    dx = math.cos(to_radians(player_angle)) * tile_size
    dy = math.sin(to_radians(player_angle)) * tile_size
    pygame.draw.line(minimap, GREEN, (int(px), int(py)), (int(px + dx), int(py + dy)), 2)
    
    # Draw minimap on screen
    screen.blit(minimap, map_pos)

# Interact with map objects
def interact():
    global player_health, pistol_ammo, shotgun_ammo, bfg_ammo, door_opening
    
    # Check for door in front of player
    check_dist = TILE_SIZE * 1.5
    check_x = player_x + math.cos(to_radians(player_angle)) * check_dist
    check_y = player_y + math.sin(to_radians(player_angle)) * check_dist
    
    map_x = int(check_x // TILE_SIZE)
    map_y = int(check_y // TILE_SIZE)
    
    # Check if coordinates are valid
    if 0 <= map_x < len(MAP[0]) and 0 <= map_y < len(MAP):
        # Check for door
        if MAP[map_y][map_x] == 2:
            # Toggle door
            door_key = f"{map_x},{map_y}"
            door_opening[door_key] = 60  # Door animation frames
            try:
                door_sound.play()
            except:
                pass
    
    # Check for items at player position
    player_map_x = int(player_x // TILE_SIZE)
    player_map_y = int(player_y // TILE_SIZE)
    
    if 0 <= player_map_x < len(MAP[0]) and 0 <= player_map_y < len(MAP):
        map_item = MAP[player_map_y][player_map_x]
        
        if map_item == 3:  # Health pack
            player_health = min(player_max_health, player_health + 25)
            MAP[player_map_y][player_map_x] = 0  # Remove item
            try:
                pickup_sound.play()
            except:
                pass
        elif map_item == 4:  # Ammo
            pistol_ammo += 20
            shotgun_ammo += 5
            bfg_ammo += 1
            MAP[player_map_y][player_map_x] = 0  # Remove item
            try:
                pickup_sound.play()
            except:
                pass

# Update door animations
def update_doors():
    doors_to_remove = []
    
    for door_key, frames in door_opening.items():
        x, y = map(int, door_key.split(","))
        
        if frames > 0:
            frames -= 1
            door_opening[door_key] = frames
            
            if frames == 0:
                # Toggle door state
                if MAP[y][x] == 2:  # If door is closed
                    MAP[y][x] = 0  # Open it
                else:  # If door is open
                    MAP[y][x] = 2  # Close it
                doors_to_remove.append(door_key)
    
    # Remove completed door animations
    for door_key in doors_to_remove:
        del door_opening[door_key]

# Game over screen
def game_over():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((200, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    font = pygame.font.SysFont('Arial', 48)
    text = font.render("GAME OVER", True, RED)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    
    restart_text = hud_font.render("Press R to restart", True, WHITE)
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return restart_game()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    
    return False

# Restart game
def restart_game():
    global player_x, player_y, player_angle, player_health, pistol_ammo, shotgun_ammo, bfg_ammo
    global current_weapon, is_firing, firing_frame, door_opening, enemies
    
    # Reset player
    player_x = TILE_SIZE * 1.5
    player_y = TILE_SIZE * 1.5
    player_angle = 0
    player_health = 100
    pistol_ammo = 50
    shotgun_ammo = 20
    bfg_ammo = 5
    current_weapon = "pistol"
    is_firing = False
    firing_frame = 0
    
    # Reset doors
    door_opening = {}
    
    # Reset enemies
    enemies = [
        Enemy(TILE_SIZE * 8.5, TILE_SIZE * 2.5),
        Enemy(TILE_SIZE * 14.5, TILE_SIZE * 8.5),
        Enemy(TILE_SIZE * 12.5, TILE_SIZE * 13.5),
        Enemy(TILE_SIZE * 3.5, TILE_SIZE * 9.5),
        Enemy(TILE_SIZE * 9.5, TILE_SIZE * 14.5)
    ]
    
    # Reset map items
    # Restore health packs and ammo
    for y in range(len(MAP)):
        for x in range(len(MAP[0])):
            if MAP[y][x] == 0:  # Check if it's an empty space now
                # Check original map for items
                if (x, y) in [(4, 2), (13, 2), (2, 12)]:  # Health pack positions
                    MAP[y][x] = 3
                elif (x, y) in [(12, 7), (11, 9)]:  # Ammo positions
                    MAP[y][x] = 4
    
    return True

def draw_pause_menu():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    pause_font = pygame.font.SysFont('Arial', 48)
    pause_text = pause_font.render("PAUSED", True, WHITE)
    
    controls_font = pygame.font.SysFont('Arial', 24)
    resume_text = controls_font.render("Press ESC to resume", True, WHITE)
    exit_text = controls_font.render("Press Ctrl+Q to quit", True, WHITE)
    
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 3))
    screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2))
    screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, HEIGHT // 2 + 40))

# Main game loop
def main_game():
    global player_x, player_y, player_angle, player_health, current_weapon, player_speed
    running = True
    paused = False
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    current_weapon = "pistol"
                elif event.key == pygame.K_2:
                    current_weapon = "shotgun"
                elif event.key == pygame.K_3:
                    current_weapon = "bfg"
                elif event.key == pygame.K_e:
                    interact()
                elif event.key == pygame.K_LSHIFT:
                    player_speed = 6  # Sprint
                elif event.key == pygame.K_ESCAPE:
                    # Toggle pause
                    paused = not paused
                elif event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Exit with Ctrl+Q
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    player_speed = 3  # Normal speed
            elif event.type == pygame.MOUSEBUTTONDOWN and not paused:
                if event.button == 1:  # Left mouse button
                    player_fire()
        
        # If game is paused, display pause menu and skip game update
        if paused:
            draw_pause_menu()
            pygame.display.flip()
            clock.tick(60)
            continue
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Move player
        if keys[pygame.K_w]:
            dx = math.cos(to_radians(player_angle)) * player_speed
            dy = math.sin(to_radians(player_angle)) * player_speed
            if not is_wall(player_x + dx, player_y):
                player_x += dx
            if not is_wall(player_x, player_y + dy):
                player_y += dy
        if keys[pygame.K_s]:
            dx = math.cos(to_radians(player_angle)) * player_speed
            dy = math.sin(to_radians(player_angle)) * player_speed
            if not is_wall(player_x - dx, player_y):
                player_x -= dx
            if not is_wall(player_x, player_y - dy):
                player_y -= dy
        if keys[pygame.K_a]:
            strafe_angle = (player_angle - 90) % 360
            dx = math.cos(to_radians(strafe_angle)) * player_speed
            dy = math.sin(to_radians(strafe_angle)) * player_speed
            if not is_wall(player_x + dx, player_y):
                player_x += dx
            if not is_wall(player_x, player_y + dy):
                player_y += dy
        if keys[pygame.K_d]:
            strafe_angle = (player_angle + 90) % 360
            dx = math.cos(to_radians(strafe_angle)) * player_speed
            dy = math.sin(to_radians(strafe_angle)) * player_speed
            if not is_wall(player_x + dx, player_y):
                player_x += dx
            if not is_wall(player_x, player_y + dy):
                player_y += dy
        
        # Rotate player
        if keys[pygame.K_LEFT]:
            player_angle = (player_angle - rotation_speed) % 360
        if keys[pygame.K_RIGHT]:
            player_angle = (player_angle + rotation_speed) % 360
        
        # Mouse look
        if pygame.mouse.get_focused():
            mouse_rel = pygame.mouse.get_rel()
            player_angle = (player_angle + mouse_rel[0] * 0.2) % 360
            pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
        
        # Update doors
        update_doors()
        
        # Update enemies and check for attacks
        for enemy in enemies:
            player_hit = enemy.update(player_x, player_y)
            if player_hit:
                player_health -= 10
                try:
                    pain_sound.play()
                except:
                    pass
        
        # Check player health
        if player_health <= 0:
            if not game_over():
                running = False
        
        # Draw everything
        screen.fill(BLACK)
        draw_scene()
        draw_weapon()
        draw_hud()
        draw_minimap(player_x, player_y, player_angle)
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)

# Start the game
def start_menu():
    menu_font = pygame.font.SysFont('Arial', 48)
    title_text = menu_font.render("DOOM CLONE", True, RED)
    
    start_font = pygame.font.SysFont('Arial', 24)
    start_text = start_font.render("Press ENTER to start", True, WHITE)
    controls_text = start_font.render("WASD - Move, Mouse - Look, Left Click - Shoot", True, WHITE)
    controls_text2 = start_font.render("E - Interact, 1/2/3 - Change Weapons", True, WHITE)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Draw menu
        screen.fill(BLACK)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))
        screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(controls_text2, (WIDTH // 2 - controls_text2.get_width() // 2, HEIGHT // 2 + 80))
        
        pygame.display.flip()
        clock.tick(60)
    
    return False

# Set mouse to center and hide cursor
pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
pygame.mouse.set_visible(False)

# Run the game
if start_menu():
    main_game()

# Quit pygame
pygame.quit()
sys.exit()