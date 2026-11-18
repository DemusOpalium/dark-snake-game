"""One-shot Soul of the Fallen animation for Classic death and final Game Over.

Only the already approved soul image is used here; fog layers come in a later PR.
The game decides when death/respawn occurs. This module only draws the effect.
"""
from dataclasses import dataclass
import logging

import pygame

from modules.resources import find_asset

LOGGER = logging.getLogger(__name__)
SOUL_ART = ("graphics", "death", "soul_of_fallen.png")
SOUL_SECONDS = 2.4
FRAME_COUNT = 28
# At 30 px per grid cell: first / second / final life.
SIZES = (60, 120, 210)


@dataclass(frozen=True)
class DeathSoulEvent:
    """Store the ORIGINAL death locations before Classic respawns the snake(s)."""
    centers: tuple[tuple[int, int], ...]
    tier: int
    began_at: float
    final: bool

    def active(self, elapsed):
        return bool(self.centers) and 0 <= elapsed < SOUL_SECONDS


class DeathSoulVisual:
    """Cached PNG sprite frames. No scaling, file I/O or fonts per displayed frame."""

    def __init__(self):
        self._frames = {}
        self._image = None
        try:
            image = pygame.image.load(str(find_asset(*SOUL_ART))).convert_alpha()
            # All displayed frames are <= 210 px: reduce the source once.
            self._image = pygame.transform.smoothscale(image, (240, 240))
        except (OSError, pygame.error) as exc:
            LOGGER.warning("Soul of the Fallen artwork not available: %s", exc)

    @staticmethod
    def frame_index(elapsed):
        """One-way, time-based animation independent of 60 FPS vs slower PCs."""
        fraction = max(0.0, min(1.0, elapsed / SOUL_SECONDS))
        return min(FRAME_COUNT - 1, int(fraction * FRAME_COUNT))

    @staticmethod
    def target_size(tier):
        return SIZES[max(0, min(2, tier - 1))]

    def _frame(self, tier, index):
        key = (tier, index)
        if key not in self._frames:
            fraction = (index + 1) / FRAME_COUNT
            final_size = self.target_size(tier)
            diameter = max(18, round(18 + (final_size - 18) * fraction ** 0.7))
            # 90% maximum opacity reads as a spirit, not a solid creature.
            opacity = min(230, round(230 * min(
                1.0, fraction / 0.15, (1.0 - fraction) / 0.22,
            )))
            if self._image is not None:
                frame = pygame.transform.smoothscale(
                    self._image, (diameter, diameter)
                )
                frame.set_alpha(opacity)
            else:
                # A missing PNG must never prevent dying or respawning.
                frame = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                pygame.draw.circle(
                    frame, (124, 69, 193, opacity),
                    (diameter // 2, diameter // 2), diameter // 2,
                )
            self._frames[key] = frame
        return self._frames[key]

    def draw(self, surface, event, elapsed):
        if event is None or not event.active(elapsed):
            return
        index = self.frame_index(elapsed)
        frame = self._frame(event.tier, index)
        # The soul grows and rises from the ORIGINAL head, never the new spawn.
        float_y = round(55 * min(1.0, elapsed / SOUL_SECONDS))
        for cx, cy in event.centers:
            origin = (round(cx - frame.get_width() / 2),
                      round(cy - frame.get_height() / 2 - float_y))
            surface.blit(frame, origin)
