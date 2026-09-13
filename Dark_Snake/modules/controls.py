import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, DARK_GREY, WHITE, PURPLE, FONT_LARGE, FONT_SMALL
from modules.enums import GameState
from modules.ui import Button

class ControlsMenu:
    def __init__(self, game):
        self.game = game
        self.actions = list(self.game.input.bindings)
        self.selected = 0
        self.waiting_for_binding = False
        self.back_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=self.back)
        self.reset_button = Button(WINDOW_WIDTH//2 + 120, WINDOW_HEIGHT - 80, 260, 60, "STANDARD", color=PURPLE, action=self.game.input.reset_defaults)

    def back(self):
        self.game.set_state(GameState.INTRO)

    def draw(self, screen):
        screen.fill(DARK_GREY)
        title = FONT_LARGE.render("STEUERUNG", True, PURPLE)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        y = 150
        for index, action in enumerate(self.actions):
            marker = ">" if index == self.selected else " "
            suffix = " – neue Taste drücken" if self.waiting_for_binding and index == self.selected else ""
            txt = FONT_SMALL.render(f"{marker} {action}: {self.game.input.label(action)}{suffix}", True, WHITE)
            screen.blit(txt, (50, y))
            y += 30
        self.back_button.draw(screen)
        self.reset_button.draw(screen)
        pygame.display.update()

    def handle_event(self, event):
        # Diese Methode wird von Game.handle_events() aufgerufen, um Events im Steuerungs-Menü abzufangen.
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.handle_event(event)
        self.reset_button.check_hover(mouse_pos)
        self.reset_button.handle_event(event)
        if self.waiting_for_binding and self.game.input.bind_event(self.actions[self.selected], event):
            self.waiting_for_binding = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.actions)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.actions)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.waiting_for_binding = True
            elif event.key == pygame.K_r:
                self.game.input.reset_defaults()
