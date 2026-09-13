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
SIMULATION_PROFILES = {"smoke": 2, "normal": 60, "stress": 300}
DEFAULT_PERCEPTION_RADIUS = 12
SCENARIOS = ("1p", "2p", "boss", "boss_final_fireball", "portal", "aoe", "projectiles", "bolbu",
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
    simulation_profile: str = "custom"
    bot_decisions: list[dict] = field(default_factory=list)
    detected_hazards: list[str] = field(default_factory=list)
    event_counts: dict = field(default_factory=dict)
    projectile_events: dict = field(default_factory=dict)
    boss_defeated_by_fireball: bool = False
    effects_triggered: list[str] = field(default_factory=list)
    boss_status_before: dict = field(default_factory=dict)
    portal_status_before: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BotWorldView:
    """Begrenzter, unveränderlicher Snapshot ausschließlich aktueller Spieldaten."""

    tick: int
    player: int
    radius: int
    head: tuple[int, int]
    direction: str
    body: tuple[tuple[int, int], ...]
    other_snake: tuple[tuple[int, int], ...]
    enemies: tuple[tuple[int, int], ...]
    boss: tuple[int, int] | None
    projectiles: tuple[tuple[int, int, str], ...]
    targets: tuple[tuple[int, int], ...]
    aoe_zones: tuple[tuple[int, int], ...]
    portal: tuple[int, int] | None
    unsafe_cells: tuple[tuple[int, int], ...]
    bounds: tuple[int, int]


class SimulationBot:
    """Kleiner lokaler Bot, der reguläre Pygame-Eingabeereignisse erzeugt."""

    _KEYS = {
        (1, "UP"): "p1_up", (1, "DOWN"): "p1_down",
        (1, "LEFT"): "p1_left", (1, "RIGHT"): "p1_right",
        (2, "UP"): "p2_up", (2, "DOWN"): "p2_down",
        (2, "LEFT"): "p2_left", (2, "RIGHT"): "p2_right",
    }

    def __init__(self, seed: int, perception_radius: int = DEFAULT_PERCEPTION_RADIUS):
        self.random = random.Random(seed)
        self.actions: list[str] = []
        self.decisions: list[dict] = []
        self.perception_radius = perception_radius

    @staticmethod
    def _distance(start, target):
        return abs(start[0] - target[0]) + abs(start[1] - target[1])

    @staticmethod
    def _position(obj):
        """Read a current grid position without exposing the object to the bot."""
        from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
        x, y = float(getattr(obj, "x", -999)), float(getattr(obj, "y", -999))
        if abs(x) >= GRID_WIDTH or abs(y) >= GRID_HEIGHT:
            x, y = x / GRID_SIZE, y / GRID_SIZE
        return int(x), int(y)

    def perceive(self, game, tick: int, player: int = 1) -> BotWorldView:
        from config import GRID_HEIGHT, GRID_WIDTH
        snake = game.snake if game.player_count == 1 else getattr(game, f"snake{player}")
        direction = (game.snake_direction if game.player_count == 1 else
                     getattr(game, f"snake_direction{player}"))
        head = tuple(snake[0]) if snake else (-1, -1)
        visible = lambda pos: self._distance(head, pos) <= self.perception_radius
        other = ()
        if game.player_count == 2:
            other = tuple(tuple(p) for p in (game.snake2 if player == 1 else game.snake1)
                          if visible(tuple(p)))
        enemies = tuple(pos for pos in map(self._position, getattr(game, "enemies", [])) if visible(pos))
        boss_obj = getattr(game, "boss", None)
        boss = self._position(boss_obj) if boss_obj else None
        if boss is not None and not visible(boss): boss = None
        projectile_rows = []
        for kind, attr in (("player", "projectiles"), ("player_flame", "flame_projectiles"),
                           ("boss", "boss_flame_projectiles"), ("enemy", "enemy_projectiles")):
            for projectile in getattr(game, attr, []):
                pos = self._position(projectile)
                if visible(pos): projectile_rows.append((pos[0], pos[1], kind))
        targets = tuple(pos for pos in map(self._position, getattr(game, "items", [])) if visible(pos))
        zones = tuple(pos for pos in map(self._position, getattr(game, "aoe_zones", [])) if visible(pos))
        portal_obj = getattr(game, "portal", None)
        portal = self._position(portal_obj) if portal_obj else None
        if portal is not None and not visible(portal): portal = None
        unsafe = set(other) | set(enemies) | set(zones)
        unsafe.update((x, y) for x, y, kind in projectile_rows if kind in ("boss", "enemy"))
        unsafe.update(tuple(p) for p in snake[1:])
        return BotWorldView(tick, player, self.perception_radius, head, direction.name,
                            tuple(tuple(p) for p in snake), other, enemies, boss,
                            tuple(projectile_rows), targets, zones, portal,
                            tuple(sorted(unsafe)), (GRID_WIDTH, GRID_HEIGHT))

    def choose_direction(self, game, player=1, view=None):
        from config import GRID_HEIGHT, GRID_WIDTH
        from modules.enums import Direction

        view = view or self.perceive(game, 0, player)
        snake = game.snake if game.player_count == 1 else getattr(game, f"snake{player}")
        current = (game.snake_direction if game.player_count == 1 else
                   getattr(game, f"snake_direction{player}"))
        if not snake:
            return current
        targets = list(view.targets) + list(view.enemies) + ([view.boss] if view.boss else [])
        target = min(targets, key=lambda pos: self._distance(snake[0], pos)) if targets else None
        occupied = set(view.unsafe_cells)
        hazards = set(view.enemies) | set(view.aoe_zones)
        if view.boss: hazards.add(view.boss)
        opposite = {Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
                    Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT}
        candidates = []
        for direction in Direction:
            if direction == opposite[current]:
                continue
            pos = (snake[0][0] + direction.value[0], snake[0][1] + direction.value[1])
            if not (0 <= pos[0] < GRID_WIDTH and 0 <= pos[1] < GRID_HEIGHT): continue
            if pos not in occupied and pos not in hazards:
                score = self._distance(pos, target) if target else 0
                candidates.append((score, self.random.random(), direction))
        return min(candidates, default=(0, 0, current))[2]

    def act(self, game, tick: int) -> list[str]:
        """Postet Richtungs-/Feueraktionen und lässt sie vom Spiel verarbeiten."""
        import pygame
        from modules.enums import Direction

        made = []
        players = (1, 2) if game.player_count == 2 else (1,)
        # One action per movement interval is sufficient and keeps reports useful.
        if tick == 0 or tick % 6 == 0:
            for player in players:
                view = self.perceive(game, tick, player)
                direction = self.choose_direction(game, player, view)
                action = self._KEYS[(player, direction.name)]
                key = game.input.bindings[action]["key"]
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
                made.append(action)
                danger_distance = min((self._distance(view.head, p) for p in view.unsafe_cells), default=None)
                target_candidates = list(view.targets) + list(view.enemies) + ([view.boss] if view.boss else [])
                target_distance = min((self._distance(view.head, p) for p in target_candidates), default=None)
                hazards = ([f"{kind}_projectile" for _, _, kind in view.projectiles if kind in ("boss", "enemy")] +
                           (["unsafe_cell_ahead"] if danger_distance is not None and danger_distance <= 1 else []))
                self.decisions.append({"tick": tick, "player": player,
                    "perception": sorted(set(hazards)), "detected_enemies": len(view.enemies),
                    "boss_detected": view.boss is not None, "detected_projectiles": len(view.projectiles),
                    "target_direction": direction.name.lower() if target_candidates else None,
                    "chosen_direction": direction.name.lower(),
                    "evasion_direction": direction.name.lower() if hazards else None,
                    "fire": False, "reason": "projectile_avoidance" if hazards else
                              ("target_approach" if target_candidates else "safe_forward"),
                    "target_distance": target_distance, "hazard_distance": danger_distance,
                    "cooldown_ready": False, "actions": [action]})
        if tick % 30 == 0:
            for player in players:
                view = self.perceive(game, tick, player)
                action = f"p{player}_fire"
                cooldown = getattr(game, f"fireball_cooldown_p{player}", getattr(game, "fireball_cooldown", 0))
                shoot_targets = list(view.enemies) + ([view.boss] if view.boss else [])
                dx, dy = Direction[view.direction].value
                clear_line = any(
                    (dx and target[1] == view.head[1] and (target[0] - view.head[0]) * dx > 0) or
                    (dy and target[0] == view.head[0] and (target[1] - view.head[1]) * dy > 0)
                    for target in shoot_targets)
                if cooldown <= 0 and clear_line:
                    key = game.input.bindings[action]["key"]
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))
                    made.append(action)
                    if self.decisions:
                        self.decisions[-1]["fire"] = True
                        self.decisions[-1]["cooldown_ready"] = True
                        self.decisions[-1]["actions"].append(action)
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
    def boss_final_fireball(game):
        # No HP/position shortcuts: the bot must navigate, aim and use p1_fire.
        game.start_game(1); game.start_boss_fight()
    def aoe(game): game.start_game(1); game.spawn_independent_aoe_zone()
    def projectiles(game):
        from config import GRID_WIDTH
        from modules.enemies import NormalEnemy
        game.start_game(1)
        game.handle_item_pickup(Item(ItemType.PROJECTILE_SHOOT))
        # A real, attackable target on the initial firing line exercises input,
        # cooldown, projectile update and collision code rather than fake values.
        enemy = NormalEnemy()
        enemy.x = min(game.snake[0][0] + 6, GRID_WIDTH - 1)
        enemy.y = game.snake[0][1]
        game.enemies.append(enemy)
    def bolbu(game):
        game.start_game(1); enemy = BolbuEnemy(); enemy.spawn_time = 0; game.enemies.append(enemy)
    def restart(game): game.start_game(1); game.score = 123; game.reset_game(); game.start_game(1)
    def game_over(game): game.start_game(1); game.lives = 1; game.player_health = 1
    return {"1p": start(), "2p": start(2), "boss": boss,
            "boss_final_fireball": boss_final_fireball, "portal": portal,
            "aoe": aoe, "projectiles": projectiles, "bolbu": bolbu,
            "restart": restart, "game_over": game_over}


