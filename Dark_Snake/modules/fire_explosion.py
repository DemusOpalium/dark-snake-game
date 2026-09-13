# modules/fire_explosion.py
import pygame
from pathlib import Path
from modules.resources import asset_path

# Globale Konstante für die Anzahl der Frames
EXPLOSION_FRAMES = 9

class FireExplosionAnimation:
    def __init__(self, center_pos, scale_factor=3):
        self.frames = []
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 4  # niedrigere Werte = schnellere Animation

        # Bilder laden
        for i in range(1, EXPLOSION_FRAMES + 1):
            filename = asset_path("graphics", "FlameExplosion", f"FireExplosionDetail_Centered_{i}.png")
            if Path(filename).exists():
                try:
                    img = pygame.image.load(filename).convert_alpha()
                    size = img.get_width() * scale_factor
                    img = pygame.transform.scale(img, (size, size))
                    self.frames.append(img)
                except Exception as e:
                    print(f"[Fehler] Explosion-Bild konnte nicht geladen werden: {filename} ({e})")
            else:
                print(f"[Fehler] Grafik nicht gefunden: {filename}")

        self.position = center_pos
        self.finished = False

    def update(self):
        if self.finished:
            return False
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_index += 1
            self.frame_timer = 0
            if self.frame_index >= len(self.frames):
                self.finished = True
                return False
        return True

    def draw(self, surface):
        if not self.finished and self.frame_index < len(self.frames):
            img = self.frames[self.frame_index]
            rect = img.get_rect(center=self.position)
            surface.blit(img, rect)
