"""Optional fireball impact zones for the developer playtest."""

from dataclasses import dataclass

import pygame

from config import GRID_SIZE


RADIUS = 2 * GRID_SIZE
DURATION = 3.0
MOVEMENT_FACTOR = 0.7


@dataclass(frozen=True)
class FrostZone:
    center: tuple[int, int]
    expires_at: float


class FrostPrototype:
    def __init__(self):
        self.enabled = False
        self.zones: list[FrostZone] = []
        self._overlay = None

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.clear()
        return self.enabled

    def clear(self):
        self.zones.clear()

    def on_fireball_hit(self, center, now):
        if self.enabled:
            self.zones.append(FrostZone(center, now + DURATION))

    def update(self, now):
        self.zones[:] = [zone for zone in self.zones if now < zone.expires_at]

    def movement_factor_at(self, cell_x, cell_y):
        x = (cell_x + 0.5) * GRID_SIZE
        y = (cell_y + 0.5) * GRID_SIZE
        if any((x - cx) ** 2 + (y - cy) ** 2 <= RADIUS ** 2
               for (cx, cy) in (zone.center for zone in self.zones)):
            return MOVEMENT_FACTOR
        return 1.0

    def draw(self, screen):
        if not self.zones:
            return
        if self._overlay is None:
            diameter = 2 * RADIUS
            self._overlay = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(self._overlay, (100, 185, 255, 75), (RADIUS, RADIUS), RADIUS)
            pygame.draw.circle(self._overlay, (155, 225, 255, 180), (RADIUS, RADIUS), RADIUS, 2)
        for zone in self.zones:
            screen.blit(self._overlay, self._overlay.get_rect(center=zone.center))
