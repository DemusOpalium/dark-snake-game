"""UI-2A: user-visible OptionsMenu layout and preserved callback behavior."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules import resources
from modules.game import Game


@pytest.fixture
def menu(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    return Game(headless=True).options_menu


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_frost_options_layout_preserves_all_controls(menu, size):
    surface = pygame.Surface(size)
    menu.draw(surface)
    assert menu._frost_view.background.get_size() == size
    for button in (menu.save_btn, menu.back_btn, menu.assign_p1_btn,
                   menu.assign_p2_btn, menu.head_tab_button, menu.body_tab_button):
        assert surface.get_rect().contains(button.rect)
    for panel in (menu.settings_panel, menu.inventory_panel, menu.preview_panel,
                  menu.final_preview_p1, menu.final_preview_p2):
        assert surface.get_rect().contains(panel.rect)
    for slider in (menu.speed_slider, menu.difficulty_slider, menu.projectile_slider,
                   menu.spawnrate_slider, menu.boss_health_slider,
                   menu.music_slider, menu.sfx_slider):
        assert surface.get_rect().contains(slider.rect)
        assert slider.rect.height > 0
    assert menu.music_dropdown is None or surface.get_rect().contains(menu.music_dropdown.rect)


def test_skin_selection_and_original_settings_keys_survive(menu):
    head = menu.head_options[0]
    body = menu.body_options[0]
    menu.current_tab = "Heads"
    menu.current_selected_img = head
    menu.assign_image(1)
    menu.current_tab = "Bodies"
    menu.current_selected_img = body
    menu.assign_image(2)
    menu.speed_slider.current_val = 9.5
    menu.spawnrate_slider.current_val = .003
    menu.save()
    game = menu.game
    assert game.settings["custom_head_p1"] == head[0]
    assert game.settings["custom_body_p2"] == body[0]
    assert game.settings["initial_speed"] == 9.5
    assert game.settings["enemy_spawn_rate"] == .003
    assert menu.get_skin_image("Heads", head[0]) is head[2]
    assert menu.get_skin_image("Bodies", body[0]) is body[2]
    assert Path(resources.user_data_path("settings.json")).is_file()


def test_spawnrate_keeps_precision_without_rewriting_its_value(menu):
    surface = pygame.Surface((1350, 930))
    menu.spawnrate_slider.current_val = .003
    menu.draw(surface)
    assert menu.spawnrate_slider.current_val == pytest.approx(.003)
    assert menu.spawnrate_slider.min_val == pytest.approx(.001)


def test_gallery_click_rejects_hidden_items_and_keeps_visible_selection(menu):
    menu.draw(pygame.Surface((1350, 930)))
    grid = menu.inventory_grid_rect
    menu.current_tab = "Heads"
    menu.current_selected_img = None
    menu._last_click_pos = (grid.left - 1, grid.top + 20)
    menu.check_inventory_click()
    assert menu.current_selected_img is None
    spacing = 10
    width = (grid.width - 5 * spacing) // 4
    menu._last_click_pos = (grid.left + spacing + width // 2,
                            grid.top + spacing + width // 2)
    menu.check_inventory_click()
    assert menu.current_selected_img[0] == menu.head_options[0][0]


def test_bounded_music_popup_keeps_selection_callback(menu):
    if menu.music_dropdown is None:
        pytest.skip("No music tracks in this build")
    menu.draw(pygame.Surface((900, 620)))
    view = menu._frost_view
    dropdown = menu.music_dropdown
    invoked = []
    dropdown.callback = invoked.append
    click = lambda pos: pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos}
    )
    assert view.handle_music_event(click(dropdown.rect.center))
    assert dropdown.expanded
    popup, row_height = view._music_popup()
    assert pygame.Rect((0, 0), view.size).contains(popup)
    assert view.handle_music_event(click((popup.left + 8, popup.top + row_height // 2)))
    assert invoked == [dropdown.options[dropdown.selected_index]]
    assert not dropdown.expanded


def test_options_scaling_is_cached_between_draws(menu, monkeypatch):
    surface = pygame.Surface((1350, 930))
    menu.draw(surface)
    bg = menu._frost_view.background
    thumbs = dict(menu._frost_view._thumb_cache)
    sprites = dict(menu._frost_view._sprite_cache)
    def unexpected_scale(*args, **kwargs):
        raise AssertionError("Second frame must not rescale Options assets")
    monkeypatch.setattr(pygame.transform, "smoothscale", unexpected_scale)
    menu.draw(surface)
    assert menu._frost_view.background is bg
    assert menu._frost_view._thumb_cache == thumbs
    assert menu._frost_view._sprite_cache == sprites
