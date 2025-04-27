import datetime
# modules/bolbu_enemy.py
"""
Neue Gegnerklasse BolbuEnemy + BolbuProjectile
Autor: ChatGPT   Datum: {}
Pfad: modules/bolbu_enemy.py

Dieses Modul integriert eine neue Gegner‑KI „Bolbu“ in Dark‑Snake.  
Bolbu kann:
* sein eigenes Projektil schießen (BolbuProjectile)
* alle {:.1f}s einen Würfel (1‑6) werfen, um Spezialaktionen auszulösen
* Animation aus 6 PNG‑Frames nutzen (1bolbugeg.png … 6bolbugeg.png)

Benötigte Assets:  
assets/graphics/bolbugeg1/1bolbugeg.png … 6bolbugeg.png  
assets/graphics/projectiles/bolbu_projectile.png
""".format(datetime.date.today(), 2.5)
import pygame, random, time, math, datetime

from pygame.math import Vector2

from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, PROJECTILE_SPEED_FACTOR
from modules.enemies import NormalEnemy
from modules.graphics import load_image
from modules.audio import SOUNDS

class BolbuProjectile:
    """Eigenes Projektil für BolbuEnemy."""
    def __init__(self, x_grid, y_grid, direction, speed_mul=1.2, damage=2, lifetime=240):
        self.pos = Vector2(x_grid, y_grid)
        self.direction = Vector2(direction).normalize()
        self.speed = PROJECTILE_SPEED_FACTOR * speed_mul
        self.damage = damage
        self.lifetime = lifetime
        self.image = load_image("bolbu_projectile.png", "projectiles")
        size = int(GRID_SIZE * 1.2)
        if self.image:
            self.image = pygame.transform.scale(self.image, (size, size))
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, size, size)

    def update(self):
        self.pos.x += self.direction.x * self.speed
        self.pos.y += self.direction.y * self.speed
        self.lifetime -= 1
        self.rect.topleft = (self.pos.x * GRID_SIZE, self.pos.y * GRID_SIZE)
        return 0 < self.lifetime and 0 <= self.pos.x < GRID_WIDTH and 0 <= self.pos.y < GRID_HEIGHT

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, (0, 200, 255), self.rect)

class BolbuEnemy(NormalEnemy):
    """Erweiterter normaler Gegner mit Würfel‑Logik und Projektilen."""
    SHOOT_COOLDOWN = 2.5
    DICE_COOLDOWN = 5

    def __init__(self):
        super().__init__()
        self.frames = [load_image(f"bolbugeg1/{i}bolbugeg.png") for i in range(1,7)]
        self.anim_index = 0
        if self.frames[0]:
            self.frames = [pygame.transform.scale(f, (GRID_SIZE, GRID_SIZE)) for f in self.frames]
            self.image = self.frames[0]
        self.anim_timer = time.time()
        self.projectiles = []
        self.last_shot = time.time()
        self.last_dice = time.time()

    # ------------------------------------------------------------
    # KI  – Bewegungs‑Update + Angriffs‑/Würfel‑Mechanik
    # ------------------------------------------------------------
    def update(self, player_x=None, player_y=None):
        super().update(player_x, player_y)

        now = time.time()

        # kleine Animation
        if now - self.anim_timer >= 0.15:
            self.anim_index = (self.anim_index + 1) % len(self.frames)
            self.image = self.frames[self.anim_index]
            self.anim_timer = now

        # Projektil‑Beschuss
        if now - self.last_shot >= self.SHOOT_COOLDOWN:
            self.shoot_projectile(player_x, player_y)
            self.last_shot = now

        # Würfel‑Event
        if now - self.last_dice >= self.DICE_COOLDOWN:
            self.roll_dice(player_x, player_y)
            self.last_dice = now

        # Update eigene Projektile
        self.projectiles = [p for p in self.projectiles if p.update()]

    # ------------------------------------------------------------
    # Attacken
    # ------------------------------------------------------------
    def shoot_projectile(self, target_x=None, target_y=None, angle_offset=0.0):
        if target_x is None or target_y is None:
            target_x = self.x
            target_y = self.y
        dx = target_x - self.x
        dy = target_y - self.y
        angle = math.atan2(dy, dx) + angle_offset
        dir_vec = (math.cos(angle), math.sin(angle))
        self.projectiles.append(BolbuProjectile(self.x, self.y, dir_vec))
        if SOUNDS.get("eat"):
            SOUNDS["eat"].play()

    def roll_dice(self, target_x=None, target_y=None):
        roll = random.randint(1,6)
        if roll == 6:
            # Geschwindigkeits‑Sprint
            self.sprint_active = True
            self.sprint_end_time = time.time() + 0.7
        elif roll in (4,5):
            # Dreifachschuss in Fächerform
            for offset in (-0.25, 0, 0.25):
                self.shoot_projectile(target_x, target_y, angle_offset=offset)
        else:
            # Einfachem Schuss
            self.shoot_projectile(target_x, target_y)

    # ------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------
    def draw(self, surface):
        super().draw(surface)
        for p in self.projectiles:
            p.draw(surface)

    # ------------------------------------------------------------
    # Zugriff für Game‑Loop (Collision)
    # ------------------------------------------------------------
    def get_projectile_rects(self):
        return [p.rect for p in self.projectiles]