def _state_name(game) -> str:
    state = getattr(game, "game_state", "unknown")
    return getattr(state, "name", str(state))


def _failure_location(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    return f"{frames[-1].filename}:{frames[-1].lineno}" if frames else "unknown"


def _snapshot(game, bot, seed, scenario, round_number, reason, ticks, elapsed,
              states, events, collisions, exception=None, profile="custom",
              event_counts=None, effects=None, boss_before=None, portal_before=None):
    two = getattr(game, "player_count", 1) == 2
    snakes = [game.snake1, game.snake2] if two else [game.snake]
    directions = ([game.snake_direction1, game.snake_direction2] if two else
                  [game.snake_direction])
    boss = getattr(game, "boss", None)
    trace = "".join(traceback.format_exception(exception)) if exception else None
    combat_events = getattr(game, "combat_events", [])
    projectile_kinds = ("player_fireball", "player_projectile", "multishot",
                        "bolbu_projectile", "boss_projectile")
    projectile_events = {
        kind: {
            "fired": sum(event.get("type") == "projectile_fired" and
                         event.get("projectile") == kind for event in combat_events),
            "hits": sum(event.get("type") == "projectile_hit" and
                        event.get("projectile") == kind for event in combat_events),
        }
        for kind in projectile_kinds
    }
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
        reason in ("survived_time_limit", "expected_game_over", "natural_game_over")
        and ticks > 0 and bool(bot.actions), elapsed,
        _state_name(game), ticks,
        type(exception).__name__ if exception else None,
        _failure_location(exception) if exception else None, trace,
        profile, bot.decisions,
        sorted({hazard for decision in bot.decisions for hazard in decision["perception"]}),
        event_counts=dict(event_counts or {}),
        projectile_events=projectile_events,
        boss_defeated_by_fireball=any(
            event.get("type") == "boss_defeated" and
            event.get("source") == "player_fireball"
            for event in getattr(game, "combat_events", [])),
        effects_triggered=list(effects or []), boss_status_before=boss_before or {},
        portal_status_before=portal_before or {})
    return result


