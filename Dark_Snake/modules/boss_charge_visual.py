"""Pure Pygame drawing for Medusa's fixed-lane charge telegraph."""
import pygame

from modules.boss_charge import WARNING_SECONDS


def draw_medusa_charge(surface, action, now, grid_size, boss_size):
    if action is None:
        return
    phase = action.phase(now)
    if phase == "done":
        return
    start = action.start
    dest = action.destination
    # Show the entire *swept* footprint, not an inaccurate point-only arrow.
    left = round(min(start[0], dest[0]) * grid_size)
    top = round(min(start[1], dest[1]) * grid_size)
    width = round((abs(start[0] - dest[0]) + boss_size) * grid_size)
    height = round((abs(start[1] - dest[1]) + boss_size) * grid_size)
    rect = pygame.Rect(left, top, width, height)
    if phase == "warning":
        progress = max(0.0, min(1.0, (now - action.began_at) / WARNING_SECONDS))
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((122, 78, 199, 25 + int(35 * progress)))
        pygame.draw.rect(overlay, (215, 177, 255, 205),
                         overlay.get_rect(), 2)
        surface.blit(overlay, rect.topleft)
        direction = action.direction
        center = (
            round((action.start[0] + boss_size / 2) * grid_size),
            round((action.start[1] + boss_size / 2) * grid_size),
        )
        distance = (abs(dest[0] - start[0]) + abs(dest[1] - start[1])) * grid_size
        end = (center[0] + direction[0] * distance,
               center[1] + direction[1] * distance)
        pygame.draw.line(surface, (240, 219, 255), center, end, 3)
        pygame.draw.circle(surface, (245, 236, 255), end,
                           max(3, grid_size // 7), 2)
    elif phase == "charge":
        pos = action.position(now)
        ghost = pygame.Rect(round(pos[0] * grid_size) - 3,
                            round(pos[1] * grid_size) - 3,
                            boss_size * grid_size + 6,
                            boss_size * grid_size + 6)
        pygame.draw.ellipse(surface, (196, 139, 250), ghost, 2)
    else:
        # Quiet cooldown cue; no flashing or camera shake.
        pos = action.destination
        pygame.draw.ellipse(surface, (116, 107, 163),
                            pygame.Rect(round(pos[0] * grid_size),
                                        round(pos[1] * grid_size),
                                        boss_size * grid_size,
                                        boss_size * grid_size), 1)
