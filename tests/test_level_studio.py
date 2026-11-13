import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_HEIGHT, GRID_WIDTH
from modules import resources
from modules.enums import GameState
from modules.game import Game
from modules import level_editor as layout
from modules import level_drafts
from modules.level_playtest import COLLISION_COLORS


@pytest.fixture
def studio(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    monkeypatch.setattr(resources, "DATA_DIR", profile)
    monkeypatch.chdir(tmp_path)
    game = Game()
    pygame.event.clear()
    return game, game.level_editor, profile


def send(game, *events):
    for event in events:
        pygame.event.post(event)
    game.handle_events()


def key(game, value, mod=0):
    send(game, pygame.event.Event(pygame.KEYDOWN, key=value, mod=mod, unicode=""))


def text(game, value):
    send(game, pygame.event.Event(pygame.TEXTINPUT, text=value))


def click(game, pos, button=1):
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=button))


def button(game, editor, label):
    rect, = [rect for name, rect, _ in editor.buttons if name == label]
    click(game, rect.center)


def cell(col, row):
    return (layout.TOOLBAR_W + col * layout.CELL_SIZE + layout.CELL_SIZE // 2,
            layout.MAP_TOP + row * layout.CELL_SIZE + layout.CELL_SIZE // 2)


def test_collision_tools_keep_graphics_and_walls_independent(studio):
    game, editor, profile = studio
    key(game, pygame.K_F2)
    assert editor.new_map("Wandlabor")
    first, second = list(editor.tiles)[:2]
    editor.current_tile = first
    spot = (4, 3)

    button(game, editor, "Grafik + Kollision")
    click(game, cell(*spot))
    assert editor.map[3][4] == first and editor.collisions == {spot: "WALL"}
    editor.current_tile = second
    button(game, editor, "Nur Grafik")
    click(game, cell(*spot))
    assert editor.map[3][4] == second and editor.collisions == {spot: "WALL"}
    click(game, cell(*spot), button=3)
    assert editor.map[3][4] is None and editor.collisions == {spot: "WALL"}

    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map[3][4] == second and editor.collisions == {spot: "WALL"}
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map[3][4] == first and editor.collisions == {spot: "WALL"}
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map[3][4] is None and editor.collisions == {}
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.map[3][4] == first and editor.collisions == {spot: "WALL"}

    button(game, editor, "Nur Kollision")
    click(game, cell(*spot), button=3)
    assert editor.collisions == {} and editor.map[3][4] == first
    button(game, editor, "BARRIER")
    click(game, cell(*spot))
    assert editor.collisions == {spot: "BARRIER"} and editor.map[3][4] == first
    button(game, editor, "WALL")
    click(game, cell(5, 3))
    assert editor.dirty
    assert editor.save_map()
    assert not editor.dirty
    saved = json.loads((profile / "levels" / "Wandlabor.json").read_text(encoding="utf-8"))
    assert saved["version"] == 1
    assert level_drafts.read_level("Wandlabor") == (editor.map, editor.collisions)
    assert saved["graphics"][3][5] is None

    reopened = Game()
    key(reopened, pygame.K_F2)
    assert reopened.level_editor.load_map("Wandlabor")
    assert reopened.level_editor.collisions == {spot: "BARRIER", (5, 3): "WALL"}
    reopened.draw()
    outline = (layout.TOOLBAR_W + 5 * layout.CELL_SIZE + 1, layout.MAP_TOP + 3 * layout.CELL_SIZE + 1)
    assert reopened.screen.get_at(outline)[:3] == COLLISION_COLORS["WALL"]
    button(reopened, reopened.level_editor, "Kollision ein/aus")
    reopened.draw()
    assert reopened.screen.get_at(outline)[:3] != COLLISION_COLORS["WALL"]
    assert not reopened.level_editor.dirty


def test_combined_wall_stroke_undo_redo_and_clear_affect_both_layers(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    button(game, editor, "Grafik + Kollision")
    start, end = cell(3, 5), cell(4, 5)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1),
         pygame.event.Event(pygame.MOUSEMOTION, pos=end, rel=(layout.CELL_SIZE, 0), buttons=(1, 0, 0)),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=end, button=1))
    assert editor.map[5][3:5] == [editor.current_tile] * 2
    assert editor.collisions == {(3, 5): "WALL", (4, 5): "WALL"}
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert not editor.dirty and editor.map[5][3:5] == [None, None] and not editor.collisions
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.dirty and editor.collisions == {(3, 5): "WALL", (4, 5): "WALL"}
    click(game, start, button=3)
    assert editor.map[5][3:5] == [None, editor.current_tile] and editor.collisions == {(4, 5): "WALL"}


