import pygame
import os
import multiprocessing
from modules.resources import ROOT
from modules.crash_reporting import install_crash_reporting, record_event

def main():
    install_crash_reporting()
    record_event("Dark Snake gestartet")
    # Legacy modules still use relative paths; anchor them independently of cwd.
    os.chdir(ROOT)
    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init()
    except pygame.error as exc:
        print(f"[WARN] Audio deaktiviert: {exc}")
    # Kleines Fenster, um convert_alpha() zu ermöglichen
    pygame.display.set_mode((1, 1))
    # game imports graphics which uses convert_alpha at module import time.
    from modules.game import Game
    game = Game()
    game.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
