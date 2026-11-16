"""Validate the learning session without loading a profile or the main game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from modules.editor_layers import LayerView
from modules.graphic_objects import GraphicObject
from modules.level_playtest import LevelPlaytest
from modules.studio_tutorial import (
    CENTER_X, CENTER_Y, FLOOR_CELLS, OBSTACLE_CELLS, PROTECTED_CORRIDOR, ROOF_ANCHORS,
    Tutorial, practice_document,
)


class PracticeDraft:
    def __init__(self):
        document = practice_document()
        self.map = document.graphics
        self.collisions = document.collision
        self.roofs = document.roofs
        self.layers = LayerView()

    def layer_locked(self, layer):
        return layer in self.layers.locked

    def layer_visible(self, layer):
        return self.layers.visible(layer)


def complete_floor(draft):
    for x, y in sorted(FLOOR_CELLS)[:3]:
        draft.map[y][x] = "frostage_1x1_001"


def stage_roof(tutorial, draft):
    complete_floor(draft)
    assert tutorial.next(draft)
    cell = min(OBSTACLE_CELLS)
    draft.collisions[cell] = "WALL"
    assert tutorial.next(draft)


def toggle_roof(tutorial, draft, *, visible):
    if visible:
        draft.layers.hidden.discard("roof")
    else:
        draft.layers.hidden.add("roof")
    tutorial.roof_visibility_changed(visible, draft.roofs)


@pytest.mark.parametrize("players", [1, 2])
def test_practice_leaves_both_native_spawn_routes_open(players):
    practice = practice_document()
    for i, cell in enumerate(OBSTACLE_CELLS):
        practice.collision[cell] = "WALL" if i % 2 == 0 else "BARRIER"

    assert PROTECTED_CORRIDOR.isdisjoint(practice.collision)
    session = LevelPlaytest(practice.collision, players, started_at=0)
    assert [p.cell for p in session.players] == [(CENTER_X, CENTER_Y + i * 2) for i in range(players)]
    for _ in range(3):
        session.update(session.players[0].next_step)
    assert [p.cell for p in session.players] == [(CENTER_X + 3, CENTER_Y + i * 2) for i in range(players)]
    assert all(p.health == 100 and p.blocked is None for p in session.players)


def test_real_ground_and_wall_are_required_to_advance_and_may_regress():
    draft, tutorial = PracticeDraft(), Tutorial()
    assert tutorial.progress(draft) == (False,) * 5
    assert not tutorial.next(draft)
    tutorial.toggle_example()
    assert tutorial.example_visible and not tutorial.next(draft)
    complete_floor(draft)
    assert tutorial.next(draft) and not tutorial.example_visible
    obstacle = min(OBSTACLE_CELLS)
    draft.collisions[obstacle] = "BARRIER"
    assert not tutorial.next(draft)
    draft.collisions[obstacle] = "WALL"
    reserved = min(PROTECTED_CORRIDOR)
    draft.collisions[reserved] = "WALL"
    assert not tutorial.next(draft)
    del draft.collisions[reserved]
    x, y = min(FLOOR_CELLS)
    draft.map[y][x] = "frozenbase_0_0"
    assert tutorial.progress(draft)[:2] == (False, True)
    assert not tutorial.next(draft)
    draft.map[y][x] = "frostage_1x1_001"
    assert tutorial.next(draft)
    assert tutorial.previous() and tutorial.reset_cells == ("collision", OBSTACLE_CELLS)


def test_roof_confirmation_belongs_to_the_visible_placed_roof():
    draft, tutorial = PracticeDraft(), Tutorial()
    stage_roof(tutorial, draft)
    toggle_roof(tutorial, draft, visible=False)
    toggle_roof(tutorial, draft, visible=True)
    anchor = min(ROOF_ANCHORS)
    roof = GraphicObject("frostage_roof_005", 4, 4)
    draft.roofs[anchor] = roof
    assert not tutorial.next(draft)
    toggle_roof(tutorial, draft, visible=False)
    assert not tutorial.next(draft)
    toggle_roof(tutorial, draft, visible=True)
    assert tutorial.progress(draft)[2]
    del draft.roofs[anchor]
    assert not tutorial.progress(draft)[2]
    draft.roofs[anchor] = roof
    assert tutorial.progress(draft)[2]
    tutorial.retry()
    assert not tutorial.progress(draft)[2]


def test_lock_needs_a_rejected_edit_and_success_needs_the_one_player_test():
    draft, tutorial = PracticeDraft(), Tutorial()
    stage_roof(tutorial, draft)
    draft.roofs[min(ROOF_ANCHORS)] = GraphicObject("frostage_roof_005", 4, 4)
    toggle_roof(tutorial, draft, visible=False)
    toggle_roof(tutorial, draft, visible=True)
    assert tutorial.next(draft)

    draft.layers.locked.add("ground")
    tutorial.layer_lock_changed("ground", True)
    draft.layers.locked.remove("ground")
    tutorial.layer_lock_changed("ground", False)
    assert not tutorial.next(draft)
    draft.layers.locked.add("ground")
    tutorial.layer_lock_changed("ground", True)
    tutorial.blocked_edit("roof")
    tutorial.blocked_edit("ground")
    assert not tutorial.next(draft)
    draft.layers.locked.remove("ground")
    tutorial.layer_lock_changed("ground", False)
    assert tutorial.next(draft)

    tutorial.playtest_started(2)
    assert not tutorial.finished(draft)
    tutorial.playtest_started(1)
    assert tutorial.finished(draft)
    tutorial.retry()
    assert not tutorial.finished(draft)
