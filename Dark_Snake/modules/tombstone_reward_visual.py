"""Portrait Frost-Abyss epitaph reward: render text and earned sprite over vetted art.

No save/award logic; the image is staging art copied into bundled runtime.
All base content, text, skull artwork, and twelve gentle aura phases are cached.
"""
from __future__ import annotations

import logging
import math

import pygame

from modules.career_reward_visual import MysticRewardPanel
from modules.career_ranks import RANK_MIN_XP
from modules.resources import find_asset

LOGGER = logging.getLogger(__name__)

EPITAPH_IMAGE = ("graphics", "game_over", "abyss_epitaph.png")
ASPECT = 1536 / 1024  # Source PNG; preserve proportions, never stretch the art.
HOLD_SECONDS = 15.0
FADE_SECONDS = 3.0

# Gothic stone should read like engraved relief, not small grey overlay text.
# Georgia is bundled with Windows; SysFont has a safe fallback elsewhere.
EPITAPH_FONT = "Georgia"
BONE = (237, 226, 204)
MINT = (193, 239, 207)
HEIRLOOM_GOLD = (239, 214, 168)
LAVENDER_FROST = (207, 200, 240)


def portrait_size(max_width: int, max_height: int) -> tuple[int, int]:
    """Fit the entire portrait (including the three skulls) into available space."""
    width = max(1, min(max_width, int(max_height / ASPECT)))
    return width, max(1, round(width * ASPECT))


