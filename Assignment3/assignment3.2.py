
"""
=== MONSTER HUNTER ===

GAME OBJECTIVE:
Survive waves of monstrous creatures and defeat the colossal final boss to survive.

CONTROLS:
* LEFT/RIGHT ARROW KEYS: Move your hunter left or right
* UP ARROW KEY: Jump
* F KEY: Shoot
* R KEY: Restart after victory/defeat
* The game features a dynamic camera that follows the hunter, allowing continuous forward 
movement without restriction from the right-edge boundary.

GAME MECHANICS:
1. SURVIVAL SYSTEM:
* Start with 5 health points and 3 lives
* Monster contact: -2 health
* Boss projectiles: -1 health
* Diamond: Restore +1 health
* Health Potion: Restore +1 life

2. SCORING:
* Small monsters: 5 points
* Elite monsters: 5 points
* Boss hits: 10 points
* Boss defeat: 100 points
* Score Prop: +10 points

3. LEVEL PROGRESSION:
* LEVEL 1: Reach 100 points (basic monsters)
* LEVEL 2: Reach 200 points (enhanced monsters)
* Final LEVEL: Defeat Alpha Beast (Boss)

4. POWER-UPS:
* Diamond: Restore vitality
* Health Potion: Extra revival chance
* Score Prop: Boost score

5. SURVIVAL TIPS:
* Keep moving to avoid mobs
* Prioritize eliminating elite monsters
* Collect power-ups when wounded
* The Alpha Beast requires sustained fire at weak points
* Jump to advoid mobs and boss' bullets

"""

import pygame
import random
import math
from pathlib import Path

pygame.init()

# --- Constants ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 550
WORLD_WIDTH = 2700  # Extended world width for camera
FPS = 60
GROUND_HEIGHT = SCREEN_HEIGHT - 50

# Level score thresholds
LEVEL1_SCORE = 100
LEVEL2_SCORE = 200
LEVEL3_SCORE = 400

# --- Setup screen BEFORE loading images ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Monster Hunter")
clock = pygame.time.Clock()

# Assets directory
ASSETS = Path(__file__).parent / "Assets"

# Load image helper
def load_img(name, scale=None):
    img = pygame.image.load(ASSETS / name).convert_alpha()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img

# Load sounds helper 
def load_sound(name):
    return pygame.mixer.Sound(str(ASSETS / name))

