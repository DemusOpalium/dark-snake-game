"""Exercise the FrostAge course through the existing sidebar controls."""

import pygame
import pytest

from test_editor_button_actions import target
from test_editor_sidebar import _action_center
from test_level_studio import click, key, studio


def _click_sidebar(game, editor, action):
    position = _action_center(editor.sidebar, editor, editor.layout.inspector, action)
    click(game, position)


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_tutorial_sidebar_controls_follow_language_and_fit(studio, size):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    game.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    editor.resize(size)
    click(game, target(editor, "nav_learn").rect.center)
    sidebar = editor.sidebar
    assert sidebar.tab == "learn"
    assert sidebar._entries(editor)[0].title == "Mein erstes FrostAge-Level"

    _click_sidebar(game, editor, "learn_start")
    session = editor.tutorial
    assert session is not None
    assert editor.tutorial_progress() == (False, False, False, False, False)
    _click_sidebar(game, editor, "learn_next")
    assert session.step_index == 0

    _click_sidebar(game, editor, "learn_example")
    assert session.example_visible
    assert any(entry.title == "Beispiel" and entry.detail for entry in sidebar._entries(editor))
    click(game, target(editor, "nav_language").rect.center)
    assert editor.tutorial is session and session.example_visible
    entries = sidebar._entries(editor)
    assert entries[0].title == "Paint the floor"
    assert entries[0].detail == "Step 1/5 · 0 checked"
    assert any(entry.title == "Example" and entry.detail for entry in entries)

    _, body, geometry, _ = sidebar._geometry(editor.layout.inspector, editor)
    for entry, _, _, rect in geometry:
        for control, hitbox in sidebar._entry_targets(entry, rect):
            assert body.left <= hitbox.left < hitbox.right <= body.right
            if control.action_id in {"learn_previous", "learn_next", "learn_retry", "learn_exit"}:
                assert sidebar.font.size(control.label)[0] + 12 <= hitbox.width
    game.draw()

    _click_sidebar(game, editor, "learn_exit")
    assert editor.active and editor.tutorial is None
