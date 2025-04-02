import pygame
from modules.game import Game

def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    # Minimaler Display, damit convert_alpha() funktioniert
    pygame.display.set_mode((1, 1))
    game = Game()
    game.run()

if __name__ == "__main__":
    main()

