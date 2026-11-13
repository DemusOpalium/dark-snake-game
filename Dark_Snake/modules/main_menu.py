"""FrostAge artwork, layout and input for the main menu."""

from dataclasses import dataclass
from math import ceil

import pygame

from modules.frostage_assets import load_frostage_image


GROUPS = (
    ("Spielen", ("single_player", "multiplayer", "continue", "boss_rush")),
    ("World Studio & Profil", ("level_studio", "workshop", "highscore", "inventory")),
    ("Spielmenü", ("options", "statistics", "credits", "quit")),
)
ARTWORK = {
    key: f"frostage_menu_{key}" for _, keys in GROUPS for key in keys
}
TEXT_LABELS = {
    "single_player": "Einzelspieler", "multiplayer": "Mehrspieler", "continue": "Fortsetzen",
    "boss_rush": "Boss Rush", "level_studio": "Level Studio", "workshop": "Workshop",
    "highscore": "Bestenliste", "inventory": "Inventar", "options": "Optionen",
    "statistics": "Statistik", "credits": "Credits", "quit": "Beenden",
    "controls": "Steuerung", "developer": "Entwickler-Simulation",
}
BACKGROUND_COLOR = (19, 23, 37)
TEXT_COLOR = (239, 245, 255)
ACCENT_COLOR = (159, 229, 255)
SECONDARY_COLOR = (199, 190, 227)
DISABLED_COLOR = (203, 209, 224)


@dataclass(slots=True)
class MenuButton:
    key: str
    asset_id: str | None
    rect: pygame.Rect
    row: int
    column: int
    image: pygame.Surface | None
    disabled_image: pygame.Surface | None