def test_collision_only_edits_use_discard_guard_and_f2_exits_test_first(studio):
    game, editor, profile = studio
    key(game, pygame.K_F2)
    assert editor.new_map("Wand")
    assert editor.save_map()
    original = (profile / "levels" / "Wand.json").read_bytes()
    button(game, editor, "Nur Kollision")
    click(game, cell(4, 3))
    assert editor.dirty and all(tile is None for tile in editor.map[3])
    button(game, editor, "Test 1P")
    assert editor.playtest is not None
    key(game, pygame.K_F2)
    assert editor.active and editor.playtest is None and editor.dirty and not editor.dialog_open
    key(game, pygame.K_F2)
    assert editor.active and editor.dialog_open
    key(game, pygame.K_v)
    assert not editor.active and not editor.dirty and not editor.collisions
    assert (profile / "levels" / "Wand.json").read_bytes() == original


def test_saved_wall_is_playable_but_classic_background_keeps_original_movement(studio, monkeypatch):
    game, editor, _ = studio
    center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    wall = (center[0] + 2, center[1])
    key(game, pygame.K_F2)
    assert editor.new_map("Classic-Hintergrund")
    button(game, editor, "Grafik + Kollision")
    click(game, cell(*wall))
    assert editor.save_map()
    button(game, editor, "Für Classic wählen")
    key(game, pygame.K_F2)
    game.start_game(1)
    assert game.level_map[wall[1]][wall[0]] == editor.current_tile

    game.items.clear()
    monkeypatch.setattr("modules.game.random.random", lambda: 1.0)
    for _ in range(2):
        game.last_update_time -= 1.0
        game.update()
    assert game.snake[0] == wall

    key(game, pygame.K_F2)
    assert editor.load_map("Classic-Hintergrund")
    button(game, editor, "Test 1P")
    session = editor.playtest
    session.update(session._next_step + session.step_seconds)
    assert session.players[0].cell == (center[0] + 1, center[1])
    assert session.players[0].blocked == "WALL"


@pytest.mark.parametrize("player_count", [1, 2])
def test_editor_playtest_hits_walls_via_game_frames_and_returns_to_unsaved_draft(studio, monkeypatch,
                                                                              player_count):
    game, editor, profile = studio
    game.start_game(1)
    regular_round = (game.game_state, game.player_count, game.snake.copy(),
                     game.score, game.lives, game.player_health, game.background)
    key(game, pygame.K_F2)
    center_x, center_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
    assert editor.new_map("Nur im Speicher")
    button(game, editor, "Nur Kollision")
    click(game, cell(center_x + 2, center_y))
    if player_count == 2:
        button(game, editor, "BARRIER")
        click(game, cell(center_x + 2, center_y + 2))
    before = deepcopy((editor.map, editor.collisions, editor.undo_stack))
    profile_before = {path.relative_to(profile): path.read_bytes()
                      for path in profile.rglob("*") if path.is_file()}

    button(game, editor, f"Test {player_count}P")
    session = editor.playtest
    assert session.player_count == player_count and game.player_count == 1
    clock = [session._next_step]
    monkeypatch.setattr("modules.game.time.monotonic", lambda: clock[0])
    rows = [center_y + index * 2 for index in range(player_count)]
    assert [player.cell for player in session.players] == [(center_x, row) for row in rows]

    game.run_frame()
    assert [player.cell for player in session.players] == [(center_x + 1, row) for row in rows]
    for _ in range(4):
        clock[0] += session.step_seconds
        game.run_frame()
    assert [player.cell for player in session.players] == [(center_x + 1, row) for row in rows]
    assert [player.blocked for player in session.players] == ["WALL", "BARRIER"][:player_count]

    key(game, pygame.K_w)
    if player_count == 2:
        key(game, pygame.K_DOWN)
    clock[0] += session.step_seconds
    game.run_frame()
    assert [player.cell for player in session.players] == [(center_x + 1, center_y - 1),
                                                          (center_x + 1, center_y + 3)][:player_count]
    key(game, pygame.K_ESCAPE)
    assert editor.active and editor.playtest is None and editor.dirty
    assert (editor.map, editor.collisions, editor.undo_stack) == before
    assert (game.game_state, game.player_count, game.snake, game.score,
            game.lives, game.player_health, game.background) == regular_round
    assert {path.relative_to(profile): path.read_bytes()
            for path in profile.rglob("*") if path.is_file()} == profile_before


