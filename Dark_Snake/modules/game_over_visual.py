"""Dark Abyss: a standalone cinematic Game Over screen with real round statistics.

No text or controls are baked into the artist's background PNG. The epitaph
library is loaded once from bundled JSON and can be edited via a reviewed PR.
"""
import json
import logging
import time

import pygame

from modules.resources import find_asset
from modules.career_reward_visual import MysticRewardPanel, PANEL_HEIGHT
from modules.tombstone_reward_visual import TombstoneRewardPanel, portrait_size

LOGGER = logging.getLogger(__name__)
ABYSS_IMAGE = ("graphics", "game_over", "dark_abyss.png")
RITES_FILE = ("text", "game_over_rites.json")
INK = (9, 14, 27)
FROST = (167, 218, 242)
ASH = (222, 225, 227)
BLOOD = (214, 99, 121)

# A non-blocking theatrical reveal, not a second score calculation.
# The values in the finished card always come from confirmed round counters.
TITLE_TEXT = "GAME OVER"
TITLE_LETTER_SECONDS = 0.125
COUNTER_START_SECONDS = len(TITLE_TEXT) * TITLE_LETTER_SECONDS + 0.25
COUNTER_DURATION_SECONDS = 2.85
# Provisional visual atmosphere thresholds – NOT skill ratings or achievements.
# Each metric needs its own scale (a boss != one ordinary enemy).
CEREMONY_TIERS = {
    "PUNKTE": (0, 200, 1000, 3000, 7000, 14000),
    "EBENE": (0, 2, 3, 4, 6, 9),
    "GEGNER": (0, 5, 15, 35, 90, 160),
    "BOSSE": (0, 1, 2, 3, 6, 10),
}
CEREMONY_COLORS = (
    (208, 211, 219),  # Asche
    (164, 217, 241),  # Frost
    (151, 230, 185),  # Myzel
    (203, 172, 236),  # Nachtviolett
    (238, 210, 147),  # Reliktgold
    (250, 232, 189),  # Legendärer Schein
)


def revealed_title_letters(elapsed):
    """Number of visible title glyphs, independent of frame rate."""
    return min(len(TITLE_TEXT), max(0, int(max(0.0, elapsed) / TITLE_LETTER_SECONDS)))


def revealed_counter(actual, elapsed):
    """Read-only ease-out counter, bounded even for millions of points."""
    total = max(0, int(actual))
    progress = max(0.0, min(1.0, (elapsed - COUNTER_START_SECONDS) /
                            COUNTER_DURATION_SECONDS))
    fraction = 1.0 - (1.0 - progress) ** 3
    return total if progress >= 1.0 else min(total, int(total * fraction))


def ceremony_color(metric, displayed):
    """Color of *visible* value; color changes as the counter passes tiers."""
    thresholds = CEREMONY_TIERS[metric]
    tier = sum(displayed >= limit for limit in thresholds) - 1
    return CEREMONY_COLORS[max(0, min(tier, len(CEREMONY_COLORS) - 1))]


RITE_FALLBACK = {
    "common": ["Die Tiefe kennt keine Rückkehr."],
    "boss_victor": ["Die Wächter fielen zuerst. Am Ende blieb nur die Tiefe."],
    "high_level": ["Viele Ebenen lagen hinter dir. Keine führte ans Licht."],
    "two_player": ["Zwei Schatten. Ein Abgrund. Kein Echo antwortet."],
}


