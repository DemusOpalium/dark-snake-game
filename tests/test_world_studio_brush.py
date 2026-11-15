"""Exercise World Studio brush and erase gestures on the real Pygame event queue."""

import pygame
import pytest

from test_level_studio import cell, click, key, send, studio, text

from modules.graphic_objects import GraphicObject
from modules.level_drafts import load_level_document
from modules.level_editor import COLOR_SELECT, DELETE_COLOR
from modules.level_effects import CellEffects, DamageField, SlowField


def drag(game, editor, start, end, *, button):
    start, end = cell(editor, *start), cell(editor, *end)
    buttons = (button == 1, False, button == 3)
    delta = end[0] - start[0], end[1] - start[1]
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=button),
         pygame.event.Event(pygame.MOUSEMOTION, pos=end, rel=delta, buttons=buttons),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=end, button=button))


def choose_tool(game, editor, section, action):
    for action_id in (section, action):
        control, = [control for control in editor.buttons if control.id == action_id]
        click(game, control.rect.center)


def test_right_drag_erases_visible_layers_in_one_undo_step(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    row = 8
    editor.map[row][3:8] = [editor.current_tile] * 5
    editor.collisions = {(3, row): "WALL", (5, row): "BARRIER", (7, row): "WALL"}
    editor.effects[(5, row)] = CellEffects(DamageField(9, 1, None), SlowField(50))
    editor.objects[(4, row - 1)] = GraphicObject("frostage_1x1_027", 2, 2)
    editor.roofs[(5, row - 1)] = GraphicObject("frostage_roof_005", 2, 2)
    editor.collisions[(8, row)] = "BARRIER"
    editor.map[row][8] = editor.current_tile
    original = editor._snapshot()

    choose_tool(game, editor, "nav_layers", "layer_collision")
    drag(game, editor, (3, row), (7, row), button=3)
    assert not editor.dialog_open
    assert editor.active_layer == "collision"
    assert editor.map[row][3:8] == [None] * 5
    assert editor.map[row][8] == editor.current_tile
    assert editor.collisions == {(8, row): "BARRIER"}
    assert not editor.effects and not editor.objects and not editor.roofs
    assert len(editor.undo_stack) == 1
    erased = editor._snapshot()
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == original
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor._snapshot() == erased


def test_right_click_respects_locks_visibility_and_solo(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    spot = (6, 6)
    editor.map[spot[1]][spot[0]] = editor.current_tile
    editor.collisions[spot] = "WALL"
    editor.roofs[spot] = GraphicObject("frostage_roof_005", 2, 2)
    editor.effects[spot] = CellEffects(slow=SlowField(50))
    editor.toggle_layer_lock("collision")
    editor.toggle_layer_visibility("roof")
    editor.toggle_layer_solo("effects")

    click(game, cell(editor, *spot), button=3)
    assert not editor.effects
    assert editor.map[spot[1]][spot[0]] == editor.current_tile
    assert spot in editor.collisions and spot in editor.roofs

    editor.toggle_layer_solo("effects")
    click(game, cell(editor, *spot), button=3)
    assert editor.map[spot[1]][spot[0]] is None
    assert spot in editor.collisions and spot in editor.roofs
    assert len(editor.undo_stack) == 2
    click(game, cell(editor, *spot), button=3)
    assert len(editor.undo_stack) == 2 and not editor.dialog_open


def test_right_click_can_be_restricted_to_the_active_layer(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    spot = (7, 8)
    editor.map[spot[1]][spot[0]] = editor.current_tile
    editor.collisions[spot] = "BARRIER"
    choose_tool(game, editor, "nav_build", "right_click_erase")
    click(game, cell(editor, *spot), button=3)
    assert editor.map[spot[1]][spot[0]] is None
    assert editor.collisions == {spot: "BARRIER"}
    assert not editor.dialog_open

    choose_tool(game, editor, "nav_build", "right_click_erase")
    click(game, cell(editor, *spot), button=3)
    assert not editor.collisions and len(editor.undo_stack) == 2


def test_right_click_scope_persists_on_restart(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    choose_tool(game, editor, "nav_build", "right_click_erase")
    reopened = type(game)()
    key(reopened, pygame.K_F2)
    assert not reopened.level_editor.right_click_erase_all
    assert any(control.id == "right_click_erase" and control.label.endswith("Aktiv")
               for control in reopened.level_editor.buttons)


def test_right_click_removes_the_selected_object_and_ends_move(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    anchor = (5, 5)
    item = GraphicObject("frostage_1x1_027", 2, 2)
    editor.objects[anchor] = item
    choose_tool(game, editor, "nav_build", "build_move_objects")
    click(game, cell(editor, 6, 6))
    assert editor._move_anchor == anchor

    click(game, cell(editor, 6, 6), button=3)
    assert not editor.objects and editor._move_anchor is None and not editor._moving_objects
    game.draw()
    click(game, cell(editor, 8, 9))
    assert not editor.objects and len(editor.undo_stack) == 1
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.objects == {anchor: item}


@pytest.mark.parametrize(("asset_id", "columns"), [
    ("frostage_1x1_001", range(3, 10)),
    ("frostage_1x1_014", range(3, 10)),
    ("frostage_2x2_001", range(3, 10, 2)),
])
def test_frost_terrain_brush_fills_pointer_gaps_and_round_trips(studio, asset_id, columns):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor._select_tile(asset_id)
    item = GraphicObject(asset_id, *editor.frost_assets[asset_id].cells)
    before = editor._snapshot()
    drag(game, editor, (3, 7), (9, 7), button=1)
    after = editor._snapshot()
    expected = {(column, 7): item for column in columns}
    assert editor.objects == expected
    assert len(editor.undo_stack) == 1 and not editor.collisions
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == before
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor._snapshot() == after
    assert editor.save_map()
    assert load_level_document(editor.name).objects == expected


def test_frost_brush_repaints_matching_terrain_footprints_only(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    original_tile = GraphicObject("frostage_1x1_001", 1, 1)
    replacement = GraphicObject("frostage_1x1_002", 1, 1)
    original = {
        (3, 7): original_tile,
        (5, 7): original_tile,
        (6, 7): GraphicObject("frostage_2x2_001", 2, 2),
        (8, 7): GraphicObject("frostage_1x1_014", 1, 2),
        (9, 7): GraphicObject("frostage_1x1_027", 1, 1),
    }
    editor.objects = original.copy()
    editor._select_tile(replacement.asset_id)
    board, size = editor.camera.board_rect, editor.camera.cell_size
    for column, outline in ((3, COLOR_SELECT), (9, DELETE_COLOR)):
        send(game, pygame.event.Event(pygame.MOUSEMOTION, pos=cell(editor, column, 7),
                                      rel=(0, 0), buttons=(0, 0, 0)))
        game.draw()
        assert game.screen.get_at((board.x + column * size, board.y + 7 * size))[:3] == outline

    drag(game, editor, (3, 7), (9, 7), button=1)
    expected = original | {(x, 7): replacement for x in (3, 4, 5)}
    assert editor.objects == expected
    assert len(editor.undo_stack) == 1
    drag(game, editor, (3, 7), (9, 7), button=1)
    assert editor.objects == expected
    assert len(editor.undo_stack) == 1
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.objects == original
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.objects == expected


@pytest.mark.parametrize("asset_id", ["frostage_1x1_027", "frostage_roof_005", "frostage_1x1_001"])
def test_prefabs_and_resized_graphics_still_stamp_once_per_press(studio, asset_id):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor._select_tile(asset_id)
    if asset_id == "frostage_1x1_001":
        choose_tool(game, editor, "nav_build", "build_object_size")
        text(game, "2x2")
        key(game, pygame.K_RETURN)
    drag(game, editor, (3, 7), (9, 7), button=1)
    placements = editor.roofs if asset_id == "frostage_roof_005" else editor.objects
    assert set(placements) == {(3, 7)}
    assert len(editor.undo_stack) == 1
