"""Small Frost throw overlay for Medusa Tactics B; graphics have no hit logic."""
import pygame

from modules.boss_tactics import MedusaTactics


def draw_medusa_volley(surface, volley, now, grid_size):
    """Draw the telegraphed destination and the travelling Frost orb.

    Render on the world-effects layer, beneath snakes/bosses. No photosensitivity
    strobe or new assets required. The gameplay timer lives in boss_tactics.
    """
    if volley is None:
        return
    phase = volley.phase(now)
    if phase == "done":
        return
    center = (round((volley.target[0] + .5) * grid_size),
              round((volley.target[1] + .5) * grid_size))
    radius = round(MedusaTactics.RADIUS_CELLS * grid_size)

    pad = 4
    overlay = pygame.Surface((radius * 2 + 2 * pad,
                              radius * 2 + 2 * pad), pygame.SRCALPHA)
    middle = (radius + pad, radius + pad)
    if phase == "warning":
        pygame.draw.circle(overlay, (168, 94, 230, 45), middle, radius)
        pygame.draw.circle(overlay, (217, 146, 255, 225), middle, radius, 2)
        pygame.draw.line(overlay, (244, 225, 255, 180),
                         (middle[0] - 7, middle[1]),
                         (middle[0] + 7, middle[1]), 2)
        pygame.draw.line(overlay, (244, 225, 255, 180),
                         (middle[0], middle[1] - 7),
                         (middle[0], middle[1] + 7), 2)
    else:
        pygame.draw.circle(overlay, (84, 185, 250, 95), middle, radius)
        pygame.draw.circle(overlay, (205, 245, 255, 225), middle, radius, 2)
        pygame.draw.circle(overlay, (227, 253, 255, 160), middle,
                           max(3, radius // 3), 2)
    surface.blit(overlay, (center[0] - middle[0], center[1] - middle[1]))

    # A visible orb moves from the *cast* position to the fixed marked cell.
    # It cannot apply contact damage; only the announced impact area can.
    if phase == "warning":
        fraction = max(0.0, min(
            1.0, (now - volley.started_at)
            / MedusaTactics.WARNING_SECONDS,
        ))
        ox = (volley.origin[0] + .5) * grid_size
        oy = (volley.origin[1] + .5) * grid_size
        px = round(ox + (center[0] - ox) * fraction)
        py = round(oy + (center[1] - oy) * fraction)
        pygame.draw.circle(surface, (110, 217, 255), (px, py),
                           max(3, grid_size // 4))
        pygame.draw.circle(surface, (239, 253, 255), (px, py),
                           max(2, grid_size // 9))
