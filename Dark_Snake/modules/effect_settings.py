"""Brush settings and map markings for the World Studio effect layer."""

import pygame

from modules.level_effects import DamageField, SlowField, SLOW_PERCENTAGES


EFFECT_COLORS = {"damage": (244, 104, 127), "slow": (197, 145, 247)}
_FIELD_LABELS = ("Schaden pro Treffer (HP)", "Trefferintervall (s)", "Wirkungsdauer (s, leer = unbegrenzt)")


def _display_number(value):
    return f"{value:g}".replace(".", ",")


class EffectSettings:
    """Edit brush presets without applying anything to the level."""

    def __init__(self, damage, slow, bounds):
        self.values = [str(damage.amount), _display_number(damage.interval),
                       "" if damage.duration is None else _display_number(damage.duration)]
        self.slow_percent = slow.percent
        self.field = 0
        self.select_all = True
        self.error = ""
        self.set_bounds(bounds)

    def set_bounds(self, bounds):
        self.panel = pygame.Rect(0, 0, min(500, bounds.width - 40), 322)
        self.panel.center = bounds.center

    def _fields(self):
        for index in range(len(_FIELD_LABELS)):
            yield pygame.Rect(self.panel.x + 20, self.panel.y + 60 + index * 48, self.panel.width - 40, 24)

    def _slow_buttons(self):
        width = (self.panel.width - 56) // len(SLOW_PERCENTAGES)
        for index, percent in enumerate(SLOW_PERCENTAGES):
            yield percent, pygame.Rect(self.panel.x + 20 + index * (width + 4),
                                       self.panel.y + 222, width, 26)

    def _confirm_button(self):
        return pygame.Rect(self.panel.right - 136, self.panel.bottom - 38, 116, 26)

    def _cancel_button(self):
        return pygame.Rect(self.panel.x + 20, self.panel.bottom - 38, 116, 26)

    def _focus(self, field):
        self.field = field
        self.select_all = True

    def _submit(self):
        amount, interval, duration = self.values
        try:
            values = (int(amount), float(interval.replace(",", ".")),
                      float(duration.replace(",", ".")) if duration.strip() else None)
        except ValueError:
            self.error = "Bitte gültige Zahlen eingeben."
            return None
        try:
            return DamageField(*values), SlowField(self.slow_percent)
        except ValueError as error:
            self.error = str(error)
            return None

    def handle_event(self, event):
        """Return an accepted brush pair or False for explicit cancel."""
        if event.type == pygame.KEYDOWN:
            mod = getattr(event, "mod", 0)
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._submit()
            if event.key == pygame.K_TAB:
                step = -1 if mod & pygame.KMOD_SHIFT else 1
                self._focus((self.field + step) % len(self.values))
            elif event.key == pygame.K_a and mod & pygame.KMOD_CTRL:
                self.select_all = True
            elif event.key == pygame.K_BACKSPACE:
                self.values[self.field] = "" if self.select_all else self.values[self.field][:-1]
                self.select_all = False
        elif event.type == pygame.TEXTINPUT:
            text = "".join(char for char in event.text if char in "0123456789.,")
            if text:
                previous = "" if self.select_all else self.values[self.field]
                self.values[self.field] = (previous + text)[:12]
                self.select_all = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self._fields()):
                if rect.collidepoint(event.pos):
                    self._focus(index)
                    return None
            for percent, rect in self._slow_buttons():
                if rect.collidepoint(event.pos):
                    self.slow_percent = percent
                    return None
            if self._cancel_button().collidepoint(event.pos):
                return False
            if self._confirm_button().collidepoint(event.pos):
                return self._submit()
        return None

    def draw(self, screen, text, button):
        panel = self.panel
        pygame.draw.rect(screen, (25, 25, 25), panel)
        pygame.draw.rect(screen, (255, 255, 0), panel, 2)
        text(screen, "Effektwerte für neue Felder", (panel.x + 20, panel.y + 12))
        for index, (label, rect, value) in enumerate(zip(_FIELD_LABELS, self._fields(), self.values)):
            text(screen, label, (rect.x, rect.y - 18))
            outline = EFFECT_COLORS["damage"] if index == self.field else None
            button(screen, value or "–", rect, outline)
            if index == self.field and self.select_all:
                text(screen, "Eingabe ersetzt Wert", (rect.right - 142, rect.y + 5), (195, 195, 195))
        text(screen, "Verlangsamung", (panel.x + 20, panel.y + 202))
        for percent, rect in self._slow_buttons():
            outline = EFFECT_COLORS["slow"] if percent == self.slow_percent else None
            button(screen, f"{percent} %", rect, outline)
        if self.error:
            text(screen, self.error, (panel.x + 20, panel.y + 255), EFFECT_COLORS["damage"],
                 max_width=panel.width - 40)
        button(screen, "Abbrechen", self._cancel_button())
        button(screen, "Übernehmen", self._confirm_button())


def draw_effect_overlay(screen, map_rect, cell_size, effects):
    for (x, y), cell in effects.items():
        left = map_rect.x + x * cell_size
        top = map_rect.y + y * cell_size
        width = cell_size - 6
        if cell.damage is not None:
            pygame.draw.rect(screen, EFFECT_COLORS["damage"], (left + 3, top + 3, width, 2))
        if cell.slow is not None:
            pygame.draw.rect(screen, EFFECT_COLORS["slow"], (left + 3, top + cell_size - 5, width, 2))