# --- Load images ---
BG_LEVELS = [
    load_img("bg_level1.png", (SCREEN_WIDTH, SCREEN_HEIGHT)),  # Original size, will tile
    load_img("bg_level2.png", (SCREEN_WIDTH, SCREEN_HEIGHT)),
    load_img("bg_level3.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
]

PLAYER_IMG = load_img("player.png", (100, 100))
ENEMY_IMG = load_img("enemy.png", (120, 120))
ADV_ENEMY_IMG = load_img("advanced_enemy.png", (100, 100))
BULLET_IMG = load_img("bullet.png", (15, 7))
BOSS_IMG = load_img("boss.png", (200, 200))
COLLECT_HEALTH_IMG = load_img("collect_health.png", (40, 40))
COLLECT_LIFE_IMG = load_img("collect_life.png", (40, 40))
COLLECT_SCORE_IMG = load_img("collect_score.png", (40, 40))

# --- Load sounds ---
SHOOT_SOUND = load_sound("shoot.wav")
HIT_SOUND = load_sound("player_hit.wav")
ENEMY_HIT_SOUND = load_sound("enemy_hit.wav")
COLLECT_SOUND = load_sound("collect.wav")
JUMP_SOUND = load_sound("jump.mp3")
pygame.mixer.music.load(str(ASSETS / "bg_music.mp3"))
pygame.mixer.music.play(-1)

# --- Camera Class ---
class Camera:
    def __init__(self):
        self.offset_x = 0
        self.lerp_speed = 0.1  # Smoothness of camera movement

    def update(self, player_rect):
        # Target camera to center player on screen
        target_x = player_rect.centerx - SCREEN_WIDTH // 2
        # Smoothly interpolate to target
        self.offset_x += (target_x - self.offset_x) * self.lerp_speed
        # Clamp offset to keep world within bounds
        self.offset_x = max(0, min(self.offset_x, WORLD_WIDTH - SCREEN_WIDTH))

    def apply(self, rect):
        # Apply camera offset to sprite positions
        return rect.move(-self.offset_x, 0)

    def draw_background(self, surface, bg_image):
        # Tile background to cover world width
        x = -self.offset_x % SCREEN_WIDTH
        for i in range(-1, int(WORLD_WIDTH / SCREEN_WIDTH) + 1):
            surface.blit(bg_image, (x + i * SCREEN_WIDTH, 0))

# --- Game Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = PLAYER_IMG
        self.rect = self.image.get_rect(midbottom=(100, GROUND_HEIGHT))
        self.speed = 5
        self.max_health = 5
        self.health = self.max_health
        self.max_lives = 3
        self.lives = self.max_lives
        self.score = 0
        
        # Jumping properties
        self.jumping = False
        self.jump_height = 18
        self.gravity = 0.8
        self.jump_velocity = 0
        self.on_ground = True

    def update(self, keys):
        # Horizontal movement controls
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WORLD_WIDTH:
            self.rect.x += self.speed
        
        # Jumping control
        if keys[pygame.K_UP] and self.on_ground:
            self.jump()
        
        # Apply gravity and jumping physics
        if self.jumping:
            self.rect.y -= self.jump_velocity
            self.jump_velocity -= self.gravity
            
            # Check if landed
            if self.rect.bottom >= GROUND_HEIGHT:
                self.rect.bottom = GROUND_HEIGHT
                self.jumping = False
                self.on_ground = True
                self.jump_velocity = 0

    def jump(self):
        if self.on_ground:
            self.jumping = True
            self.on_ground = False
            self.jump_velocity = self.jump_height
            JUMP_SOUND.play()

    def draw_health_bar(self, surface, camera):
        # Draw health bar above player with camera offset
        bar_width = 70
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.centerx - bar_width//2, self.rect.top - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.centerx - bar_width//2, self.rect.top - 10, fill, bar_height)
        outline_rect = camera.apply(outline_rect)
        fill_rect = camera.apply(fill_rect)
        pygame.draw.rect(surface, (255,0,0), fill_rect)
        pygame.draw.rect(surface, (255,255,255), outline_rect, 1)

class BossBullet(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=pos)
        self.speed = 7
        self.direction = -1  # Move left

    def update(self):
        self.rect.x += self.direction * self.speed
        if self.rect.right < camera.offset_x:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, camera_offset):
        super().__init__()
        self.image = BOSS_IMG
        self.rect = self.image.get_rect(midbottom=(camera_offset + SCREEN_WIDTH + 50, GROUND_HEIGHT))  # x=offset_x+950
        self.max_health = 500
        self.health = self.max_health
        self.speed = 2
        self.move_direction = 1
        
        # Boss jumping properties
        self.jumping = False
        self.jump_height = 8
        self.gravity = 0.6
        self.jump_velocity = 0
        self.on_ground = True
        self.jump_timer = 0
        
        self.shoot_timer = 0
        self.bullets = pygame.sprite.Group()

    def update(self):
        # Horizontal movement
        if self.rect.left > camera.offset_x + SCREEN_WIDTH - 200:  # Move to x=offset_x+700
            self.rect.x -= self.speed
        
        # Boss jumping logic
        self.jump_timer += 1
        if self.jump_timer >= 90 and self.on_ground:
            self.jump()
            self.jump_timer = 0
        
        # Apply gravity and jumping physics
        if self.jumping:
            self.rect.y -= self.jump_velocity
            self.jump_velocity -= self.gravity
            
            if self.rect.bottom >= GROUND_HEIGHT:
                self.rect.bottom = GROUND_HEIGHT
                self.jumping = False
                self.on_ground = True
                self.jump_velocity = 0

    def jump(self):
        if self.on_ground:
            self.jumping = True
            self.on_ground = False
            self.jump_velocity = self.jump_height

    def shoot(self):
        for i in range(-1, 2):
            bullet = BossBullet((self.rect.left, self.rect.bottom - 50 + i*10))
            self.bullets.add(bullet)

    def draw_health_bar(self, surface):
        # Draw health bar in fixed screen position (right-top corner)
        bar_width = 200
        bar_height = 15
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(SCREEN_WIDTH - bar_width - 10, 10, bar_width, bar_height)
        fill_rect = pygame.Rect(SCREEN_WIDTH - bar_width - 10, 10, fill, bar_height)
        pygame.draw.rect(surface, (0,255,0), fill_rect)
        pygame.draw.rect(surface, (255,255,255), outline_rect, 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, camera_offset):
        super().__init__()
        self.image = ENEMY_IMG
        self.rect = self.image.get_rect(midbottom=(camera_offset + SCREEN_WIDTH + random.randint(0, 100), GROUND_HEIGHT))
        self.speed = random.randint(5, 8)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < camera.offset_x:
            self.kill()

