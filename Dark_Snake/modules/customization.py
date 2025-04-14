import pygame
import os
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_MEDIUM, DARK_GREY, WHITE, PURPLE, GRID_SIZE
from modules.ui import Button
from modules.graphics import SNAKE_HEAD_IMG, SNAKE_HEAD1G20, SNAKE_HEAD2G20, SNAKE_HEAD3G20, scale_to_thumbnail

class CustomizationMenu:
    def __init__(self, game):
        self.game = game
        # Kopfoptionen (wie bisher, hier werden Thumbnails erzeugt)
        self.head_options = [
            ("Standard", scale_to_thumbnail(SNAKE_HEAD_IMG, 0.75)),
            ("Option 1", scale_to_thumbnail(SNAKE_HEAD1G20, 0.75)),
            ("Option 2", scale_to_thumbnail(SNAKE_HEAD2G20, 0.75)),
            ("Option 3", scale_to_thumbnail(SNAKE_HEAD3G20, 0.75))
        ]
        # Lade die Körperoptionen aus dem vorbereiteten Ordner
        self.body_options = self.load_body_options()
        self.head_buttons = []
        self.body_buttons = []
        self.selected_head_index = 0
        self.selected_body_index = 0
        self.create_head_buttons()
        self.create_body_buttons()
        self.back_button = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=self.back)

    def load_body_options(self):
        # Ordner mit Schlangenkörper-Bildern
        body_folder = os.path.join("assets", "graphics", "SnakeBodysBibliothek")
        body_images = []
        try:
            filenames = os.listdir(body_folder)
            # Filtere nach passenden Bilddateien
            for fname in filenames:
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    # Wir laden das Bild, skalieren es als Thumbnail und speichern auch den Dateinamen ohne Erweiterung
                    full_path = os.path.join(body_folder, fname)
                    img = pygame.image.load(full_path).convert_alpha()
                    thumb = scale_to_thumbnail(img, 0.75)
                    label = os.path.splitext(fname)[0]
                    body_images.append((label, thumb))
        except Exception as e:
            print(f"Fehler beim Laden der Schlangenkörper-Bilder: {e}")
        return body_images

    def create_head_buttons(self):
        start_x = 50
        start_y = 50
        spacing = 20
        button_width = 100
        button_height = 100
        self.head_buttons = []
        for i, (label, img) in enumerate(self.head_options):
            x = start_x + i * (button_width + spacing)
            y = start_y
            btn = Button(x, y, button_width, button_height, label, action=self.make_head_select_action(i), image=img)
            self.head_buttons.append(btn)

    def create_body_buttons(self):
        start_x = 50
        start_y = 200
        spacing = 20
        button_width = 100
        button_height = 100
        self.body_buttons = []
        for i, (label, img) in enumerate(self.body_options):
            x = start_x + i * (button_width + spacing)
            y = start_y
            btn = Button(x, y, button_width, button_height, label, action=self.make_body_select_action(i), image=img)
            self.body_buttons.append(btn)

    def make_head_select_action(self, index):
        return lambda: self.select_head(index)

    def make_body_select_action(self, index):
        return lambda: self.select_body(index)

    def select_head(self, index):
        self.selected_head_index = index
        original_heads = [SNAKE_HEAD_IMG, SNAKE_HEAD1G20, SNAKE_HEAD2G20, SNAKE_HEAD3G20]
        self.game.settings['custom_head'] = original_heads[index]
        print(f"Schlangenkopf ausgewählt: Option {index}")

    def select_body(self, index):
        self.selected_body_index = index
        # Hier wird der vollständige Körperbild geladen (angenommen, es handelt sich um PNG-Dateien)
        body_folder = os.path.join("assets", "graphics", "SnakeBodysBibliothek")
        label, _ = self.body_options[index]
        full_path = os.path.join(body_folder, label + ".png")
        try:
            full_img = pygame.image.load(full_path).convert_alpha()
            self.game.settings['custom_body'] = full_img
            print(f"Schlangenkörper ausgewählt: {label}")
        except Exception as e:
            print(f"Fehler beim Laden von {full_path}: {e}")

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.head_buttons:
            btn.check_hover(mouse_pos)
            btn.handle_event(event)
        for btn in self.body_buttons:
            btn.check_hover(mouse_pos)
            btn.handle_event(event)
        self.back_button.check_hover(mouse_pos)
        self.back_button.handle_event(event)

    def back(self):
        self.game.set_state(self.game.intro_state())

    def draw(self, screen):
        screen.fill(DARK_GREY)
        title = FONT_MEDIUM.render("Wähle deinen Schlangenkopf", True, WHITE)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 10))
        for i, btn in enumerate(self.head_buttons):
            if i == self.selected_head_index:
                pygame.draw.rect(screen, WHITE, btn.rect, 3)
            btn.draw(screen)

        title2 = FONT_MEDIUM.render("Wähle deinen Schlangenkörper", True, WHITE)
        screen.blit(title2, (WINDOW_WIDTH // 2 - title2.get_width() // 2, 160))
        for i, btn in enumerate(self.body_buttons):
            if i == self.selected_body_index:
                pygame.draw.rect(screen, WHITE, btn.rect, 3)
            btn.draw(screen)

        self.back_button.draw(screen)
        pygame.display.update()
