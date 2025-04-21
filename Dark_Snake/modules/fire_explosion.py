
import pygame, time
from modules.graphics import get_image
from pygame.math import Vector2

class FireExplosionAnimation:
    """6‑Frame Feuerexplosion, gespielt mit 6 FPS (~1 s)"""

    FRAME_KEYS = [
        "FireExplosionDetail1",
        "FireExplosionDetail2",
        "FireExplosionDetail3",
        "FireExplosionDetail4",
        "FireExplosionDetail5",
        "FireExplosionDetail6",
    ]

    def __init__(self, center_pos, scale_factor=1):
        self.frames = [pygame.transform.scale(get_image(k),
                                              (int(get_image(k).get_width() * scale_factor),
                                               int(get_image(k).get_height() * scale_factor)))
                       for k in self.FRAME_KEYS]
        self.center = Vector2(center_pos)
        self.frame_index = 0
        self.frame_duration = 10      # 10 Ticks @60 FPS = 6 FPS
        self.ticks = 0
        self.alive = True
        # Pre‑compute rect positions per frame for draw‑effizienz
        self.rects = []
        for img in self.frames:
            r = img.get_rect(center=self.center)
            self.rects.append(r)

    def update(self):
        if not self.alive:
            return False
        self.ticks += 1
        if self.ticks % self.frame_duration == 0:
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.alive = False
        return self.alive

    def draw(self, screen):
        if self.alive:
            screen.blit(self.frames[self.frame_index], self.rects[self.frame_index])
