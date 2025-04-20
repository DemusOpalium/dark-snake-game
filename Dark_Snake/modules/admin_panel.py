import pygame
import time
from modules.ui import Button
from modules.enums import ItemType
from modules.graphics import load_image

class AdminPanel:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.background = load_image("Devpanel/Backrounddev.png").convert_alpha()
        self.background.set_alpha(150)
        self.buttons = []
        self.clicked_effects = {}
        self._setup_buttons()

    def debug_log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        print(f"{timestamp} [ADMIN] {message}")

    def _setup_buttons(self):
        icons = [
            ("emoji1.png", self.spawn_item),          # Item: Fireshoot
            ("emoji2.png", self.spawn_boss),          # Boss
            ("emoji3.png", self.spawn_enemy),         # Enemy
            ("emoji5.png", self.trigger_portal_event),# Portal Event
            ("emoji6.png", self.placeholder),
            ("emoji7.png", self.placeholder),
            ("emoji8.png", self.placeholder),
            ("emoji9.png", self.placeholder)
        ]

        x0, y0 = 30, 70
        padding_x, padding_y = 80, 80
        for idx, (filename, action) in enumerate(icons):
            row = idx // 3
            col = idx % 3
            x = x0 + col * padding_x
            y = y0 + row * padding_y
            image = load_image(f"Devpanel/{filename}")
            if image:
                def wrapped_action(act=action, label=filename, i=idx):
                    self.debug_log(f"Button '{label}' wurde gedrückt.")
                    self.clicked_effects[i] = time.time()
                    return act()
                self.buttons.append(Button(x, y, 64, 64, "", image=image, action=wrapped_action))

    def toggle(self):
        self.active = not self.active
        self.debug_log("AdminPanel toggled: {}".format("Aktiv" if self.active else "Inaktiv"))

    def spawn_item(self):
        if hasattr(self.game, "spawn_item_at"):
            head = getattr(self.game.snake, "head", None)
            if head:
                self.game.spawn_item_at(ItemType.FLAMEBALL_TRIGGER, head.x + 1, head.y)
                self.debug_log("Flameball-Item gespawnt")

    def spawn_boss(self):
        if hasattr(self.game, "start_boss_fight") and not getattr(self.game, "boss_fight_active", False):
            self.game.start_boss_fight()
            self.debug_log("Boss-Spawn ausgelöst")

    def spawn_enemy(self):
        if hasattr(self.game, "spawn_enemy"):
            self.game.spawn_enemy()
            self.debug_log("Enemy gespawnt")
        else:
            self.debug_log("Enemy-Spawning noch nicht implementiert")

    def trigger_portal_event(self):
        if hasattr(self.game, "activate_portal"):
            self.game.activate_portal("event")
            self.debug_log("Portal Event getriggert")
        else:
            self.debug_log("Portal Event nicht verfügbar")

    def placeholder(self):
        self.debug_log("Platzhalter – bald verfügbar")

    def handle_event(self, event):
        if self.active:
            for btn in self.buttons:
                btn.check_hover(pygame.mouse.get_pos())
                btn.handle_event(event)

    def draw(self, screen):
        if self.active:
            screen.blit(self.background, (10, 30))
            current_time = time.time()
            for i, btn in enumerate(self.buttons):
                if btn.image:
                    screen.blit(btn.image, btn.rect)
                if i in self.clicked_effects:
                    elapsed = current_time - self.clicked_effects[i]
                    if elapsed <= 1.0:
                        pygame.draw.rect(screen, (128, 0, 128), btn.rect, 3)
                    else:
                        del self.clicked_effects[i]
