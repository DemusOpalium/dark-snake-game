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

from modules.effect_manager import DEFAULTS, EffectManager


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


def test_stop_removes_only_the_selected_effect_instance():
    manager = EffectManager()
    first = manager.spawn("boss_aura", (10, 10), {"loop": True})
    second = manager.spawn("boss_aura", (10, 10), {"loop": True})
    assert first == second

    manager.stop(second)
    manager.stop(second)

    remaining, = manager.active_effects()
    assert remaining is first


def test_shared_animation_frame_keeps_each_effect_opacity():
    manager = EffectManager()
    frame = pygame.Surface((2, 2), pygame.SRCALPHA)
    frame.fill((255, 0, 0, 255))
    manager._cache["explosion"] = (dict(DEFAULTS), [frame])
    surface = pygame.Surface((24, 12))
    manager.spawn("explosion", (6, 6), {"opacity": 64, "scale": 2})
    manager.spawn("explosion", (18, 6), {"opacity": 255, "scale": 2})

    for _ in range(2):
        surface.fill((0, 0, 0))
        manager.draw(surface, "world")
        assert 0 < surface.get_at((6, 6)).r < 128
        assert surface.get_at((18, 6)).r == 255
        assert frame.get_alpha() == 255