class AdvancedEnemy(pygame.sprite.Sprite):
    def __init__(self, camera_offset):
        super().__init__()
        self.image = ADV_ENEMY_IMG
        self.rect = self.image.get_rect(midbottom=(camera_offset + SCREEN_WIDTH + random.randint(0, 100), GROUND_HEIGHT))
        self.speed = random.randint(8, 12)
        # Health properties
        self.max_health = 2
        self.health = self.max_health
        # Jumping properties
        self.jumping = False
        self.jump_height = 15  # ~140.6 pixels to dodge bullets
        self.gravity = 0.8
        self.jump_velocity = 0
        self.on_ground = True
        self.jump_timer = random.randint(30, 60)

    def update(self):
        # Horizontal movement during jumping and on ground
        self.rect.x -= self.speed
        
        # Jumping logic
        self.jump_timer += 1
        if self.jump_timer >= 60 and self.on_ground:  # Jump every 1 second
            self.jump()
            self.jump_timer = 0
        
        # Apply gravity and jumping physics
        if self.jumping:
            self.rect.y -= self.jump_velocity
            self.jump_velocity -= self.gravity
            
            if self.rect.bottom >= GROUND_HEIGHT:
                self.rect.bottom = GROUND_HEIGHT
                self.jumping = False
                self.on_ground = True
                self.jump_velocity = 0
                self.jump_timer = random.randint(30, 60)

        if self.rect.right < camera.offset_x:
            self.kill()

    def jump(self):
        if self.on_ground:
            self.jumping = True
            self.on_ground = False
            self.jump_velocity = self.jump_height

    def draw_health_bar(self, surface, camera):
        # Draw health bar above enemy
        bar_width = 50
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.centerx - bar_width//2, self.rect.top - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.centerx - bar_width//2, self.rect.top - 10, fill, bar_height)
        outline_rect = camera.apply(outline_rect)
        fill_rect = camera.apply(fill_rect)
        pygame.draw.rect(surface, (255,0,0), fill_rect)
        pygame.draw.rect(surface, (255,255,255), outline_rect, 1)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = BULLET_IMG
        self.rect = self.image.get_rect(center=pos)
        self.speed = 10

    def update(self):
        self.rect.x += self.speed
        if self.rect.left > camera.offset_x + SCREEN_WIDTH:
            self.kill()

class Collectible(pygame.sprite.Sprite):
    def __init__(self, camera_offset, kind):
        super().__init__()
        self.kind = kind
        if kind == 'health':
            self.image = COLLECT_HEALTH_IMG
        elif kind == 'life':
            self.image = COLLECT_LIFE_IMG
        else:
            self.image = COLLECT_SCORE_IMG
        
        # Position collectibles at jumpable heights
        max_jump_height = 200
        min_height = GROUND_HEIGHT - max_jump_height
        max_height = GROUND_HEIGHT - 80
        self.rect = self.image.get_rect(midbottom=(camera_offset + SCREEN_WIDTH + random.randint(0, 100), random.randint(min_height, max_height)))
        self.speed = 4

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < camera.offset_x:
            self.kill()

# --- Game Groups ---
player = Player()
player_group = pygame.sprite.GroupSingle(player)
enemy_group = pygame.sprite.Group()
advanced_enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
collectibles = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

# --- Camera ---
camera = Camera()

# --- Game Variables ---
spawn_timer = 0
collect_timer = 0
boss_spawned = False
level = 0
level_cleared = False
game_over = False
win_message_timer = 0
game_timer = 0  # Track game time for guide message
player_idle_timer = 0  # Track player idle time

