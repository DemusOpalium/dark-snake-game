
# modules/boss_projectiles.py
# Enthält alle Boss-Projektilklassen für Dark Snake

import pygame
from modules.graphics import load_image
from math import atan2, degrees

class BossProjectile:
    """
    Allgemeines Boss-Projektil mit Richtung, Bild, Geschwindigkeit und optionaler Explosion.
    """
    def __init__(self, x, y, direction, speed=2.0, damage=5, image_name="projectiles/bossprojectile1.png", lifetime=600):
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.from_boss = True

        self.image_orig = load_image(image_name)
        angle = degrees(atan2(-self.direction[1], self.direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.speed * self.direction[0]
        self.rect.y += self.speed * self.direction[1]
        self.lifetime -= 1
        return self.lifetime > 0 and self.is_on_screen()

    def is_on_screen(self):
        screen_rect = pygame.Rect(0, 0, pygame.display.get_surface().get_width(), pygame.display.get_surface().get_height())
        return self.rect.colliderect(screen_rect)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def collides_with(self, target_rect):
        return self.rect.colliderect(target_rect)



class BossFlameProjectile:
    """
    Projektil speziell für den Boss – explodiert bei Treffer auf Spieler mit visuellem Effekt.
    """
    def __init__(self, x, y, direction, speed=2.4, damage=8, lifetime=1200, image_name="projectiles/bossprojectile1.png"):
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.from_boss = True

        # Bild laden und ausrichten
        self.image_orig = load_image(image_name)
        angle = degrees(atan2(-direction[1], direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))

        # DEBUG
        print(f"[BOSS-FLAME] 🔥 Neues BossFlameProjectile gespawnt: Pos=({x},{y}), Dir={direction}, DMG={damage}")

        # Spezialeffekt beim Spawnen (z. B. Glow)
        self.spawn_effect_done = False
        self.spawn_flash_surface = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(self.spawn_flash_surface, (255, 120, 0, 100), (45, 45), 40)

    def update(self):
        self.rect.x += self.speed * self.direction[0]
        self.rect.y += self.speed * self.direction[1]
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
