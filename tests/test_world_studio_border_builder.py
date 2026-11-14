"""Exercise Rand-Builder through editor events and the shared tile library."""

from copy import deepcopy

import pygame

from test_level_studio import button, click, key, send, studio, text

from config import GRID_HEIGHT, GRID_WIDTH
from modules.border_builder_ui import ACCENT, CORNER as CORNER_COLOR, OVERWRITE, UNCHANGED
from modules.graphic_objects import GraphicObject
from modules.level_drafts import load_level_document, write_draft
from modules.level_effects import CellEffects, DamageField, SlowField
from modules.roof_settings import RoofVisibility


LEFT = "frosthauch_0_0"
RIGHT = "frosthauch_0_1"
TOP = "frosthauch_0_2"
BOTTOM = "frosthauch_0_3"
CORNER = "frosthauch_1_0"
EXISTING = "frosthauch_1_1"
MIDDLE = "frosthauch_1_2"


def open_builder(game, editor):
    button(game, editor, "Rand")
    assert editor.dialog_open and editor._dialog["kind"] == "border"
    return editor.border_builder


def choose_floor(game, editor, row, tile):
    click(game, row.choose.center)
    click(game, editor.tile_library.clear_rect.center)
    text(game, f"{tile}.png")
    key(game, pygame.K_RETURN)
    assert editor.dialog_open


def preview_of(builder, level_map):
    return {(cell.x, cell.y): cell for cell in builder.plan.preview(level_map)}


def preview_cell(builder, x, y):
    rect = builder.preview_rect
    size = rect.width // GRID_WIDTH
    return pygame.Rect(rect.x + x * size, rect.y + y * size, size, size)


def test_independent_edges_and_corner_preview_apply_as_one_undoable_floor_edit(studio):
    game, editor, profile = studio
    graphics = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    graphics[0][0] = EXISTING
    graphics[0][1] = TOP
    graphics[1][0] = EXISTING
    graphics[2][2] = MIDDLE
    collision = {(0, 0): "WALL", (GRID_WIDTH - 1, 2): "BARRIER"}
    effects = {(0, 1): CellEffects(DamageField(7, 1.5, 4), SlowField(25))}
    objects = {(0, 0): GraphicObject("frostage_1x1_007", 1, 1)}
    roofs = {(GRID_WIDTH - 2, GRID_HEIGHT - 2): GraphicObject("frostage_roof_005", 2, 2)}
    visibility = RoofVisibility(enabled=False, radius=3, transparency=65, softness=0.5)
    write_draft("Randprobe", graphics, collision=collision, effects=effects, objects=objects,
                roofs=roofs, roof_visibility=visibility)
    draft_file = profile / "levels" / "Randprobe.json"
    before_disk = draft_file.read_bytes()

    key(game, pygame.K_F2)
    assert editor.load_map("Randprobe")
    before = editor._snapshot()
    previous_brush = editor.current_tile
    builder = open_builder(game, editor)
    assert not preview_of(builder, editor.map)

    for side, tile in (("left", LEFT), ("right", RIGHT), ("top", TOP), ("bottom", BOTTOM)):
        choose_floor(game, editor, builder.side_rows[side], tile)
    choose_floor(game, editor, builder.corner_rows["top_left"], CORNER)
    preview = preview_of(builder, editor.map)
    game.draw()
    assert game.screen.get_at(preview_cell(builder, 0, 0).center)[:3] == CORNER_COLOR
    assert game.screen.get_at(preview_cell(builder, 1, 0).topleft)[:3] == UNCHANGED
    assert game.screen.get_at(preview_cell(builder, 0, 1).topleft)[:3] == OVERWRITE
    assert game.screen.get_at(preview_cell(builder, GRID_WIDTH - 1, 1).topleft)[:3] == ACCENT
    assert len(preview) == 2 * GRID_WIDTH + 2 * GRID_HEIGHT - 4

    assert preview[0, 0].tile == CORNER
    assert preview[GRID_WIDTH - 1, 0].tile == TOP
    assert preview[0, GRID_HEIGHT - 1].tile == BOTTOM
    assert preview[GRID_WIDTH - 1, GRID_HEIGHT - 1].tile == BOTTOM
    assert preview[0, 1].tile == LEFT
    assert preview[GRID_WIDTH - 1, 1].tile == RIGHT
    assert preview[2, 0].tile == TOP
    assert preview[2, GRID_HEIGHT - 1].tile == BOTTOM
    assert {pos for pos, cell in preview.items() if cell.overwrites} == {(0, 0), (0, 1)}
    assert preview[0, 0].previous == EXISTING and preview[0, 1].previous == EXISTING
    assert not preview[1, 0].changed and not preview[1, 0].overwrites
    assert (2, 2) not in preview

    assert editor._snapshot() == before
    assert not editor.undo_stack and not editor.redo_stack and not editor.dirty
    assert draft_file.read_bytes() == before_disk
    click(game, builder.apply_button.center)

    assert not editor.dialog_open
    assert editor.current_tile == previous_brush
    assert len(editor.undo_stack) == 1 and editor.dirty
    expected = deepcopy(graphics)
    for cell in preview.values():
        expected[cell.y][cell.x] = cell.tile
    assert editor.map == expected
    assert editor._snapshot()[1:] == before[1:]

    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor._snapshot() == before
    assert not editor.undo_stack and len(editor.redo_stack) == 1 and not editor.dirty
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.map == expected and editor._snapshot()[1:] == before[1:]
    assert draft_file.read_bytes() == before_disk

    assert editor.save_map()
    saved = load_level_document("Randprobe")
    assert saved.graphics == expected
    assert saved.collision == collision
    assert saved.effects == effects
    assert saved.objects == objects
    assert saved.roofs == roofs
    assert saved.roof_visibility == visibility