class TombstoneRewardPanel(MysticRewardPanel):
    """A tall, center-aligned medal/title/scroll composition over actual PNG."""

    def __init__(self):
        super().__init__()
        self._art = None
        try:
            self._art = pygame.image.load(str(find_asset(*EPITAPH_IMAGE))).convert_alpha()
        except (OSError, pygame.error) as exc:
            LOGGER.warning("Dark Abyss epitaph PNG unavailable: %s", exc)
        self._scaled_art_size = None
        self._scaled_art = None
        self.last_slots = {}

    @staticmethod
    def _words(font, text: str, max_width: int, max_lines: int) -> list[str]:
        """Wrap full phrases rather than shrinking every line to tiny text."""
        words = str(text).split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if font.size(trial)[0] <= max_width:
                current = trial
                continue
            if current:
                lines.append(current)
                current = ""
            if font.size(word)[0] <= max_width:
                current = word
            else:
                # Rare long words cannot extend past the engraved face.
                part = ""
                for char in word:
                    if part and font.size(part + char)[0] > max_width:
                        lines.append(part)
                        part = char
                    else:
                        part += char
                current = part
        if current:
            lines.append(current)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            while lines[-1] and font.size(lines[-1] + "…")[0] > max_width:
                lines[-1] = lines[-1][:-1]
            lines[-1] += "…"
        return lines

    def _center_lines(self, target, font, text, *, y, color, max_width, max_lines=3):
        lines = self._words(font, text, max_width, max_lines)
        for index, line in enumerate(lines):
            label = font.render(line, True, color)
            rect = label.get_rect(midtop=(
                target.get_width() // 2, y + index * (font.get_linesize() + 3)
            ))
            # Cached soft engraving shadow gives light letters definition on
            # the photographed rock without per-frame surface generation.
            shadow = font.render(line, True, (8, 8, 20))
            shadow.set_alpha(190)
            target.blit(shadow, rect.move(1, 2))
            target.blit(label, rect)
        return len(lines)

    def _prepare(self, width, career, warning):
        key = (width, career, warning)
        if key == self._key and self._base is not None:
            return
        self._key = key
        height = round(width * ASPECT)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if self._art is not None:
            if self._scaled_art_size != surface.get_size():
                self._scaled_art = pygame.transform.smoothscale(
                    self._art, surface.get_size())
                self._scaled_art_size = surface.get_size()
            surface.blit(self._scaled_art, (0, 0))
        else:
            # Runtime failure degrades to a legible neutral shield, not a crash.
            pygame.draw.rect(surface, (7, 13, 29, 238),
                             (18, 18, width - 36, height - 36),
                             border_radius=max(8, width // 15))
            pygame.draw.rect(surface, (114, 91, 156, 180),
                             (20, 20, width - 40, height - 40), 2,
                             border_radius=max(8, width // 15))

        cx = width // 2
        font_title = pygame.font.SysFont(
            EPITAPH_FONT, max(19, int(width * .046)), bold=True
        )
        font_body = pygame.font.SysFont(
            EPITAPH_FONT, max(16, int(width * .036)), bold=True
        )
        font_praise = pygame.font.SysFont(
            EPITAPH_FONT, max(16, int(width * .035)), bold=True, italic=True
        )
        font_small = pygame.font.SysFont(
            EPITAPH_FONT, max(15, int(width * .033)), bold=True
        )
        self._font_cache = (font_title, font_body, font_praise, font_small)

        art = self._picture(career)
        icon_centre = (cx, round(height * .202))
        if art is not None:
            icon_side = int(min(width * .25, height * .14))
            icon = pygame.transform.smoothscale(art, (icon_side, icon_side))
            surface.blit(icon, icon.get_rect(center=icon_centre))
        else:
            # Decorative emblem is deliberately NOT an invented item reward.
            radius = round(width * .053)
            pygame.draw.circle(surface, (106, 170, 158, 142),
                               icon_centre, radius + 12, 2)
            pygame.draw.circle(surface, (185, 119, 211, 178),
                               icon_centre, radius, 2)

        face_width = int(width * .69)
        title, reason, praise = self._narrative(career, warning)
        title_y = int(height * .353)
        reason_y = int(height * .457)
        praise_y = int(height * .557)
        rank_y = int(height * .657)
        progress_y = int(height * .711)
        bar_y = int(height * .797)
        self._center_lines(surface, font_title, title, y=title_y,
                           max_width=face_width, max_lines=2,
                           color=MINT if art is not None
                           else (220, 187, 241))
        self._center_lines(surface, font_body, reason, y=reason_y,
                           max_width=face_width, max_lines=3,
                           color=BONE)
        self._center_lines(surface, font_praise, praise, y=praise_y,
                           max_width=face_width, max_lines=3,
                           color=LAVENDER_FROST)
        if career is not None:
            earned = f"{career.earned_xp:,}".replace(",", ".")
            total = f"{career.total_xp:,}".replace(",", ".")
            rank = (f"RANG {career.rank_before} → {career.rank_after}  ·  "
                    f"+{earned} XP")
            self._center_lines(surface, font_small, rank, y=rank_y,
                               max_width=face_width, max_lines=2,
                               color=HEIRLOOM_GOLD)
            if career.next_rank_xp is None:
                progress = f"{total} XP GESAMT · MAXIMALRANG"
                ratio = 1.0
            else:
                until = f"{career.xp_to_next_rank:,}".replace(",", ".")
                progress = f"{total} XP GESAMT · NOCH {until} BIS RANG {career.rank_after + 1}"
                previous = RANK_MIN_XP[career.rank_after - 1]
                ratio = max(0., min(1., (career.total_xp - previous) /
                                    max(1, career.next_rank_xp - previous)))
            self._center_lines(surface, font_small, progress, y=progress_y,
                               max_width=face_width, max_lines=2,
                               color=(183, 225, 220))
            bar = pygame.Rect(cx - int(width * .30), bar_y,
                              int(width * .60), max(3, round(width * .008)))
            pygame.draw.rect(surface, (34, 48, 66, 200), bar, border_radius=3)
            fill_width = round(bar.width * ratio)
            if fill_width:
                pygame.draw.rect(surface, (125, 226, 173, 224),
                                 (bar.x, bar.y, fill_width, bar.height),
                                 border_radius=3)
        # Slots in local coordinates for visual and non-overlap tests.
        self.last_slots = {
            "icon": pygame.Rect(cx - int(width * .13), int(height * .133),
                                int(width * .26), int(height * .14)),
            "title": pygame.Rect(cx - face_width // 2, title_y, face_width,
                                 int(height * .085)),
            "reason": pygame.Rect(cx - face_width // 2, reason_y, face_width,
                                  int(height * .09)),
            "praise": pygame.Rect(cx - face_width // 2, praise_y, face_width,
                                  int(height * .09)),
            "rank": pygame.Rect(cx - face_width // 2, rank_y, face_width,
                                int(height * .052)),
            "progress": pygame.Rect(cx - face_width // 2, progress_y, face_width,
                                    int(height * .079)),
        }

        self._base = surface
        self._aura = []
        for phase in range(12):
            glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            strength = round(27 + 9 * math.sin(math.tau * phase / 12))
            pygame.draw.circle(glow, (167, 85, 216, strength),
                               icon_centre, int(width * .183), 3)
            pygame.draw.circle(glow, (96, 227, 179, strength),
                               icon_centre, int(width * .190), 1)
            # Tiny slow highlights follow the carved side pillars.
            for x in (int(width * .095), int(width * .905)):
                pygame.draw.line(glow, (124, 193, 181, strength),
                                 (x, int(height * .34)),
                                 (x, int(height * .70)), 2)
            self._aura.append(glow)

    def draw(self, target, *, career, warning, rect, now, sequence):
        """The tombstone fades; name entry/buttons drawn independently still work."""
        self.last_rect = rect.copy()
        stamp = (sequence, career, warning)
        if stamp != self._shown_key:
            self._shown_key = stamp
            self._shown_at = now
        age = max(0.0, now - self._shown_at)
        alpha = 255 if age <= HOLD_SECONDS else round(
            max(0.0, 1.0 - (age - HOLD_SECONDS) / FADE_SECONDS) * 255
        )
        if not alpha:
            return 0
        self._prepare(rect.width, career, warning)
        self._base.set_alpha(alpha)
        aura = self._aura[int(age * 2.2) % len(self._aura)]
        aura.set_alpha(alpha)
        target.blit(self._base, rect.topleft)
        target.blit(aura, rect.topleft)
        return alpha
