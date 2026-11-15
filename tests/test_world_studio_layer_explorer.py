"""Exercise visibility, editing protection and scoped deletion through World Studio."""

import pygame
import pytest

from test_level_studio import button, cell, click, key, send, studio, text

from modules.graphic_objects import GraphicObject
from modules.level_drafts import load_level_document
from modules.level_editor import DELETE_COLOR
from modules.level_effects import CellEffects, DamageField, SlowField


LAYERS = ("ground", "objects", "roof", "collision", "effects")
ROOF = "frostage_roof_005"
OBJECT = "frostage_1x1_007"


def visible_layers(editor):
    return {layer for layer in LAYERS if editor.layer_visible(layer)}


def test_visibility_is_independent_from_selection_and_solo_is_reversible(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.toggle_layer_visibility("roof")
    editor.toggle_layer_visibility("objects")
    assert visible_layers(editor) == {"ground", "collision", "effects"}

    button(game, editor, "Dach / Foreground")
    assert editor.active_layer == "roof"
    assert visible_layers(editor) == {"ground", "collision", "effects"}
    editor.toggle_layer_solo("roof")
    assert editor.solo_layer == "roof" and visible_layers(editor) == {"roof"}
    editor.toggle_layer_solo("effects")
    assert editor.solo_layer == "effects" and visible_layers(editor) == {"effects"}
    editor.toggle_layer_solo("effects")
    assert editor.solo_layer is None
    assert visible_layers(editor) == {"ground", "collision", "effects"}

    editor.toggle_layer_solo("ground")
    editor.show_all_layers()
    assert editor.solo_layer is None and visible_layers(editor) == set(LAYERS)
    assert editor.active_layer == "roof"
    assert not editor.dirty and not editor.undo_stack


def test_hidden_ground_is_really_not_rendered_or_painted(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    spot, fresh = (6, 4), (7, 5)
    image = pygame.Surface((16, 16))
    image.fill((53, 179, 217))
    editor.tiles["qa_blue_tile"] = image
    editor.current_tile = "qa_blue_tile"
    click(game, cell(editor, *spot))
    point = cell(editor, *spot)
    game.draw()
    assert game.screen.get_at(point)[:3] == (53, 179, 217)

    editor.toggle_layer_visibility("ground")
    game.draw()
    assert game.screen.get_at(point)[:3] != (53, 179, 217)
    click(game, cell(editor, *fresh))
    assert editor.map[spot[1]][spot[0]] == "qa_blue_tile"
    assert editor.map[fresh[1]][fresh[0]] is None
    assert len(editor.undo_stack) == 1
    editor.toggle_layer_visibility("ground")
    game.draw()
    assert game.screen.get_at(point)[:3] == (53, 179, 217)


def test_editor_solo_leaves_full_roof_demo_playtest_and_collision_paths_intact(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    button(game, editor, "Dach-Demo")
    editor.toggle_layer_visibility("roof")
    editor.toggle_layer_solo("collision")
    board = editor.camera.board_rect.copy()
    roof_probe = cell(editor, 22, 11)
    game.draw()
    editor_pixel = game.screen.get_at(roof_probe)

    button(game, editor, "Test 2P")
    assert editor.camera.board_rect == board
    game.draw()
    assert game.screen.get_at(roof_probe) != editor_pixel
    session = editor.playtest
    session.update(session.players[0].next_step)
    assert [player.blocked for player in session.players] == ["WALL", "WALL"]
    key(game, pygame.K_w)
    key(game, pygame.K_UP)
    for _ in range(6):
        session.update(session.players[0].next_step)
    assert all(player.blocked is None and player.cell[0] == 22 and player.cell[1] <= 11
               for player in session.players)

    key(game, pygame.K_ESCAPE)
    assert editor.solo_layer == "collision" and visible_layers(editor) == {"collision"}
    editor.toggle_layer_solo("collision")
    assert visible_layers(editor) == set(LAYERS) - {"roof"}
    assert not editor.dirty


@pytest.mark.parametrize("layer", ["ground", "collision"])
def test_combined_stroke_is_atomic_when_either_layer_is_locked(studio, layer):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    button(game, editor, "Grafik + Kollision")
    spot = (6, 4)
    editor.toggle_layer_lock(layer)
    click(game, cell(editor, *spot))
    assert not editor.dirty and not editor.undo_stack and not editor.collisions
    editor.toggle_layer_lock(layer)
    click(game, cell(editor, *spot))
    assert editor.map[spot[1]][spot[0]] == editor.current_tile
    assert editor.collisions == {spot: "WALL"} and len(editor.undo_stack) == 1

    editor.toggle_layer_lock(layer)
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map[spot[1]][spot[0]] == editor.current_tile
    assert editor.collisions == {spot: "WALL"} and len(editor.undo_stack) == 1
    assert not editor.redo_stack
    editor.toggle_layer_lock(layer)
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert not editor.dirty and not editor.collisions and len(editor.redo_stack) == 1
    editor.toggle_layer_visibility(layer)
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert not editor.dirty and not editor.collisions and len(editor.redo_stack) == 1
    editor.toggle_layer_visibility(layer)
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.collisions == {spot: "WALL"} and editor.dirty


def test_locked_ground_guards_middle_and_border_bulk_actions(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.toggle_layer_lock("ground")
    button(game, editor, "Mittelfeld")
    button(game, editor, "Rand")
    assert not editor.dialog_open
    assert not editor.dirty and not editor.undo_stack

    editor.toggle_layer_lock("ground")
    button(game, editor, "Rand")
    assert editor.border_builder is not None
    click(game, editor.border_builder.all_button.center)
    editor.toggle_layer_lock("ground")
    click(game, editor.border_builder.apply_button.center)
    assert not editor.dirty and not editor.undo_stack


@pytest.mark.parametrize("blocked", ["objects", "roof"])
def test_roof_transfer_requires_both_layers_to_be_editable(studio, blocked):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    anchor = (3, 4)
    item = GraphicObject(ROOF, 2, 2)
    editor.objects[anchor] = item
    button(game, editor, "Auf Dachebene")
    editor.toggle_layer_lock(blocked)
    click(game, cell(editor, 4, 5))
    assert editor.objects == {anchor: item}
    assert not editor.roofs
    editor.toggle_layer_lock(blocked)
    click(game, cell(editor, 4, 5))
    assert not editor.objects and editor.roofs == {anchor: item}
    assert len(editor.undo_stack) == 1


def test_locked_or_hidden_object_cannot_be_painted_moved_resized_or_deleted(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    origin, destination = (4, 4), (8, 8)
    item = GraphicObject(OBJECT, 2, 2)
    editor.objects[origin] = item
    editor._select_tile(OBJECT)
    editor.toggle_layer_lock("objects")
    original = editor._snapshot()

    click(game, cell(editor, *destination))
    click(game, cell(editor, 5, 5), button=3)
    assert not editor.dialog_open
    button(game, editor, "Objekt verschieben")
    click(game, cell(editor, 5, 5))
    click(game, cell(editor, *destination))
    button(game, editor, "Objektgröße")
    if editor.dialog_open:
        text(game, "3x3")
        key(game, pygame.K_RETURN)
    assert editor._snapshot() == original and not editor.undo_stack

    editor.toggle_layer_lock("objects")
    editor.toggle_layer_visibility("objects")
    editor.toggle_eraser()
    click(game, cell(editor, 5, 5))
    assert editor._snapshot() == original and not editor.undo_stack


def test_right_click_confirms_whole_multitile_deletion_and_undo_redo(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    anchor, inner = (4, 4), (5, 5)
    item = GraphicObject(OBJECT, 2, 2)
    editor.objects[anchor] = item
    editor.roofs[anchor] = GraphicObject(ROOF, 2, 2)
    editor.collisions[inner] = "WALL"
    editor.effects[inner] = CellEffects(DamageField(9, 1, None), SlowField(50))
    editor.map[inner[1]][inner[0]] = editor.current_tile
    original = editor._snapshot()
    button(game, editor, "Objekte")

    click(game, cell(editor, *inner), button=3)
    assert editor._dialog["kind"] == "delete"
    assert editor._snapshot() == original and not editor.undo_stack
    game.draw()
    board, size = editor.camera.board_rect, editor.camera.cell_size
    outline = (board.left + anchor[0] * size, board.top + (anchor[1] + 2) * size - 1)
    assert game.screen.get_at(outline)[:3] == DELETE_COLOR
    key(game, pygame.K_ESCAPE)
    assert editor._snapshot() == original and not editor.undo_stack

    click(game, cell(editor, *inner), button=3)
    editor.toggle_layer_lock("objects")
    key(game, pygame.K_RETURN)
    assert not editor.dialog_open
    assert editor._snapshot() == original and not editor.undo_stack
    editor.toggle_layer_lock("objects")

    click(game, cell(editor, *inner), button=3)
    confirm = editor._discard_buttons(editor._dialog_panel())[1]
    click(game, confirm.center)
    after = editor._snapshot()
    assert not editor.dialog_open and not editor.objects
    assert after[:3] == original[:3] and after[4:] == original[4:]
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == original
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor._snapshot() == after


def test_eraser_drag_changes_only_the_active_layer_in_one_step(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    first, second = (4, 4), (5, 4)
    for x, y in (first, second):
        editor.map[y][x] = editor.current_tile
        editor.collisions[x, y] = "WALL"
    original = editor._snapshot()
    editor.toggle_eraser()
    a, b = cell(editor, *first), cell(editor, *second)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=a, button=1),
         pygame.event.Event(pygame.MOUSEMOTION, pos=b, rel=(editor.camera.cell_size, 0), buttons=(1, 0, 0)),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=b, button=1))
    assert editor.map[first[1]][first[0]:second[0] + 1] == [None, None]
    assert editor.collisions == {first: "WALL", second: "WALL"}
    assert len(editor.undo_stack) == 1 and not editor.dialog_open
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == original


def test_inspected_collision_edit_is_undoable_and_keeps_other_layers(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    spot = (4, 3)
    editor.collisions[spot] = "WALL"
    editor.effects[spot] = CellEffects(DamageField(9, 1.5, 8), SlowField(25))
    editor.map[spot[1]][spot[0]] = editor.current_tile
    before = editor._snapshot()
    button(game, editor, "Zelle untersuchen")
    click(game, cell(editor, *spot))
    assert editor.inspected_cell == spot and editor._snapshot() == before
    editor.toggle_layer_lock("collision")
    editor.edit_inspected_collision("BARRIER")
    assert editor.collisions[spot] == "WALL" and not editor.undo_stack
    editor.toggle_layer_lock("collision")
    editor.edit_inspected_collision("BARRIER")
    assert editor.collisions[spot] == "BARRIER"
    after = editor._snapshot()
    assert after[:1] == before[:1] and after[2:] == before[2:]
    assert editor.save_map()
    saved = load_level_document(editor.name)
    assert saved.collision == {spot: "BARRIER"} and saved.effects == editor.effects
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == before


def test_inspected_effect_edit_and_deletion_keep_the_other_effect(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    spot = (4, 7)
    initial = CellEffects(DamageField(9, 1.5, 8), SlowField(25))
    editor.effects[spot] = initial
    button(game, editor, "Zelle untersuchen")
    click(game, cell(editor, *spot))

    editor.toggle_layer_lock("effects")
    editor.edit_inspected_effect("damage")
    assert not editor.dialog_open and not editor.undo_stack
    editor.toggle_layer_lock("effects")
    editor.edit_inspected_effect("damage")
    assert editor.effect_settings is not None
    text(game, "14")
    key(game, pygame.K_RETURN)
    edited_damage = DamageField(14, 1.5, 8)
    assert editor.effects[spot] == CellEffects(edited_damage, initial.slow)

    editor.edit_inspected_effect("slow")
    slow_buttons = dict(editor.effect_settings._slow_buttons())
    click(game, slow_buttons[75].center)
    key(game, pygame.K_RETURN)
    assert editor.effects[spot] == CellEffects(edited_damage, SlowField(75))

    editor.delete_inspected("effects", effect="damage")
    assert editor._dialog["kind"] == "delete"
    assert editor.effects[spot] == CellEffects(edited_damage, SlowField(75))
    key(game, pygame.K_RETURN)
    assert editor.effects[spot] == CellEffects(slow=SlowField(75))
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.effects[spot] == CellEffects(edited_damage, SlowField(75))
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.effects[spot] == initial
