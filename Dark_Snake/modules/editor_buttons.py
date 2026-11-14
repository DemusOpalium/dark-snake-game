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
    "nav_file": "Level öffnen, speichern und organisieren.",
    "nav_build": "Bodenflächen und Grafikobjekte bearbeiten.",
    "nav_layers": "Arbeitsebenen und Kollisionswerkzeuge wählen.",
    "nav_effects": "Schaden, Verlangsamung und Dachwerte einstellen.",
    "nav_view": "Kartenausschnitt, Seitenleisten und Markierungen einstellen.",
    "nav_test": "Vorschau und isolierte Leveltests öffnen.",
    "nav_learn": "Die spielbare Dach-Demo und ihre Anleitung öffnen.",
    "file_new": "Einen leeren Levelentwurf anlegen.",
    "file_open": "Einen gespeicherten Levelentwurf öffnen.",
    "file_save": "Den aktuellen Levelentwurf speichern.",
    "file_worlds": "Entwürfe nach Themenwelten organisieren.",
    "file_undo": "Die letzte Kartenänderung rückgängig machen.",
    "file_redo": "Eine rückgängig gemachte Änderung wiederholen.",
    "file_use_classic": "Diesen Entwurf für die nächste Classic-Runde wählen.",
    "file_classic_default": "Die Standardkarte für die nächste Classic-Runde wählen.",
    "build_middle": "Die Bodenfläche innerhalb des Randes füllen.",
    "build_move_objects": "Ein Grafikobjekt und danach sein Ziel anklicken.",
    "build_object_size": "Die Größe des Grafikobjekts in Rasterfeldern einstellen.",
    "build_tile_library": "Die Suche in der Kachelbibliothek links öffnen.",
    "border_all": "Alle vier Seiten für die Randvorschau ein- oder ausschalten.",
    "border_left": "Die linke Randseite für die Vorschau ein- oder ausschalten.",
    "border_right": "Die rechte Randseite für die Vorschau ein- oder ausschalten.",
    "border_top": "Die obere Randseite für die Vorschau ein- oder ausschalten.",
    "border_bottom": "Die untere Randseite für die Vorschau ein- oder ausschalten.",
    "border_corner": "Die Auswahl für die vier Eckgrafiken ein- oder ausblenden.",
    "layer_ground": "Einzelne Bodenkacheln bearbeiten.",
    "layer_objects": "Grafikobjekte bearbeiten.",
    "layer_roof": "Dächer auf der Vordergrundebene bearbeiten.",
    "layer_collision": "WALL- und BARRIER-Kollisionsfelder bearbeiten.",
    "layer_effects": "Effektfelder bearbeiten oder anzeigen.",
    "collision_wall": "WALL-Felder blockieren im isolierten Leveltest.",
    "collision_barrier": "BARRIER-Felder blockieren im isolierten Leveltest.",
    "effect_damage": "Felder mit wiederholtem Schaden platzieren.",
    "effect_slow": "Felder mit verlangsamter Bewegung platzieren.",
    "effect_values": "Schaden, Trefferintervall, Dauer und Verlangsamung einstellen.",
    "roof_settings": "Radius, Stärke und weichen Rand der Dach-Sichtfenster einstellen.",
    "view_fit_map": "Das gesamte Spielfeld anzeigen.",
    "view_library": "Den Baukasten ein- oder ausblenden.",
    "view_panel": "Den Arbeitsbereich rechts ein- oder ausblenden.",
    "view_cell": "Eine Zelle und ihre Ebenen ansehen.",
    "view_collision": "Kollisionsmarkierungen ein- oder ausblenden.",
    "view_effects": "Effektmarkierungen ein- oder ausblenden.",
    "view_roof": "Dächer in der Editoransicht ein- oder ausblenden.",
    "test_preview": "Die Karte als Vorschau anzeigen.",
    "test_player_1": "Den isolierten Leveltest für einen Spieler starten.",
    "test_player_2": "Den isolierten Leveltest für beide Spieler starten.",
    "test_roof_demo": "Den mitgelieferten FrostAge-Dachbogen öffnen.",
    "test_stop": "Den Leveltest beenden und zur Bearbeitung zurückkehren.",
}


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
        return HINTS.get(action_id, label)

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
