import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, DARK_GREY, WHITE, PURPLE, FONT_LARGE, FONT_SMALL
from modules.enums import GameState
from modules.ui import Button

class ControlsMenu:
    def __init__(self, game):
        self.game = game
        self.controls = {
            "Spieler1 - Oben": "Pfeiltaste ↑",
            "Spieler1 - Unten": "Pfeiltaste ↓",
            "Spieler1 - Links": "Pfeiltaste ←",
            "Spieler1 - Rechts": "Pfeiltaste →",
            "Schießen": "+",
            "Spieler2 - Oben": "W",
            "Spieler2 - Unten": "S",
            "Spieler2 - Links": "A",
            "Spieler2 - Rechts": "D",
            "Schießen": "SPACE"
        }
        self.back_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=self.back)

    def back(self):
        self.game.set_state(GameState.INTRO)

    def draw(self, screen):
        screen.fill(DARK_GREY)
        title = FONT_LARGE.render("STEUERUNG", True, PURPLE)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        y = 150
        for key, val in self.controls.items():
            txt = FONT_SMALL.render(f"{key}: {val}", True, WHITE)
            screen.blit(txt, (50, y))
            y += 30
        self.back_button.draw(screen)
        pygame.display.update()

