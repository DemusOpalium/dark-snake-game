import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.effect_manager import EffectManager


def test_effects_draw_without_assets_and_expire():
    manager = EffectManager()
    surface = pygame.Surface((100, 100), pygame.SRCALPHA)
    manager.spawn("hit", (50, 50), {"lifetime": 0.1})
    manager.draw(surface, "world")
    assert pygame.mask.from_surface(surface).count()
    assert len(manager.active_effects()) == 1
    manager.update(0.2)
    assert not manager.active_effects()


def test_clear_removes_looping_effects():
    manager = EffectManager()
    manager.spawn("rain", (10, 10), {"loop": True})
    manager.update(100)
    assert manager.active_effects()
    manager.clear()
    assert not manager.active_effects()