def test_single_side_and_middle_fill_change_separate_regions(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.current_tile = MIDDLE
    builder = open_builder(game, editor)
    choose_floor(game, editor, builder.side_rows["left"], LEFT)
    preview = preview_of(builder, editor.map)
    assert set(preview) == {(0, y) for y in range(GRID_HEIGHT)}
    assert all(cell.tile == LEFT for cell in preview.values())
    click(game, builder.apply_button.center)

    border_only = [[LEFT] + [None] * (GRID_WIDTH - 1) for _ in range(GRID_HEIGHT)]
    assert editor.map == border_only
    button(game, editor, "Mittelfeld")
    assert editor.map[0] == editor.map[-1] == border_only[0]
    assert all(row == [LEFT] + [MIDDLE] * (GRID_WIDTH - 2) + [None] for row in editor.map[1:-1])
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map == border_only
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert not any(any(row) for row in editor.map)


def test_all_edges_preview_survives_resize_and_escape_cancels(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.current_tile = MIDDLE
    builder = open_builder(game, editor)
    click(game, builder.all_button.center)
    before = editor._snapshot()
    preview = preview_of(builder, editor.map)
    assert len(preview) == 2 * GRID_WIDTH + 2 * GRID_HEIGHT - 4
    assert all(cell.tile == MIDDLE for cell in preview.values())
    game.draw()

    pygame.display.set_mode((900, 620), pygame.RESIZABLE)
    send(game, pygame.event.Event(pygame.WINDOWSIZECHANGED, x=900, y=620))
    game.draw()
    assert editor.dialog_open
    builder = editor.border_builder
    assert preview_of(builder, editor.map) == preview
    assert game.screen.get_rect().contains(builder.preview_rect)
    assert game.screen.get_rect().contains(builder.apply_button)
    assert not builder.preview_rect.colliderect(builder.apply_button)
    key(game, pygame.K_ESCAPE)
    assert not editor.dialog_open and editor.active
    assert editor._snapshot() == before
    assert not editor.undo_stack and not editor.redo_stack


def test_invalid_or_unchanged_floor_selection_keeps_preview_uncommitted(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.current_tile = MIDDLE
    editor.map[0] = [MIDDLE] * GRID_WIDTH
    before = editor._snapshot()
    builder = open_builder(game, editor)
    click(game, builder.side_rows["top"].toggle.center)
    assert len(preview_of(builder, editor.map)) == GRID_WIDTH
    assert not any(cell.changed for cell in preview_of(builder, editor.map).values())
    click(game, builder.apply_button.center)
    assert editor.dialog_open and not editor.undo_stack

    click(game, builder.side_rows["left"].choose.center)
    click(game, editor.tile_library.clear_rect.center)
    text(game, "frostage_roof_005")
    key(game, pygame.K_RETURN)
    assert builder.target_pending
    assert "left" not in builder.plan.sides
    assert editor.current_tile == MIDDLE

    click(game, editor.tile_library.clear_rect.center)
    text(game, f"{LEFT}.png")
    key(game, pygame.K_RETURN)
    assert not builder.target_pending
    assert builder.plan.sides["left"] == LEFT
    assert editor.current_tile == MIDDLE
    click(game, builder.cancel_button.center)
    assert not editor.dialog_open
    assert editor._snapshot() == before
    assert not editor.undo_stack
