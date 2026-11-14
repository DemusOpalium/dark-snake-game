"""Edit the per-level player visibility windows for the roof layer."""

import pygame

from modules.roof_settings import RoofVisibility


FIELDS = ("Sichtradius in Rasterfeldern", "Transparenz in Prozent", "Weicher Rand in Rasterfeldern")
OUTLINE = (142, 210, 250)
ERROR = (244, 104, 127)


class RoofSettingsEditor:
    def __init__(self, settings, bounds):
        self.enabled = settings.enabled
        self.values = [f"{settings.radius:g}", str(settings.transparency), f"{settings.softness:g}"]
        self.field = 0
        self.select_all = True
        self.error = ""
        self.panel = pygame.Rect(0, 0, min(520, bounds.width - 40), 307)
        self.panel.center = bounds.center
        self.toggle = pygame.Rect(self.panel.x + 20, self.panel.y + 36, self.panel.width - 40, 26)
        self.fields = tuple(pygame.Rect(self.panel.x + 20, self.panel.y + 88 + index * 48,
                                        self.panel.width - 40, 26)
                            for index in range(len(FIELDS)))
        self.cancel = pygame.Rect(self.panel.x + 20, self.panel.bottom - 39, 116, 26)
        self.confirm = pygame.Rect(self.panel.right - 136, self.panel.bottom - 39, 116, 26)

    def _focus(self, index):
        self.field = index
        self.select_all = True

    def _submit(self):
        radius, transparency, softness = self.values
        try:
            values = float(radius.replace(",", ".")), int(transparency), float(softness.replace(",", "."))
        except ValueError:
            self.error = "Bitte gültige Zahlen eingeben. Transparenz als ganze Zahl."
            return None
        try:
            return RoofVisibility(self.enabled, *values)
        except ValueError as error:
            self.error = str(error)
            return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            mod = getattr(event, "mod", 0)
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._submit()
            if event.key == pygame.K_TAB:
                step = -1 if mod & pygame.KMOD_SHIFT else 1
                self._focus((self.field + step) % len(self.fields))
            elif event.key == pygame.K_a and mod & pygame.KMOD_CTRL:
                self.select_all = True
            elif event.key == pygame.K_BACKSPACE:
                value = self.values[self.field]
                self.values[self.field] = "" if self.select_all else value[:-1]
                self.select_all = False
        elif event.type == pygame.TEXTINPUT:
            value = "".join(char for char in event.text if char in "0123456789.,")
            if value:
                previous = "" if self.select_all else self.values[self.field]
                self.values[self.field] = (previous + value)[:12]
                self.select_all = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle.collidepoint(event.pos):
                self.enabled = not self.enabled
            elif self.cancel.collidepoint(event.pos):
                return False
            elif self.confirm.collidepoint(event.pos):
                return self._submit()
            else:
                for index, rect in enumerate(self.fields):
                    if rect.collidepoint(event.pos):
                        self._focus(index)
                        break
        return None

    def draw(self, screen, text, button):
        panel = self.panel
        pygame.draw.rect(screen, (25, 25, 25), panel)
        pygame.draw.rect(screen, OUTLINE, panel, 2)
        text(screen, "Dach-Sichtfenster für dieses Level", (panel.x + 20, panel.y + 12))
        button(screen, "Sichtfenster an" if self.enabled else "Sichtfenster aus",
               self.toggle, OUTLINE if self.enabled else None)
        for index, (label, rect, value) in enumerate(zip(FIELDS, self.fields, self.values)):
            text(screen, label, (rect.x, rect.y - 18))
            button(screen, value or "–", rect, OUTLINE if index == self.field else None)
            if index == self.field and self.select_all:
                text(screen, "Eingabe ersetzt Wert", (rect.right - 142, rect.y + 5), (195, 195, 195))
        text(screen, self.error or "Ein Sichtfenster pro Spieler unter dem Dach.",
             (panel.x + 20, panel.y + 238), ERROR if self.error else (195, 195, 195),
             max_width=panel.width - 40)
        button(screen, "Abbrechen", self.cancel)
        button(screen, "Übernehmen", self.confirm)
