#// [SUCHTAG: AOE_ZONES_MODIFICATION - EFFECT IMAGE LAYOUT]
"""
Modul: aoe_zones.py
Zweck: Temporäre AoE-Flächen (Area of Effect) mit verschiedenen Effekten implementieren.
       Zusätzlich werden nun für Schadens- und Heilzonen (sowie Slow/Aura) passende Effektbilder aus dem
       vorbereiteten Ordner geladen und skaliert dargestellt.
Kontext: Erweiterung des bestehenden aoe_zones-Systems; die Effektbilder ersetzen die klassischen
         farbigen Kreise.
"""

import os
import random
import pygame, time, math
from pygame.math import Vector2
from config import GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

# Neue Hilfsfunktion zum Laden des Effektbilds für einen bestimmten Typ
def get_effect_by_type(effect_type):
    """
    Lädt ein spezifisches Effektbild anhand des Typ-Parameters.
    Mögliche effect_type-Werte: "damage", "heal", "slow", "aura"
    """
    effect_folder = os.path.join("assets", "graphics", "AOEEffekte")
    
    # Hier werden für die einzelnen Typen feste Bilddateien definiert:
    if effect_type == "damage":
        filename = "FireAOE1.png"
    elif effect_type == "heal":
        filename = "HolyAOE1.png"
    elif effect_type == "slow":
        # Beispiel: für Slow-Effekt kann hier ein alternatives Bild gewählt werden
        filename = "DarkAOE1.png"
    elif effect_type == "aura":
        # Beispiel: für Aura-Effekt
        filename = "MagicAOE1.png"
    else:
        return None

    path = os.path.join(effect_folder, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            # Skaliere das Bild auf einen sinnvollen Effektbereich – hier analog zur Skalierung in get_aoe_effect()
            img = pygame.transform.scale(img, (int(GRID_SIZE * 3), int(GRID_SIZE * 3)))
            print("DEBUG: Effektbild geladen für", effect_type, ":", img)
            return img
        except Exception as e:
            print(f"Fehler beim Laden von {filename}: {e}")
            return None
    print("DEBUG: Kein Effektbild gefunden im Ordner", effect_folder)
    return None

# Bereits bestehende Funktion (kann unverändert bleiben, falls gebraucht)
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
        color: (R,G,B,A) – Farbe (z. B. halbtransparent)
        effect_type: z. B. "damage", "heal", "slow", "aura"
        """
        self.pos = Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.color = color
        self.effect_type = effect_type
        self.created_time = time.time()
        self.alive = True
        # Eigentliches Effektbild (falls gesetzt) – ansonsten None
        self.image = None

    def update(self):
        if time.time() - self.created_time >= self.duration:
            self.alive = False

    def draw(self, surface):
        diameter = self.radius * 2
        if self.image:
            # Skaliere das Effektbild nur für diese Zone (nicht wie beim Background auf das ganze Fenster)
            scaled_img = pygame.transform.scale(self.image, (diameter, diameter))
            # Setze die Alphawerte analog zur aktuellen Farbe
            scaled_img.set_alpha(self.color[3] if len(self.color) == 4 else 255)
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
    def __init__(self, pos, radius, duration, color, effect_type="damage"):
        super().__init__(pos, radius, duration, color, effect_type)
        # Lade das spezifische Effektbild für Schadenszonen (z. B. Feuer-Effekt)
        self.image = get_effect_by_type("damage")
    
    def apply_effect(self, entity):
        elapsed = time.time() - self.created_time
        damage = 10 * (elapsed / self.duration)
        entity.health -= damage

# Heilzone: regeneriert Gesundheit
class HealZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="heal"):
        super().__init__(pos, radius, duration, color, effect_type)
        # Lade das spezifische Effektbild für Heilungszonen (z. B. Holy-Effekt)
        self.image = get_effect_by_type("heal")
    
    def apply_effect(self, entity):
        elapsed = time.time() - self.created_time
        healing = 5 * (elapsed / self.duration)
        entity.health += healing

# DebuffZone: verringert die Geschwindigkeit (hier Beispiel: 50 %)
class DebuffZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="slow"):
        super().__init__(pos, radius, duration, color, effect_type)
        # Lade das spezifische Effektbild für Slow-Zonen
        self.image = get_effect_by_type("slow")
    
    def apply_effect(self, entity):
        entity.speed = max(entity.base_speed * 0.5, 1)

# FollowZone: Beispiel einer Aura – hier ohne konkreten Effekt (erweiterbar)
class FollowZone(AoEZone):
    def __init__(self, pos, radius, duration, color, effect_type="aura"):
        super().__init__(pos, radius, duration, color, effect_type)
        # Lade das spezifische Effektbild für Aura-Zonen
        self.image = get_effect_by_type("aura")
    
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

