"""Exercise the complete practice course through World Studio's existing controls."""

import pygame
import pytest

from test_editor_button_actions import target
from test_editor_sidebar import _action_center, _tab_center
from test_level_studio import cell, click, key, send, studio

from modules.studio_tutorial import CENTER_X, CENTER_Y, FLOOR_CELLS, OBSTACLE_CELLS, ROOF_ANCHORS


def choose(game, editor, action_id):
    click(game, target(editor, action_id).rect.center)


def tab(game, editor, tab_id):
    click(game, _tab_center(editor.sidebar, editor, editor.layout.inspector, tab_id))
    assert editor.sidebar.tab == tab_id


def sidebar_action(game, editor, action_id):
    click(game, _action_center(editor.sidebar, editor, editor.layout.inspector, action_id))


def drag_floor(game, editor, first, last):
    start, finish = cell(editor, *first), cell(editor, *last)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1),
         pygame.event.Event(pygame.MOUSEMOTION, pos=finish, rel=(finish[0] - start[0], 0), buttons=(1, 0, 0)),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=finish, button=1))


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_learning_course_validates_real_editor_actions_in_both_languages(studio, size):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    game.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    editor.resize(size)
    choose(game, editor, "nav_learn")
    sidebar_action(game, editor, "learn_start")
    tutorial = editor.tutorial
    assert tutorial is not None and editor.active_layer == "ground"

    sidebar_action(game, editor, "learn_example")
    assert tutorial.example_visible and not any(editor.tutorial_progress())
    sidebar_action(game, editor, "learn_next")
    assert tutorial.step_index == 0
    game.draw()
    german = pygame.image.tobytes(game.screen.subsurface(editor.layout.inspector), "RGB")
    choose(game, editor, "nav_language")
    assert editor.tr.language == "en" and editor.tutorial is tutorial and tutorial.example_visible
    game.draw()
    english = pygame.image.tobytes(game.screen.subsurface(editor.layout.inspector), "RGB")
    assert german != english
    assert "Paint the floor" in [entry.title for entry in editor.sidebar._entries(editor)]

    # Choose a real palette entry, then paint three cells with one real mouse stroke.
    editor._select_tile("frostage_1x1_001")
    assert editor.active_layer == "ground"
    x, y = min(FLOOR_CELLS)
    practice_tile = editor.map[y][x]
    drag_floor(game, editor, (x, y), (x + 2, y))
    assert editor.map[y][x:x + 3] == ["frostage_1x1_001"] * 3
    assert editor.tutorial_progress()[0]
    sidebar_action(game, editor, "learn_retry")
    assert editor.map[y][x:x + 3] == [practice_tile] * 3
    assert not editor.tutorial_progress()[0]
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.tutorial_progress()[0]
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert not editor.tutorial_progress()[0]
    drag_floor(game, editor, (x, y), (x + 2, y))
    sidebar_action(game, editor, "learn_next")
    assert tutorial.step_index == 1
    sidebar_action(game, editor, "learn_previous")
    assert tutorial.step_index == 0 and editor.tutorial_progress()[0]
    sidebar_action(game, editor, "learn_next")

    ground = [row.copy() for row in editor.map]
    choose(game, editor, "nav_layers")
    choose(game, editor, "layer_collision")
    choose(game, editor, "collision_barrier")
    click(game, cell(editor, CENTER_X, CENTER_Y))
    assert (CENTER_X, CENTER_Y) not in editor.collisions
    barrier, wall = sorted(OBSTACLE_CELLS)[:2]
    click(game, cell(editor, *barrier))
    assert editor.collisions[barrier] == "BARRIER" and not editor.tutorial_progress()[1]
    choose(game, editor, "collision_wall")
    click(game, cell(editor, *wall))
    assert editor.collisions[wall] == "WALL" and editor.map == ground
    sidebar_action(game, editor, "learn_next")
    assert tutorial.step_index == 2

    editor._select_tile("frostage_roof_005")
    anchor = min(ROOF_ANCHORS)
    click(game, cell(editor, *anchor))
    assert editor.roofs[anchor].asset_id == "frostage_roof_005" and not editor.tutorial_progress()[2]
    tab(game, editor, "layers")
    sidebar_action(game, editor, "layer_visibility_roof")
    assert not editor.show_roofs and not editor.tutorial_progress()[2]
    sidebar_action(game, editor, "layer_visibility_roof")
    assert editor.show_roofs and editor.tutorial_progress()[2]
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert anchor not in editor.roofs and not editor.tutorial_progress()[2]
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert anchor in editor.roofs and editor.tutorial_progress()[2]
    tab(game, editor, "learn")
    sidebar_action(game, editor, "learn_next")
    assert tutorial.step_index == 3

    tab(game, editor, "layers")
    sidebar_action(game, editor, "layer_ground")
    editor._select_tile("frostage_1x1_001")
    sidebar_action(game, editor, "layer_lock_ground")
    click(game, cell(editor, x, y))
    sidebar_action(game, editor, "layer_lock_ground")
    assert not editor.tutorial_progress()[3]

    editor._select_tile("frostage_1x1_002")
    sidebar_action(game, editor, "layer_lock_ground")
    history = len(editor.undo_stack)
    click(game, cell(editor, x, y))
    assert editor.layer_locked("ground") and not editor.tutorial_progress()[3]
    assert editor.map == ground and len(editor.undo_stack) == history
    sidebar_action(game, editor, "layer_lock_ground")
    assert editor.tutorial_progress()[3]
    tab(game, editor, "learn")
    sidebar_action(game, editor, "learn_next")
    assert tutorial.step_index == 4

    sidebar_action(game, editor, "test_player_2")
    assert editor.playtest is None and not tutorial.finished(editor)
    for player_count in (1, 2):
        sidebar_action(game, editor, f"test_player_{player_count}")
        session = editor.playtest
        assert session is not None and session.player_count == player_count
        for _ in range(3):
            session.update(session.players[0].next_step)
        assert [p.cell for p in session.players] == [(CENTER_X + 3, CENTER_Y + i * 2) for i in range(player_count)]
        assert all(p.health == 100 and p.blocked is None for p in session.players)
        key(game, pygame.K_ESCAPE)
        assert editor.playtest is None and tutorial.finished(editor)
        assert "Congratulations! Your first FrostAge level is complete." in [
            entry.title for entry in editor.sidebar._entries(editor)
        ]

    sidebar_action(game, editor, "learn_exit")
    assert editor.active and editor.tutorial is None
