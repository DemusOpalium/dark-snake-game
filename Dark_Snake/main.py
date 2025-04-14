import pygame
from modules.game import Game

def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    # Kleines Fenster, um convert_alpha() zu ermöglichen
    pygame.display.set_mode((1, 1))
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
