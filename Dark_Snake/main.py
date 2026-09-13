import pygame
import os
from modules.resources import ROOT
from modules.crash_reporting import configure_crash_reporting, record_event

def main():
    reporter = configure_crash_reporting()
    record_event("Programmstart")
    # Legacy modules still use relative paths; anchor them independently of cwd.
    os.chdir(ROOT)
    from modules.game import Game
    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init()
    except pygame.error as exc:
        print(f"[WARN] Audio deaktiviert: {exc}")
    # Kleines Fenster, um convert_alpha() zu ermöglichen
    pygame.display.set_mode((1, 1))
    game = Game()
    if reporter is not None:
        reporter.attach_game(game)
    record_event("Game initialisiert")
    game.run()

if __name__ == "__main__":
    main()
