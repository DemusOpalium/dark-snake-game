"""FrostAge D20 result panel: one cached modern card for every rolled outcome.

The existing Random-D20 PNG is rendered separately above this panel in game.py.
No scoring, random rolls, display deadlines or game state are changed here.
"""
from math import sin

import pygame


CARD_SIZE = (496, 206)
DICE_DURATION = 5.0


def outcome_for_roll(roll):
    """Return the label, secondary line and accent of an actual D20 result."""
    if roll == 1:
        return ("KRITISCHER", "FEHLSCHLAG", (252, 92, 118))
    if roll == 20:
        return ("KRITISCHER", "ERFOLG", (255, 213, 121))
    if roll >= 16:
        return ("GROSSER ERFOLG", "SELTENER WURF", (242, 185, 100))
    if roll >= 11:
        return ("ERFOLG", "WURF BESTÄTIGT", (99, 234, 203))
    if roll >= 6:
        return ("KLEINER ERFOLG", "WURF BESTÄTIGT", (132, 188, 252))
    return ("FEHLSCHLAG", "NEUER VERSUCH", (227, 112, 145))


class FrostDiceResultVisual:
    """Read-only HUD art. Each number's card is built once; animation is cheap."""

    def __init__(self):
        self._cards = {}
        self._glows = {}
        self._small = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self._tag = pygame.font.SysFont("Segoe UI", 17, bold=True)
        self._title = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self._number = pygame.font.SysFont("Segoe UI", 87, bold=True)

    @staticmethod
    def card_rect(surface):
        return pygame.Rect(
            (surface.get_width() - CARD_SIZE[0]) // 2,
            surface.get_height() // 2 - 43,
            *CARD_SIZE,
        )

    def _create_card(self, roll):
        label, subtitle, accent = outcome_for_roll(roll)
        width, height = CARD_SIZE
        panel = pygame.Surface(CARD_SIZE, pygame.SRCALPHA)

        # Frosted panel with a restrained blue-black gradient and crystalline rim.
        for y in range(height):
            t = y / height
            pygame.draw.line(
                panel,
                (int(12 + 9 * t), int(27 + 7 * t), int(49 + 12 * t), 234),
                (0, y), (width - 1, y),
            )
        # Keep the rounded silhouette; the game below remains softly visible.
        pygame.draw.rect(panel, (7, 17, 33, 234), (0, 0, width, height), border_radius=17)
        pygame.draw.rect(panel, (24, 40, 67, 232), (7, 7, width - 14, height - 14), border_radius=13)
        pygame.draw.rect(panel, (*accent, 174), (1, 1, width - 2, height - 2), 2, border_radius=17)
        pygame.draw.rect(panel, (141, 201, 233, 74), (8, 8, width - 16, height - 16), 1, border_radius=13)
        pygame.draw.line(panel, (*accent, 185), (26, 49), (width - 27, 49), 2)
        pygame.draw.line(panel, (125, 171, 205, 95), (177, 66), (177, 157), 1)
        pygame.draw.rect(panel, (*accent, 185), (15, 20, 4, 30), border_radius=2)

        # Fine "spore" rings: atmosphere without adding a second image pipeline.
        for x, y, radius in ((452, 87, 10), (424, 111, 7), (466, 139, 5),
                             (400, 93, 3), (450, 128, 2)):
            pygame.draw.circle(panel, (*accent, 85), (x, y), radius, 1)

        head = self._small.render("FROSTAGE   /   D20 SIGNAL", True, (190, 218, 237))
        panel.blit(head, (33, 24))
        roll_label = self._small.render("WURF", True, (152, 188, 217))
        panel.blit(roll_label, roll_label.get_rect(center=(100, 72)))
        number = self._number.render(f"{roll:02d}", True, (240, 249, 255))
        panel.blit(number, number.get_rect(center=(100, 122)))

        title = self._title.render(label, True, accent)
        if title.get_width() > width - 230:
            title = self._tag.render(label, True, accent)
        panel.blit(title, (201, 76))
        info = self._tag.render(subtitle, True, (214, 235, 243))
        panel.blit(info, (201, 111))

        # Twenty discrete pips reveal the result at a glance (no extra sprite files).
        for index in range(20):
            filled = index < roll
            color = (*accent, 239) if filled else (77, 98, 131, 132)
            pygame.draw.rect(
                panel, color, (33 + index * 22, 168, 16, 6), border_radius=2,
            )
        hint = self._small.render("WÜRFELPROTOKOLL  /  20", True, (141, 182, 209))
        panel.blit(hint, (34, 182))
        return panel

    def _glow_frames(self, accent):
        if accent not in self._glows:
            frames = []
            for strength in (45, 70, 100, 70):
                light = pygame.Surface((CARD_SIZE[0] - 54, 4), pygame.SRCALPHA)
                light.fill((*accent, strength))
                frames.append(light)
            self._glows[accent] = frames
        return self._glows[accent]

    def draw(self, surface, roll, *, display_until=None, now=None):
        """Display outcome; fade only in the final half-second of a timed roll."""
        if roll not in self._cards:
            self._cards[roll] = self._create_card(roll)
        card = self._cards[roll]
        rect = self.card_rect(surface)
        if now is None:
            import time
            now = time.time()
        alpha = 255
        if display_until is not None and now < display_until:
            remaining = display_until - now
            if remaining < 0.5:
                alpha = max(0, min(255, int(255 * remaining / 0.5)))
        card.set_alpha(alpha)
        surface.blit(card, rect)
        card.set_alpha(255)

        # A lightweight 4-frame light pulse, instead of rebuilding the card at 60 FPS.
        if alpha > 0:
            accent = outcome_for_roll(roll)[2]
            frames = self._glow_frames(accent)
            index = int((sin(now * 5) + 1) * 1.5)
            light = frames[min(len(frames) - 1, index)]
            surface.blit(light, (rect.x + 27, rect.y + 49))
