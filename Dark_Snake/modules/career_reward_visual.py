"""Dark Abyss reward ceremony: decorative, read-only, cached Pygame surface.

This component has NO ownership of XP, skins, persistence or player input.
Only already confirmed CareerCeremony results may name an earned reward.
"""
from __future__ import annotations

import logging
import math

import pygame

from modules.resources import find_asset

LOGGER = logging.getLogger(__name__)
PURPLE = (183, 115, 234)
MYCELIUM = (113, 231, 182)
FROST = (177, 219, 240)
IVORY = (237, 237, 245)
PANEL_HEIGHT = 188
HOLD_SECONDS = 7.0
FADE_SECONDS = 2.0


class MysticRewardPanel:
    """One cached translucent panel, a restrained 12-step aura and slow fade."""

    def __init__(self):
        self.title_font = pygame.font.SysFont("Segoe UI", 23, bold=True)
        self.body_font = pygame.font.SysFont("Segoe UI", 16)
        self.praise_font = pygame.font.SysFont("Segoe UI", 16, italic=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self._key = None
        self._base = None
        self._aura = []
        self._images = {}
        self._shown_key = None
        self._shown_at = None
        self.last_rect = None

    @staticmethod
    def _fit(font, text, width, color):
        original = str(text)
        label = original
        if font.size(label)[0] > width:
            while len(label) > 1 and font.size(label + "…")[0] > width:
                label = label[:-1]
            label += "…"
        return font.render(label, True, color)

    def _picture(self, career):
        if career is None or career.reward_state != "granted":
            return None
        if career.reward_type not in ("head", "body"):
            return None
        key = (career.reward_type, career.reward_filename)
        if not key[1]:
            return None
        if key not in self._images:
            folder = ("SnakeHeadsbibliothek" if key[0] == "head"
                      else "SnakeBodysBibliothek")
            try:
                source = pygame.image.load(
                    str(find_asset("graphics", folder, key[1]))
                ).convert_alpha()
                self._images[key] = pygame.transform.smoothscale(source, (84, 84))
            except (OSError, pygame.error) as exc:
                LOGGER.warning("Reward icon unavailable: %s", exc)
                self._images[key] = None
        return self._images[key]

    @staticmethod
    def _narrative(career, warning):
        if career is None:
            return ("CHRONIK UNGEWISS",
                    "Die Speicherung dieser Runde wurde nicht bestätigt.",
                    "Kein Rang und kein Relikt ohne sicheren Nachweis.")
        if career.reward_state == "granted":
            if career.reward_type == "head":
                name = "SCHLANGENKRONE ERRUNGEN"
                item = "ein neuer Snake Head"
            else:
                name = "PANZER DER TIEFE ERRUNGEN"
                item = "ein neuer Snake Body"
            if career.reward_required_rank is not None:
                why = (f"Für Karriererang {career.reward_required_rank} "
                       f"hast du {item} erhalten.")
            else:
                why = f"Diese Runde hat dir {item} eingebracht."
            return (name, why, "Eine neue Gestalt erhebt sich aus dem Abgrund.")
        if career.reward_state == "pending":
            return ("DIE CHRONIK WARTET",
                    "XP bestätigt. Die Skin-Vergabe ist noch ungeprüft.",
                    "Die Tiefe vergisst nicht – wir prüfen den Eintrag.")
        if career.rank_after > career.rank_before:
            return ("RANGAUFSTIEG IM SCHATTEN",
                    f"Du hast Karriererang {career.rank_after} erreicht.",
                    "Dein Weg durch die Dunkelheit trägt Früchte.")
        return ("CHRONIK DER TIEFE",
                f"Du hast {career.earned_xp:,} XP in dieser Runde verdient.".replace(",", "."),
                "Auch ohne neues Relikt wächst deine Legende.")

    def _prepare(self, width, career, warning):
        key = (width, career, warning)
        if key == self._key and self._base is not None:
            return
        self._key = key
        w, h = width, PANEL_HEIGHT
        base = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(base, (5, 12, 30, 222), (9, 9, w - 18, h - 18),
                         border_radius=20)
        pygame.draw.rect(base, (20, 19, 50, 112), (14, 14, w - 28, h - 28),
                         border_radius=18)
        # Thin stationary smoke wisps; the pulse moves only on the outer aura.
        for rect, color in [
            ((17, 22, w // 2, h - 44), (103, 42, 153, 24)),
            ((w // 2 - 20, 30, w // 2, h - 58), (36, 161, 126, 19)),
            ((w // 4, 72, w // 2, 69), (102, 67, 146, 11)),
        ]:
            pygame.draw.ellipse(base, color, rect)
        pygame.draw.rect(base, (171, 125, 204, 125), (17, 17, w - 34, h - 34),
                         1, border_radius=15)
        pygame.draw.line(base, (103, 188, 160, 74),
                         (w // 2, 20), (w - 37, 20))

        title, reason, praise = self._narrative(career, warning)
        # An actual inventory PNG is shown ONLY for a confirmed reward.
        art = self._picture(career)
        ax, ay = 28, 43
        pygame.draw.circle(base, (91, 45, 127, 112), (70, 84), 54)
        pygame.draw.circle(base, (127, 200, 170, 133), (70, 84), 46, 2)
        pygame.draw.circle(base, (195, 147, 236, 180), (70, 84), 50, 1)
        if art is not None:
            base.blit(art, (ax, ay))
        else:
            # An abstract seal is not a falsely claimed item.
            pygame.draw.circle(base, (83, 174, 147, 129), (70, 84), 21, 2)
            pygame.draw.circle(base, (190, 120, 216, 155), (70, 84), 12, 1)
            pygame.draw.line(base, (170, 206, 199, 170), (70, 65), (70, 103), 2)
            pygame.draw.line(base, (170, 206, 199, 170), (51, 84), (89, 84), 2)

        x = 132
        content_width = w - x - 42
        label = self._fit(self.title_font, title, content_width,
                          MYCELIUM if art is not None else PURPLE)
        base.blit(label, (x, 24))
        base.blit(self._fit(self.body_font, reason, content_width, IVORY),
                  (x, 59))
        base.blit(self._fit(self.praise_font, praise, content_width, FROST),
                  (x, 86))
        if career is not None:
            earned = f"+{career.earned_xp:,} XP".replace(",", ".")
            line = (f"RANG {career.rank_before} → {career.rank_after}   ·   "
                    f"{earned}   ·   GESAMT {career.total_xp:,} XP").replace(",", ".")
            base.blit(self._fit(self.small_font, line, w - 54, FROST),
                      (28, 126))
            if career.next_rank_xp is None:
                progress = "MAXIMALRANG ERREICHT"
                ratio = 1.0
            else:
                progress = (f"NOCH {career.xp_to_next_rank:,} XP "
                            f"BIS RANG {career.rank_after + 1}").replace(",", ".")
                # Ranks 1-40 use verified career thresholds, not guessed
                # scores. Only prepare the bar when the immutable data changes.
                from modules.career_ranks import RANK_MIN_XP
                origin = RANK_MIN_XP[career.rank_after - 1]
                span = career.next_rank_xp - origin
                ratio = max(0., min(1., (career.total_xp - origin) / max(1, span)))
            base.blit(self._fit(self.small_font, progress, w - 54,
                                (163, 194, 210)), (28, 148))
            bar = pygame.Rect(29, 171, w - 58, 4)
            pygame.draw.rect(base, (57, 73, 94, 215), bar, border_radius=2)
            if ratio:
                pygame.draw.rect(base, (137, 222, 170, 210),
                                 (bar.left, bar.top, round(bar.width * ratio), 4),
                                 border_radius=2)
        self._base = base
        # Twelve precomputed glows; no per-frame allocation/gradient generation.
        self._aura = []
        for phase in range(12):
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            strength = int(100 + 35 * math.sin(phase * math.tau / 12))
            for inset, alpha in ((0, 18), (3, 34), (6, strength)):
                outer = pygame.Rect(inset, inset, w - 2 * inset, h - 2 * inset)
                pygame.draw.rect(glow, (156, 81, 216, alpha), outer,
                                 2, border_radius=23)
            center = w // 2
            pygame.draw.line(glow, (*PURPLE, strength),
                             (23, 13), (center, 13), 2)
            pygame.draw.line(glow, (*MYCELIUM, strength),
                             (center, 13), (w - 23, 13), 2)
            pygame.draw.line(glow, (*MYCELIUM, strength // 2),
                             (23, h - 13), (center, h - 13), 1)
            pygame.draw.line(glow, (*PURPLE, strength // 2),
                             (center, h - 13), (w - 23, h - 13), 1)
            self._aura.append(glow)

    def draw(self, target, *, career, warning, rect, now, sequence):
        """Draw to a safe outer-area rect; return current global alpha."""
        self.last_rect = rect.copy()
        stamp = (sequence, career, warning)
        if stamp != self._shown_key:
            self._shown_key = stamp
            self._shown_at = now
        age = max(0.0, now - self._shown_at)
        alpha = 255 if age <= HOLD_SECONDS else int(
            max(0., 1. - (age - HOLD_SECONDS) / FADE_SECONDS) * 255
        )
        if not alpha:
            return 0
        self._prepare(rect.width, career, warning)
        self._base.set_alpha(alpha)
        phase = (int(age * 2.6) % len(self._aura))
        aura = self._aura[phase]
        aura.set_alpha(alpha)
        target.blit(self._base, rect.topleft)
        target.blit(aura, rect.topleft)
        return alpha
