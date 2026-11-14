"""Decorative multi-tile placements with independent grid footprints."""

from dataclasses import dataclass
from functools import lru_cache
import re

import pygame

from config import GRID_HEIGHT, GRID_WIDTH


@dataclass(frozen=True, slots=True)
class GraphicObject:
    asset_id: str
    width: int
    height: int

    def __post_init__(self):
        if not isinstance(self.asset_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,120}", self.asset_id):
            raise ValueError("Ungültige Grafik-ID.")
        if (type(self.width) is not int or type(self.height) is not int
                or not (1 <= self.width <= GRID_WIDTH and 1 <= self.height <= GRID_HEIGHT)):
            raise ValueError("Ungültige Rastergröße des Grafikobjekts.")


GraphicObjects = dict[tuple[int, int], GraphicObject]


def _footprint(anchor, item):
    return pygame.Rect(*anchor, item.width, item.height)


def object_anchor_at(objects: GraphicObjects, cell):
    return next((anchor for anchor, item in objects.items()
                 if _footprint(anchor, item).collidepoint(cell)), None)


def can_place_graphic_object(objects: GraphicObjects, anchor, item: GraphicObject, *, moving=None):
    if moving is not None and moving not in objects:
        return False
    area = _footprint(anchor, item)
    return pygame.Rect(0, 0, GRID_WIDTH, GRID_HEIGHT).contains(area) and not any(
        area.colliderect(_footprint(position, other))
        for position, other in objects.items() if position != moving
    )


def place_graphic_object(objects: GraphicObjects, anchor, item: GraphicObject, *, moving=None):
    if not can_place_graphic_object(objects, anchor, item, moving=moving):
        return False
    if moving is not None:
        del objects[moving]
    objects[anchor] = item
    return True


@lru_cache(maxsize=96)
def _scaled_image(asset_id, width, height):
    from modules.frostage_assets import load_frostage_image

    image = load_frostage_image(asset_id)
    if image is None:
        return None
    scale = min(width / image.get_width(), height / image.get_height())
    size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
    return pygame.transform.smoothscale(image, size)


def graphic_cell_size(board_rect):
    return board_rect.width // GRID_WIDTH, board_rect.height // GRID_HEIGHT


def graphic_object_art(board_rect, anchor, item: GraphicObject):
    """Return the cached art and its aspect-fit position in the target board."""
    cell_width, cell_height = graphic_cell_size(board_rect)
    x, y = anchor
    target = pygame.Rect(board_rect.x + x * cell_width, board_rect.y + y * cell_height,
                         item.width * cell_width, item.height * cell_height)
    image = _scaled_image(item.asset_id, target.width, target.height)
    if image is None:
        return None
    return image, image.get_rect(center=target.center)


def draw_graphic_object(surface, board_rect, anchor, item: GraphicObject, *, preview=False):
    art = graphic_object_art(board_rect, anchor, item)
    if art is None:
        return
    image, rect = art
    if preview:
        image = image.copy()
        image.set_alpha(145)
    surface.blit(image, rect)


def draw_graphic_objects(surface, board_rect, objects: GraphicObjects):
    for anchor, item in objects.items():
        draw_graphic_object(surface, board_rect, anchor, item)