def load_rites():
    """Gracefully accept curated extra lines, never download text during gameplay."""
    try:
        with open(find_asset(*RITES_FILE), encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return RITE_FALLBACK
        return {
            key: [line for line in data.get(key, [])
                  if isinstance(line, str) and 0 < len(line) <= 180][:100]
            or list(RITE_FALLBACK[key])
            for key in RITE_FALLBACK
        }
    except (OSError, ValueError, TypeError) as exc:
        LOGGER.warning("Game Over rites unavailable; using fallback: %s", exc)
        return RITE_FALLBACK


def tombstone_scene_layout(size):
    """Side-by-side: full-size engraved reward and untouched stats/input area.

    Smaller windows intentionally retain the earlier compact layout. The
    portrait never overlaps the 700px stats panel, name field or action buttons.
    """
    width, height = size
    if width < 1180 or height < 820:
        return None
    panel_width = 700
    gap = 30
    # Keep the proven statistics/name column nearly where it was. Give the
    # entire gothic outline a deliberate right-side breathing margin instead
    # of letting its frosty spires almost meet the window edge.
    left = max(20, round(width * .025))
    right_margin = max(48, round(width * .058))
    stone_width, stone_height = portrait_size(
        width - left - panel_width - gap - right_margin, height - 112,
    )
    if stone_width < 350:
        return None
    # Ground the skull-carved foot precisely at the screen's lower edge.
    # The PNG itself remains fully visible and keeps its 2:3 aspect ratio.
    stone_rect = pygame.Rect(left + panel_width + gap,
                             height - stone_height,
                             stone_width, stone_height)
    return left, panel_width, stone_rect


def choose_rite(rites, *, score, level, foes, relics, bosses, players):
    """Select a deterministic epitaph using only real round information."""
    category = ("two_player" if players == 2 else
                "boss_victor" if bosses else
                "high_level" if level >= 4 else "common")
    variants = rites.get(category) or RITE_FALLBACK[category]
    index = (max(0, score) + max(1, level) + max(0, foes) + max(0, relics)) % len(variants)
    return variants[index]


class DarkAbyssGameOver:
    """Lazy image load and cached typography for the fatal, non-interactive scene."""

    def __init__(self):
        self._image = None
        try:
            self._image = pygame.image.load(str(find_asset(*ABYSS_IMAGE))).convert()
        except (OSError, pygame.error) as exc:
            LOGGER.warning("Dark Abyss artwork unavailable; dark fallback: %s", exc)
        self._backdrop = None
        self._backdrop_size = None
        self._panel = None
        self._panel_size = None
        self._rites = load_rites()
        self._font_kicker = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self._font_title = pygame.font.SysFont("Segoe UI", 59, bold=True)
        self._font_subtitle = pygame.font.SysFont("Segoe UI", 21)
        self._font_rite = pygame.font.SysFont("Segoe UI", 23)
        self._font_stat_name = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self._font_stat_value = pygame.font.SysFont("Segoe UI", 29, bold=True)
        self._font_button = pygame.font.SysFont("Segoe UI", 21, bold=True)
        self._font_input = pygame.font.SysFont("Segoe UI", 24)
        self._font_career_small = pygame.font.SysFont("Segoe UI", 13)
        # The full title and its typed prefixes stay at one stable anchor.
        self._reveal_title_frames = tuple(
            self._font_title.render(TITLE_TEXT[:i], True, (234, 235, 240))
            for i in range(len(TITLE_TEXT) + 1)
        )
        self._reveal_started = None
        self._reveal_sequence = None
        self._metric_label_cache = {}
        self.last_reveal_numbers = None  # diagnostic only, no gameplay write
        self.last_reveal_title = ""
        self._career_card_key = None
        self._career_card_cache = None
        self._reward_images = {}
        self._mystic_reward = MysticRewardPanel()  # Medium-window fallback.
        self._tombstone_reward = TombstoneRewardPanel()
        self._cached_rite_key = None
        self._cached_rite_surface = None

    def _elapsed_since_abyss(self, now, sequence, values):
        # When the death-soul/fog sequence is shown, draw() is not called.
        # Therefore the ceremony begins when this real Game-Over view appears.
        stamp = (sequence, values)
        if self._reveal_sequence != stamp:
            self._reveal_sequence = stamp
            self._reveal_started = now
            self._metric_label_cache.clear()
        return max(0.0, now - self._reveal_started)

    def _metric_number(self, index, visible, color, max_width):
        key = (visible, color, max_width)
        cached = self._metric_label_cache.get(index)
        if cached is not None and cached[0] == key:
            return cached[1]
        # Keep every digit, including six-digit and higher scores. Smaller
        # fonts beat accidental numerical truncation on the game-over card.
        text = f"{visible:,}".replace(",", ".")
        font = self._font_stat_value
        if font.size(text)[0] > max_width:
            for size in range(27, 15, -1):
                candidate = pygame.font.SysFont("Segoe UI", size, bold=True)
                if candidate.size(text)[0] <= max_width:
                    font = candidate
                    break
        label = font.render(text, True, color)
        self._metric_label_cache[index] = (key, label)
        return label

    def _image_for(self, size):
        if self._backdrop_size != size:
            w, h = size
            if self._image is not None:
                iw, ih = self._image.get_size()
                # Cover instead of distortion: preserve cliff shapes and the abyss.
                ratio = max(w / iw, h / ih)
                image = pygame.transform.smoothscale(
                    self._image, (max(w, round(iw * ratio)), max(h, round(ih * ratio))),
                )
                source = pygame.Rect(
                    (image.get_width() - w) // 2,
                    (image.get_height() - h) // 2, w, h,
                )
                self._backdrop = image.subsurface(source).copy()
            else:
                self._backdrop = pygame.Surface(size)
                self._backdrop.fill((8, 15, 28))
                for x, y, radius in ((w // 5, h // 3, 55), (4 * w // 5, h // 2, 70)):
                    pygame.draw.circle(self._backdrop, (13, 33, 53), (x, y), radius)
            self._backdrop_size = size
        return self._backdrop

    def _panel_for(self, width):
        size = (width, 418)
        if size != self._panel_size:
            self._panel = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(self._panel, (7, 13, 27, 221),
                             (0, 0, width, 418), border_radius=20)
            pygame.draw.rect(self._panel, (111, 164, 190, 162),
                             (1, 1, width - 2, 416), 2, border_radius=20)
            pygame.draw.rect(self._panel, (63, 100, 145, 100),
                             (10, 10, width - 20, 398), 1, border_radius=15)
            pygame.draw.line(self._panel, (169, 73, 97, 190),
                             (32, 106), (width - 32, 106), 2)
            # Tiny celestial seals and fungal spores, always outside the text area.
            for x, y, radius in ((width - 43, 43, 12), (width - 72, 61, 5),
                                 (width - 30, 80, 3), (30, 382, 4)):
                pygame.draw.circle(self._panel, (122, 189, 218, 110),
                                   (x, y), radius, 1)
            self._panel_size = size
        return self._panel

    @staticmethod
    def _blit_center(surface, label, center_x, top):
        surface.blit(label, label.get_rect(midtop=(center_x, top)))

    def _fit(self, font, text, color, max_width):
        rendered = font.render(str(text), True, color)
        if rendered.get_width() <= max_width:
            return rendered
        label = str(text)
        while len(label) > 1 and font.size(label + "…")[0] > max_width:
            label = label[:-1]
        return font.render(label + "…", True, color)

    def _draw_buttons(self, surface, buttons):
        for btn in buttons:
            frame = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
            frame.fill((12, 22, 43, 218) if not btn.is_hovered else
                       (34, 58, 78, 238))
            surface.blit(frame, btn.rect)
            pygame.draw.rect(surface,
                             (111, 185, 210) if btn.is_hovered else (80, 127, 158),
                             btn.rect, 2, border_radius=8)
            label = self._font_button.render(btn.text, True, FROST)
            surface.blit(label, label.get_rect(center=btn.rect.center))

    def _draw_name_input(self, surface, *, name, width, top, clock_time,
                         center_x=None):
        center_x = surface.get_width() // 2 if center_x is None else center_x
        x = center_x - width // 2
        label = self._font_kicker.render("EINTRAG INS TOTENBUCH  ·  NAME", True, FROST)
        self._blit_center(surface, label, center_x, top)
        rect = pygame.Rect(x + 90, top + 30, width - 180, 51)
        pygame.draw.rect(surface, (6, 14, 29), rect, border_radius=7)
        pygame.draw.rect(surface, (117, 180, 200), rect, 2, border_radius=7)
        shown = str(name)
        # Leave the user's full input untouched; only clip its visible tail.
        while shown and self._font_input.size(shown)[0] > rect.width - 38:
            shown = shown[1:]
        text = self._font_input.render(shown, True, ASH)
        surface.blit(text, (rect.x + 12, rect.y + (rect.height - text.get_height()) // 2))
        if int(clock_time * 2) % 2 == 0:
            cx = min(rect.right - 14, rect.x + 14 + text.get_width())
            pygame.draw.line(surface, FROST,
                             (cx, rect.y + 9), (cx, rect.bottom - 9), 2)

    @staticmethod
    def _format_xp(number):
        return f"{number:,}".replace(",", ".")

    def _reward_image(self, career):
        """Load the confirmed cosmetic once, never reread the PNG per frame."""
        if career.reward_state != "granted" or not career.reward_filename:
            return None
        key = (career.reward_type, career.reward_filename)
        if key not in self._reward_images:
            folder = ("SnakeHeadsbibliothek" if career.reward_type == "head"
                      else "SnakeBodysBibliothek")
            try:
                image = pygame.image.load(
                    str(find_asset("graphics", folder, career.reward_filename))
                ).convert_alpha()
                self._reward_images[key] = pygame.transform.smoothscale(image, (47, 47))
            except (OSError, pygame.error) as exc:
                LOGGER.warning("Confirmed Snake reward artwork unavailable: %s", exc)
                self._reward_images[key] = None
        return self._reward_images[key]

    def _career_card(self, width, career, warning):
        """Cache a compact FrostAge career card below metrics, above name input."""
        key = (width, career, warning)
        if key == self._career_card_key and self._career_card_cache is not None:
            return self._career_card_cache
        card = pygame.Surface((width - 56, 65), pygame.SRCALPHA)
        pygame.draw.rect(card, (9, 25, 44, 247), card.get_rect(),
                         border_radius=8)
        pygame.draw.rect(card, (76, 142, 176, 201), card.get_rect(), 1,
                         border_radius=8)
        if career is None:
            title = ("KARRIERE · SPEICHERUNG NICHT BESTÄTIGT" if warning
                     else "DIE CHRONIK ENDET HIER")
            self._blit_center(card, self._fit(
                self._font_stat_name, title, FROST, card.get_width() - 26
            ), card.get_width() // 2, 23)
        else:
            header = (f"KARRIERE  ·  RANG {career.rank_before} → "
                      f"{career.rank_after}   ·   +{self._format_xp(career.earned_xp)} XP")
            if career.reward_state == "granted":
                kind = "SNAKE HEAD" if career.reward_type == "head" else "SNAKE BODY"
                reward = f"NEU FREIGESCHALTET: {kind}"
            elif career.reward_state == "pending":
                reward = "SKIN-BELOHNUNG WIRD NOCH GEPRÜFT"
            else:
                reward = "KEIN NEUER SKIN IN DIESER RUNDE"
            if career.next_rank_xp is None:
                progress = f"{self._format_xp(career.total_xp)} XP GESAMT · MAXIMALRANG"
            else:
                progress = (f"{self._format_xp(career.total_xp)} / "
                            f"{self._format_xp(career.next_rank_xp)} XP · "
                            f"NOCH {self._format_xp(career.xp_to_next_rank)} BIS "
                            f"RANG {career.rank_after + 1}")
            image = self._reward_image(career)
            text_width = card.get_width() - (83 if image is not None else 28)
            for value, font, color, y in (
                (header, self._font_stat_name, FROST, 4),
                (reward, self._font_stat_name, (223, 202, 139)
                 if image is not None else ASH, 25),
                (progress, self._font_career_small, (153, 188, 204), 47),
            ):
                card.blit(self._fit(font, value, color, text_width),
                          (13, y))
            if image is not None:
                card.blit(image, (card.get_width() - 57, 9))
        self._career_card_key = key
        self._career_card_cache = card
        return card

    def draw(self, surface, *, score, level, enemies, items, bosses, players,
             highscore_entry, name_input, buttons, now=None,
             career=None, career_warning=False, reward_sequence=None):
        """Render an epitaph above the abyss without modifying gameplay state."""
        now = time.monotonic() if now is None else now
        width, height = surface.get_size()
        surface.blit(self._image_for((width, height)), (0, 0))
        # The title sits high so the luminous falling abyss remains visible below.
        scene = (tombstone_scene_layout((width, height))
                 if career is not None or career_warning else None)
        panel_width = scene[1] if scene is not None else min(700, width - 40)
        left = scene[0] if scene is not None else (width - panel_width) // 2
        top = max(20, int(height * 0.057))
        surface.blit(self._panel_for(panel_width), (left, top))
        center_x = left + panel_width // 2
        actual_values = (score, level, enemies, bosses, items, players)
        elapsed = self._elapsed_since_abyss(
            now, reward_sequence, actual_values
        )

        kicker = self._font_kicker.render("DARK SNAKE   /   THE LAST RITE", True, FROST)
        self._blit_center(surface, kicker, center_x, top + 19)
        letters = revealed_title_letters(elapsed)
        self.last_reveal_title = TITLE_TEXT[:letters]
        complete_title_width = self._reveal_title_frames[-1].get_width()
        # Anchor left to the FINISHED centred text. Typing never jumps.
        surface.blit(self._reveal_title_frames[letters],
                     (center_x - complete_title_width // 2, top + 43))
        subtitle = self._font_subtitle.render(
            "DER ABGRUND HAT EINEN WEITEREN NAMEN", True, BLOOD)
        self._blit_center(surface, subtitle, center_x, top + 118)

        values = (score, level, enemies, items, bosses, players)
        if values != self._cached_rite_key:
            rite = choose_rite(self._rites, score=score, level=level,
                               foes=enemies, relics=items, bosses=bosses, players=players)
            self._cached_rite_surface = self._fit(
                self._font_rite, rite, (224, 231, 238), panel_width - 74)
            self._cached_rite_key = values
        self._blit_center(surface, self._cached_rite_surface,
                          center_x, top + 156)

        chronicle = f"Bis Ebene {level}. {enemies} Feinde gefallen. {items} Relikte geborgen."
        self._blit_center(surface,
                          self._fit(self._font_subtitle, chronicle, FROST,
                                    panel_width - 72),
                          center_x, top + 203)

        # Only real gameplay counters. Two-player values describe the shared run.
        metrics = (("PUNKTE", score), ("EBENE", level),
                   ("GEGNER", enemies), ("BOSSE", bosses))
        gap = 12
        margin = 28
        metric_width = (panel_width - 2 * margin - 3 * gap) // 4
        visible_values = []
        for index, (title_text, number) in enumerate(metrics):
            shown = revealed_counter(number, elapsed)
            visible_values.append(shown)
            tint = ceremony_color(title_text, shown)
            rect = pygame.Rect(left + margin + index * (metric_width + gap),
                               top + 265, metric_width, 82)
            pygame.draw.rect(surface, (16, 28, 48), rect, border_radius=8)
            pygame.draw.rect(surface, tint, rect, 1, border_radius=8)
            tag = self._font_stat_name.render(title_text, True, (145, 187, 207))
            value = self._metric_number(index, shown, tint, rect.width - 18)
            surface.blit(tag, tag.get_rect(center=(rect.centerx, rect.y + 20)))
            surface.blit(value, value.get_rect(center=(rect.centerx, rect.y + 53)))
        self.last_reveal_numbers = tuple(visible_values)

        # Recover the original breathing space below the four stat boxes.
        # On large screens the separate ceremony appears well BELOW the
        # leaderboard input/buttons, in the luminous abyss itself.
        last_line = ("ZWEI GEFALLENE · EIN GEMEINSAMES SCHICKSAL"
                     if players == 2 else "DIE CHRONIK ENDET HIER")
        line = self._font_kicker.render(last_line, True, (167, 183, 195))
        self._blit_center(surface, line, center_x, top + 376)

        if highscore_entry:
            self._draw_name_input(surface, name=name_input, width=panel_width,
                                  top=top + 450, clock_time=now, center_x=center_x)
        else:
            self._draw_buttons(surface, buttons)

        if career is not None or career_warning:
            if scene is not None:
                # Gothic portrait is next to the original Game Over summary,
                # never squeezed below the name entry at 1350×930.
                self._tombstone_reward.draw(
                    surface, career=career, warning=career_warning,
                    rect=scene[2], now=now, sequence=reward_sequence,
                )
            else:
                reward_width = min(742, width - 52)
                reward_top = top + 564
                if reward_top + PANEL_HEIGHT + 17 <= height:
                    reward_rect = pygame.Rect(
                        (width - reward_width) // 2, reward_top,
                        reward_width, PANEL_HEIGHT,
                    )
                    self._mystic_reward.draw(
                        surface, career=career, warning=career_warning,
                        rect=reward_rect, now=now, sequence=reward_sequence,
                    )
                else:
                    # At 900×620 there is not enough space below the name box.
                    # Preserve an unobstructed compact XP card instead.
                    surface.blit(self._career_card(
                        panel_width, career, career_warning
                    ), (left + 28, top + 350))
