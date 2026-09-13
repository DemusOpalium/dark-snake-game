#!/usr/bin/env python
"""Beschleunigter, headless Entwickler-Simulator für Dark Snake."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import time
import traceback
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from unittest.mock import patch


class SimulationControl:
    """Thread-safe cooperative pause/cancel and live progress state."""
    def __init__(self):
        self._resume = threading.Event()
        self._resume.set()
        self._cancel = threading.Event()
        self.completed = 0
        self.errors = 0
        self.last_error = None

    @property
    def paused(self): return not self._resume.is_set()
    @property
    def cancelled(self): return self._cancel.is_set()
    def toggle_pause(self): self._resume.clear() if self._resume.is_set() else self._resume.set()
    def cancel(self): self._cancel.set(); self._resume.set()
    def checkpoint(self): self._resume.wait(); return not self.cancelled


@dataclass
class SimulatedClock:
    """Eine explizite Spieluhr, die niemals auf Echtzeit warten muss."""

    current: float = 1_000_000.0

    def time(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


@dataclass
class RunResult:
    seed: int
    scenario: str
    game_time: float
    game_state: str
    level: int
    score: int
    exception: str | None = None
    code_line: str | None = None
    stacktrace: str | None = None


def _scenario_actions():
    from modules.bolbu_enemy import BolbuEnemy
    from modules.enums import GameState, ItemType
    from modules.game import Item

    def one_player(game):
        game.start_game(1)

    def two_player(game):
        game.start_game(2)

    def portal(game):
        game.start_game(1)
        game.activate_portal("color_change")

    def boss(game):
        game.start_game(1)
        game.start_boss_fight()

    def aoe(game):
        game.start_game(1)
        game.spawn_independent_aoe_zone()

    def projectiles(game):
        game.start_game(1)
        game.handle_item_pickup(Item(ItemType.PROJECTILE_SHOOT))

    def bolbu(game):
        game.start_game(1)
        enemy = BolbuEnemy()
        enemy.spawn_time = 0
        game.enemies.append(enemy)

    def restart(game):
        game.start_game(1)
        game.score = 123
        game.reset_game()
        game.start_game(1)

    def game_over(game):
        game.start_game(1)
        game.lives = 1
        game.player_health = 0
        game.handle_death()

    return {
        "portal": portal,
        "boss": boss,
        "aoe": aoe,
        "projectiles": projectiles,
        "bolbu": bolbu,
        "1p": one_player,
        "2p": two_player,
        "restart": restart,
        "game_over": game_over,
    }


def _state_name(game) -> str:
    state = getattr(game, "game_state", "unknown")
    return getattr(state, "name", str(state))


def _failure_location(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return "unknown"
    frame = frames[-1]
    return f"{Path(frame.filename).name}:{frame.lineno}"


def run_simulation(rounds: int = 3, steps: int = 120, step_seconds: float = 1.0,
                   base_seed: int | None = None, scenarios=None,
                   control: SimulationControl | None = None) -> dict:
    """Führt alle Szenarien mit echter Spiellogik und einer virtuellen Uhr aus."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import pygame
        from modules.game import Game

        pygame.init()
        pygame.display.set_mode((1, 1))
    available = _scenario_actions()
    scenarios = available if scenarios is None else {name: available[name] for name in scenarios}
    control = control or SimulationControl()
    first_seed = random.SystemRandom().randrange(2**32) if base_seed is None else base_seed
    results = []

    for round_number in range(rounds):
        for scenario_number, (name, setup) in enumerate(scenarios.items()):
            if not control.checkpoint():
                break
            seed = (first_seed + round_number * len(scenarios) + scenario_number) % (2**32)
            random.seed(seed)
            clock = SimulatedClock()
            game = None
            started_at = clock.time()
            try:
                # Alle Gameplay-Module verwenden dasselbe `time`-Modul. Der Patch ist
                # auf einen Lauf begrenzt und wird anschließend sicher zurückgenommen.
                with patch("time.time", clock.time), contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    game = Game()
                    setup(game)
                    for _ in range(steps):
                        if not control.checkpoint():
                            break
                        clock.advance(step_seconds)
                        if _state_name(game) in ("GAME", "BOSS_FIGHT"):
                            game.update()
                results.append(RunResult(seed, name, clock.time() - started_at,
                                         _state_name(game), game.level, game.score))
            except Exception as exc:  # Der Simulator muss weitere Seeds noch prüfen.
                results.append(RunResult(
                    seed=seed,
                    scenario=name,
                    game_time=clock.time() - started_at,
                    game_state=_state_name(game) if game else "not_initialized",
                    level=getattr(game, "level", 0),
                    score=getattr(game, "score", 0),
                    exception=type(exc).__name__,
                    code_line=_failure_location(exc),
                    stacktrace="".join(traceback.format_exception(exc)),
                ))
                control.errors += 1
                control.last_error = f"{name}, Seed {seed}: {type(exc).__name__}: {exc}"
            control.completed += 1
        if control.cancelled:
            break

    serialized = [asdict(result) for result in results]
    failures = [result for result in serialized if result["exception"]]
    groups = {}
    for failure in failures:
        key = f'{failure["exception"]}@{failure["code_line"]}'
        groups.setdefault(key, []).append(failure)
    return {
        "configuration": {"rounds": rounds, "steps": steps,
                          "step_seconds": step_seconds, "base_seed": first_seed},
        "seeds": [result["seed"] for result in serialized],
        "runs": serialized,
        "failure_groups": groups,
    }


def format_text_report(report: dict) -> str:
    lines = [
        "Dark Snake – Headless-Simulationsbericht",
        f"Läufe: {len(report['runs'])}",
        f"Fehler: {sum(len(group) for group in report['failure_groups'].values())}",
        f"Basis-Seed: {report['configuration']['base_seed']}",
    ]
    for key, failures in report["failure_groups"].items():
        lines.append(f"\n{key} ({len(failures)} Vorkommen)")
        for failure in failures:
            lines.append(
                "  Seed={seed} Szenario={scenario} Spielzeit={game_time:.3f} "
                "GameState={game_state} Level={level} Score={score}".format(**failure)
            )
            lines.append(failure["stacktrace"].rstrip())
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--step-seconds", type=float, default=1.0)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--json", type=Path, default=Path("simulation-report.json"))
    parser.add_argument("--text", type=Path, default=Path("simulation-report.txt"))
    args = parser.parse_args(argv)
    report = run_simulation(args.rounds, args.steps, args.step_seconds, args.seed)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.text.write_text(format_text_report(report), encoding="utf-8")
    return 1 if report["failure_groups"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
