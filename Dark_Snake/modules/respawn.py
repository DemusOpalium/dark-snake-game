"""Classic respawn: deterministic safe placement, a paused countdown, and FrostAge art.

The countdown runs on sampled wall time, but advances only in active gameplay.
This module deliberately does not change Classic enemy/weapon/collision rules.
"""

from dataclasses import dataclass
from math import ceil, sin, tau

import pygame

from modules.frostage_assets import load_frostage_image


RESPAWN_SECONDS = 3.0
POST_RESPAWN_PROTECTION = 1.0
FROST_ART_ID = "frostage_aoe_001"  # Already bundled, not a new runtime asset.


def preferred_spawn_cells(players, width, height):
    """Classic's existing opening locations: P2 starts two cells below P1."""
    middle = (width // 2, height // 2)
    return (middle,) if players == 1 else (middle, (middle[0], min(height - 1, middle[1] + 2)))


def safe_spawn_cells(players, width, height, safe):
    """Prefer existing spawn locations, then search outward without RNG.

    A fully crowded board cannot guarantee a safe cell; distinct in-bounds
    fallbacks preserve an opportunity to escape during spawn protection.
    """
    chosen = []
    for preferred in preferred_spawn_cells(players, width, height):
        x, y = preferred
        candidates = sorted(
            ((xx, yy) for yy in range(height) for xx in range(width)),
            key=lambda point: (abs(point[0] - x) + abs(point[1] - y),
                               abs(point[1] - y), abs(point[0] - x), point[1], point[0]),
        )
        # Avoid overlaps and an immediate unavoidable head-to-head start.
        valid = lambda cell: (cell not in chosen
                              and all(abs(cell[0] - a) + abs(cell[1] - b) >= 2
                                      for a, b in chosen))
        position = next((cell for cell in candidates if valid(cell) and safe(cell)), None)
        if position is None:
            position = next((cell for cell in candidates if valid(cell)), preferred)
        chosen.append(position)
    return tuple(chosen)


@dataclass
class RespawnCountdown:
    """Sampled active-gameplay timer. Pauses while menus/tools are on top."""
    elapsed: float = 0.0
    last_sample: float | None = None
    active: bool = False

    def begin(self, now):
        self.elapsed = 0.0
        self.last_sample = now
        self.active = True

    def clear(self):
        self.elapsed = 0.0
        self.last_sample = None
        self.active = False

    def step(self, now, *, playing):
        """Return True only when the three active seconds have just elapsed."""
        if not self.active:
            return False
        if playing and self.last_sample is not None:
            self.elapsed += max(0.0, now - self.last_sample)
        self.last_sample = now
        if self.elapsed < RESPAWN_SECONDS:
            return False
        self.elapsed = RESPAWN_SECONDS
        self.active = False
        return True

    @property
    def number(self):
        return max(1, ceil(RESPAWN_SECONDS - self.elapsed))


def shift_round_timers(game, seconds):
    """Preserve pending game-world wall-clock deadlines during the frozen scene.

    Active updates do not run during respawn. Existing time.time() timestamps
    still need rebasing or enemies/bosses would immediately burst into action.
    This is separate from regular menu/pause time behavior.
    """
    if seconds <= 0:
        return

    def shift(obj, *names):
        for name in names:
            value = getattr(obj, name, None)
            if isinstance(value, (int, float)) and value != 0:
                setattr(obj, name, value + seconds)

    shift(game, "boss_spawn_timer", "portal_spawn_cooldown", "special_level_timer",
          "portal_effect_end", "last_boss_effect_time", "last_auto_shoot",
          "last_auto_shoot1", "last_auto_shoot2", "last_anim_time", "dice_display_until")
    for kind, expires in game.effects.items():
        if expires > 0:
            game.effects[kind] = expires + seconds
    game.achievement_messages = [(message, end + seconds)
                                 for message, end in game.achievement_messages]

    for enemy in game.enemies:
        shift(enemy, "spawn_time", "last_move", "_frame_time", "sprint_end_time",
              "anim_timer", "last_shot", "last_dice")
    if game.boss is not None:
        shift(game.boss, "spawn_time", "last_move", "last_frame_time",
              "special_attack_timer", "next_aoe", "next_proj")
        if game.boss.aoe_effect is not None:
            game.boss.aoe_effect["start_time"] += seconds
    if game.portal is not None:
        shift(game.portal, "start_time")
    for zone in game.aoe_zones:
        shift(zone, "created_time")
    # Frost prototype stores time.monotonic() deadlines in immutable records.
    game.frost.zones = [type(z)(z.center, z.expires_at + seconds)
                        for z in game.frost.zones]


class FrostRespawnVisual:
    """A small lightweight graphic, cached once and rendered above gameplay."""

    def __init__(self):
        self.title = pygame.font.SysFont("Segoe UI", 29, bold=True)
        self.number = pygame.font.SysFont("Segoe UI", 70, bold=True)
        self.hint = pygame.font.SysFont("Segoe UI", 20)
        art = load_frostage_image(FROST_ART_ID)
        self.art = (pygame.transform.smoothscale(art, (110, 110))
                    if art is not None else None)
        self.pulse_frames = []
        if self.art is not None:
            for alpha in (80, 115, 155, 195, 225):
                frame = self.art.copy()
                frame.set_alpha(alpha)
                self.pulse_frames.append(frame)

    def draw(self, surface, countdown, heads):
        if not countdown.active:
            return
        width, height = surface.get_size()
        # Visual breathing effect. Existing artwork is not copied each frame.
        frame = None
        if self.pulse_frames:
            pulse = (sin(countdown.elapsed * tau * 2) + 1) / 2
            frame = self.pulse_frames[round(pulse * (len(self.pulse_frames) - 1))]
        if frame:
            for x, y in heads:
                origin = (x - frame.get_width() // 2, y - frame.get_height() // 2)
                surface.blit(frame, origin)

        card = pygame.Surface((410, 208), pygame.SRCALPHA)
        card.fill((8, 21, 43, 200))
        pygame.draw.rect(card, (102, 190, 235, 220), card.get_rect(), 2, border_radius=15)
        pygame.draw.rect(card, (40, 88, 136, 105), (7, 7, 396, 194), 1, border_radius=12)
        title = self.title.render("FROSTAGE  ·  RESPAWN", True, (185, 233, 255))
        digit = self.number.render(str(countdown.number), True, (240, 250, 255))
        hint = self.hint.render("RICHTUNG JETZT WÄHLEN", True, (198, 223, 235))
        card.blit(title, title.get_rect(center=(205, 35)))
        card.blit(digit, digit.get_rect(center=(205, 103)))
        card.blit(hint, hint.get_rect(center=(205, 170)))
        surface.blit(card, card.get_rect(center=(width // 2, height // 2)))
