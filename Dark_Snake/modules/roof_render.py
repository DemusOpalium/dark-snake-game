"""Draw the foreground and cut soft visibility windows around player heads."""

from functools import lru_cache
from math import ceil, hypot

import pygame

from modules.graphic_objects import GraphicObjects, graphic_cell_size, graphic_object_art
from modules.roof_settings import RoofVisibility


@lru_cache(maxsize=24)
def _window_mask(radius, softness, transparency):
    edge = ceil(radius)
    diameter = edge * 2 + 1
    pixels = bytearray(b"\xff" * (diameter * diameter * 4))
    for y in range(-edge, edge + 1):
        for x in range(-edge, edge + 1):
            distance = hypot(x, y)
            if distance >= radius:
                continue
            fade = min(1, (radius - distance) / softness) if softness else 1
            # Smoothstep gives a soft slope at both ends of the transition.
            strength = fade * fade * (3 - 2 * fade) * transparency / 100
            offset = ((y + edge) * diameter + x + edge) * 4
            pixels[offset + 3] = 255 - round(255 * strength)
    return pygame.image.frombytes(bytes(pixels), (diameter, diameter), "RGBA")


def _apply_windows(image, rect, heads, mask):
    windows = [
        mask.get_rect(center=(x - rect.x, y - rect.y))
        for x, y in heads
    ]
    result = image.copy()
    if len(windows) == 1 or (len(windows) == 2 and not windows[0].colliderect(windows[1])):
        for window in windows:
            result.blit(mask, window, special_flags=pygame.BLEND_RGBA_MULT)
        return result

    bounds = windows[0].unionall(windows[1:]).clip(image.get_rect())
    merged = pygame.Surface(bounds.size, pygame.SRCALPHA)
    merged.fill((255, 255, 255, 255))
    for window in windows:
        offset = (window.x - bounds.x, window.y - bounds.y)
        # Choose the clearer of the two windows. Overlap does not stack opacity changes.
        merged.blit(mask, offset, special_flags=pygame.BLEND_RGBA_MIN)
    result.blit(merged, bounds, special_flags=pygame.BLEND_RGBA_MULT)
    return result


def draw_roof_objects(
    surface, board_rect, objects: GraphicObjects, settings: RoofVisibility, *, head_centers=(),
):
    """Draw roof art over the world using absolute pixel centers for visible players."""
    if not objects:
        return
    heads = ()
    if settings.enabled and settings.transparency:
        heads = tuple((round(x), round(y)) for x, y in head_centers)
    mask = None
    for anchor, item in objects.items():
        art = graphic_object_art(board_rect, anchor, item)
        if art is None:
            continue
        image, rect = art
        if heads:
            covered_heads = [head for head in heads if rect.collidepoint(head)]
            if covered_heads:
                if mask is None:
                    cell_pixels = min(graphic_cell_size(board_rect))
                    mask = _window_mask(
                        settings.radius * cell_pixels, settings.softness * cell_pixels,
                        settings.transparency,
                    )
                image = _apply_windows(image, rect, covered_heads, mask)
        surface.blit(image, rect)
