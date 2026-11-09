"""Measure identical seeded game-loop workloads in two source checkouts."""

import argparse
from collections import defaultdict
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from math import ceil
import os
from pathlib import Path
import platform
import random
from statistics import median
import sys
from tempfile import TemporaryDirectory
import time
from unittest.mock import patch


def summary(samples):
    ordered = sorted(samples)
    if not ordered:
        return {"n": 0}
    n = len(ordered)
    return {
        "n": n,
        "median_ms": round(median(ordered) / 1e6, 4),
        "p95_ms": round(ordered[ceil(n * 0.95) - 1] / 1e6, 4),
        "max_ms": round(ordered[-1] / 1e6, 4),
    }


def measure(args, scenario, pygame, game_module, clock_class):
    samples = defaultdict(list)
    event_read = present_end = None
    presentation = 0
    measuring = False
    read_events = pygame.event.get
    display_update = pygame.display.update
    logic_clock = clock_class()

    def timed_events(*values, **options):
        nonlocal event_read
        events = read_events(*values, **options)
        event_read = time.perf_counter_ns()
        return events

    def timed_present(*values, **options):
        nonlocal presentation, present_end
        before = time.perf_counter_ns()
        display_update(*values, **options)
        after = time.perf_counter_ns()
        presentation += after - before
        if measuring and present_end is not None:
            samples["interval"].append(after - present_end)
        present_end = after

    class MeasuredGame(game_module.Game):
        def __setattr__(self, name, value):
            if (measuring and event_read is not None
                    and name in ("next_direction", "next_direction1", "next_direction2")
                    and getattr(self, name, None) != value):
                samples["direction_accept"].append(time.perf_counter_ns() - event_read)
            super().__setattr__(name, value)

        def handle_events(self):
            nonlocal event_read
            event_read = None
            start = time.perf_counter_ns()
            super().handle_events()
            if measuring:
                samples["events"].append(time.perf_counter_ns() - start)
            event_read = None

        def update(self):
            start = time.perf_counter_ns()
            super().update()
            if measuring:
                samples["update"].append(time.perf_counter_ns() - start)

        def draw(self):
            nonlocal presentation
            presentation = 0
            start = time.perf_counter_ns()
            super().draw()
            if measuring:
                samples["draw"].append(time.perf_counter_ns() - start - presentation)
                samples["present"].append(presentation)

        def run_frame(self):
            if hasattr(game_module.Game, "run_frame"):
                super().run_frame()
                return
            # Equivalent order on the baseline, where Game.run is an endless loop.
            self.handle_events()
            if (self.game_state in (game_module.GameState.GAME, game_module.GameState.BOSS_FIGHT)
                    and not self.admin_panel.active and not self.level_editor.active):
                self.update()
            self.draw()

    class MeasuredFlame(game_module.FlameProjectile):
        def __init__(self, *values, **options):
            # The baseline has no acceptance hook. Entry into construction
            # is the first common observable operation after the cooldown gate.
            if measuring and event_read is not None:
                samples["fire_accept"].append(time.perf_counter_ns() - event_read)
            super().__init__(*values, **options)

    players = 1 if scenario == "1p" else 2
    turns = ((pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_d),
             (pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_RIGHT))
    fire = (pygame.K_SPACE, pygame.K_RETURN)
    random.seed(args.seed)
    with (patch("time.time", logic_clock.time), patch("time.monotonic", logic_clock.monotonic),
          patch.object(pygame.event, "get", timed_events),
          patch.object(pygame.display, "update", timed_present),
          patch.object(game_module, "FlameProjectile", MeasuredFlame)):
        game = MeasuredGame()
        game.start_game(players)
        game.respawn_invincible_until = float("inf")
        if args.overlay:
            game.metrics.toggle()
            draw_overlay = game.metrics.draw

            def timed_overlay(screen):
                before = time.perf_counter_ns()
                draw_overlay(screen)
                if measuring:
                    samples["overlay_draw"].append(time.perf_counter_ns() - before)

            game.metrics.draw = timed_overlay
        if scenario == "load":
            game.start_boss_fight()
            for index in range(12):
                game.effect_manager.spawn(("fog", "portal", "boss_aura")[index % 3],
                                          (80 + 70 * index, 170 + 30 * index),
                                          {"loop": True, "lifetime": 120})
        pygame.event.clear()
        clock = pygame.time.Clock()
        for frame in range(args.frames + args.warmup):
            if frame == args.warmup:
                measuring = True
                present_end = None
                if args.overlay:
                    game.metrics.samples.clear()
                    game.metrics.rejected.clear()
            if scenario == "load":
                game.projectiles[:] = [
                    {"pos": (3 + index, 3 + index % 12), "dir": (0.2, 0),
                     "from_boss": True, "scale": 2}
                    for index in range(24)
                ]
            for player in range(players):
                keys = []
                if frame % 12 == player * 3:
                    keys.append(turns[player][frame // 12 % 4])
                if frame % 21 == player * 5:
                    keys.append(fire[player])
                for key in keys:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
            logic_clock.advance()
            start = time.perf_counter_ns()
            game.run_frame()
            if measuring:
                samples["work"].append(time.perf_counter_ns() - start)
            if not args.uncapped:
                clock.tick(60)

    if args.overlay:
        for kind, phases in (("direction", ("accept", "wait", "present", "visible")),
                             ("fire", ("accept", "apply", "present", "visible"))):
            for phase in phases:
                samples[f"overlay_{kind}_{phase}"].extend(game.metrics.samples[kind, phase])
    result = {name: summary(values) for name, values in samples.items()}
    result["intervals_over_33_3_ms"] = sum(value > 33_300_000 for value in samples["interval"])
    if args.overlay:
        result["overlay_rejected"] = {f"{kind}: {reason}": count
                                      for (kind, reason), count in game.metrics.rejected.items()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--frames", type=int, default=360)
    parser.add_argument("--warmup", type=int, default=60)
    parser.add_argument("--seed", type=int, default=16000)
    parser.add_argument("--driver", default="dummy")
    parser.add_argument("--overlay", action="store_true")
    parser.add_argument("--uncapped", action="store_true")
    args = parser.parse_args()
    if args.frames < 2 or args.warmup < 0:
        parser.error("--frames must be at least 2 and --warmup nonnegative")
    os.environ["SDL_VIDEODRIVER"] = args.driver
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    sys.path.insert(0, str(args.checkout.resolve() / "Dark_Snake"))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        import pygame
        pygame.init()
        pygame.display.set_mode((1, 1))
        from modules import game as game_module, resources
        from developer_simulator import SimulatedClock

        if args.overlay and not hasattr(game_module, "FrameMetrics"):
            parser.error("--overlay needs a checkout with the timing overlay")
        with TemporaryDirectory(prefix="dark-snake-profile-") as profile:
            results = {}
            with patch.object(resources, "DATA_DIR", Path(profile)):
                for scenario in ("1p", "2p", "load"):
                    results[scenario] = measure(args, scenario, pygame, game_module, SimulatedClock)
        pygame.quit()
    print(json.dumps({"driver": args.driver, "platform": platform.platform(),
                      "pygame": pygame.version.ver, "seed": args.seed, "frames": args.frames,
                      "warmup": args.warmup, "overlay": args.overlay, "capped": not args.uncapped,
                      "scenarios": results}, indent=2))


if __name__ == "__main__":
    main()
