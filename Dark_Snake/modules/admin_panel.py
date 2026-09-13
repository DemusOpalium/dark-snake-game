"""In-game developer menu and its deliberately immediate test actions."""

import random
import time

import pygame

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules.aoe_zones import DamageZone, DebuffZone, HealZone
from modules.enums import ItemType
from modules.graphics import load_image
from modules.ui import Button


class AdminPanel:
    ACTIONS = (
        ("emoji1.png", "Feuerball", "Erzeugt einen Feuerball direkt vor Spieler 1.", "spawn_fireball"),
        ("emoji2.png", "Bosskampf", "Startet einen Bosskampf, wenn noch kein Boss aktiv ist.", "spawn_boss"),
        ("emoji3.png", "Heilen", "Setzt die Lebenspunkte aller aktiven Spieler auf 100.", "full_heal"),
        ("emoji4.png", "Multi-Schuss", "Aktiviert projectile_shoot für 90 Sekunden.", "enable_multi_shot"),
        ("emoji5.png", "Hitboxen", "Schaltet die vorhandene Debug-Hitboxanzeige um.", "toggle_hitboxes"),
        ("emoji6.png", "Bolbu-Item", "Legt ein Item neben Spieler 1; beim Einsammeln erscheint Bolbu.", "spawn_bolbu_item"),
        ("emoji7.png", "Explosion", "Erzeugt eine Explosion an der Position von Spieler 1.", "spawn_explosion"),
        ("emoji8.png", "Schadenszone", "Erzeugt dort eine rote, zeitlich begrenzte Schadenszone.", "spawn_damage_zone"),
        ("emoji9.png", "Zufallszone", "Erzeugt sofort eine zufällige Schadens-, Heil- oder Slow-Zone.", "spawn_random_zone"),
    )

    def __init__(self, game):
        self.game = game
        self.active = False
        self.buttons = []
        self.status = "Bereit. Aktion auswählen."
        self.clicked_effects = {}
        self.title_font = pygame.font.SysFont("Arial", 25, bold=True)
        self.label_font = pygame.font.SysFont("Arial", 14, bold=True)
        self.info_font = pygame.font.SysFont("Arial", 15)
        self.panel_rect = pygame.Rect(12, 24, 344, 380)
        self._setup_buttons()

    def debug_log(self, message):
        print(f"{time.strftime('[%H:%M:%S]')} [ADMIN] {message}")

    def _setup_buttons(self):
        for index, (filename, _name, _description, method_name) in enumerate(self.ACTIONS):
            row, col = divmod(index, 3)
            x = self.panel_rect.x + 25 + col * 106
            y = self.panel_rect.y + 58 + row * 86
            image = load_image(f"Devpanel/{filename}")
            image = pygame.transform.smoothscale(image, (58, 58)) if image else None

            def run_action(i=index, method=method_name):
                self.clicked_effects[i] = time.time()
                try:
                    message = getattr(self, method)()
                    self.status = message or "Aktion ausgeführt."
                    self.debug_log(self.status)
                    return True
                except Exception as error:  # Developer tools must never terminate a match.
                    self.status = f"Fehler: {error}"
                    self.debug_log(self.status)
                    return False

            self.buttons.append(Button(x, y, 58, 58, "", image=image, action=run_action))

    def toggle(self):
        self.active = not self.active
        self.status = "Admin-Menü geöffnet." if self.active else "Admin-Menü geschlossen."
        self.debug_log(self.status)

    def close(self):
        if self.active:
            self.active = False
            self.debug_log("Admin-Menü geschlossen.")

    def _player_one(self):
        snake = self.game.snake if self.game.player_count == 1 else self.game.snake1
        if not snake:
            raise RuntimeError("Spieler 1 ist nicht verfügbar")
        return snake

    def _adjacent_cell(self):
        x, y = self._player_one()[0]
        direction = self.game.snake_direction if self.game.player_count == 1 else self.game.snake_direction1
        dx, dy = direction.value
        return ((x + dx) % GRID_WIDTH, (y + dy) % GRID_HEIGHT)

    def _head_pixels(self):
        x, y = self._player_one()[0]
        return (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2)

    def spawn_fireball(self):
        from modules.game import FlameProjectile

        x, y = self._adjacent_cell()
        direction = self.game.snake_direction if self.game.player_count == 1 else self.game.snake_direction1
        self.game.flame_projectiles.append(
            FlameProjectile(x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2, direction.value)
        )
        return "Feuerball vor Spieler 1 erzeugt."

    def spawn_boss(self):
        if self.game.boss is not None:
            return "Bosskampf läuft bereits."
        self.game.start_boss_fight()
        self.game.boss_fight_active = True
        return "Bosskampf gestartet."

    def full_heal(self):
        if self.game.player_count == 2:
            self.game.player_health_p1 = self.game.player_health_p2 = 100
            return "Beide Spieler vollständig geheilt."
        self.game.player_health = 100
        return "Spieler 1 vollständig geheilt."

    def enable_multi_shot(self):
        self.game.effects["projectile_shoot"] = time.time() + 90
        self.game.extra_auto_shots = max(1, self.game.extra_auto_shots)
        return "Multi-Schuss für 90 Sekunden aktiviert."

    def toggle_hitboxes(self):
        self.game.debug_show_hitboxes = not self.game.debug_show_hitboxes
        state = "aktiviert" if self.game.debug_show_hitboxes else "deaktiviert"
        return f"Hitboxen {state}."

    def spawn_bolbu_item(self):
        x, y = self._adjacent_cell()
        self.game.spawn_item_at(ItemType.SPAWN_BOLBU, x, y)
        return "Bolbu-Item neben Spieler 1 platziert."

    def spawn_explosion(self):
        self.game.spawn_fire_explosion(self._head_pixels())
        return "Explosion an Spieler 1 erzeugt."

    def _zone(self, zone_type):
        pos = self._head_pixels()
        radius = GRID_SIZE * 3
        constructors = {
            "damage": lambda: DamageZone(pos, radius, 6, (255, 0, 0, 150)),
            "heal": lambda: HealZone(pos, radius, 6, (0, 220, 80, 140)),
            "slow": lambda: DebuffZone(pos, radius, 6, (70, 90, 255, 150)),
        }
        self.game.aoe_zones.append(constructors[zone_type]())

    def spawn_damage_zone(self):
        self._zone("damage")
        return "Rote Schadenszone für 6 Sekunden erzeugt."

    def spawn_random_zone(self):
        zone_type = random.choice(("damage", "heal", "slow"))
        self._zone(zone_type)
        names = {"damage": "Schadenszone", "heal": "Heilzone", "slow": "Slow-Zone"}
        return f"Zufällig gewählt: {names[zone_type]}."

    def handle_event(self, event):
        if not self.active:
            return False
        mouse_pos = getattr(event, "pos", pygame.mouse.get_pos())
        for button in self.buttons:
            button.check_hover(mouse_pos)
            button.handle_event(event)
        return True

    def _draw_wrapped(self, screen, text, rect, color):
        words, line, y = text.split(), "", rect.y
        for word in words:
            candidate = f"{line} {word}".strip()
            if self.info_font.size(candidate)[0] > rect.width and line:
                screen.blit(self.info_font.render(line, True, color), (rect.x, y))
                line, y = word, y + 18
            else:
                line = candidate
        if line:
            screen.blit(self.info_font.render(line, True, color), (rect.x, y))

    def draw(self, screen):
        if not self.active:
            return
        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        panel.fill((13, 9, 24, 235))
        screen.blit(panel, self.panel_rect)
        pygame.draw.rect(screen, (184, 84, 255), self.panel_rect, 2, border_radius=8)
        title = self.title_font.render("ADMIN-MENÜ", True, (255, 205, 80))
        screen.blit(title, (self.panel_rect.centerx - title.get_width() // 2, self.panel_rect.y + 13))

        now, hovered = time.time(), None
        for index, button in enumerate(self.buttons):
            button.draw(screen)
            name = self.ACTIONS[index][1]
            label = self.label_font.render(name, True, (245, 245, 245))
            screen.blit(label, (button.rect.centerx - label.get_width() // 2, button.rect.bottom + 3))
            if button.is_hovered:
                hovered = index
                pygame.draw.rect(screen, (255, 220, 75), button.rect.inflate(6, 6), 3, border_radius=7)
            if now - self.clicked_effects.get(index, 0) <= 1:
                pygame.draw.rect(screen, (120, 255, 150), button.rect.inflate(4, 4), 3, border_radius=7)

        info = self.ACTIONS[hovered][2] if hovered is not None else self.status
        info_rect = pygame.Rect(self.panel_rect.x + 16, self.panel_rect.bottom - 54, self.panel_rect.width - 32, 42)
        pygame.draw.rect(screen, (45, 31, 65), info_rect, border_radius=5)
        self._draw_wrapped(screen, info, info_rect.inflate(-8, -5), (255, 255, 255))