def world_action(game, tree, label):
    rect, = [rect for rect, name, _ in tree._controls() if name == label]
    click(game, rect.center)


def world_row(tree, area, item_id):
    rect, = [rect for rect, kind, entry, _ in tree._rows(area)
             if kind == "level" and entry == item_id]
    return rect


def test_world_studio_organizes_drafts_and_reloads_order(studio):
    game, editor, profile = studio
    key(game, pygame.K_F2)
    for index, name in enumerate(("Anfang", "Arena")):
        assert editor.new_map(name)
        click(game, cell(index, 0))
        assert editor.save_map()
    originals = {path.name: path.read_bytes() for path in (profile / "levels").glob("*.json")}

    button(game, editor, "Welten")
    tree = editor.world_tree
    game.draw()
    start_id = tree.library.level_for_draft("Anfang").id
    arena_id = tree.library.level_for_draft("Arena").id
    world_action(game, tree, "Welt neu")
    text(game, "Galaxie")
    key(game, pygame.K_RETURN)
    world_id = tree.target_world
    world_action(game, tree, "Welt umbenennen")
    text(game, "Sternenwelt")
    key(game, pygame.K_RETURN)
    assert tree.library.worlds[world_id].name == "Sternenwelt"

    click(game, world_row(tree, tree.design, start_id).midleft)
    world_action(game, tree, "Zuordnen")
    world_action(game, tree, "Level umbenennen")
    text(game, "Sternentor")
    key(game, pygame.K_RETURN)
    world_action(game, tree, "Zur Reihenfolge")
    click(game, world_row(tree, tree.design, arena_id).midleft)
    world_action(game, tree, "Zur Reihenfolge")
    world_action(game, tree, "Nach oben")
    assert tree.library.game_order == (arena_id, start_id)

    source = world_row(tree, tree.order, arena_id)
    target = world_row(tree, tree.order, start_id)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=source.midleft, button=1),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=target.midleft, button=1))
    assert tree.library.game_order == (start_id, arena_id)

    restarted = Game()
    key(restarted, pygame.K_F2)
    button(restarted, restarted.level_editor, "Welten")
    reopened = restarted.level_editor.world_tree
    assert reopened.library.game_order == (start_id, arena_id)
    assert reopened.library.levels[start_id].name == "Sternentor"
    assert reopened.library.levels[start_id].world_id == world_id
    click(restarted, reopened._open_rect(world_row(reopened, reopened.order, start_id)).center)
    assert restarted.level_editor.name == "Anfang"
    assert restarted.level_editor._display_name() == "Sternentor"
    assert restarted.level_editor.map[0][0]
    assert restarted.classic_level_name is None

    button(restarted, restarted.level_editor, "Welten")
    world_action(restarted, reopened, "Entfernen")
    assert reopened.library.game_order == (arena_id,)
    world_action(restarted, reopened, "Entfernen")
    assert reopened.message == "Dieses Level steht nicht in der Reihenfolge."
    assert {path.name: path.read_bytes() for path in (profile / "levels").glob("*.json")} == originals


