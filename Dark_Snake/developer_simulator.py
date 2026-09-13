#!/usr/bin/env python
"""Deterministische Bot- und Batch-Simulation für Dark Snake."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import threading
import time
import traceback
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

TICK_SECONDS = 1.0 / 60.0
SCENARIOS = ("1p", "2p", "boss", "portal", "aoe", "projectiles", "bolbu",
             "restart", "game_over")


class SimulationControl:
    """Thread-sichere Pause-/Abbruchsteuerung mit Fortschrittswerten."""

    def __init__(self, resume_event=None, cancel_event=None):
        self._resume = resume_event or threading.Event()
        self._resume.set()
        self._cancel = cancel_event or threading.Event()
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
    """Gemeinsame virtuelle Uhr; jeder Aufruf von ``advance`` ist ein Tick."""

    current: float = 1_000_000.0

    def time(self) -> float: return self.current
    def monotonic(self) -> float: return self.current
    def advance(self, seconds: float = TICK_SECONDS) -> None: self.current += seconds


@dataclass
class RunResult:
    seed: int
    scenario: str
    round: int
    completion_reason: str
    simulation_ticks: int
    virtual_game_time: float
    game_state_history: list[str]
    level: int
    score: int
    lives: int
    health: object
    snake_position: object
    snake_length: object
    movement_direction: object
    enemy_count: int
    item_count: int
    projectile_count: int
    aoe_zone_count: int
    boss_status: dict
    portal_status: dict
    bot_actions: list[str]
    collisions_and_hits: list[str]
    important_events: list[str]
    completed: bool
    game_time: float = 0.0
    game_state: str = "unknown"
    steps_completed: int = 0
    exception: str | None = None
    code_line: str | None = None
    stacktrace: str | None = None


class SimulationBot:
    """Kleiner lokaler Bot, der reguläre Pygame-Eingabeereignisse erzeugt."""

    _KEYS = {
        (1, "UP"): "p1_up", (1, "DOWN"): "p1_down",
        (1, "LEFT"): "p1_left", (1, "RIGHT"): "p1_right",
        (2, "UP"): "p2_up", (2, "DOWN"): "p2_down",
        (2, "LEFT"): "p2_left", (2, "RIGHT"): "p2_right",
    }

    def __init__(self, seed: int):
        self.random = random.Random(seed)
        self.actions: list[str] = []

    @staticmethod
    def _distance(start, target):
        return abs(start[0] - target[0]) + abs(start[1] - target[1])

    def choose_direction(self, game, player=1):
        from config import GRID_HEIGHT, GRID_WIDTH
        from modules.enums import Direction

        snake = game.snake if game.player_count == 1 else getattr(game, f"snake{player}")
        current = (game.snake_direction if game.player_count == 1 else
                   getattr(game, f"snake_direction{player}"))
        if not snake:
            return current
        targets = [(item.x, item.y) for item in getattr(game, "items", [])]
        target = min(targets, key=lambda pos: self._distance(snake[0], pos)) if targets else None
        occupied = set(snake[1:])
        if game.player_count == 2:
            other = game.snake2 if player == 1 else game.snake1
            occupied.update(other)
        hazards = set()
        for enemy in getattr(game, "enemies", []):
            hazards.add((int(getattr(enemy, "x", -10)), int(getattr(enemy, "y", -10))))
        boss = getattr(game, "boss", None)
        if boss:
            hazards.update((x, y) for x in range(int(boss.x) - 1, int(boss.x + boss.size) + 1)
                           for y in range(int(boss.y) - 1, int(boss.y + boss.size) + 1))
        opposite = {Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
                    Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT}
        candidates = []
        for direction in Direction:
            if direction == opposite[current]:
                continue
            pos = ((snake[0][0] + direction.value[0]) % GRID_WIDTH,
                   (snake[0][1] + direction.value[1]) % GRID_HEIGHT)
            if pos not in occupied and pos not in hazards:
                score = self._distance(pos, target) if target else 0
                candidates.append((score, self.random.random(), direction))
        return min(candidates, default=(0, 0, current))[2]

    def act(self, game, tick: int) -> list[str]:
        """Postet Richtungs-/Feueraktionen und lässt sie vom Spiel verarbeiten."""
        import pygame

        made = []
        players = (1, 2) if game.player_count == 2 else (1,)
        # One action per movement interval is sufficient and keeps reports useful.
        if tick == 0 or tick % 6 == 0:
            for player in players:
                direction = self.choose_direction(game, player)
                action = self._KEYS[(player, direction.name)]
                key = game.input.bindings[action]["key"]
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
                made.append(action)
        if tick % 30 == 0:
            for player in players:
                action = f"p{player}_fire"
                key = game.input.bindings[action]["key"]
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
                made.append(action)
        if made:
            game.handle_events()
            self.actions.extend(made)
        return made


def _scenario_actions():
    from modules.bolbu_enemy import BolbuEnemy
    from modules.enums import ItemType
    from modules.game import Item

    def start(players=1): return lambda game: game.start_game(players)
    def portal(game): game.start_game(1); game.activate_portal("color_change")
    def boss(game): game.start_game(1); game.start_boss_fight()
    def aoe(game): game.start_game(1); game.spawn_independent_aoe_zone()
    def projectiles(game): game.start_game(1); game.handle_item_pickup(Item(ItemType.PROJECTILE_SHOOT))
    def bolbu(game):
        game.start_game(1); enemy = BolbuEnemy(); enemy.spawn_time = 0; game.enemies.append(enemy)
    def restart(game): game.start_game(1); game.score = 123; game.reset_game(); game.start_game(1)
    def game_over(game): game.start_game(1); game.lives = 1; game.player_health = 1
    return {"1p": start(), "2p": start(2), "boss": boss, "portal": portal,
            "aoe": aoe, "projectiles": projectiles, "bolbu": bolbu,
            "restart": restart, "game_over": game_over}


def _state_name(game) -> str:
    state = getattr(game, "game_state", "unknown")
    return getattr(state, "name", str(state))


def _failure_location(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    return f"{frames[-1].filename}:{frames[-1].lineno}" if frames else "unknown"


def _snapshot(game, bot, seed, scenario, round_number, reason, ticks, elapsed,
              states, events, collisions, exception=None):
    two = getattr(game, "player_count", 1) == 2
    snakes = [game.snake1, game.snake2] if two else [game.snake]
    directions = ([game.snake_direction1, game.snake_direction2] if two else
                  [game.snake_direction])
    boss = getattr(game, "boss", None)
    trace = "".join(traceback.format_exception(exception)) if exception else None
    result = RunResult(
        seed, scenario, round_number, reason, ticks, elapsed, states,
        getattr(game, "level", 0), getattr(game, "score", 0), getattr(game, "lives", 0),
        ([game.player_health_p1, game.player_health_p2] if two else game.player_health),
        ([snake[0] if snake else None for snake in snakes] if two else
         (snakes[0][0] if snakes[0] else None)),
        ([len(snake) for snake in snakes] if two else len(snakes[0])),
        ([direction.name for direction in directions] if two else directions[0].name),
        len(game.enemies), len(game.items),
        len(game.projectiles) + len(game.flame_projectiles) +
        len(game.boss_flame_projectiles) + len(game.enemy_projectiles),
        len(game.aoe_zones),
        {"active": boss is not None, "health": getattr(boss, "health", None),
         "fight_active": bool(game.boss_fight_active)},
        {"present": game.portal is not None, "effect_active": game.portal_effect_active,
         "effect_type": game.portal_effect_type},
        bot.actions, collisions, list(events)[-20:],
        reason not in ("exception", "cancelled") and ticks > 0 and bool(bot.actions), elapsed,
        _state_name(game), ticks,
        type(exception).__name__ if exception else None,
        _failure_location(exception) if exception else None, trace)
    return result


def run_simulation(rounds: int = 3, steps: int = 120, step_seconds: float = 1.0,
                   base_seed: int | None = None, scenarios=None,
                   control: SimulationControl | None = None, progress=None,
                   max_simulation_time: float | None = None) -> dict:
    """Führt isolierte Läufe mit exakt 60 echten ``Game.update``-Aufrufen/s aus.

    ``step_seconds`` bleibt aus Kompatibilitätsgründen ein Fast-Forward-Wert,
    verändert aber niemals die Tickdauer. ``steps`` begrenzt die Tickanzahl.
    """
    if not 1 <= rounds <= 99: raise ValueError("rounds muss zwischen 1 und 99 liegen")
    if steps < 1: raise ValueError("steps muss positiv sein")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import pygame
        pygame.init(); pygame.font.init(); pygame.display.set_mode((1, 1), pygame.HIDDEN)
        from modules.enums import GameState
        from modules.game import Game
    available = _scenario_actions()
    names = list(SCENARIOS if scenarios is None else scenarios)
    unknown = set(names) - set(available)
    if unknown: raise ValueError(f"Unbekannte Szenarien: {sorted(unknown)}")
    control = control or SimulationControl()
    first_seed = random.SystemRandom().randrange(2**32) if base_seed is None else base_seed
    results, real_started = [], time.monotonic()
    planned = rounds * len(names)

    for name in names:
        for round_number in range(1, rounds + 1):
            if not control.checkpoint(): break
            index = len(results); seed = (first_seed + index) % 2**32
            random.seed(seed); clock = SimulatedClock(); game = None; bot = SimulationBot(seed)
            ticks = 0; states = []; events = deque(maxlen=20); collisions = []
            reason, exc = "max_simulation_time", None
            try:
                with patch("time.time", clock.time), patch("time.monotonic", clock.monotonic), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    game = Game(headless=True); available[name](game)
                    states.append(_state_name(game)); events.append(f"Szenario {name} vorbereitet")
                    previous = {"score": game.score, "lives": game.lives,
                                "health": getattr(game, "player_health", 100)}
                    for tick in range(steps):
                        if not control.checkpoint(): reason = "cancelled"; break
                        actions = bot.act(game, tick)
                        if actions: events.append("Bot: " + ", ".join(actions))
                        clock.advance(TICK_SECONDS)
                        if _state_name(game) in ("GAME", "BOSS_FIGHT"):
                            game.update()
                        ticks += 1
                        state = _state_name(game)
                        if state != states[-1]: states.append(state); events.append(f"GameState -> {state}")
                        if game.score != previous["score"]: events.append(f"Score {previous['score']} -> {game.score}")
                        if game.lives != previous["lives"]: collisions.append(f"Leben {previous['lives']} -> {game.lives}")
                        health = getattr(game, "player_health", 100)
                        if health < previous["health"]: collisions.append(f"Treffer: HP {previous['health']} -> {health}")
                        previous = {"score": game.score, "lives": game.lives, "health": health}
                        if name == "game_over" and ticks == 1:
                            game.player_health = 0; game.handle_death(); state = _state_name(game)
                            if state != states[-1]: states.append(state)
                        if state == GameState.GAME_OVER.name:
                            reason = "game_over"; break
                        if max_simulation_time is not None and ticks * TICK_SECONDS >= max_simulation_time:
                            reason = "timeout"; break
                        if progress and tick % 60 == 0:
                            progress({"type": "heartbeat", "scenario": name, "round": round_number,
                                      "bot_action": actions[-1] if actions else "–", "game_state": state})
                    else:
                        reason = "completed"
            except Exception as error:
                reason, exc = "exception", error; control.errors += 1
                control.last_error = f"{name}, Seed {seed}: {type(error).__name__}: {error}"
            if game is None:
                # Minimal object allows a complete failure record even during construction.
                game = type("FailedGame", (), {"game_state": "not_initialized", "level": 0,
                    "score": 0, "lives": 0, "player_health": 0, "player_count": 1,
                    "snake": [], "snake_direction": type("D", (), {"name": "unknown"})(),
                    "enemies": [], "items": [], "projectiles": [], "flame_projectiles": [],
                    "boss_flame_projectiles": [], "enemy_projectiles": [], "aoe_zones": [],
                    "boss": None, "boss_fight_active": False, "portal": None,
                    "portal_effect_active": False, "portal_effect_type": None})()
            results.append(_snapshot(game, bot, seed, name, round_number, reason, ticks,
                                     ticks * TICK_SECONDS, states, events, collisions, exc))
            control.completed += 1
            if progress:
                progress({"type": "progress", "scenario": name, "round": round_number,
                          "completed": control.completed, "total": planned,
                          "errors": control.errors, "last_error": control.last_error,
                          "bot_action": bot.actions[-1] if bot.actions else "–",
                          "game_state": _state_name(game)})
        if control.cancelled: break

    serialized = [asdict(result) for result in results]
    failures = [run for run in serialized if run["exception"]]
    groups = {}
    for failure in failures:
        groups.setdefault(f'{failure["exception"]}@{failure["code_line"]}', []).append(failure)
    reasons = Counter(run["completion_reason"] for run in serialized)
    valid_runs = sum(run["completed"] for run in serialized)
    successful = reasons["completed"]
    return {
        "configuration": {"rounds_per_scenario": rounds, "rounds": rounds, "steps": steps,
                          "tick_seconds": TICK_SECONDS, "fast_forward_factor": step_seconds,
                          "step_seconds": step_seconds, "base_seed": first_seed,
                          "scenarios": names},
        "summary": {"total_runs": len(serialized), "successful_runs": successful,
                    "game_over_runs": reasons["game_over"], "timeouts": reasons["timeout"] + reasons["max_simulation_time"],
                    "errors": reasons["exception"], "cancelled": reasons["cancelled"],
                    "scenario_coverage": sorted({run["scenario"] for run in serialized}),
                    "state_transitions": sum(max(0, len(run["game_state_history"]) - 1) for run in serialized),
                    "most_common_failure_groups": Counter(
                        f'{run["exception"]}@{run["code_line"]}' for run in failures).most_common(),
                    "base_seed": first_seed, "duration_seconds": time.monotonic() - real_started,
                    "virtual_game_time": sum(run["virtual_game_time"] for run in serialized)},
        "seeds": [run["seed"] for run in serialized], "runs": serialized,
        "failure_groups": groups,
        "completion": {"planned_runs": planned, "completed_runs": valid_runs,
                       "executed_runs": len(serialized),
                       "complete": len(serialized) == planned and not failures and
                                   all(run["simulation_ticks"] > 0 and run["bot_actions"] for run in serialized)},
    }


def format_text_report(report: dict) -> str:
    summary = report.get("summary", {})
    lines = ["Dark Snake – Bot-Batch-Simulationsbericht",
             f"Läufe: {len(report['runs'])}",
             f"Fehler: {sum(len(group) for group in report['failure_groups'].values())}",
             f"Basis-Seed: {report['configuration']['base_seed']}",
             f"Vollständig: {report.get('completion', {}).get('completed_runs', 0)}/{report.get('completion', {}).get('planned_runs', len(report['runs']))}",
             f"Virtuelle Spielzeit: {summary.get('virtual_game_time', 0):.3f} s"]
    for run in report["runs"]:
        # Die erste Zeile bleibt mit alten Berichten/Analysewerkzeugen kompatibel.
        lines.append("Seed={seed} Szenario={scenario} Spielzeit={game_time:.3f} "
                     "GameState={game_state} Level={level} Score={score}".format(**run))
        lines.append(f"\n{run['scenario']} Runde {run.get('round', 1)} Seed={run['seed']} "
                     f"Abschluss={run.get('completion_reason', 'unbekannt')} Ticks={run.get('simulation_ticks', 0)} "
                     f"Spielzeit={run.get('virtual_game_time', run.get('game_time', 0)):.3f} "
                     f"GameState={run['game_state']} Level={run['level']} Score={run['score']}")
        if run.get("stacktrace"): lines.append(run["stacktrace"].rstrip())
    for key, failures in report["failure_groups"].items():
        lines.append(f"\nFehlergruppe {key} ({len(failures)} Vorkommen)")
    return "\n".join(lines) + "\n"


def unique_report_paths(directory: Path, scenario: str, seed: int, now=None):
    """Reserviert nichts, liefert aber ein gemeinsames, noch freies TXT/JSON-Paar."""
    stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    slug = "all" if scenario in ("all", "ALL", "alle") else scenario.lower().replace("_", "-")
    stem = f"simulation-report-{slug}-{stamp}-seed-{seed}"
    suffix = 0
    while True:
        numbered = stem if suffix == 0 else f"{stem}-{suffix}"
        paths = (directory / f"{numbered}.txt", directory / f"{numbered}.json")
        if not any(path.exists() for path in paths): return paths
        suffix += 1


def save_report(report: dict, directory: Path, scenario="all"):
    directory.mkdir(parents=True, exist_ok=True)
    txt, json_path = unique_report_paths(directory, scenario,
                                         report["configuration"]["base_seed"])
    txt.write_text(format_text_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return txt, json_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3); parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--speed", "--step-seconds", dest="speed", type=float, default=1.0)
    parser.add_argument("--seed", type=int); parser.add_argument("--scenario", action="append", choices=SCENARIOS)
    parser.add_argument("--output", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    report = run_simulation(args.rounds, args.steps, args.speed, args.seed, args.scenario)
    save_report(report, args.output, "all" if not args.scenario or len(args.scenario) > 1 else args.scenario[0])
    return 1 if report["failure_groups"] else 0


if __name__ == "__main__": raise SystemExit(main())
