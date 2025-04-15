#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Modul: aoe_zones.py
# Zweck: Temporäre AoE-Flächen (Area of Effect) mit verschiedenen Effekten
#        implementieren: Schadenszonen, Debuff-Zonen, Heilzonen und Auren.
# Kontext: Diese Zonen wirken über Zeit auf Entitys, die sich in ihrem Wirkungsbereich befinden.
#
import os
import random  # <-- Diese Zeile hinzufügen
import pygame, time, math
from pygame.math import Vector2
from config import GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

# Funktion zum Laden eines AoE-Effektbilds, jetzt auf Modul-Ebene
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

# Basis-Klasse für alle AoE-Zonen
class AoEZone:
    def __init__(self, pos, radius, duration, color, effect_type="none"):
        """
        pos: Startposition als (x,y)-Tuple (in Pixeln)
        radius: Wirkradius der Zone in Pixeln
        duration: Dauer der Zone in Sekunden
        color: (R,G,B,A) – Farbe für die Darstellung (z.B. halbtransparent)
        effect_type: z.B. "damage", "heal", "slow", "aura"
        """
        self.pos = Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.color = color
        self.effect_type = effect_type
        self.created_time = time.time()
        self.alive = True

    def update(self):
        if time.time() - self.created_time >= self.duration:
            self.alive = False

    def draw(self, surface):
        diameter = self.radius * 2
        if hasattr(self, "image") and self.image:
            scaled_img = pygame.transform.scale(self.image, (diameter, diameter))
            scaled_img.set_alpha(self.color[3] if len(self.color) == 4 else 128)
            surface.blit(scaled_img, (self.pos.x - self.radius, self.pos.y - self.radius))
        else:
            overlay = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(overlay, self.color, (self.radius, self.radius), self.radius)
            surface.blit(overlay, (self.pos.x - self.radius, self.pos.y - self.radius))

    def is_inside(self, entity_pos):
        return (Vector2(entity_pos) - self.pos).length() <= self.radius

    def apply_effect(self, entity):
        # Basisaktion – in Unterklassen spezifizieren
        pass

# Schadenszone: fügt Schaden zu
class DamageZone(AoEZone):
    def apply_effect(self, entity):
        elapsed = time.time() - self.created_time
        damage = 10 * (elapsed / self.duration)
        entity.health -= damage

# Heilzone: regeneriert Gesundheit
class HealZone(AoEZone):
    def apply_effect(self, entity):
        elapsed = time.time() - self.created_time
        healing = 5 * (elapsed / self.duration)
        entity.health += healing

# DebuffZone: verringert die Geschwindigkeit (hier Beispiel: 50 %)
class DebuffZone(AoEZone):
    def apply_effect(self, entity):
        entity.speed = max(entity.base_speed * 0.5, 1)

# FollowZone: Beispiel einer Aura – hier ohne konkreten Effekt (erweiterbar)
class FollowZone(AoEZone):
    def apply_effect(self, entity):
        pass

# BackgroundEffectZone: Vollflächiger AOE-Hintergrundeffekt
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
