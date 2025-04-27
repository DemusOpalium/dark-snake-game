
""" 
Modul: aoe_zones.py
Zweck: Temporäre AoE-Flächen (Area of Effect) mit visuellen Effekten, Debug-Hitboxen und Gameplay-Wirkung.
Erweitert für Boss-AoE mit Quelle ("source") und Debug-Darstellung.
"""

import os
import random
import pygame
import time
import math
from pygame.math import Vector2
from config import GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

# --------------------------------------------------
# Hilfsfunktionen zum Laden von Effektbildern
# --------------------------------------------------

def get_effect_by_type(effect_type):
    effect_folder = os.path.join("assets", "graphics", "AOEEffekte")
    type_map = {
        "damage": "FireAOE1.png",
        "heal": "HolyAOE1.png",
        "slow": "DarkAOE1.png",
        "aura": "MagicAOE1.png"
    }
    filename = type_map.get(effect_type)
    if not filename:
        return None
    path = os.path.join(effect_folder, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (int(GRID_SIZE * 3), int(GRID_SIZE * 3)))
            print("DEBUG: Effektbild geladen für", effect_type, ":", img)
            return img
        except Exception as e:
            print(f"Fehler beim Laden von {filename}: {e}")
    return None

# --------------------------------------------------
# Basiszone
# --------------------------------------------------

class AoEZone:
    def __init__(self, pos, radius, duration, color, effect_type="none"):
        self.pos = Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.color = color
        self.effect_type = effect_type
        self.created_time = time.time()
        self.alive = True
        self.image = None
        self.source = "neutral"

    def update(self):
        if time.time() - self.created_time >= self.duration:
            self.alive = False

    def draw(self, surface):
        diameter = self.radius * 2
        if self.image:
            scaled_img = pygame.transform.scale(self.image, (diameter, diameter))
            scaled_img.set_alpha(self.color[3] if len(self.color) == 4 else 255)
            surface.blit(scaled_img, (self.pos.x - self.radius, self.pos.y - self.radius))
        else:
            overlay = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(overlay, self.color, (self.radius, self.radius), self.radius)
            surface.blit(overlay, (self.pos.x - self.radius, self.pos.y - self.radius))

    def draw_hitbox(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius, 2)

    def is_inside(self, entity_pos):
        return (Vector2(entity_pos) - self.pos).length() <= self.radius

    def apply_effect(self, entity):
        pass

# --------------------------------------------------
# Spezielle Zonen
# --------------------------------------------------

class DamageZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="damage"):
        super().__init__(pos, radius, duration, color, effect_type)
        self.image = get_effect_by_type("damage")
        self.source = "neutral"

    def apply_effect(self, entity):
        if hasattr(entity, "pos") and self.is_inside((entity.pos.x, entity.pos.y)):
            entity.health -= 0.5

class HealZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="heal"):
        super().__init__(pos, radius, duration, color, effect_type)
        self.image = get_effect_by_type("heal")
        self.source = "neutral"

    def apply_effect(self, entity):
        if hasattr(entity, "pos") and self.is_inside((entity.pos.x, entity.pos.y)):
            entity.health += 0.3

class DebuffZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="slow"):
        super().__init__(pos, radius, duration, color, effect_type)
        self.image = get_effect_by_type("slow")
        self.source = "neutral"

    def apply_effect(self, entity):
        if hasattr(entity, "pos") and self.is_inside((entity.pos.x, entity.pos.y)):
            entity.speed = max(entity.base_speed * 0.5, 1)

class FollowZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="aura"):
        super().__init__(pos, radius, duration, color, effect_type)
        self.image = get_effect_by_type("aura")
        self.source = "neutral"

    def apply_effect(self, entity):
        pass

