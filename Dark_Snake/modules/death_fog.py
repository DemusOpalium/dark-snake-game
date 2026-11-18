"""Three-layer Abyss fog for the LAST death only.

The user's original transparent PNGs stay in GamePICs. Bundled copies under
assets/ are loaded and scaled once; drawing uses alpha and position only.
"""
import logging

import pygame

from modules.resources import find_asset

LOGGER = logging.getLogger(__name__)

FINAL_DEATH_SECONDS = 3.0
FOG_ASSETS = tuple(
    ("graphics", "death", f"fog_{index:02}.png") for index in (1, 2, 3)
)
FOG_STARTS = (0.45, 1.05, 1.65)
FOG_RAMP_SECONDS = 0.80
FOG_MAX_OPACITY = (170, 177, 200)


def layer_opacity(elapsed, index):
    """Independent, deterministic entrance for each of the three fog layers."""
    if not 0 <= index < len(FOG_ASSETS):
        raise ValueError("Unknown fog layer")
    amount = min(1.0, max(0.0, (elapsed - FOG_STARTS[index]) / FOG_RAMP_SECONDS))
    return round(FOG_MAX_OPACITY[index] * amount)


def darkness_opacity(elapsed):
    """The world slowly disappears into black immediately before Dark Abyss."""
    progress = min(1.0, max(0.0, (elapsed - 1.5) / (FINAL_DEATH_SECONDS - 1.5)))
    return round(215 * progress ** 1.5)


class AbyssFogVisual:
    """Reuse cached surfaces; no resizing, frame allocation or I/O at 60 FPS."""

    def __init__(self):
        self._sources = None
        self._layers = None
        self._darkness = None
        self._screen_size = None

    def _prepare(self, size):
        if self._sources is None:
            images = []
            for asset in FOG_ASSETS:
                try:
                    image = pygame.image.load(str(find_asset(*asset))).convert_alpha()
                    # Limit large source resolution and decode memory once.
                    images.append(pygame.transform.smoothscale(image, (1024, 512)))
                except (OSError, pygame.error) as exc:
                    LOGGER.warning("Abyss fog asset missing: %s (%s)", asset[-1], exc)
                    images.append(None)
            self._sources = tuple(images)
        if self._screen_size != size:
            width, height = size
            # Three 2:1 transparent overlays span most of a 1350x930 playfield.
            fog_width = round(width * 1.13)
            fog_height = round(fog_width / 2)
            self._layers = tuple(
                pygame.transform.smoothscale(image, (fog_width, fog_height))
                if image is not None else None
                for image in self._sources
            )
            self._darkness = pygame.Surface(size)
            self._darkness.fill((0, 0, 0))
            self._screen_size = size

    def draw(self, surface, elapsed):
        """Animate entrance and horizontal drift; draw only during the final 3 s."""
        if not FOG_STARTS[0] <= elapsed < FINAL_DEATH_SECONDS:
            return
        self._prepare(surface.get_size())
        screen_width, screen_height = surface.get_size()
        for index, layer in enumerate(self._layers):
            alpha = layer_opacity(elapsed, index)
            if layer is None or alpha == 0:
                continue
            layer.set_alpha(alpha)
            # A small, constant-rate drift gives movement even with static PNGs.
            progress = min(1.0, max(0.0,
                         (elapsed - FOG_STARTS[index]) / 2.0))
            dx = round((index % 2 * 2 - 1) * 65 * progress)
            x = (screen_width - layer.get_width()) // 2 + dx
            y = round(screen_height * (0.02 + index * 0.19))
            surface.blit(layer, (x, y))
        darkness = darkness_opacity(elapsed)
        if darkness:
            self._darkness.set_alpha(darkness)
            surface.blit(self._darkness, (0, 0))
