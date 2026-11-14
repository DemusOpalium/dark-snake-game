import pygame

from test_level_studio import button, cell, click, key, studio, text

from modules.graphic_objects import GraphicObject
from modules.level_drafts import load_level_document, write_draft
from modules.roof_settings import RoofVisibility


ROOF = "frostage_roof_005"
OBJECT = "frostage_1x1_007"


def select_from_library(game, editor, asset_id):
    button(game, editor, "Tile-Bibliothek")
    click(game, editor.tile_library.clear_rect.center)
    text(game, asset_id)
    key(game, pygame.K_RETURN)
    assert editor.current_tile == asset_id and not editor.dialog_open


def test_roof_tools_edit_only_the_selected_layer_and_save_undo_redo(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    anchor = (5, 5)
    target = (10, 10)
    ground = editor.current_tile
    click(game, cell(editor, *anchor))
    button(game, editor, "Nur Kollision")
    click(game, cell(editor, *anchor))
    select_from_library(game, editor, OBJECT)
    click(game, cell(editor, *anchor))
    item = GraphicObject(OBJECT, *editor.frost_assets[OBJECT].cells)
    assert editor.objects == {anchor: item}

    select_from_library(game, editor, ROOF)
    assert editor.graphic_layer == "roof"
    button(game, editor, "Grafik + Kollision")
    click(game, cell(editor, *anchor))
    roof = GraphicObject(ROOF, *editor.frost_assets[ROOF].cells)
    assert editor.roofs == {anchor: roof}
    assert editor.collisions == {anchor: "WALL"}
    assert editor.map[anchor[1]][anchor[0]] == ground
    assert editor.objects == {anchor: item}

    button(game, editor, "Objekt verschieben")
    click(game, cell(editor, 6, 6))
    click(game, cell(editor, 11, 11))
    assert editor.roofs == {target: roof}
    click(game, cell(editor, *target))
    button(game, editor, "Objektgröße")
    text(game, "6x3")
    key(game, pygame.K_RETURN)
    resized = GraphicObject(ROOF, 6, 3)
    assert editor.roofs == {target: resized}
    key(game, pygame.K_ESCAPE)

    button(game, editor, "Dachansicht")
    assert not editor.show_roofs
    button(game, editor, "Dach / Foreground")
    assert editor.show_roofs
    click(game, cell(editor, 15, 12), 3)
    assert not editor.roofs
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.roofs == {target: resized}
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert not editor.roofs
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.save_map()
    document = load_level_document(editor.name)
    assert document.roofs == {target: resized}
    assert document.objects == {anchor: item}
    assert document.collision == {anchor: "WALL"}
    assert document.graphics[anchor[1]][anchor[0]] == ground


def test_legacy_roof_transfer_is_explicit_and_reversible(studio):
    game, editor, _ = studio
    anchor = (7, 7)
    roof = GraphicObject(ROOF, 4, 4)
    collision = {anchor: "WALL"}
    write_draft("Altes Dach", editor.map, objects={anchor: roof}, collision=collision)
    key(game, pygame.K_F2)
    assert editor.load_map("Altes Dach")
    assert editor.objects == {anchor: roof} and not editor.roofs

    button(game, editor, "Auf Dachebene")
    click(game, cell(editor, 9, 9))
    assert editor.roofs == {anchor: roof} and not editor.objects
    assert editor.collisions == collision and editor.dirty
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.objects == {anchor: roof} and not editor.roofs and not editor.dirty
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.roofs == {anchor: roof} and not editor.objects
    assert editor.save_map()
    assert editor.load_map("Altes Dach")
    assert editor.roofs == {anchor: roof} and not editor.objects and not editor.dirty
    assert editor.collisions == collision


def test_roof_settings_are_per_level_validated_and_undoable(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    assert editor.new_map("Sichtfenster")
    button(game, editor, "Dachwerte")
    dialog = editor.roof_settings_editor
    text(game, "0,2")
    key(game, pygame.K_RETURN)
    assert editor.dialog_open and dialog.error and not editor.dirty
    click(game, dialog.fields[0].center)
    text(game, "2,5")
    key(game, pygame.K_TAB)
    text(game, "60")
    key(game, pygame.K_TAB)
    text(game, "0,6")
    click(game, dialog.toggle.center)
    click(game, dialog.confirm.center)

    visibility = RoofVisibility(False, 2.5, 60, 0.6)
    assert not editor.dialog_open and editor.roof_visibility == visibility and editor.dirty
    key(game, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.roof_visibility == RoofVisibility() and not editor.dirty
    key(game, pygame.K_y, pygame.KMOD_CTRL)
    assert editor.roof_visibility == visibility
    assert editor.save_map()
    assert editor.new_map("Neues Dach")
    assert editor.roof_visibility == RoofVisibility()
    assert editor.load_map("Sichtfenster")
    assert editor.roof_visibility == visibility and not editor.dirty
