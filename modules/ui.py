import pygame
from config import DARK_GREY, WHITE, ORANGE, PURPLE, FONT_SMALL, FONT_MEDIUM

class Button:
    def __init__(self, x, y, width, height, text, color=DARK_GREY, text_color=WHITE, action=None, image=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (min(color[0]+30,255), min(color[1]+30,255), min(color[2]+30,255))
        self.text_color = text_color
        self.action = action
        self.is_hovered = False
        self.image = image

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            color = self.hover_color if self.is_hovered else self.color
            pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, ORANGE, self.rect, 2, border_radius=8)
        txt = FONT_MEDIUM.render(self.text, True, self.text_color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                return self.action()
        return None

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, current_val, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = current_val
        self.text = text
        self.dragging = False
        self.handle_rect = pygame.Rect(self.get_handle_x(), y - 5, 20, height + 10)

    def get_handle_x(self):
        if self.max_val - self.min_val == 0:
            return self.rect.x
        ratio = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)

    def update_handle_position(self):
        self.handle_rect.x = self.get_handle_x()

    def draw(self, screen):
        pygame.draw.rect(screen, DARK_GREY, self.rect)
        value_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_rect.x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, ORANGE, value_rect)
        pygame.draw.rect(screen, WHITE, self.handle_rect)
        txt = FONT_SMALL.render(f"{self.text}: {self.current_val:.1f}", True, WHITE)
        screen.blit(txt, (self.rect.x, self.rect.y - 25))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
            self.current_val = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
            self.update_handle_position()
            return self.current_val
        return None

    def check_hover(self, pos):
        # Hier wird einfach die gesamte Schieberegler-Fläche überprüft
        return self.rect.collidepoint(pos)

class CheckBox:
    def __init__(self, x, y, size, text, checked=False):
        self.rect = pygame.Rect(x, y, size, size)
        self.text = text
        self.checked = checked

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        if self.checked:
            inner = self.rect.inflate(-8, -8)
            pygame.draw.rect(screen, ORANGE, inner)
        txt = FONT_SMALL.render(self.text, True, WHITE)
        screen.blit(txt, (self.rect.x + self.rect.width + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                return self.checked
        return None

    def check_hover(self, pos):
        return self.rect.collidepoint(pos)

def create_ui_elements(self):
    center_x = WINDOW_WIDTH // 2
    button_width = 200
    button_height = 60

    def scale_image(img):
        if img:
            w, h = img.get_size()
            return pygame.transform.scale(img, (int(w * 0.6), int(h * 0.6)))
        return None

    # Neuer Button für die Spielfeldgröße:
    self.playfield_size_button = Button(
        center_x - 100, WINDOW_HEIGHT - 280, button_width, button_height,
        f"{WINDOW_WIDTH} x {WINDOW_HEIGHT}",
        action=self.cycle_playfield_size,
        image=scale_image(PLAY_BUTTON_IMG)
    )

    # Erstelle Dropdown für Hintergrundmusik:
    # Lade die Musikoptionen aus dem Musikordner
    music_options = get_music_library()
    if not music_options:
        music_options = ["Default"]
    # Hier wird FONT_SMALL als Schriftart verwendet – passe dies ggf. an
    # Wir positionieren den Dropdown an (center_x - 150, 240) mit einer Breite von 300 und Höhe von 20
    self.bg_music_dropdown = Dropdown(center_x - 150, 240, 300, 20, music_options, music_options[0], FONT_SMALL, self.change_bg_music)

    # Füge die Elemente zu den Einstellungen hinzu:
    self.settings_elements = [
        Slider(center_x - 150, 200, 300, 20, 1, 15, self.settings['initial_speed'], "Geschwindigkeit"),
        self.bg_music_dropdown,  # Dropdown für Hintergrundmusik einfügen
        self.playfield_size_button,
        Button(center_x - 100, WINDOW_HEIGHT - 150, 200, 60, "SPEICHERN", action=lambda: self.save_settings()),
        Button(center_x - 100, WINDOW_HEIGHT - 80, 200, 60, "CHARAKTER", action=self.open_customization, color=PURPLE)
    ]