def run_simulation(rounds: int = 3, steps: int = 120, step_seconds: float = 1.0,
                   base_seed: int | None = None, scenarios=None,
                   control: SimulationControl | None = None, progress=None,
                   max_simulation_time: float | None = None,
                   profile: str | None = None,
                   perception_radius: int = DEFAULT_PERCEPTION_RADIUS) -> dict:
    """Führt isolierte Läufe mit exakt 60 echten ``Game.update``-Aufrufen/s aus.

    ``step_seconds`` bleibt aus Kompatibilitätsgründen ein Fast-Forward-Wert,
    verändert aber niemals die Tickdauer. ``steps`` begrenzt die Tickanzahl.
    """
    if not 1 <= rounds <= 99: raise ValueError("rounds muss zwischen 1 und 99 liegen")
    if profile is not None:
        profile = profile.lower()
        if profile not in SIMULATION_PROFILES:
            raise ValueError(f"Unbekanntes Simulationsprofil: {profile}")
        steps = SIMULATION_PROFILES[profile] * 60
    elif steps < 1: raise ValueError("steps muss positiv sein")
    profile_name = profile or "custom"
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
            random.seed(seed); clock = SimulatedClock(); game = None
            bot = SimulationBot(seed, perception_radius)
            ticks = 0; states = []; events = deque(maxlen=20); collisions = []
            reason, exc = "max_simulation_time", None
            counts = Counter({name: 0 for name in ("collisions", "hits", "shots", "projectile_hits",
                "enemy_spawns", "enemy_deaths", "item_pickups", "boss_damage", "boss_phase_changes",
                "portal_starts", "portal_ends", "aoe_damage", "level_changes", "lives_lost", "game_over")})
            effects = []
            combat_event_index = 0
            boss_before = {}; portal_before = {}
            try:
                with patch("time.time", clock.time), patch("time.monotonic", clock.monotonic), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    game = Game(headless=True); available[name](game)
                    boss_before = {"active": game.boss is not None,
                                   "health": getattr(game.boss, "health", None)}
                    portal_before = {"present": game.portal is not None,
                                     "effect_active": game.portal_effect_active,
                                     "effect_type": game.portal_effect_type}
                    if portal_before["effect_active"]: counts["portal_starts"] += 1
                    states.append(_state_name(game)); events.append(f"Szenario {name} vorbereitet")
                    previous = {"score": game.score, "lives": game.lives,
                                "health": getattr(game, "player_health", 100), "level": game.level,
                                "enemies": len(game.enemies), "items": len(game.items),
                                "projectiles": 0, "portal": game.portal_effect_active,
                                "boss_health": getattr(game.boss, "health", None)}
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
                        if game.lives < previous["lives"]:
                            collisions.append(f"Leben {previous['lives']} -> {game.lives}")
                            counts["collisions"] += 1; counts["lives_lost"] += previous["lives"] - game.lives
                        health = getattr(game, "player_health", 100)
                        if health < previous["health"]:
                            collisions.append(f"Treffer: HP {previous['health']} -> {health}"); counts["hits"] += 1
                        projectile_total = sum(len(getattr(game, attr, [])) for attr in
                            ("projectiles", "flame_projectiles", "boss_flame_projectiles", "enemy_projectiles"))
                        if projectile_total > previous["projectiles"]: counts["shots"] += projectile_total - previous["projectiles"]
                        if len(game.enemies) > previous["enemies"]: counts["enemy_spawns"] += len(game.enemies) - previous["enemies"]
                        if len(game.enemies) < previous["enemies"]: counts["enemy_deaths"] += previous["enemies"] - len(game.enemies)
                        if len(game.items) < previous["items"]: counts["item_pickups"] += previous["items"] - len(game.items)
                        boss_health = getattr(game.boss, "health", None)
                        combat_events = getattr(game, "combat_events", [])
                        new_combat_events = combat_events[combat_event_index:]
                        combat_event_index = len(combat_events)
                        counts["projectile_hits"] += sum(
                            event.get("type") == "projectile_hit" for event in new_combat_events)
                        counts["boss_damage"] += sum(
                            event.get("damage", 0) for event in new_combat_events
                            if event.get("type") == "boss_damage")
                        for event in new_combat_events:
                            if event.get("type") in ("projectile_fired", "projectile_hit",
                                                     "boss_damage", "boss_defeated"):
                                events.append(f"{event['type']}: {event}")
                        if game.level != previous["level"]: counts["level_changes"] += 1
                        if previous["portal"] and not game.portal_effect_active: counts["portal_ends"] += 1
                        manager = getattr(game, "effect_manager", None)
                        active_effects = [getattr(effect, "name", type(effect).__name__)
                                          for effect in getattr(manager, "_effects", [])]
                        effects.extend(effect for effect in active_effects if effect not in effects)
                        previous = {"score": game.score, "lives": game.lives, "health": health,
                            "level": game.level, "enemies": len(game.enemies), "items": len(game.items),
                            "projectiles": projectile_total, "portal": game.portal_effect_active,
                            "boss_health": boss_health}
                        if name == "game_over" and ticks == 1:
                            game.player_health = 0; game.handle_death(); state = _state_name(game)
                            if state != states[-1]: states.append(state)
                        if state == GameState.GAME_OVER.name:
                            counts["game_over"] += 1
                            reason = "expected_game_over" if name == "game_over" else "natural_game_over"; break
                        if max_simulation_time is not None and ticks * TICK_SECONDS >= max_simulation_time:
                            reason = "timeout"; break
                        if progress and tick % 60 == 0:
                            progress({"type": "heartbeat", "scenario": name, "round": round_number,
                                      "bot_action": actions[-1] if actions else "–", "game_state": state})
                    else:
                        reason = "survived_time_limit"
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
                                     ticks * TICK_SECONDS, states, events, collisions, exc,
                                     profile_name, counts, effects, boss_before, portal_before))
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
    successful = reasons["survived_time_limit"]
    totals = Counter()
    for run in serialized: totals.update(run["event_counts"])
    action_counts = Counter(action for run in serialized for action in run["bot_actions"])
    return {
        "configuration": {"rounds_per_scenario": rounds, "rounds": rounds, "steps": steps,
                          "tick_seconds": TICK_SECONDS, "fast_forward_factor": step_seconds,
                          "step_seconds": step_seconds, "base_seed": first_seed,
                          "scenarios": names, "profile": profile_name,
                          "profile_seconds": SIMULATION_PROFILES.get(profile_name),
                          "perception_radius": perception_radius},
        "summary": {"total_runs": len(serialized), "successful_runs": successful,
                    "planned_runs": planned, "executed_runs": len(serialized),
                    "successful_time_limit_runs": successful,
                    "expected_game_overs": reasons["expected_game_over"],
                    "natural_game_overs": reasons["natural_game_over"],
                    "game_over_runs": reasons["expected_game_over"] + reasons["natural_game_over"],
                    "timeouts": reasons["timeout"], "max_simulation_time": reasons["max_simulation_time"],
                    "errors": reasons["exception"], "unexpected_errors": reasons["exception"],
                    "cancelled": reasons["cancelled"],
                    "scenario_coverage": sorted({run["scenario"] for run in serialized}),
                    "state_transitions": sum(max(0, len(run["game_state_history"]) - 1) for run in serialized),
                    "most_common_failure_groups": Counter(
                        f'{run["exception"]}@{run["code_line"]}' for run in failures).most_common(),
                    "base_seed": first_seed, "duration_seconds": time.monotonic() - real_started,
                    "virtual_game_time": sum(run["virtual_game_time"] for run in serialized),
                    "bot_action_statistics": dict(action_counts),
                    "event_statistics": dict(totals),
                    "collision_statistics": totals["collisions"], "hit_statistics": totals["hits"],
                    "projectile_statistics": {"shots": totals["shots"], "hits": totals["projectile_hits"]},
                    "boss_damage_statistics": totals["boss_damage"],
                    "portal_statistics": {"starts": totals["portal_starts"], "ends": totals["portal_ends"]},
                    "effect_statistics": dict(Counter(effect for run in serialized for effect in run["effects_triggered"]))},
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
             f"Virtuelle Spielzeit: {summary.get('virtual_game_time', 0):.3f} s",
             f"Zeitlimit überlebt: {summary.get('successful_time_limit_runs', 0)}",
             f"Erwartete Game Overs: {summary.get('expected_game_overs', 0)}",
             f"Natürliche Game Overs: {summary.get('natural_game_overs', 0)}",
             f"Timeouts: {summary.get('timeouts', 0)}",
             f"Abbrüche: {summary.get('cancelled', 0)}"]
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
    parser.add_argument("--profile", choices=SIMULATION_PROFILES, default="normal")
    parser.add_argument("--seed", type=int); parser.add_argument("--scenario", action="append", choices=SCENARIOS)
    parser.add_argument("--output", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    report = run_simulation(args.rounds, args.steps, args.speed, args.seed, args.scenario,
                            profile=args.profile)
    save_report(report, args.output, "all" if not args.scenario or len(args.scenario) > 1 else args.scenario[0])
    return 1 if report["failure_groups"] else 0


if __name__ == "__main__": raise SystemExit(main())