def cover_background(image: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    """Scale a background proportionally and crop the center to fill the menu."""
    width, height = size
    source_width, source_height = image.get_size()
    factor = max(width / source_width, height / source_height)
    scaled = pygame.transform.smoothscale(
        image, (ceil(source_width * factor), ceil(source_height * factor))
    )
    covered = pygame.Surface(size)
    covered.fill(BACKGROUND_COLOR)
    covered.blit(scaled, scaled.get_rect(center=covered.get_rect().center))
    return covered


def _menu_background(image, size):
    background = (cover_background(image, size) if image is not None else pygame.Surface(size))
    if image is None:
        background.fill(BACKGROUND_COLOR)
    # The cool scrim keeps the same buttons readable with bright or transparent artwork.
    shade = pygame.Surface(size, pygame.SRCALPHA)
    shade.fill((9, 13, 28, 140))
    background.blit(shade, (0, 0))
    return background


class FrostAgeMenu:
    def __init__(self, actions, *, can_continue, background=None):
        self.actions = actions
        self.can_continue = can_continue
        self._background_source = background
        self._art = {}
        self._size = None
        self.buttons: tuple[MenuButton, ...] = ()
        self.background = None
        self.focus = "single_player"
        self.hover = None

    def is_enabled(self, key):
        return key in self.actions and (key != "continue" or self.can_continue())

    def _button(self, key, slot, row, column):
        asset_id = ARTWORK.get(key)
        image = None
        disabled_image = None
        if asset_id is not None:
            if asset_id not in self._art:
                self._art[asset_id] = load_frostage_image(asset_id)
            art = self._art[asset_id]
            if art is not None:
                rect = art.get_rect().fit(slot)
                rect.center = slot.center
                image = pygame.transform.smoothscale(art, rect.size)
                disabled_image = image.copy()
                disabled_image.set_alpha(124)
            else:
                rect = slot.copy()
        else:
            rect = slot.copy()
        return MenuButton(key, asset_id, rect, row, column, image, disabled_image)

    def layout(self, size):
        """Prepare cached graphics and click targets for the current viewport."""
        if self._size == size:
            return
        self._size = size
        width, height = size
        self.background = _menu_background(self._background_source, size)
        scale = min(width / 900, height / 620)
        self._label_font = pygame.font.SysFont("Segoe UI", max(14, round(17 * scale)), bold=True)
        self._small_font = pygame.font.SysFont("Segoe UI", max(13, round(14 * scale)))
        self._title = pygame.font.SysFont("Georgia", max(36, round(49 * scale)), bold=True).render(
            "DARK SNAKE", True, TEXT_COLOR
        )
        self._title_pos = self._title.get_rect(center=(width // 2, round(height * 0.091)))
        self._subtitle = self._label_font.render("FROST AGE", True, ACCENT_COLOR)
        self._subtitle_pos = self._subtitle.get_rect(midtop=(width // 2, self._title_pos.bottom + 2))
        self._rule_y = round(height * 0.174)
        margin = round(width * 0.052)
        gap = round(width * 0.018)
        panel_width = (width - 2 * margin - 2 * gap) // 3
        panel_top = round(height * 0.196)
        panel_bottom = round(height * 0.882)
        heading_height = round(height * 0.063)
        row_height = (panel_bottom - panel_top - heading_height - 4) // 4
        art_height = row_height - self._small_font.get_linesize() - 4
        buttons = []
        self._panels = []
        for column, (title, keys) in enumerate(GROUPS):
            x = margin + column * (panel_width + gap)
            panel = pygame.Rect(x, panel_top, panel_width, panel_bottom - panel_top)
            heading = self._label_font.render(title, True, SECONDARY_COLOR)
            heading_pos = heading.get_rect(center=(panel.centerx, panel_top + heading_height // 2))
            self._panels.append((panel, heading, heading_pos))
            for row, key in enumerate(keys):
                slot = pygame.Rect(x + 12, panel_top + heading_height + row * row_height,
                                   panel_width - 24, art_height)
                buttons.append(self._button(key, slot, row, column))

        links = tuple(key for key in ("controls", "developer") if key in self.actions)
        link_width = min(round(225 * scale), (width - 2 * margin - gap) // 2)
        link_height = round(height * 0.056)
        links_width = len(links) * link_width + max(0, len(links) - 1) * gap
        for column, key in enumerate(links):
            slot = pygame.Rect((width - links_width) // 2 + column * (link_width + gap),
                               round(height * 0.912), link_width, link_height)
            buttons.append(self._button(key, slot, 4, column))
        self.buttons = tuple(buttons)
        self.hover = None

        self._panel_backdrops = []
        for panel, _, _ in self._panels:
            panel_image = pygame.Surface(panel.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_image, (13, 16, 29, 222), panel_image.get_rect(), border_radius=14)
            self._panel_backdrops.append(panel_image)
        self._disabled_labels = {
            "continue": self._small_font.render("Keine pausierte Runde", True, DISABLED_COLOR),
            "unavailable": self._small_font.render("Nicht verfügbar", True, DISABLED_COLOR),
        }
        self._fallback_labels = {
            key: self._label_font.render(TEXT_LABELS[key], True, TEXT_COLOR)
            for key in (*ARTWORK, *links)
        }

    def _ensure_focus(self):
        if not self.is_enabled(self.focus):
            self.focus = next((button.key for button in self.buttons if self.is_enabled(button.key)), None)

    def _cycle_focus(self, offset):
        enabled = [button.key for button in self.buttons if self.is_enabled(button.key)]
        if enabled:
            index = enabled.index(self.focus)
            self.focus = enabled[(index + offset) % len(enabled)]

    def _move_horizontal(self, offset):
        current = next((button for button in self.buttons if button.key == self.focus), None)
        if current is None:
            return
        candidates = [button for button in self.buttons if self.is_enabled(button.key)
                      and (button.column - current.column) * offset > 0]
        if candidates:
            self.focus = min(candidates, key=lambda button: (
                abs(button.row - current.row), abs(button.column - current.column)
            )).key

    def _at(self, pos):
        return next((button.key for button in self.buttons if button.rect.collidepoint(pos)), None)

    def handle_event(self, event, actions):
        self._ensure_focus()
        if event.type == pygame.WINDOWLEAVE:
            self.hover = None
            return
        if event.type == pygame.MOUSEMOTION:
            self.hover = self._at(event.pos)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            key = self._at(event.pos)
            if self.is_enabled(key):
                self.focus = key
                self.actions[key]()
            return

        key = event.key if event.type == pygame.KEYDOWN else None
        if "menu_accept" in actions:
            if self.is_enabled(self.focus):
                self.actions[self.focus]()
        elif key == pygame.K_DOWN or "p1_down" in actions or "p2_down" in actions:
            self._cycle_focus(1)
        elif key == pygame.K_UP or "p1_up" in actions or "p2_up" in actions:
            self._cycle_focus(-1)
        elif key == pygame.K_RIGHT or "p1_right" in actions or "p2_right" in actions:
            self._move_horizontal(1)
        elif key == pygame.K_LEFT or "p1_left" in actions or "p2_left" in actions:
            self._move_horizontal(-1)

    def draw(self, screen):
        self.layout(screen.get_size())
        self._ensure_focus()
        screen.blit(self.background, (0, 0))
        screen.blit(self._title, self._title_pos)
        screen.blit(self._subtitle, self._subtitle_pos)
        pygame.draw.line(screen, (111, 120, 164), (self._size[0] // 5, self._rule_y),
                         (self._size[0] * 4 // 5, self._rule_y))
        for (panel, heading, heading_pos), panel_image in zip(self._panels, self._panel_backdrops):
            screen.blit(panel_image, panel)
            pygame.draw.rect(screen, (89, 88, 127), panel, width=1, border_radius=14)
            screen.blit(heading, heading_pos)

        for button in self.buttons:
            enabled = self.is_enabled(button.key)
            active = enabled and button.key in (self.focus, self.hover)
            if active:
                outline = ACCENT_COLOR if button.key == self.focus else SECONDARY_COLOR
                pygame.draw.rect(screen, (38, 51, 77), button.rect.inflate(8, 5), border_radius=8)
                pygame.draw.rect(screen, outline, button.rect.inflate(8, 5), width=2, border_radius=8)
            if button.image is not None:
                screen.blit(button.image if enabled else button.disabled_image, button.rect)
            else:
                pygame.draw.rect(screen, (39, 43, 66) if enabled else (35, 37, 51),
                                 button.rect, border_radius=7)
                label = self._fallback_labels[button.key]
                screen.blit(label, label.get_rect(center=button.rect.center))
            if not enabled:
                reason = self._disabled_labels.get(button.key, self._disabled_labels["unavailable"])
                screen.blit(reason, reason.get_rect(midtop=(button.rect.centerx, button.rect.bottom)))
