import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules import resources
from modules.enums import GameState
from modules.game import Game
from modules import level_editor as layout


def test_editor_saves_loads_and_draws_from_other_working_directory(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    monkeypatch.setattr(resources, "DATA_DIR", profile)
    monkeypatch.chdir(tmp_path)
    game = Game()
    editor = game.level_editor
    tiles = Path(resources.asset_path("graphics", "tiles"))
    assert editor.tiles.keys() == {path.stem for path in tiles.iterdir()
                                  if path.suffix.lower() == ".png"}
    assert editor.tiles

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2))
    game.handle_events()
    assert editor.active
    editor.new_map("Auswärts")
    pos = (layout.TOOLBAR_W + 1, layout.MAP_TOP + 1)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
    game.handle_events()
    assert editor.map[0][0] == editor.current_tile
    editor.undo()
    assert editor.map[0][0] is None
    editor.redo()
    assert editor.map[0][0] == editor.current_tile
    assert editor.save_map()
    assert (profile / "levels" / "Auswärts.json").is_file()
    editor.draw(game.screen)

    reopened = Game()
    reopened.level_editor.load_map("Auswärts")
    assert reopened.level_editor.map == editor.map
    reopened.start_game(1)
    assert reopened.game_state == GameState.GAME
    assert not reopened.level_map
    reopened.draw_game()


def test_options_save_music_and_skin_for_next_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    game = Game()
    menu = game.options_menu
    menu.music_slider.current_val = 0.4
    menu.sfx_slider.current_val = 0.2
    menu.current_selected_img = menu.head_options[0]
    menu.assign_image(1)
    menu.save()

    restarted = Game()
    assert restarted.settings["bg_music_volume"] == 0.4
    assert restarted.settings["sfx_volume"] == 0.2
    assert restarted.settings["custom_head_p1"] == menu.selected_head_p1
