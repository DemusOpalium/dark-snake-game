
# modules/boss_projectiles.py
# Enthält alle Boss-Projektilklassen für Dark Snake

import pygame
from modules.graphics import load_projectile_image
from modules.projectile_config import (
    BOSS_FLAME_DAMAGE, BOSS_FLAME_LIFETIME_TICKS, BOSS_FLAME_SPEED_PX_PER_TICK,
    BOSS_PROJECTILE_DAMAGE, BOSS_PROJECTILE_LIFETIME_TICKS,
    BOSS_PROJECTILE_SPEED_PX_PER_TICK,
)
from math import atan2, degrees


class _PreciseBossShot:
    """Keep fractional pixel movement; pygame.Rect coordinates are integers."""

    def _setup_motion(self):
        if self.speed and self.direction[0] == 0 and self.direction[1] == 0:
            # Direct callers must not spawn a forever-stationary projectile.
            self.direction = (1, 0)
        self._precise_x = float(self.rect.x)
        self._precise_y = float(self.rect.y)

    def _advance_motion(self):
        # Allow tests/external effects to reposition a rect intentionally.
        if (self.rect.x != round(self._precise_x)
                or self.rect.y != round(self._precise_y)):
            self._precise_x = float(self.rect.x)
            self._precise_y = float(self.rect.y)
        self._precise_x += self.speed * self.direction[0]
        self._precise_y += self.speed * self.direction[1]
        self.rect.x = round(self._precise_x)
        self.rect.y = round(self._precise_y)


class BossProjectile(_PreciseBossShot):
    """
    Allgemeines Boss-Projektil mit Richtung, Bild, Geschwindigkeit und optionaler Explosion.
    """
    def __init__(self, x, y, direction, speed=BOSS_PROJECTILE_SPEED_PX_PER_TICK,
                 damage=BOSS_PROJECTILE_DAMAGE, image_name="projectiles/bossprojectile1.png",
                 lifetime=BOSS_PROJECTILE_LIFETIME_TICKS):
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.from_boss = True

        self.image_orig = load_projectile_image(image_name)
        angle = degrees(atan2(-self.direction[1], self.direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self._setup_motion()

    def update(self):
        self._advance_motion()
        self.lifetime -= 1
        return self.lifetime > 0 and self.is_on_screen()

    def is_on_screen(self):
        screen_rect = pygame.Rect(0, 0, pygame.display.get_surface().get_width(), pygame.display.get_surface().get_height())
        return self.rect.colliderect(screen_rect)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def collides_with(self, target_rect):
        return self.rect.colliderect(target_rect)



class BossFlameProjectile(_PreciseBossShot):
    """
    Projektil speziell für den Boss – explodiert bei Treffer auf Spieler mit visuellem Effekt.
    """
    def __init__(self, x, y, direction, speed=BOSS_FLAME_SPEED_PX_PER_TICK,
                 damage=BOSS_FLAME_DAMAGE, lifetime=BOSS_FLAME_LIFETIME_TICKS,
                 image_name="projectiles/bossprojectile1.png"):
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.from_boss = True

        # Bild laden und ausrichten
        self.image_orig = load_projectile_image(image_name)
        angle = degrees(atan2(-direction[1], direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self._setup_motion()

        # DEBUG
        print(f"[BOSS-FLAME] 🔥 Neues BossFlameProjectile gespawnt: Pos=({x},{y}), Dir={direction}, DMG={damage}")

        # Spezialeffekt beim Spawnen (z. B. Glow)
        self.spawn_effect_done = False
        self.spawn_flash_surface = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(self.spawn_flash_surface, (255, 120, 0, 100), (45, 45), 40)

    def update(self):
        self._advance_motion()
        self.lifetime -= 1
        return self.lifetime > 0 and self.is_on_screen()

    def is_on_screen(self):
        screen_rect = pygame.Rect(0, 0, pygame.display.get_surface().get_width(), pygame.display.get_surface().get_height())
        return self.rect.colliderect(screen_rect)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if not self.spawn_effect_done:
            screen.blit(self.spawn_flash_surface, self.rect.move(-13, -13))
            self.spawn_effect_done = True

    def collides_with(self, target_rect):
        return self.rect.colliderect(target_rect)
