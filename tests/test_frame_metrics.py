import os
from pathlib import Path
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enums import Direction
from modules.frame_metrics import FrameMetrics, summarize_ns
from modules.game import Game


def test_direction_separates_acceptance_grid_wait_and_first_changed_frame(monkeypatch):
    clock = iter((1_100_000, 10_000_000))
    monkeypatch.setattr("modules.frame_metrics.time.perf_counter_ns", lambda: next(clock))
    metrics = FrameMetrics()
    assert metrics.stamp() is None
    assert metrics.toggle()

    metrics.head_drawn(1, (10, 10), 1)
    metrics.accept_direction(1, Direction.UP, 1_000_000)
    metrics.apply_direction(1, Direction.UP)
    metrics.head_drawn(2, (10, 9), 0)
    metrics.head_drawn(1, (10, 10), 1)
    metrics.finish_frame(11_000_000)
    assert list(metrics.samples["direction", "visible"]) == []
    metrics.head_drawn(1, (10, 9), 0)
    metrics.finish_frame(15_000_000)
    metrics.finish_frame(20_000_000)
    assert list(metrics.samples["direction", "accept"]) == [100_000]
    assert list(metrics.samples["direction", "wait"]) == [8_900_000]
    assert list(metrics.samples["direction", "visible"]) == [14_000_000]
    assert list(metrics.samples["direction", "present"]) == [5_000_000]


def test_fire_cooldown_and_removed_projectile_do_not_create_latency_samples(monkeypatch):
    clock = iter((4, 7))
    monkeypatch.setattr("modules.frame_metrics.time.perf_counter_ns", lambda: next(clock))
    metrics = FrameMetrics()
    metrics.toggle()
    shot = object()
    metrics.reject("fire", "cooldown")
    metrics.apply_fire(shot, 1, 2)
    metrics.apply_fire(object(), 5, 6)
    metrics.fire_drawn(shot)
    metrics.finish_frame(8)
    assert list(metrics.samples["fire", "accept"]) == [1, 1]
    assert list(metrics.samples["fire", "visible"]) == [7]
    assert metrics.rejected["fire", "cooldown"] == 1
    assert metrics.rejected["fire", "vor Bild entfernt"] == 1


def test_buffer_is_bounded_and_slow_counter_is_separate():
    metrics = FrameMetrics(capacity=3)
    metrics.toggle()
    for timestamp in (1, 17, 51, 68, 86, 126):
        metrics.finish_frame(timestamp * 1_000_000)
    assert summarize_ns(metrics.samples["interval"]) == (3, 18, 40, 40)
    assert metrics.slow_frames == 2
    metrics.toggle()
    assert not metrics.enabled and not metrics.samples


def test_admin_overlay_stays_enabled_when_admin_menu_closes(monkeypatch):
    game = Game()
    game.start_game(1)
    game.admin_panel.toggle()
    draws = []
    monkeypatch.setattr(game.metrics, "draw", draws.append)
    game.draw()
    assert not draws
    game.admin_panel.toggle_metrics()
    game.draw()
    assert not draws
    game.admin_panel.close()
    game.run_frame()
    assert draws == [game.screen]
    assert game.metrics.samples["events"]
    assert game.metrics.samples["update"]
    assert game.metrics.samples["draw"]
    assert game.metrics.samples["present"]


def test_real_events_measure_turn_at_grid_step_and_separate_fire_cooldown(monkeypatch):
    monkeypatch.setattr("modules.game.random.random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(1)
    game.metrics.toggle()
    game.draw()
    pygame.event.clear()
    for key in (pygame.K_a, pygame.K_w, pygame.K_SPACE, pygame.K_SPACE):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))

    game.last_update_time = time.time() + 10
    game.run_frame()
    metrics = game.metrics
    assert metrics.rejected["direction", "Gegenrichtung"] == 1
    assert metrics.rejected["fire", "cooldown"] == 1
    assert len(metrics.samples["direction", "accept"]) == 1
    assert not metrics.samples["direction", "wait"]
    assert not metrics.samples["direction", "visible"]
    assert len(metrics.samples["fire", "accept"]) == 1
    assert len(metrics.samples["fire", "visible"]) == 1

    game.last_update_time = 0
    game.run_frame()
    assert game.snake_direction == Direction.UP
    assert len(metrics.samples["direction", "wait"]) == 1
    assert len(metrics.samples["direction", "visible"]) == 1
