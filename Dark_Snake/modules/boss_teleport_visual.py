"""Visual-only ground portals, burrowing shadows and leap landing markers.

Art is intentionally code-drawn for this first slice. Each personality
preserves its own unchanged sprite. A future artwork pack can replace these
marker functions without changing teleport safety or the BossTeleport API.
"""
from __future__ import annotations

from math import sin, pi
import pygame

COLORS = {
    "portal": (183, 117, 247),  # Medusa / violet portal
    "tunnel": (186, 147, 100),  # Guardian / underground tunnel
    "leap": (117, 205, 235),    # Hunter / landing shadow
}
NAMES = {
    "portal": "PORTAL",
    "tunnel": "TUNNEL",
    "leap": "SPRUNG",
}


def draw_teleport_markers(screen, action, now, tile_size, boss_size):
    """Source and destination telegraph persist while the boss transitions."""
    style = action.style
    color = COLORS[style]
    phase = action.phase(now)
    size_px = tile_size * boss_size
    source = ((action.origin[0] + boss_size / 2) * tile_size,
              (action.origin[1] + boss_size / 2) * tile_size)
    target = ((action.destination[0] + boss_size / 2) * tile_size,
              (action.destination[1] + boss_size / 2) * tile_size)
    pulse = .5 + .5 * sin(now * 9)
    radius = int(size_px * (.45 + .05 * pulse))
    shadow_y = round(size_px * .35)

    # Compact underfoot shadow with a brighter concentric arrival warning.
    for center, arriving in ((source, False), (target, True)):
        cx, cy = int(center[0]), int(center[1] + shadow_y)
        outer = pygame.Rect(cx - radius, cy - radius // 3,
                            radius * 2, radius * 2 // 3)
        pygame.draw.ellipse(screen, (13, 13, 23), outer)
        pygame.draw.ellipse(screen, color if arriving else (86, 84, 112),
                            outer, 3 if arriving else 2)
        if arriving:
            inset = outer.inflate(-12, -6)
            if inset.width > 0 and inset.height > 0:
                pygame.draw.ellipse(screen, color, inset, 1)
            # Two clear rings give the player >1 second to leave the lane.
            if phase == "warning":
                ring = pygame.Rect(int(center[0] - radius * 1.25),
                                   int(center[1] - radius * 1.25),
                                   int(radius * 2.5), int(radius * 2.5))
                pygame.draw.ellipse(screen, color, ring, 2)

    # Same simple rendering system, but distinct recognizable presentation.
    if style == "leap":
        if phase in ("warning", "sink"):
            pygame.draw.line(
                screen, color,
                (int(source[0]), int(source[1])),
                (int(target[0]), int(target[1])), 2,
            )
    elif style == "tunnel":
        # Earthen dotted route: a burrow through the *ground*, not walls.
        for index in range(1, 4):
            t = index / 4.
            x = int(source[0] + (target[0] - source[0]) * t)
            y = int(source[1] + (target[1] - source[1]) * t + shadow_y)
            pygame.draw.circle(screen, color, (x, y), 3)
    else:
        # Two magic concentric nodes, so portal and swipe are distinguishable.
        for center in (source, target):
            pygame.draw.circle(
                screen, color, (int(center[0]), int(center[1])),
                max(4, size_px // 7), 2,
            )


def draw_teleport_sprite(screen, image, pos, size_px, action, now):
    """Scale/alpha only the rendering; NEVER change the boss's hitbox."""
    phase = action.phase(now)
    progress = action.progress(now)
    if phase == "sink":
        height_fraction = max(.06, 1 - progress)
        opacity = max(35, round(255 * (1 - progress)))
    elif phase == "emerge":
        height_fraction = max(.06, progress)
        opacity = min(255, max(35, round(255 * progress)))
    else:
        height_fraction = 1
        opacity = 255

    width = size_px
    height = max(1, round(size_px * height_fraction))
    if image is not None:
        surface = pygame.transform.scale(image, (width, height)).copy()
        if opacity < 255:
            surface.set_alpha(opacity)
    else:
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((220, 70, 80, opacity))
    px, py = pos
    # Sink downward into the ground and rise vertically, not a map-long warp.
    screen.blit(surface, (px, py + size_px - height))
