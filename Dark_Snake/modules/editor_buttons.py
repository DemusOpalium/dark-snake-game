"""Load and draw World Studio button graphics by stable action ID."""

from dataclasses import dataclass
from functools import lru_cache
import json
import logging
from pathlib import Path
import re

import pygame

from modules.resources import find_asset


LOGGER = logging.getLogger(__name__)
BUTTON_HEIGHT = 44
MAX_ART_WIDTH = 180
PAD = 2
TEXT = (232, 240, 250)
MUTED = (166, 181, 202)
BUTTON = (29, 43, 62)
STROKE = (61, 87, 111)
HOVER = (175, 223, 247)
ACTIVE = (122, 206, 252)
SELECTED = (252, 208, 134)

HINTS = {
    "nav_file": ("Level öffnen, speichern und organisieren.", "Open, save, and organize levels."),
    "nav_build": ("Bodenflächen und Grafikobjekte bearbeiten.", "Edit floor tiles and graphical objects."),
    "nav_layers": ("Arbeitsebenen und Kollisionswerkzeuge wählen.", "Choose editing layers and collision tools."),
    "nav_effects": ("Schaden, Verlangsamung und Dachwerte einstellen.",
                    "Configure damage, slow fields, and roof settings."),
    "nav_view": ("Kartenausschnitt, Seitenleisten und Markierungen einstellen.",
                 "Adjust the map view, sidebars, and overlays."),
    "nav_test": ("Vorschau und isolierte Leveltests öffnen.", "Open the preview and standalone level tests."),
    "nav_learn": ("Die spielbare Dach-Demo und ihre Anleitung öffnen.", "Open the playable roof demo and its guide."),
    "nav_help": ("Die Hilfe zum World Studio öffnen.", "Open World Studio help."),
    "nav_language": ("Editor-Sprache zwischen Deutsch und Englisch wechseln.",
                     "Switch the editor language between English and German."),
    "sidebar_properties": ("Eigenschaften des gewählten Werkzeugs anzeigen.",
                           "Show settings for the selected tool."),
    "sidebar_layers": ("Den Layer Explorer anzeigen.", "Show the Layer Explorer."),
    "sidebar_cell": ("Den Zellen-Inspektor anzeigen.", "Show the Cell Inspector."),
    "sidebar_help": ("Die Bedienung des Editors erklären.", "Learn how to use the editor."),
    "sidebar_learn": ("Die Dach-Demo und ihre Anleitung anzeigen.", "Show the roof demo and its guide."),
    "file_new": ("Einen leeren Levelentwurf anlegen.", "Create an empty level draft."),
    "file_open": ("Einen gespeicherten Levelentwurf öffnen.", "Open a saved level draft."),
    "file_save": ("Den aktuellen Levelentwurf speichern.", "Save the current level draft."),
    "file_worlds": ("Entwürfe nach Themenwelten organisieren.", "Organize drafts into themed worlds."),
    "file_undo": ("Die letzte Kartenänderung rückgängig machen.", "Undo the last map change."),
    "file_redo": ("Eine rückgängig gemachte Änderung wiederholen.", "Redo an undone change."),
    "file_use_classic": ("Diesen Entwurf für die nächste Classic-Runde wählen.",
                         "Select this draft for the next Classic round."),
    "file_classic_default": ("Die Standardkarte für die nächste Classic-Runde wählen.",
                             "Select the default map for the next Classic round."),
    "build_middle": ("Die Bodenfläche innerhalb des Randes füllen.", "Fill the floor area inside the border."),
    "build_border": ("Bodenkacheln am Kartenrand mit Vorschau gestalten.", "Design and preview the map's floor border."),
    "build_move_objects": ("Ein Grafikobjekt und danach sein Ziel anklicken.",
                           "Click a graphical object, then its destination."),
    "build_object_size": ("Die Größe des Grafikobjekts in Rasterfeldern einstellen.",
                          "Set the graphical object's size in grid cells."),
    "build_tile_library": ("Die Suche in der Kachelbibliothek links öffnen.", "Search the tile library on the left."),
    "build_transfer_roof": ("Ein Dachobjekt auf die Vordergrundebene verschieben.",
                            "Move a roof object to the foreground layer."),
    "border_all": ("Alle vier Seiten für die Randvorschau ein- oder ausschalten.",
                   "Toggle all four sides of the border preview."),
    "border_left": ("Die linke Randseite für die Vorschau ein- oder ausschalten.",
                    "Toggle the left side of the border preview."),
    "border_right": ("Die rechte Randseite für die Vorschau ein- oder ausschalten.",
                     "Toggle the right side of the border preview."),
    "border_top": ("Die obere Randseite für die Vorschau ein- oder ausschalten.",
                   "Toggle the top side of the border preview."),
    "border_bottom": ("Die untere Randseite für die Vorschau ein- oder ausschalten.",
                      "Toggle the bottom side of the border preview."),
    "border_corner": ("Die Auswahl für die vier Eckgrafiken ein- oder ausblenden.",
                      "Show or hide the four corner tile selectors."),
    "layer_ground": ("Einzelne Bodenkacheln bearbeiten.", "Edit ground tiles."),
    "layer_objects": ("Grafikobjekte bearbeiten.", "Edit graphical objects."),
    "layer_roof": ("Dächer auf der Vordergrundebene bearbeiten.", "Edit roofs on the foreground layer."),
    "layer_collision": ("WALL- und BARRIER-Kollisionsfelder bearbeiten.", "Edit WALL and BARRIER collision cells."),
    "layer_effects": ("Effektfelder bearbeiten oder anzeigen.", "Edit or display effect fields."),
    "tool_graphics": ("Grafiken bearbeiten.", "Edit graphics."),
    "tool_combined": ("Grafik und Kollision gemeinsam bearbeiten.", "Edit graphics and collision together."),
    "collision_wall": ("WALL-Felder blockieren im isolierten Leveltest.", "WALL cells block movement in the level test."),
    "collision_barrier": ("BARRIER-Felder blockieren im isolierten Leveltest.",
                          "BARRIER cells block movement in the level test."),
    "effect_damage": ("Felder mit wiederholtem Schaden platzieren.", "Place fields that deal recurring damage."),
    "effect_slow": ("Felder mit verlangsamter Bewegung platzieren.", "Place fields that slow movement."),
    "effect_values": ("Schaden, Trefferintervall, Dauer und Verlangsamung einstellen.",
                      "Set damage, hit interval, duration, and slow amount."),
    "roof_settings": ("Radius, Stärke und weichen Rand der Dach-Sichtfenster einstellen.",
                      "Set the roof reveal radius, transparency, and edge softness."),
    "view_fit_map": ("Das gesamte Spielfeld anzeigen.", "Fit the whole map in view."),
    "view_library": ("Den Baukasten ein- oder ausblenden.", "Show or hide the tile library."),
    "view_panel": ("Den Arbeitsbereich rechts ein- oder ausblenden.", "Show or hide the workspace on the right."),
    "view_cell": ("Eine Zelle und ihre Ebenen ansehen.", "Inspect a cell and its layers."),
    "view_collision": ("Kollisionsmarkierungen ein- oder ausblenden.", "Show or hide collision markers."),
    "view_effects": ("Effektmarkierungen ein- oder ausblenden.", "Show or hide effect markers."),
    "view_roof": ("Dächer in der Editoransicht ein- oder ausblenden.", "Show or hide roofs in the editor."),
    "test_preview": ("Die Karte als Vorschau anzeigen.", "Preview the map."),
    "preview_stop": ("Die Kartenvorschau beenden und zur Bearbeitung zurückkehren.",
                     "Stop the map preview and return to editing."),
    "test_player_1": ("Den isolierten Leveltest für einen Spieler starten.", "Start a standalone one-player level test."),
    "test_player_2": ("Den isolierten Leveltest für beide Spieler starten.", "Start a standalone two-player level test."),
    "test_roof_demo": ("Den mitgelieferten FrostAge-Dachbogen öffnen.", "Open the bundled FrostAge roof demo."),
    "test_stop": ("Den Leveltest beenden und zur Bearbeitung zurückkehren.", "Stop the level test and return to editing."),
}

