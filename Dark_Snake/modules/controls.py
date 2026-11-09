"""Display and edit input mappings without sending them to gameplay."""

import pygame

from config import WINDOW_WIDTH, WINDOW_HEIGHT, DARK_GREY, WHITE, PURPLE, ORANGE
from modules.enums import GameState
from modules.input_manager import JOYSTICK_EVENTS, RESERVED_KEYS


PLAYER_ACTIONS = ("up", "down", "left", "right", "fire")
ACTION_NAMES = {
    "up": "Hoch", "down": "Runter", "left": "Links", "right": "Rechts",
    "fire": "Feuerball", "pause": "Pause", "special_effect": "Spezialeffekt",
    "navigation": "Reservierte Menütaste",
}
GROUPS = ("Spieler 1", "Spieler 2", "Allgemein")


def action_name(action, with_player=False):
    if action.startswith(("p1_", "p2_")):
        name = ACTION_NAMES[action[3:]]
        return f"P{action[1]} {name}" if with_player else name
    return ACTION_NAMES.get(action, action)


class ControlsMenu:
    def __init__(self, game):
        self.game = game
        self.input = game.input
        self.group = 0
        self.device = None
        self.selected = 0
        self.waiting_for_binding = False
        self.testing = False
        self.status = "Änderungen mit Speichern dauerhaft übernehmen."
        self.font = pygame.font.SysFont("Arial", min(25, WINDOW_WIDTH // 48))
        self.title_font = pygame.font.SysFont("Arial", min(45, WINDOW_WIDTH // 25), bold=True)
        self.margin = 24
        self.group_rect = pygame.Rect(24, 77, 200, 38)
        self.device_rect = pygame.Rect(234, 77, WINDOW_WIDTH - 258, 38)
        self.device_buttons = self._row(123, (
            ("Spieler wechseln", self._route), ("Profil wechseln", self._cycle_profile),
            ("Totzone −", lambda: self._change_deadzone(-0.05)),
            ("Totzone +", lambda: self._change_deadzone(0.05)),
        ))
        self.buttons = self._row(WINDOW_HEIGHT - 62, (
            ("Zuweisen", self._capture), ("Entfernen", self._remove),
            ("Eingabetest", self._test), ("Speichern", self._save),
            ("Standard", self._reset), ("Zurück", self.back),
        ))

    def _row(self, y, buttons):
        gap = 8
        width = (WINDOW_WIDTH - 2 * self.margin - (len(buttons) - 1) * gap) // len(buttons)
        return [(pygame.Rect(self.margin + index * (width + gap), y, width, 38), label, action)
                for index, (label, action) in enumerate(buttons)]

    @property
    def actions(self):
        if self.group == 2:
            return ("pause", "special_effect")
        return tuple(f"p{self.group + 1}_{action}" for action in PLAYER_ACTIONS)

    def _change_group(self):
        self.group = (self.group + 1) % len(GROUPS)
        self.selected = 0

    def _change_device(self, step):
        devices = (None, *self.input.profiles)
        index = devices.index(self.device) if self.device in devices else 0
        self.device = devices[(index + step) % len(devices)]

    def _route(self):
        profile = self.input.profiles[self.device]
        player = 3 - profile["player"]
        self.input.set_player(self.device, player)
        self.group = player - 1
        self.selected = 0
        self.status = f"Gerät steuert Spieler {player}."

    def _cycle_profile(self):
        selected = self.input.cycle_device_slot(self.device)
        self.status = ("Profil für das verbundene Gerät gewechselt." if selected != self.device else
                       "Kein weiteres Profil für dieses Gerät verfügbar.")
        self.device = selected

    def _change_deadzone(self, delta):
        self.input.change_deadzone(self.device, delta)
        self.status = "Totzone geändert. Neue Achsbewegung aus der Mitte testen."

    def _capture(self):
        if self.device is not None:
            if not any(device.slot == self.device for device in self.input.devices.values()):
                self.status = "Gerät zuerst verbinden."
                return
            if self.group < 2 and self.input.profiles[self.device]["player"] != self.group + 1:
                self.status = "Gerät zuerst diesem Spieler zuordnen."
                return
        self.waiting_for_binding = True
        self.testing = False
        self.status = "Taste, Achse oder D-Pad bewegen. ESC bricht ab."

    def _remove(self):
        self.input.remove(self.actions[self.selected], self.device)
        self.status = "Belegung entfernt."

    def _test(self):
        self.testing = not self.testing
        self.waiting_for_binding = False
        self.status = "Eingabe testen. ESC beendet den Test." if self.testing else "Test beendet."

    def _save(self):
        try:
            self.input.save()
        except OSError:
            self.status = "Speichern fehlgeschlagen. Bisherige Datei bleibt erhalten."
        else:
            self.status = "Steuerung gespeichert."

    def _reset(self):
        self.input.reset_defaults(save=False)
        self.device = None
        self.status = "Standard wiederhergestellt. Speichern übernimmt die Änderung dauerhaft."

    def back(self):
        self.waiting_for_binding = self.testing = False
        self.game.set_state(GameState.INTRO)

    def _text(self, screen, text, x, y, width, color=WHITE):
        if self.font.size(text)[0] > width:
            while text and self.font.size(text + "…")[0] > width:
                text = text[:-1]
            text += "…"
        screen.blit(self.font.render(text, True, color), (x, y))

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, PURPLE, rect, border_radius=5)
        pygame.draw.rect(screen, ORANGE, rect, 1, border_radius=5)
        self._text(screen, label, rect.x + 8, rect.y + (rect.height - self.font.get_height()) // 2,
                   rect.width - 16)

    def _action_rect(self, index):
        return pygame.Rect(self.margin, 190 + index * 45, WINDOW_WIDTH - 2 * self.margin, 40)

    def draw(self, screen):
        screen.fill(DARK_GREY)
        title = self.title_font.render("STEUERUNG", True, WHITE)
        screen.blit(title, (self.margin, 14))
        self._draw_button(screen, self.group_rect, GROUPS[self.group] + "  ›")
        name = self.input.device_options().get(self.device, "Tastatur")
        self._draw_button(screen, self.device_rect, name + "  ›")
        if self.device is not None:
            profile = self.input.profiles[self.device]
            for rect, label, _ in self.device_buttons:
                self._draw_button(screen, rect, label)
            self._text(screen, f"Spieler {profile['player']} · Achsen-Totzone {profile['deadzone']:.0%}",
                       self.margin, 165, WINDOW_WIDTH - 2 * self.margin)
        else:
            self._text(screen, "TAB wählt Spieler, ←/→ wählt Geräte.", self.margin, 133,
                       WINDOW_WIDTH - 2 * self.margin)
        for index, action in enumerate(self.actions):
            rect = self._action_rect(index)
            color = ORANGE if index == self.selected else WHITE
            pygame.draw.rect(screen, color, rect, 1, border_radius=4)
            self._text(screen, action_name(action), rect.x + 10, rect.y + 7, 155, color)
            label = self.input.label(action, self.device)
            conflicts = self.input.conflicts(action, self.device)
            if conflicts:
                label += "  ·  Konflikt mit " + ", ".join(action_name(other, True) for other in conflicts)
            self._text(screen, label, rect.x + 175, rect.y + 7, rect.width - 185,
                       ORANGE if conflicts else WHITE)
        self._text(screen, self.status, self.margin, WINDOW_HEIGHT - 131,
                   WINDOW_WIDTH - 2 * self.margin, ORANGE)
        self._text(screen, "↑/↓ wählen · Enter weist zu · Entf entfernt · T testet · ESC zurück",
                   self.margin, WINDOW_HEIGHT - 99, WINDOW_WIDTH - 2 * self.margin)
        for rect, label, _ in self.buttons:
            self._draw_button(screen, rect, label)

    def handle_event(self, event):
        if self.input.handle_device_event(event):
            if self.waiting_for_binding and self.device not in (
                    None, *(device.slot for device in self.input.devices.values())):
                self.waiting_for_binding = False
                self.status = "Gerät wurde getrennt. Zuweisung abgebrochen."
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.waiting_for_binding:
                self.waiting_for_binding = False
                self.status = "Zuweisung abgebrochen."
            elif self.testing:
                self._test()
            else:
                self.back()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons[-1][0].collidepoint(event.pos):
                self.back()
                return
            if self.waiting_for_binding:
                return
            if self.group_rect.collidepoint(event.pos):
                self._change_group()
                return
            if self.device_rect.collidepoint(event.pos):
                self._change_device(1)
                return
            buttons = self.buttons if self.device is None else self.buttons + self.device_buttons
            for rect, _, action in buttons:
                if rect.collidepoint(event.pos):
                    action()
                    return
            for index in range(len(self.actions)):
                if self._action_rect(index).collidepoint(event.pos):
                    self.selected = index
                    return
        if self.waiting_for_binding:
            if event.type == pygame.KEYDOWN and event.key in RESERVED_KEYS:
                self.status = "Diese Taste ist für die Navigation oder Entwicklerwerkzeuge reserviert."
            elif event.type in JOYSTICK_EVENTS and self.input.event_device(event) != self.device:
                self.input.actions_for(event, player_count=2)
            elif self.input.bind_event(self.actions[self.selected], event, device=self.device, save=False):
                self.waiting_for_binding = False
                self.status = "Belegung übernommen."
            return
        actions = self.input.actions_for(event, player_count=1 if self.group == 0 else 2)
        if self.testing:
            if event.type == pygame.KEYDOWN or event.type in JOYSTICK_EVENTS:
                slot = self.input.event_device(event)
                source = self.input.device_options().get(slot, "Tastatur" if event.type == pygame.KEYDOWN else "Gerät")
                names = ", ".join(action_name(action, True) for action in sorted(actions)
                                  if action != "menu_accept")
                self.status = f"{source} · {names or 'keine neue Aktion'}"
            return
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        if key == pygame.K_TAB:
            self._change_group()
        elif key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._change_device(-1 if key == pygame.K_LEFT else 1)
        elif key in (pygame.K_UP, pygame.K_DOWN):
            self.selected = (self.selected + (-1 if key == pygame.K_UP else 1)) % len(self.actions)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._capture()
        elif key == pygame.K_DELETE:
            self._remove()
        elif key == pygame.K_t:
            self._test()
        elif key == pygame.K_s:
            self._save()
        elif key == pygame.K_r:
            self._reset()
