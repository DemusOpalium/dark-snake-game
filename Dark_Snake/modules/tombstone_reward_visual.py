"""Portrait Frost-Abyss epitaph reward: render text and earned sprite over vetted art.

No save/award logic; the image is staging art copied into bundled runtime.
All base content, text, skull artwork, and twelve gentle aura phases are cached.
"""
from __future__ import annotations

import hashlib
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

# name, title, description, praise, rank, progress. Light pigments remain
# legible on near-black stone; no random dark-on-dark text or per-frame flicker.
INK_THEMES = (
    ("Frosttinte", MINT, BONE, LAVENDER_FROST, HEIRLOOM_GOLD, (183, 225, 220)),
    ("Purpurnacht", (218, 184, 244), (237, 225, 242),
     (200, 219, 243), (236, 199, 239), (190, 226, 211)),
    ("Blutmond", (244, 180, 196), (238, 225, 216),
     (228, 199, 237), (244, 214, 181), (193, 226, 218)),
    ("Nebelgrün", (190, 236, 189), (230, 240, 221),
     (193, 225, 207), (235, 221, 177), (182, 229, 216)),
    ("Eiskönig", (179, 218, 248), (226, 236, 246),
     (203, 209, 249), (239, 221, 187), (187, 230, 246)),
)


def epitaph_ink(career):
    """Stable 'draw' from unlocked Gothic palettes, only once per saved run.

    Higher career ranks unlock additional visual variants. This selection
    changes NO XP, award probability or inventory state.
    """
    if career is None:
        return INK_THEMES[0]
    available = 2 + (career.rank_after >= 5) + (career.rank_after >= 10) + (
        career.rank_after >= 20
    )
    identity = (
        f"{career.rank_before}:{career.rank_after}:{career.total_xp}:"
        f"{career.earned_xp}:{career.reward_id or ''}"
    ).encode("utf-8")
    roll = int.from_bytes(hashlib.blake2s(identity, digest_size=4).digest(), "big")
    return INK_THEMES[roll % available]


def career_rank_inscription(career) -> str:
    """Avoid missing U+2192 arrow glyph in the installed Gothic serif face."""
    earned = f"{career.earned_xp:,}".replace(",", ".")
    if career.rank_after > career.rank_before:
        return (f"RANG {career.rank_before} AUF {career.rank_after}"
                f"  ·  +{earned} XP")
    return f"RANG {career.rank_after}  ·  +{earned} XP"


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

    def _engrave(self, target, text, *, name, slot, color, font_size,
                 min_size=13, max_lines=2, italic=False):
        """Draw centered text *inside* its stone slot; shrink before clipping.

        Layout and font creation are cached in _prepare, never recalculated
        on every frame. A dark 1px shadow makes the engraving readable.
        """
        width = max(1, slot.width - 4)
        height = max(1, slot.height - 4)
        chosen = None
        for size in range(font_size, min_size - 1, -1):
            font = pygame.font.SysFont(EPITAPH_FONT, size, bold=True,
                                       italic=italic)
            # First try to keep *all* the text, even with high XP totals.
            wrapped = self._words(font, text, width, 100)
            step = font.get_linesize() + 3
            if len(wrapped) <= max_lines and len(wrapped) * step - 3 <= height:
                chosen = font, wrapped, step
                break
        if chosen is None:
            # Pathological localized text: clamp the final line rather than
            # letting it spill onto the carved pillars or three skulls.
            font = pygame.font.SysFont(EPITAPH_FONT, min_size, bold=True,
                                       italic=italic)
            step = font.get_linesize() + 3
            allowed = max(1, min(max_lines, (height + 3) // step))
            chosen = font, self._words(font, text, width, allowed), step
        font, lines, step = chosen
        rects = []
        for index, line in enumerate(lines):
            label = font.render(line, True, color)
            label_rect = label.get_rect(midtop=(
                target.get_width() // 2, slot.top + 1 + index * step
            ))
            shadow = font.render(line, True, (8, 8, 20))
            shadow.set_alpha(190)
            target.blit(shadow, label_rect.move(1, 1))
            target.blit(label, label_rect)
            rects.append(label_rect)
        self.last_text_bounds[name] = tuple(rects)
        return lines

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

        face_width = int(width * .66)
        title, reason, praise = self._narrative(career, warning)
        palette = epitaph_ink(career)
        self.last_ink_theme = palette[0]
        cx = width // 2
        # Relative safe zones sit strictly inside the smooth central stone.
        # They never reach the external Gothic spires or the skull pedestal.
        def slot(y, span):
            return pygame.Rect(cx - face_width // 2, round(height * y),
                               face_width, round(height * span))

        self.last_slots = {
            "icon": pygame.Rect(cx - int(width * .13), int(height * .133),
                                int(width * .26), int(height * .14)),
            "title": slot(.350, .089),
            "reason": slot(.450, .096),
            "praise": slot(.551, .098),
            "rank": slot(.660, .052),
            "progress": slot(.721, .073),
        }
        self.last_text_bounds = {}
        self._engrave(surface, title, name="title", slot=self.last_slots["title"],
                      color=palette[1], font_size=max(19, int(width * .046)),
                      min_size=15, max_lines=2)
        self._engrave(surface, reason, name="reason", slot=self.last_slots["reason"],
                      color=palette[2], font_size=max(16, int(width * .036)),
                      min_size=13, max_lines=3)
        self._engrave(surface, praise, name="praise", slot=self.last_slots["praise"],
                      color=palette[3], font_size=max(16, int(width * .035)),
                      min_size=13, max_lines=3, italic=True)
        if career is not None:
            total = f"{career.total_xp:,}".replace(",", ".")
            rank = career_rank_inscription(career)
            self._engrave(surface, rank, name="rank", slot=self.last_slots["rank"],
                          color=palette[4], font_size=max(15, int(width * .033)),
                          min_size=12, max_lines=2)
            if career.next_rank_xp is None:
                progress = f"{total} XP GESAMT · MAXIMALRANG"
                ratio = 1.0
            else:
                until = f"{career.xp_to_next_rank:,}".replace(",", ".")
                progress = (f"{total} XP GESAMT · NOCH {until} XP "
                            f"BIS RANG {career.rank_after + 1}")
                previous = RANK_MIN_XP[career.rank_after - 1]
                ratio = max(0., min(1., (career.total_xp - previous) /
                                    max(1, career.next_rank_xp - previous)))
            self._engrave(surface, progress, name="progress",
                          slot=self.last_slots["progress"], color=palette[5],
                          font_size=max(15, int(width * .033)),
                          min_size=12, max_lines=2)
            # Compact engraved XP gauge, centred above the skull pedestal.
            # An inset border makes it a distinct small stone field. The gauge
            # occupies 44% instead of 60% of the original width and is twice
            # as thick for visual weight without touching the side carvings.
            bar = pygame.Rect(cx - round(width * .22), round(height * .812),
                              round(width * .44), max(7, round(width * .016)))
            border = bar.inflate(10, 8)
            pygame.draw.rect(surface, (10, 15, 30, 218), border,
                             border_radius=6)
            pygame.draw.rect(surface, (133, 102, 168, 180), border, 1,
                             border_radius=6)
            pygame.draw.rect(surface, (44, 59, 73, 232), bar,
                             border_radius=4)
            fill_width = round(bar.width * ratio)
            if fill_width:
                pygame.draw.rect(surface, (125, 226, 173, 230),
                                 (bar.x, bar.y, fill_width, bar.height),
                                 border_radius=4)
            self.last_slots["xp_bar"] = border.copy()

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
