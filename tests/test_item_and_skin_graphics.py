import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enums import ItemType
from modules.game import Game, Item
from modules.graphics import ITEM_IMAGES
from modules.resources import find_asset


@pytest.mark.parametrize("item_type", list(ItemType.__members__.values()),
                         ids=list(ItemType.__members__))
def test_each_item_draws_its_visible_icon(item_type):
    icon = ITEM_IMAGES[item_type.name]
    assert icon.get_bounding_rect(min_alpha=128).width > 0
    item = Item(item_type)
    item.x = item.y = 0
    surface = pygame.Surface(item.get_render_rect().size, pygame.SRCALPHA)
    item.draw(surface)
    assert pygame.image.tobytes(surface, "RGBA") == pygame.image.tobytes(icon, "RGBA")


def test_speed_boost_uses_orange_icon_and_applies_effect():
    game = Game(headless=True)
    game.start_game(1)
    item = Item(ItemType.SPEED_BOOST)
    icon = ITEM_IMAGES[item.type.name]
    expected = pygame.image.load(str(find_asset("graphics", "ItemOrangeradG20.png")))
    assert pygame.image.tobytes(icon, "RGBA") == pygame.image.tobytes(expected, "RGBA")
    speed = game.speed
    game.handle_item_pickup(item)
    assert game.speed > speed
    assert game.effects["speed_boost"] > 0


def test_loot_box_can_award_speed_boost_without_recursive_loot(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)

    def choose_reward(rewards):
        assert ItemType.LOOT_BOX not in rewards
        assert ItemType.SPAWN_BOLBU not in rewards
        assert ItemType.SPEED_BOOST in rewards
        return ItemType.SPEED_BOOST

    monkeypatch.setattr("modules.game.random.choice", choose_reward)
    game.handle_item_pickup(Item(ItemType.LOOT_BOX))
    assert game.effects["speed_boost"] > 0
    assert game.score == 35


def test_options_keep_head_and_body_images_separate():
    game = Game(headless=True)
    menu = game.options_menu
    head = menu.get_skin_image("Heads", "SnakeHead1G60.png")
    body = menu.get_skin_image("Bodies", "items3.png")
    assert head is not None and body is not None
    assert pygame.image.tobytes(head, "RGBA") != pygame.image.tobytes(body, "RGBA")
    assert menu.get_skin_image("Heads", "items3.png") is None
    assert menu.get_skin_image("Bodies", "SnakeHead1G60.png") is None
