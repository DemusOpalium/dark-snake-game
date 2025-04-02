import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_MEDIUM, DARK_GREY, WHITE, PURPLE
from modules.ui import Button

class CustomizationMenu:
    def __init__(self, game):
        self.game = game
        # Importiere die Kopf-Bilder aus dem Grafik-Modul
        from modules.graphics import SNAKE_HEAD_IMG, SNAKE_HEAD1G20, SNAKE_HEAD2G20, SNAKE_HEAD3G20
        # Liste verfügbarer Kopfoptionen: (Label, Bild)
        self.head_options = [
            ("Standard", SNAKE_HEAD_IMG),
            ("Option 1", SNAKE_HEAD1G20),
            ("Option 2", SNAKE_HEAD2G20),
            ("Option 3", SNAKE_HEAD3G20)
        ]
        self.buttons = []
        self.selected_index = 0  # Standardmäßig der erste Kopf
        self.create_buttons()
        self.back_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=self.back)

    def open_customization(self):
        self.set_state(GameState.CUSTOMIZATION)
        self.custom_menu = CustomizationMenu(self)

    # SAVE_SETTINGS: Speichert die aktuellen Einstellungen
    def save_settings(self):
        # Hier kannst du den Code zum Speichern der Einstellungen implementieren.
        # Beispiel: Schreibe die Einstellungen in eine Datei oder übernehme sie in deine Konfiguration.
        print("Einstellungen wurden gespeichert!")

    def create_buttons(self):
        start_x = 50
        start_y = 100
        spacing = 20
        button_width = 100
        button_height = 100
        self.buttons = []
        for i, (label, img) in enumerate(self.head_options):
            x = start_x + i * (button_width + spacing)
            y = start_y
            btn = Button(x, y, button_width, button_height, label, action=self.make_select_action(i))
            self.buttons.append(btn)

    def make_select_action(self, index):
        return lambda: self.select_head(index)

    def select_head(self, index):
        self.selected_index = index
        _, img = self.head_options[index]
        self.game.settings['custom_head'] = img

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.check_hover(mouse_pos)
            btn.handle_event(event)
        self.back_button.check_hover(mouse_pos)
        self.back_button.handle_event(event)

    def back(self):
        self.game.set_state(self.game.intro_state())

    def draw(self, screen):
        screen.fill(DARK_GREY)
        title = FONT_MEDIUM.render("Wähle deinen Schlangenkopf", True, WHITE)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 20))
        for i, btn in enumerate(self.buttons):
            if i == self.selected_index:
                pygame.draw.rect(screen, WHITE, btn.rect, 3)
            btn.draw(screen)
        self.back_button.draw(screen)
        pygame.display.update()

