"""Exercise the World Studio button catalogue and shared Pygame renderer."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from modules import editor_buttons


@pytest.fixture
def renderer():
    pygame.font.init()
    return editor_buttons.EditorButtons(pygame.font.Font(None, 24))


@pytest.fixture
def sample_catalogue(tmp_path, monkeypatch):
    image = pygame.Surface((60, 20), pygame.SRCALPHA)
    image.fill((234, 36, 92, 255), (10, 5, 40, 10))
    image.set_at((29, 9), (234, 36, 92, 96))
    asset_path = tmp_path / "file_save.png"
    pygame.image.save(image, str(asset_path))
    digest = sha256(asset_path.read_bytes()).hexdigest()
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({
        "version": 1,
        "buttons": {
            "file_save": {
                "file": asset_path.name, "source": "GamePICs/File/Save.png",
                "width": 60, "height": 20, "art_bounds": [10, 5, 40, 10], "sha256": digest,
            },
            "invalid": {
                "file": "../outside.png", "source": "", "sha256": digest,
                "width": 60, "height": 20, "art_bounds": [10, 5, 40, 10],
            },
        },
        "aliases": {
            "sidebar_save": "file_save",
            "alias_of_alias": "sidebar_save",
            "dangling_alias": "missing",
            "file_save": "invalid",
            "wrong_type": ["file_save"],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(editor_buttons, "find_asset", lambda *parts: path)
    editor_buttons.load_editor_button_catalog.cache_clear()
    yield asset_path
    editor_buttons.load_editor_button_catalog.cache_clear()


def test_catalogue_artwork_is_exactly_packaged_under_runtime_asset_root():
    catalogue = editor_buttons.load_editor_button_catalog()
    assert "file_save" in catalogue and "border_left" in catalogue
    assert len(catalogue) == 62
    project_root = Path(__file__).resolve().parents[1]
    physical_assets = set(catalogue.values())
    assert len(physical_assets) == 58
    for asset in physical_assets:
        assert asset.path.parent.name == "editor_ui"
        assert asset.path.read_bytes() == (project_root / asset.source).read_bytes()
        assert sha256(asset.path.read_bytes()).hexdigest() == asset.sha256
        original = pygame.image.load(str(asset.path))
        assert original.get_size() == (asset.width, asset.height)
        assert original.get_bounding_rect() == pygame.Rect(asset.art_bounds)


def test_layer_explorer_uses_its_seven_sources_and_reuses_tab_artwork(renderer):
    catalogue = editor_buttons.load_editor_button_catalog()
    additions = {
        "nav_help": "Help.png",
        "build_border": "Border_Builder.png",
        "build_transfer_roof": "Move_to_Roof.png",
        "tool_graphics": "Graphics_Only.png",
        "tool_combined": "Graphics_Collision.png",
        "sidebar_properties": "Properties.png",
        "preview_stop": "Stop.png",
    }
    button = pygame.Rect(0, 0, 180, 44)
    for action, filename in additions.items():
        assert catalogue[action].source == f"GamePICs/Nachtrag Fehlende Buttons/{filename}"
        screen = pygame.Surface(button.size, pygame.SRCALPHA)
        renderer.draw(screen, action, "Ersatztext", button)
        assert screen.get_bounding_rect() == screen.get_bounding_rect().clip(button.inflate(-4, -4))
        assert screen.get_bounding_rect().width > 150
    assert catalogue["sidebar_layers"] is catalogue["nav_layers"]
    assert catalogue["sidebar_cell"] is catalogue["view_cell"]
    assert catalogue["sidebar_help"] is catalogue["nav_help"]
    assert catalogue["sidebar_learn"] is catalogue["nav_learn"]


def test_bilingual_language_button_renders_the_staged_artwork(renderer):
    asset = editor_buttons.load_editor_button_catalog()["nav_language"]
    assert asset.source == "GamePICs/General/De-En_Language-removebg-preview.png"
    button = pygame.Rect(0, 0, 140, 44)
    surface = pygame.Surface(button.size, pygame.SRCALPHA)
    renderer.draw(surface, "nav_language", "Deutsch / English", button)
    visible = surface.get_bounding_rect()
    assert visible.width == button.width - 4
    assert visible.center == button.center


@pytest.mark.parametrize(("action_id", "source"), [
    ("learn_start", "My_FIrst_LvL-removebg-preview.png"),
    ("learn_example", "Examples-removebg-preview.png"),
])
def test_learning_buttons_render_the_staged_artwork(renderer, action_id, source):
    asset = editor_buttons.load_editor_button_catalog()[action_id]
    assert asset.source == f"GamePICs/Learn/{source}"
    button = pygame.Rect(0, 0, 172, 36)
    surface = pygame.Surface(button.size, pygame.SRCALPHA)
    renderer.draw(surface, action_id, "Ersatztext", button)
    visible = surface.get_bounding_rect()
    assert visible.width == button.width - 4
    assert visible.center == button.center


def test_renderer_fits_alpha_art_and_draws_no_additional_label(renderer, sample_catalogue, monkeypatch):
    screen = pygame.Surface((90, 66), pygame.SRCALPHA)
    button = pygame.Rect(20, 14, 44, 36)
    expected_art = pygame.Rect(0, 0, 40, 10)
    expected_art.center = button.center
    catalogue = editor_buttons.load_editor_button_catalog()
    assert set(catalogue) == {"file_save", "sidebar_save"}
    assert catalogue["sidebar_save"] is catalogue["file_save"]

    class TextMustNotRender:
        def render(self, *args):
            pytest.fail("Packaged art already contains its English label.")

    renderer.font = TextMustNotRender()
    renderer.draw(screen, "file_save", "Speichern", button)
    assert screen.get_bounding_rect() == expected_art
    assert screen.get_at((expected_art.x + 19, expected_art.y + 4)).a == 96
    assert screen.get_at(button.topleft).a == 0

    def unexpected_image_read(path):
        pytest.fail(f"Cached art was read again: {path}")

    monkeypatch.setattr(pygame.image, "load", unexpected_image_read)
    screen.fill((0, 0, 0, 0))
    renderer.draw(screen, "file_save", "Save", button, enabled=False)
    assert screen.get_bounding_rect() == expected_art
    assert screen.get_at(expected_art.topleft).a < 255
    renderer.draw(screen, "sidebar_save", "Speichern", button, hovered=True)
    assert screen.get_at((button.centerx, button.top))[:3] == editor_buttons.HOVER
    renderer.draw(screen, "file_save", "Speichern", button, active=True)
    assert screen.get_at((button.centerx, button.top))[:3] == editor_buttons.ACTIVE
    renderer.draw(screen, "file_save", "Speichern", button, selected=True)
    assert screen.get_at((button.centerx, button.top))[:3] == editor_buttons.SELECTED


@pytest.mark.parametrize("mapped", [False, True])
def test_missing_art_draws_legible_text_fallback(renderer, sample_catalogue, mapped):
    sample_catalogue.unlink()
    screen = pygame.Surface((160, 66), pygame.SRCALPHA)
    button = pygame.Rect(20, 14, 120, 36)
    action_id = "file_save" if mapped else "unmapped"
    assert renderer.preferred_size(action_id, "Speichern")[0] >= renderer.font.size("Speichern")[0] + 18
    renderer.draw(screen, action_id, "Speichern", button, active=True)
    assert screen.get_bounding_rect() == button
    assert screen.get_at((button.centerx, button.top))[:3] == editor_buttons.ACTIVE
    assert any(screen.get_at((x, y))[:3] == editor_buttons.TEXT
               for y in range(button.top + 3, button.bottom - 3)
               for x in range(button.left + 3, button.right - 3))
