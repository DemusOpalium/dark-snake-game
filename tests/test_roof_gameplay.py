"""Play the bundled roof demo and verify the foreground in both render paths."""

from dataclasses import replace
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((1, 1))

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules import resources, roof_render
from modules.enums import Direction, GameState
from modules.game import Game
from modules.graphic_objects import GraphicObject
from modules.level_editor import CELL_SIZE, MAP_RECT
from modules.level_playtest import PLAYER_COLORS
from modules.roof_settings import RoofVisibility


def click_editor_button(game, label):
    rect, = [rect for name, rect, _ in game.level_editor.buttons if name == label]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    game.handle_events()


def editor_pixel(x, y):
    return MAP_RECT.x + x * CELL_SIZE + CELL_SIZE // 2, MAP_RECT.y + y * CELL_SIZE + CELL_SIZE // 2


@pytest.mark.parametrize("players", [1, 2])
def test_bundled_demo_drives_snakes_through_opaque_arch_with_windows(tmp_path, monkeypatch, players):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game()
    pygame.event.clear()
    editor = game.level_editor
    editor.toggle()
    click_editor_button(game, "Dach-Demo")
    assert not editor.dirty and not list((tmp_path / "levels").glob("*.json"))
    assert editor.roofs == {(20, 11): GraphicObject("frostage_roof_005", 5, 3)}

    click_editor_button(game, f"Test {players}P")
    session = editor.playtest
    assert session.player_count == players
    assert tuple(player.cell for player in session.players) == ((22, 15), (22, 17))[:players]
    step = session.players[0].next_step
    session.update(step)
    assert all(player.blocked == "WALL" for player in session.players)
    assert tuple(player.cell for player in session.players) == ((22, 15), (22, 17))[:players]

    if players == 2:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
        game.handle_events()
        session.update(session.players[0].next_step)
        assert session.players[0].blocked == "WALL"
        assert session.players[1].cell == (22, 16)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
    game.handle_events()
    assert all(player.direction == Direction.UP for player in session.players)

    # Both players pass under opaque spans, and can travel out the other side.
    observed_under_roof = set()
    observed_together = False
    for _ in range(7):
        session.update(session.players[0].next_step)
        game.draw()
        with_windows = game.screen.copy()
        session._roof_visibility = replace(editor.roof_visibility, enabled=False)
        game.draw()
        without_windows = game.screen.copy()
        session._roof_visibility = editor.roof_visibility
        observed_together |= all(player.cell[1] in (11, 12) for player in session.players)
        for index, player in enumerate(session.players):
            x, y = player.cell
            assert x == 22 and player.blocked is None and player.health == 100
            if y not in (11, 12):
                continue
            px, py = editor_pixel(x, y)
            pos = px + 3, py + 3
            shown, hidden = with_windows.get_at(pos), without_windows.get_at(pos)
            assert shown != hidden
            assert shown[:3] != PLAYER_COLORS[index]
            assert sum(abs(shown[c] - PLAYER_COLORS[index][c]) for c in range(3)) < sum(
                abs(hidden[c] - PLAYER_COLORS[index][c]) for c in range(3)
            )
            observed_under_roof.add(index)
        # Behind neither window the same roof art stays over the map.
        edge = editor_pixel(24, 13)
        assert with_windows.get_at(edge) == without_windows.get_at(edge)

    assert observed_under_roof == set(range(players))
    assert observed_together
    assert all(player.cell[1] < 11 for player in session.players)
    assert game.game_state is GameState.INTRO


def test_classic_foreground_covers_world_objects_and_preserves_hud(monkeypatch):
    game = Game(headless=True)
    game.choose_classic_background(
        "Foreground",
        [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)],
        roof_objects={(0, 0): GraphicObject("frostage_roof_005", 16, 8)},
        roof_visibility=RoofVisibility(enabled=False),
    )
    game.start_game(2)
    game.snake1, game.snake2 = [(3, 5)], [(5, 5)]
    game._reset_snake_interpolation()
    game.items.clear()
    roof_rect = pygame.Rect(0, 0, 16 * GRID_SIZE, 8 * GRID_SIZE)
    roof_color = (73, 33, 142, 255)
    art = pygame.Surface(roof_rect.size, pygame.SRCALPHA)
    art.fill(roof_color)
    monkeypatch.setattr(roof_render, "graphic_object_art", lambda *args: (art, roof_rect))

    class WorldMarker:
        def __init__(self, cell):
            self.pos = tuple(value * GRID_SIZE for value in cell)

        def draw(self, surface):
            surface.fill((239, 35, 103), (*self.pos, GRID_SIZE, GRID_SIZE))

        def draw_aoe(self, _surface):
            pass

    game.enemies = [WorldMarker((7, 5))]
    game.boss = WorldMarker((9, 5))
    game.enemy_projectiles = [WorldMarker((11, 5))]
    shot = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
    shot.fill((210, 220, 70))
    monkeypatch.setattr("modules.game.PROJECTILE_IMG", shot)
    game.projectiles = [{"pos": pygame.Vector2(13, 5)}]
    samples = [(x * GRID_SIZE + GRID_SIZE // 2, 5 * GRID_SIZE + GRID_SIZE // 2)
               for x in (3, 5, 7, 9, 11, 13)]
    saved_roofs = game._roof_objects
    game._roof_objects = {}
    game.draw()
    assert [game.screen.get_at(pos)[:3] for pos in samples[2:]] == [
        (239, 35, 103), (239, 35, 103), (239, 35, 103), (210, 220, 70),
    ]
    game._roof_objects = saved_roofs
    game.draw()
    assert all(game.screen.get_at(pos) == roof_color for pos in samples)
    hud_pixel = game.screen.get_at((40, 90))
    assert hud_pixel != roof_color and hud_pixel.g > hud_pixel.r

    game._roof_visibility = RoofVisibility(radius=1.0, transparency=100, softness=0.5)
    game.draw_game()
    assert all(game.screen.get_at(pos) != roof_color for pos in samples[:2])
    assert all(game.screen.get_at(pos) == roof_color for pos in samples[2:])
    assert game.screen.get_at((40, 90)) == hud_pixel

    game.choose_classic_background(None, None)
    assert game._roof_objects
    game.start_game(1)
    assert not game._roof_objects
