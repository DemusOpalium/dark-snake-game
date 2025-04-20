
import pygame
from config import DARK_GREY, WHITE, ORANGE, PURPLE, FONT_SMALL, FONT_MEDIUM, WINDOW_WIDTH, WINDOW_HEIGHT
from modules.graphics import PLAY_BUTTON_IMG  # z. B. für Skalierung im Optionsmenü

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

class Dropdown:
    def __init__(self, x, y, width, height, options, current_option, font, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = options.index(current_option) if current_option in options else 0
        self.font = font
        self.callback = callback
        self.expanded = False

    def draw(self, surface):
        pygame.draw.rect(surface, DARK_GREY, self.rect)
        text = self.font.render(self.options[self.selected_index], True, WHITE)
        surface.blit(text, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.polygon(surface, WHITE, [
            (self.rect.right - 15, self.rect.y + 10),
            (self.rect.right - 5, self.rect.y + 10),
            (self.rect.right - 10, self.rect.y + 20)
        ])
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(surface, DARK_GREY, option_rect)
                opt_text = self.font.render(option, True, WHITE)
                surface.blit(opt_text, (option_rect.x + 5, option_rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.expanded = not self.expanded
            elif self.expanded:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                    if option_rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        self.callback(self.options[i])
                        self.expanded = False
                        break