# BackgroundEffectZone: Vollflächiger AOE-Hintergrundeffekt (bleibt unverändert)
class BackgroundEffectZone(AoEZone):
    """
    Modul: BackgroundEffectZone
    Zweck: Implementiert einen vollflächigen Hintergrund-AoE-Effekt, der das gesamte Spielfeld abdeckt.
           Das übergebene Bild wird exakt auf die Fenstergröße skaliert.
    Kontext: Erweitert das bestehende aoe_zones-System, getriggert per Taste "ü".
    """
    def __init__(self, image, duration):
        pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        radius = int(math.hypot(WINDOW_WIDTH, WINDOW_HEIGHT) // 2)
        super().__init__(pos, radius, duration, (255, 255, 255, 255), effect_type="background")
        self.image = image

    def draw(self, surface):
        scaled_img = pygame.transform.scale(self.image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        scaled_img.set_alpha(self.color[3] if len(self.color) == 4 else 255)
        surface.blit(scaled_img, (0, 0))
# --------------------------------------------------
# Boss-AOE (dynamisch wachsend, mit Quelle)
# --------------------------------------------------

class GrowingBossAOEZone(AoEZone):
    def __init__(self, pos, base_radius, max_radius, duration, color, effect_type="damage", source="boss"):
        super().__init__(pos, base_radius, duration, color, effect_type)
        self.base_radius = base_radius
        self.max_radius = max_radius
        self.source = source
        self.image = get_effect_by_type(effect_type)

    def update(self):
        super().update()
        if self.alive:
            elapsed = time.time() - self.created_time
            progress = min(1.0, elapsed / self.duration)
            self.radius = int(self.base_radius + (self.max_radius - self.base_radius) * progress)

    def draw_hitbox(self, screen):
        if self.alive:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius, 2)

    def apply_effect(self, entity):
        if hasattr(entity, "source") and entity.source == self.source:
            return
        if hasattr(entity, "pos") and self.is_inside((entity.pos.x, entity.pos.y)):
            entity.health -= 0.8



def get_aoe_effect():
    effect_folder = os.path.join("assets", "graphics", "AOEEffekte")
    effect_files = [
        "AcidAOE1.png", "AcidAOE2.png", "AcidAOE3.png", "AcidAOE4.png",
        "AcidBlop1.png", "AcidBlop2.png", "AcidBlop3.png", "AcidBlop4.png",
        "DarkAOE1.png", "DarkAOE2.png", "DarkAOE3.png", "DarkAOE4.png",
        "DarkBlob1.png", "DarkBlop2.png", "DarkBlop3.png",
        "DungeonAOE.png", "DungeonAOE2.png", "DungeonAOE3.png", "DungeonAOE4.png",
        "FigurAOE1.png", "FigurAOE2.png", "FigurAOE3.png",
        "FireAOE1.png", "FireAOE2.png", "FireAOE3.png", "FireAOE4.png",
        "Fire-FeuerHoch.png", "Fire-FireHoch2.png",
        "GhostAOE1.png", "GhostAOE2.png", "GhostAOE3.png", "GhostAOE4.png",
        "GhostAOE6.png", "GhostAOE7.png", "GhostAOE8.png", "GhostAOE9.png",
        "GohstAOE5.png",
        "HolyAOE1.png", "HolyAOE2.png", "HolyAOE3.png",
        "IceAOE1.png",
        "LightAOE.png", "LightAOE2.png", "LightAOE3.png",
        "MagicAOE1.png", "MagicAOE2.png",
        "MetallAOE1.png",
        "ParadoxAOE1.png",
        "WaterAOE1.png", "WaterAOE2.png",
        "WindAOE1.png", "WindAOE2.png"
    ]
    available_effects = []
    for fname in effect_files:
        path = os.path.join(effect_folder, fname)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (int(GRID_SIZE * 3), int(GRID_SIZE * 3)))
                available_effects.append(img)
            except Exception as e:
                print(f"Fehler beim Laden von {fname}: {e}")
    if available_effects:
        effect = random.choice(available_effects)
        print("DEBUG: Effektbild geladen:", effect)
        return effect
    print("DEBUG: Kein Effektbild gefunden im Ordner", effect_folder)
    return None