BUTTON_EN = dict(HINTS.values())


@dataclass(frozen=True, slots=True)
class EditorButtonAsset:
    file: str
    source: str
    sha256: str
    width: int
    height: int
    art_bounds: tuple[int, int, int, int]
    path: Path


def _decode_asset(catalog, metadata):
    filename = metadata["file"]
    if not isinstance(filename, str) or not re.fullmatch(r"[a-z0-9_]+\.png", filename):
        raise ValueError("Ungültiger Dateiname.")
    source, sha256 = metadata["source"], metadata["sha256"]
    if not isinstance(source, str) or not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Ungültige Bildquelle oder Prüfsumme.")
    width, height = metadata["width"], metadata["height"]
    art_bounds = tuple(metadata["art_bounds"])
    if (type(width) is not int or type(height) is not int or len(art_bounds) != 4
            or any(type(value) is not int for value in art_bounds)):
        raise ValueError("Ungültige Bildmaße.")
    x, y, art_width, art_height = art_bounds
    if not (0 <= x < x + art_width <= width and 0 <= y < y + art_height <= height):
        raise ValueError("Ungültiger Bildbereich.")
    return EditorButtonAsset(filename, source, sha256, width, height, art_bounds, catalog.parent / filename)


@lru_cache(maxsize=1)
def load_editor_button_catalog() -> dict[str, EditorButtonAsset]:
    """Read the bundled mapping without decoding any PNGs."""
    catalog = find_asset("graphics", "editor_ui", "catalog.json")
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
        if data["version"] != 1 or not isinstance(data["buttons"], dict):
            raise ValueError("Unbekanntes Editor-Button-Format.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        LOGGER.warning("Editor-Button-Katalog konnte nicht geladen werden: %s", error)
        return {}

    assets = {}
    for action_id, metadata in data["buttons"].items():
        try:
            assets[action_id] = _decode_asset(catalog, metadata)
        except (ValueError, KeyError, TypeError) as error:
            LOGGER.warning("Editor-Button %s konnte nicht zugeordnet werden: %s", action_id, error)
    aliases = data.get("aliases", {})
    if not isinstance(aliases, dict):
        LOGGER.warning("Ungültige Wiederverwendung im Editor-Button-Katalog.")
        return assets
    for action_id, target in aliases.items():
        if (action_id not in data["buttons"] and isinstance(target, str)
                and target in data["buttons"] and target in assets):
            assets[action_id] = assets[target]
        else:
            LOGGER.warning("Editor-Button %s kann seine Grafik nicht wiederverwenden.", action_id)
    return assets


@lru_cache(maxsize=64)
def _load_image(asset: EditorButtonAsset) -> pygame.Surface | None:
    try:
        image = pygame.image.load(str(asset.path))
        if image.get_size() != (asset.width, asset.height):
            raise ValueError("Bildmaße weichen vom Katalog ab.")
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        # Omit only the transparent margins described by the packaged catalogue.
        return image.subsurface(asset.art_bounds)
    except (OSError, pygame.error, ValueError) as error:
        LOGGER.warning("Editor-Button %s konnte nicht geladen werden: %s", asset.file, error)
        return None


@lru_cache(maxsize=256)
def _scaled_image(asset: EditorButtonAsset, width: int, height: int, enabled: bool) -> pygame.Surface | None:
    if not enabled:
        image = _scaled_image(asset, width, height, True)
        if image is None:
            return None
        dimmed = image.copy()
        dimmed.set_alpha(145)
        return dimmed

    original = _load_image(asset)
    if original is None:
        return None
    source_width, source_height = original.get_size()
    scale = min(width / source_width, height / source_height)
    size = max(1, round(source_width * scale)), max(1, round(source_height * scale))
    return pygame.transform.smoothscale(original, size)


class EditorButtons:
    """Keep artwork and readable text controls interchangeable at the same hit target."""

    def __init__(self, font: pygame.font.Font):
        self.font = font

    def preferred_size(self, action_id: str, label: str) -> tuple[int, int]:
        asset = load_editor_button_catalog().get(action_id)
        fallback_width = max(62, self.font.size(label)[0] + 18)
        if asset is None:
            return fallback_width, BUTTON_HEIGHT
        art_width, art_height = asset.art_bounds[2:]
        content_width = round(art_width * (BUTTON_HEIGHT - 2 * PAD) / art_height)
        return max(fallback_width, min(MAX_ART_WIDTH, content_width + 2 * PAD)), BUTTON_HEIGHT

    def hint(self, action_id: str, label: str) -> str:
        translations = HINTS.get(action_id)
        return translations[0] if translations else label

    def draw(self, screen, action_id: str, label: str, rect, *,
             active=False, selected=False, hovered=False, enabled=True):
        if rect.width <= 2 * PAD or rect.height <= 2 * PAD:
            return
        asset = load_editor_button_catalog().get(action_id)
        image = (_scaled_image(asset, rect.width - 2 * PAD, rect.height - 2 * PAD, enabled)
                 if asset is not None else None)
        signal = SELECTED if selected else ACTIVE if active else HOVER if hovered else None
        if image is not None:
            screen.blit(image, image.get_rect(center=rect.center))
        else:
            pygame.draw.rect(screen, BUTTON, rect, border_radius=5)
            pygame.draw.rect(screen, STROKE, rect, width=1, border_radius=5)
            self._draw_label(screen, label, rect, enabled)

        if enabled and signal is not None:
            pygame.draw.rect(screen, signal, rect, width=2, border_radius=6)
            if hovered and (active or selected):
                pygame.draw.rect(screen, HOVER, rect.inflate(-4, -4), width=1, border_radius=4)

    def _draw_label(self, screen, label, rect, enabled):
        available = rect.width - 12
        if available <= 0:
            return
        if self.font.size(label)[0] > available:
            label = label.rstrip()
            while label and self.font.size(label + "…")[0] > available:
                label = label[:-1]
            label = label + "…" if label else ""
        text = self.font.render(label, True, TEXT if enabled else MUTED)
        text_rect = text.get_rect(center=rect.center)
        old_clip = screen.get_clip()
        screen.set_clip(old_clip.clip(rect))
        screen.blit(text, text_rect)
        screen.set_clip(old_clip)
