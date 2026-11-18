"""UI-2C: six connected, cosmetic Snake segments in the Options preview.

The preview reads existing P1/P2 skins; it never affects gameplay timing.
"""
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
from modules.options_frostage import snake_preview_positions


@pytest.fixture
def menu(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    return Game(headless=True).options_menu


def test_six_segment_sprites_follow_one_track_with_overlapping_edges():
    stage = pygame.Rect(80, 100, 310, 90)
    size = 39
    step = 32
    at_start = snake_preview_positions(stage, size, step, 0, phase=210)
    later = snake_preview_positions(stage, size, step, 0.75, phase=210)
    assert len(at_start) == len(later) == 6  # 1 head and 5 body segments
    for sequence in (at_start, later):
        assert len({part.y for part in sequence}) == 1
        assert all(part.size == (size, size) for part in sequence)
        assert all(front.x - back.x == step
                   for front, back in zip(sequence, sequence[1:]))
        assert step <= size  # no gaps, slight overlap in the showcase
    assert later[0].x > at_start[0].x
    travel = stage.width + 5 * step + 2 * size
    period = travel / 32
    assert snake_preview_positions(stage, size, step, period, phase=210) == at_start


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_options_preview_animates_on_screen_without_mutating_game(menu, size, monkeypatch):
    view = menu._frost_view
    view.layout(size)
    original_settings = menu.game.settings.copy()
    original_state = menu.game.game_state
    start = view._preview_epoch
    monkeypatch.setattr("modules.options_frostage.time.monotonic", lambda: start)
    before = pygame.Surface(size)
    menu.draw(before)
    region = menu.final_preview_p1.rect
    first = pygame.image.tobytes(before.subsurface(region), "RGB")
    monkeypatch.setattr("modules.options_frostage.time.monotonic", lambda: start + .85)
    after = pygame.Surface(size)
    menu.draw(after)
    second = pygame.image.tobytes(after.subsurface(region), "RGB")
    assert first != second  # moving heads/bodies actually change the visible image
    assert menu.game.settings == original_settings
    assert menu.game.game_state is original_state


def test_both_previews_use_the_correct_assigned_head_body_and_player(menu, monkeypatch):
    menu.current_tab = "Heads"
    menu.current_selected_img = menu.head_options[1]
    menu.assign_image(1)
    menu.current_selected_img = menu.head_options[-1]
    menu.assign_image(2)
    menu.current_tab = "Bodies"
    menu.current_selected_img = menu.body_options[1]
    menu.assign_image(1)
    menu.current_selected_img = menu.body_options[-1]
    menu.assign_image(2)

    view = menu._frost_view
    captured = []
    original = view._preview_sprite

    def record(tab, name, size, player):
        captured.append((tab, name, size, player))
        return original(tab, name, size, player)

    monkeypatch.setattr(view, "_preview_sprite", record)
    menu.draw(pygame.Surface((1350, 930)))
    for player, head, body in (
        (1, menu.selected_head_p1, menu.selected_body_p1),
        (2, menu.selected_head_p2, menu.selected_body_p2),
    ):
        assert any(tab == "Heads" and name == head and who == player and
                   scale > 30 for tab, name, scale, who in captured)
        assert any(tab == "Bodies" and name == body and who == player and
                   scale > 30 for tab, name, scale, who in captured)
        assert ("Heads", head, 30, player) in captured
        assert ("Bodies", body, 30, player) in captured


def test_no_custom_skin_uses_actual_game_fallback_for_both_players(menu):
    from modules.graphics import SNAKE_BODY_IMG, SNAKE_HEAD_BETA, SNAKE_HEAD_IMG
    view = menu._frost_view
    for player, source in ((1, SNAKE_HEAD_IMG), (2, SNAKE_HEAD_BETA)):
        assert pygame.image.tobytes(
            view._preview_sprite("Heads", None, 30, player), "RGBA"
        ) == pygame.image.tobytes(
            pygame.transform.smoothscale(source, (30, 30)), "RGBA"
        )
        assert pygame.image.tobytes(
            view._preview_sprite("Bodies", None, 30, player), "RGBA"
        ) == pygame.image.tobytes(
            pygame.transform.smoothscale(SNAKE_BODY_IMG, (30, 30)), "RGBA"
        )


def test_animation_scales_once_but_not_each_frame(menu, monkeypatch):
    surface = pygame.Surface((1350, 930))
    view = menu._frost_view
    menu.draw(surface)
    cache_size = len(view._sprite_cache)

    def surprise(*args, **kwargs):
        raise AssertionError("Moving the Snake must not rescale its PNG every frame")

    monkeypatch.setattr(pygame.transform, "smoothscale", surprise)
    for _ in range(3):
        menu.draw(surface)
    assert len(view._sprite_cache) == cache_size


def test_preview_both_panels_preserve_clip_after_animation(menu):
    view = menu._frost_view
    surface = pygame.Surface((1350, 930), pygame.SRCALPHA)
    original = surface.get_clip()
    view.draw(surface)
    assert surface.get_clip() == original
    for panel in (menu.final_preview_p1, menu.final_preview_p2):
        assert surface.get_rect().contains(panel.rect)