def test_world_tree_open_respects_draft_discard_guard(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    assert editor.new_map("Gespeichert")
    assert editor.save_map()
    assert editor.new_map("In Arbeit")
    click(game, cell(1, 0))
    button(game, editor, "Welten")
    tree = editor.world_tree
    level = tree.library.level_for_draft("Gespeichert")
    row = world_row(tree, tree.design, level.id)
    click(game, tree._open_rect(row).center)
    assert editor.dirty and editor.dialog_open
    key(game, pygame.K_ESCAPE)
    assert editor.name == "In Arbeit" and editor.map[0][1]


def test_tile_library_search_selects_original_key_for_painting(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    tile = next(key for key in editor.tiles if key.startswith("frosthauch_"))
    button(game, editor, "Tile-Bibliothek")
    text(game, f"{tile}.png")
    game.draw()
    key(game, pygame.K_RETURN)
    assert editor.current_tile == tile and not editor.dialog_open
    click(game, cell(2, 2))
    assert editor.map[2][2] == tile


def legacy_file(profile, tile):
    legacy = profile / "custom_level.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    level_map = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    level_map[0][0] = tile
    legacy.write_text(json.dumps(level_map), encoding="utf-8")
    return legacy, level_map


def test_f2_opens_and_closes_clean_editor_without_starting_a_round(studio):
    game, editor, _ = studio
    assert not editor.active

    key(game, pygame.K_F2)
    assert editor.active and not editor.dirty
    game.draw()
    assert game.game_state == GameState.INTRO

    key(game, pygame.K_F2)
    assert not editor.active
    assert game.game_state == GameState.INTRO


def test_creates_two_named_drafts_and_reopens_first_from_keyboard(studio):
    game, editor, profile = studio
    key(game, pygame.K_F2)

    key(game, pygame.K_n, pygame.KMOD_CTRL)
    assert editor.dialog_open
    text(game, "Level_001")
    key(game, pygame.K_RETURN)
    click(game, cell(0, 0))
    key(game, pygame.K_s, pygame.KMOD_CTRL)
    first = deepcopy(editor.map)
    original = (profile / "levels" / "Level_001.json").read_bytes()
    assert editor.name == "Level_001" and not editor.dirty

    button(game, editor, "Neu")
    text(game, "Pilzwelt_01")
    key(game, pygame.K_RETURN)
    click(game, cell(1, 0))
    button(game, editor, "Speichern")
    assert editor.name == "Pilzwelt_01" and not editor.dirty
    assert (profile / "levels" / "Pilzwelt_01.json").is_file()
    assert (profile / "levels" / "Level_001.json").read_bytes() == original
    assert editor.map != first

    key(game, pygame.K_o, pygame.KMOD_CTRL)
    assert editor.dialog_open
    key(game, pygame.K_RETURN)
    assert editor.name == "Level_001"
    assert editor.map == first
    assert not editor.dirty
    assert not editor.undo_stack and not editor.redo_stack

    # The same chooser is usable with a mouse.
    button(game, editor, "Öffnen")
    panel = editor._dialog_panel()
    click(game, (panel.x + 30, panel.y + 50 + layout.OPEN_ROW_H))
    assert editor.name == "Pilzwelt_01"
    button(game, editor, "Öffnen")
    key(game, pygame.K_RETURN)
    assert editor.name == "Level_001"

    # An explicit save updates the currently loaded draft only.
    second_path = profile / "levels" / "Pilzwelt_01.json"
    second_original = second_path.read_bytes()
    click(game, cell(2, 0))
    key(game, pygame.K_s, pygame.KMOD_CTRL)
    assert not editor.dirty
    assert (profile / "levels" / "Level_001.json").read_bytes() != original
    assert second_path.read_bytes() == second_original


def test_dirty_close_and_switch_require_confirmation(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.new_map("Erster")
    click(game, cell(1, 0))
    before = deepcopy(editor.map)

    key(game, pygame.K_F2)
    assert editor.active and editor.dialog_open
    key(game, pygame.K_ESCAPE)
    assert editor.active and editor.dirty and not editor.dialog_open
    assert editor.map == before

    editor.new_map("Zweiter")
    assert editor.dialog_open and editor.name == "Erster"
    key(game, pygame.K_v)
    assert editor.name == "Zweiter"
    assert editor.map[0][1] is None and not editor.undo_stack

    click(game, cell(1, 0))
    key(game, pygame.K_TAB)
    assert editor.active and editor.dialog_open and not game.admin_panel.active
    key(game, pygame.K_v)
    assert not editor.active and game.admin_panel.active


def test_window_close_keeps_dirty_level_until_confirmed(studio):
    game, editor, profile = studio
    key(game, pygame.K_F2)
    click(game, cell(0, 0))

    send(game, pygame.event.Event(pygame.QUIT))
    assert editor.active and editor.dialog_open and editor.dirty
    key(game, pygame.K_ESCAPE)
    assert editor.active and editor.dirty
    assert editor.map[0][0] == editor.current_tile

    send(game, pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        key(game, pygame.K_v)
    assert not list((profile / "levels").glob("*.json"))


@pytest.mark.parametrize("bad_data", ["{falsch", "[]", "[null]"])
def test_invalid_level_preserves_open_draft_and_undo_history(studio, bad_data):
    game, editor, profile = studio
    key(game, pygame.K_F2)
    editor.new_map("Gut")
    click(game, cell(0, 0))
    assert editor.save_map()
    click(game, cell(1, 0))
    editor.undo()
    before = deepcopy((editor.map, editor.undo_stack, editor.redo_stack))
    (profile / "levels" / "Kaputt.json").write_text(bad_data, encoding="utf-8")

    editor.load_map("Kaputt")

    assert editor.name == "Gut" and not editor.dirty
    assert (editor.map, editor.undo_stack, editor.redo_stack) == before
    assert "nicht" in editor.info.lower() or "ungültig" in editor.info.lower()
    editor.redo()
    assert editor.map[0][1] == editor.current_tile


def test_legacy_is_readable_and_standard_classic_does_not_load_it(studio):
    game, editor, profile = studio
    legacy, expected = legacy_file(profile, editor.current_tile)
    old_bytes = legacy.read_bytes()
    game.start_game(1)
    assert not game.level_map and game.classic_level_name is None
    assert game.background.get_at((0, 0)) == game.default_background_surface.get_at((0, 0))

    key(game, pygame.K_F2)
    editor.load_legacy_map()
    assert editor.map == expected and not editor.dirty
    assert editor.collisions == {}
    assert not game.level_map and game.classic_level_name is None
    button(game, editor, "Für Classic wählen")
    assert game.classic_level_name is not None and not game.level_map
    key(game, pygame.K_F2)
    game.start_game(1)
    assert game.level_map == expected
    assert legacy.read_bytes() == old_bytes

    key(game, pygame.K_F2)
    click(game, cell(1, 0))
    key(game, pygame.K_s, pygame.KMOD_CTRL)
    assert editor.dialog_open
    text(game, "Alte_Karte")
    key(game, pygame.K_RETURN)
    assert level_drafts.read_level("Alte_Karte") == (editor.map, {})
    assert legacy.read_bytes() == old_bytes


def test_classic_explicit_selection_copies_saved_draft_and_can_be_cleared(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    editor.new_map("Arena")
    click(game, cell(0, 0))
    assert editor.save_map()
    saved = deepcopy(editor.map)
    assert game.classic_level_name is None

    button(game, editor, "Für Classic wählen")
    assert game.classic_level_name == "Arena"
    click(game, cell(1, 0))
    assert editor.dirty and editor.map != saved
    game.start_game(1)
    assert game.level_map == saved and game.level_map is not editor.map
    assert editor.map[0][1] == editor.current_tile

    button(game, editor, "Classic-Standard")
    game.start_game(1)
    assert game.classic_level_name is None and not game.level_map
    game.build_background_from_map()
    assert game.level_background_surface.get_at((0, 0)) == game.default_background_surface.get_at((0, 0))


def test_visual_preview_leaves_round_files_and_edit_history_intact(studio):
    game, editor, profile = studio
    legacy, _ = legacy_file(profile, editor.current_tile)
    previous_legacy = legacy.read_bytes()
    game.start_game(2)
    round_before = (game.game_state, game.score, game.lives, game.background, game.level_map)
    key(game, pygame.K_F2)
    editor.new_map("Vorschaukarte")
    click(game, cell(0, 0))
    before = deepcopy((editor.map, editor.undo_stack, editor.redo_stack))
    profile_before = {path.relative_to(profile): path.read_bytes()
                      for path in profile.rglob("*") if path.is_file()}

    button(game, editor, "Vorschau starten")
    assert editor.preview_active and editor.active
    assert (game.game_state, game.score, game.lives, game.background, game.level_map) == round_before
    game.draw()
    default_pixel = (2 * layout.GRID_SIZE + layout.GRID_SIZE // 2, layout.GRID_SIZE // 2)
    assert game.screen.get_at(cell(2, 0)) == game.default_background_surface.get_at(default_pixel)
    click(game, cell(1, 0))
    key(game, pygame.K_ESCAPE)

    assert not editor.preview_active and editor.active and editor.dirty
    assert (editor.map, editor.undo_stack, editor.redo_stack) == before
    assert (game.game_state, game.score, game.lives, game.background, game.level_map) == round_before
    assert legacy.read_bytes() == previous_legacy
    assert {path.relative_to(profile): path.read_bytes()
            for path in profile.rglob("*") if path.is_file()} == profile_before


def test_tile_drag_overwrite_erase_and_border_have_undo_redo(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    first, second = list(editor.tiles)[:2]
    a, b = cell(0, 0), cell(1, 0)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=a, button=1),
         pygame.event.Event(pygame.MOUSEMOTION, pos=b, rel=(layout.CELL_SIZE, 0), buttons=(1, 0, 0)),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=b, button=1))
    assert editor.map[0][:2] == [first, first]
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.map[0][:2] == [None, None]
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.map[0][:2] == [first, first]

    editor.current_tile = second
    click(game, b)
    assert editor.map[0][:2] == [first, second]
    click(game, b, button=3)
    assert editor.map[0][:2] == [first, None]
    editor.undo()
    assert editor.map[0][:2] == [first, second]

    last = cell(GRID_WIDTH - 1, GRID_HEIGHT - 1)
    assert game.screen.get_rect().collidepoint(last)
    click(game, last)
    assert editor.map[-1][-1] == second
    before_border = deepcopy(editor.map)
    button(game, editor, "Rand")
    assert editor.map != before_border
    editor.undo()
    assert editor.map == before_border


def test_palette_scroll_reaches_last_tile_and_favorites_are_selectable(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    first, second = list(editor._visible_tiles())[:2]
    assert editor.current_tile == first[0]
    click(game, second[1].center)
    assert editor.current_tile == second[0]

    palette = layout.PALETTE_RECT
    send(game, pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-10000, pos=layout.MAP_RECT.center))
    assert editor.tile_scroll_offset == 0
    send(game, pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-10000, pos=palette.center))
    assert editor.tile_scroll_offset < 0
    last_tile = next(reversed(editor.tiles))
    rect = dict(editor._visible_tiles())[last_tile]
    assert palette.contains(rect)
    assert 0 <= palette.bottom - rect.bottom < rect.height
    click(game, rect.center, button=3)
    assert editor.favorites == [last_tile]
    click(game, editor._favorite_rect(0).center)
    assert editor.current_tile == last_tile
    click(game, cell(0, 0))
    assert editor.map[0][0] == last_tile


def test_undo_ends_an_active_paint_stroke_before_more_mouse_motion(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    a, b = cell(0, 0), cell(1, 0)
    send(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=a, button=1))
    assert editor.map[0][0] == editor.current_tile

    key(game, pygame.K_z, pygame.KMOD_CTRL)
    send(game, pygame.event.Event(pygame.MOUSEMOTION, pos=b, rel=(layout.CELL_SIZE, 0),
                                  buttons=(1, 0, 0)),
         pygame.event.Event(pygame.MOUSEBUTTONUP, pos=b, button=1))
    assert editor.map[0][:2] == [None, None]
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.map[0][:2] == [editor.current_tile, None]