# Font for UI and messages
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 50)

# --- Functions for showing messages ---
def show_message(text, duration=180):
    global win_message_timer, win_message
    win_message = big_font.render(text, True, (255, 255, 255))
    win_message_timer = duration

# --- Game Loop ---
running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f and not level_cleared and not game_over:
                bullet = Bullet(player.rect.midright)
                bullet_group.add(bullet)
                SHOOT_SOUND.play()

            if event.key == pygame.K_r and (level_cleared or game_over):
                player.health = player.max_health
                player.lives = player.max_lives
                player.score = 0
                level = 0
                level_cleared = False
                game_over = False
                boss_spawned = False
                enemy_group.empty()
                advanced_enemy_group.empty()
                bullet_group.empty()
                collectibles.empty()
                boss_group.empty()
                boss_bullets.empty()
                player.rect.midbottom = (100, GROUND_HEIGHT)
                camera.offset_x = 0  # Reset camera
                game_timer = 0
                player_idle_timer = 0
                spawn_timer = 0
                collect_timer = 0
                show_message("")

    # Track game time and player idle
    if not game_over and not level_cleared:
        game_timer += 1
        if not keys[pygame.K_RIGHT] and player.rect.right < 150:
            player_idle_timer += 1
        else:
            player_idle_timer = 0

    # Only update game if not game over and not level cleared
    if not game_over and not level_cleared:
        spawn_timer += 1
        if level < 2:  # Stop collectibles in level 3 after victory
            collect_timer += 1

        if level == 0:
            if spawn_timer > 30:  # 0.5 seconds
                enemy_group.add(Enemy(camera.offset_x))
                spawn_timer = 0
        elif level == 1:
            if spawn_timer > 50:
                advanced_enemy_group.add(AdvancedEnemy(camera.offset_x))
                spawn_timer = 0
        elif level == 2:
            if spawn_timer > 50:
                advanced_enemy_group.add(AdvancedEnemy(camera.offset_x))
                spawn_timer = 0

        if collect_timer > 300 and (not level_cleared or level < 2):
            collect_timer = 0
            spawned_collectibles = 0
            if player.lives < player.max_lives:
                collectibles.add(Collectible(camera.offset_x, 'life'))
                spawned_collectibles += 1
            if player.health < player.max_health and spawned_collectibles < 2:
                count = random.randint(1, 2 - spawned_collectibles)
                for _ in range(count):
                    collectibles.add(Collectible(camera.offset_x, 'health'))
                    spawned_collectibles += 1
            while spawned_collectibles < 2:
                collectibles.add(Collectible(camera.offset_x, 'score'))
                spawned_collectibles += 1

    # --- Update Sprites ---
    player_group.update(keys)
    enemy_group.update()
    advanced_enemy_group.update()
    bullet_group.update()
    collectibles.update()
    boss_group.update()

    if boss_group:
        boss = boss_group.sprites()[0]
        boss.shoot_timer += 1
        if boss.shoot_timer >= 90:  # 1.5 seconds
            boss.shoot()
            boss.shoot_timer = 0
        boss.bullets.update()

    # Update camera
    camera.update(player.rect)

    # --- Collision Detection ---
    for bullet in bullet_group:
        hit_enemies = pygame.sprite.spritecollide(bullet, enemy_group, True)
        hit_adv_enemies = pygame.sprite.spritecollide(bullet, advanced_enemy_group, False)
        hit_boss = pygame.sprite.spritecollide(bullet, boss_group, False)
        if hit_enemies:
            bullet.kill()
            ENEMY_HIT_SOUND.play()
            player.score += 5
        if hit_adv_enemies:
            bullet.kill()
            ENEMY_HIT_SOUND.play()
            for enemy in hit_adv_enemies:
                enemy.health -= 1
                if enemy.health <= 0:
                    enemy.kill()
                    player.score += 5
        if hit_boss:
            bullet.kill()
            ENEMY_HIT_SOUND.play()
            boss = hit_boss[0]
            boss.health -= 20
            player.score += 10
            if boss.health <= 0:
                boss.kill()
                player.score += 100

    if player.on_ground:
        if pygame.sprite.spritecollide(player, enemy_group, True) or \
           pygame.sprite.spritecollide(player, advanced_enemy_group, True):
            player.health -= 2
            HIT_SOUND.play()  
            if player.health <= 0:
                player.lives -= 1
                player.health = player.max_health
                if player.lives <= 0:
                    game_over = True
                    show_message("Game Over! Press R to restart", 9999) 

    if not game_over and boss_group:
        for bullet in boss.bullets:
            if pygame.sprite.collide_rect(player, bullet):
                player.health -= 1
                HIT_SOUND.play()
                bullet.kill()
                if player.health <= 0:
                    player.lives -= 1
                    player.health = player.max_health
                    if player.lives <= 0:
                        game_over = True
                        show_message("Game Over! Press R to restart", 9999)

    hits = pygame.sprite.spritecollide(player, collectibles, True)
    for c in hits:
        COLLECT_SOUND.play()
        if c.kind == 'health' and player.health < player.max_health:
            player.health = min(player.max_health, player.health + 1)
        elif c.kind == 'life' and player.lives < player.max_lives:
            player.lives = min(player.max_lives, player.lives + 1)
        elif c.kind == 'score':
            player.score += 10

    # --- Level progression ---
    if not level_cleared and not game_over:
        if level == 0 and player.score >= LEVEL1_SCORE:
            level_cleared = True
            show_message("You win! Proceed to next level", 180)
        elif level == 1 and player.score >= LEVEL2_SCORE:
            level_cleared = True
            show_message("You win! Proceed to next level", 180)
        elif level == 2:
            if not boss_spawned:
                boss = Boss(camera.offset_x)
                boss_group.add(boss)
                boss_spawned = True
            if len(boss_group) == 0:
                level_cleared = True
                collectibles.empty()  # Clear collectibles on victory
                collect_timer = 0  # Reset to prevent new collectibles
                show_message("Congratulations! You won! Press R to restart", 9999)

    else:
        if level < 2:  # Only decrease timer for levels 1 and 2
            win_message_timer -= 1
            if win_message_timer <= 0:
                level += 1
                level_cleared = False
                boss_spawned = False
                enemy_group.empty()
                advanced_enemy_group.empty()
                bullet_group.empty()
                collectibles.empty()
                boss_group.empty()
                boss_bullets.empty()
                spawn_timer = 0
                collect_timer = 0
                show_message("")

    # --- Drawing ---
    camera.draw_background(screen, BG_LEVELS[min(level, 2)])
    
    if not game_over:
        for sprite in player_group:
            screen.blit(sprite.image, camera.apply(sprite.rect))
        for sprite in enemy_group:
            screen.blit(sprite.image, camera.apply(sprite.rect))
        for sprite in advanced_enemy_group:
            screen.blit(sprite.image, camera.apply(sprite.rect))
            sprite.draw_health_bar(screen, camera)
        for sprite in bullet_group:
            screen.blit(sprite.image, camera.apply(sprite.rect))
        for sprite in collectibles:
            screen.blit(sprite.image, camera.apply(sprite.rect))
        for sprite in boss_group:
            screen.blit(sprite.image, camera.apply(sprite.rect))
            sprite.draw_health_bar(screen)  # Fixed position
        if boss_group:
            for bullet in boss.bullets:
                screen.blit(bullet.image, camera.apply(bullet.rect))

    player.draw_health_bar(screen, camera)

    lives_text = font.render(f"Lives: {player.lives}", True, (255, 255, 255))
    score_text = font.render(f"Score: {player.score}", True, (255, 255, 255))
    level_text = font.render(f"Level: {level + 1}", True, (255, 255, 255))
    
    screen.blit(lives_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(level_text, (10, 70))
    
    controls_text = small_font.render("Controls: Left/Right move, Up jump, F shoot, R restart", True, (200, 200, 200))
    screen.blit(controls_text, (SCREEN_WIDTH - controls_text.get_width() - 10, SCREEN_HEIGHT - 30))

    # Show guide message
    if game_timer < 300 or player_idle_timer > 60:  # First 5 seconds or idle 1 second
        guide_text = small_font.render("Press RIGHT to proceed!", True, (255, 255, 255))
        guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(guide_text, guide_rect)

    if win_message_timer > 0:
        text_rect = win_message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(win_message, text_rect)

    pygame.display.flip()

pygame.quit()