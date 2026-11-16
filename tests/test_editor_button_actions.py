"""Exercise graphic toolbar layout, click targets and the action bindings."""

from dataclasses import replace
from itertools import combinations

import pygame
import pytest

from test_level_studio import click, key, studio

from modules.editor_buttons import load_editor_button_catalog


def target(editor, action_id):
    control, = [control for control in editor.buttons if control.id == action_id]
    return control


@pytest.mark.parametrize("size", [(900, 620), (1350, 930), (2560, 1369)])
def test_drawn_toolbar_controls_fit_and_receive_mouse_at_each_size(studio, size):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    pygame.display.set_mode(size, pygame.RESIZABLE)
    pygame.event.post(pygame.event.Event(pygame.WINDOWSIZECHANGED, x=size[0], y=size[1]))
    game.handle_events()
    catalog = load_editor_button_catalog()
    sections = ("nav_file", "nav_build", "nav_layers", "nav_effects", "nav_view", "nav_test", "nav_learn", "nav_help")
    seen = set()
    for section in sections:
        click(game, target(editor, section).rect.center)
        assert editor.section == section
        controls = tuple(editor.buttons)
        assert all(editor.layout.header.contains(control.rect) for control in controls)
        assert not any(a.rect.colliderect(b.rect) for a, b in combinations(controls, 2))
        assert editor.camera.viewport == editor.layout.viewport
        game.draw()
        for index, control in enumerate(controls):
            if control.id not in catalog:
                continue
            seen.add(control.id)
            calls = []
            editor.buttons[index] = replace(control, action=lambda: calls.append(control.id))
            click(game, control.rect.center)
            assert calls == ([control.id] if editor._button_available(control.id) else [])
            editor.buttons[index] = control
    secondary_controls = {
        "border_all", "border_corner", "border_left", "border_right", "border_top", "border_bottom",
        "layer_effects", "test_stop", "preview_stop", "sidebar_properties", "sidebar_layers",
        "sidebar_cell", "sidebar_help", "sidebar_learn", "learn_start", "learn_example",
    }
    assert seen == set(catalog) - secondary_controls


def test_artwork_selects_damage_slow_roof_and_real_playtest_actions(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    click(game, target(editor, "nav_effects").rect.center)
    click(game, target(editor, "effect_damage").rect.center)
    assert editor.placement_mode == "damage"
    click(game, target(editor, "effect_slow").rect.center)
    assert editor.placement_mode == "slow"
    click(game, target(editor, "roof_settings").rect.center)
    assert editor.roof_settings_editor is not None and editor.effect_settings is None
    key(game, pygame.K_ESCAPE)

    click(game, target(editor, "nav_test").rect.center)
    click(game, target(editor, "test_roof_demo").rect.center)
    assert editor.roofs
    click(game, target(editor, "test_player_2").rect.center)
    assert editor.playtest.player_count == 2
    stop = target(editor, "test_stop")
    assert editor.layout.header.contains(stop.rect)
    click(game, stop.rect.center)
    assert editor.playtest is None
    click(game, target(editor, "test_player_1").rect.center)
    assert editor.playtest.player_count == 1


def test_preview_stop_art_leaves_the_map_unchanged(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    click(game, target(editor, "nav_test").rect.center)
    click(game, target(editor, "test_preview").rect.center)
    assert editor.preview_active
    stop = target(editor, "preview_stop")
    assert editor.layout.header.contains(stop.rect)
    assert "preview_stop" in load_editor_button_catalog()
    game.draw()
    click(game, stop.rect.center)
    assert not editor.preview_active and not editor.dirty
