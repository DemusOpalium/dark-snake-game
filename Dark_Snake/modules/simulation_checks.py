"""Gezielte Spielregelprüfungen neben den regulären Bot-Läufen."""

from __future__ import annotations

import contextlib
import io
import random
import traceback
from unittest.mock import patch

from modules.enums import Direction, GameState


class RuleCheckFailure(AssertionError):
    """Ein Vergleich mit der erwarteten Spielregel ist fehlgeschlagen."""


def _expect(actual, expected, detail):
    if actual != expected:
        raise RuleCheckFailure(f"{detail}. Erwartet {expected!r}, beobachtet {actual!r}.")


def _body_stall(game, clock):
    from config import GRID_HEIGHT, GRID_WIDTH

    game.start_game(1)
    body = [(4, 4), (4, 3), (5, 3), (5, 4), (6, 4)]
    game.items.clear()
    game.snake = body.copy()
    game.snake_direction = Direction.DOWN
    game.next_direction = Direction.RIGHT
    game.respawn_invincible_until = clock.time() - 1
    game.last_update_time = clock.time() - 1
    lives = game.lives
    game.player_health = 60

    game.update()
    _expect((game.snake, game.lives, game.player_health), (body, lives, 60),
            "Der erste blockierte Zug erhält Körper, Leben und HP")
    clock.advance(1.0)
    game.update()
    game.set_state(GameState.PAUSE)
    clock.advance(10.0)
    game.update()
    game.set_state(GameState.GAME)
    clock.advance(1.875)
    game.update()
    _expect((game.snake, game.lives, game.player_health), (body, lives, 60),
            "Vor drei aktiven Sekunden kostet der Stillstand kein Leben")
    clock.advance(0.125)
    game.update()
    _expect((game.lives, game.snake, game.player_health),
            (lives - 1, [(GRID_WIDTH // 2, GRID_HEIGHT // 2)], 100),
            "Nach drei aktiven Sekunden folgt ein einzelner Lebensverlust mit Respawn")


def _fire_at(game, target):
    from modules.game import FlameProjectile

    projectile = FlameProjectile(*target.get_hitbox().center, (1, 0), speed=0)
    game.flame_projectiles.append(projectile)
    return projectile


def _boss_damage(game, clock):
    game.start_game(1)
    _expect(game.start_boss_fight(), True, "Der Bosskampf startet")
    boss = game.boss
    boss.x, boss.y = 8, 6
    health, score = boss.health, game.score

    shot = _fire_at(game, boss)
    game.update()
    _expect((game.boss is boss, boss.health, game.score),
            (True, health - shot.damage, score),
            "Der Feuerball senkt die Boss-HP um seinen Schaden")

    shot = _fire_at(game, boss)
    boss.health = shot.damage
    clock.advance()
    game.update()
    clock.advance()
    game.update()
    defeats = sum(event["type"] == "boss_defeated" for event in game.combat_events)
    _expect((game.boss is None, game.boss_fight_active, game.score, defeats),
            (True, False, score + 100 * game.level, 1),
            "Der tödliche Feuerball beendet den Kampf und vergibt die Prämie einmal")


def _classic_boss_shot(game, clock):
    game.start_game(2)
    game.items.clear()
    game.snake1, game.snake2 = [(4, 4)], [(5, 4)]
    game.respawn_invincible_until = clock.time() - 1
    game.projectiles.append({"from_boss": True, "pos": (4, 4), "dir": (0.5, 0)})

    game.update()
    _expect((game.player_health_p1, game.player_health_p2), (90, 100),
            "Der klassische Schuss trifft zuerst nur P1 für 10 HP")
    clock.advance()
    game.update()
    _expect((game.player_health_p1, game.player_health_p2), (90, 90),
            "Derselbe Schuss trifft P2 und zieht P1 keine weiteren HP ab")
    clock.advance()
    game.update()
    _expect((game.player_health_p1, game.player_health_p2), (90, 90),
            "Auch bei einem weiteren Kontakt bleibt der Schaden pro Spieler einmalig")


def _frost_target(game, clock):
    from config import GRID_SIZE
    from modules.enemies import NormalEnemy

    game.start_game(1)
    game.frost.toggle()
    enemy = NormalEnemy()
    enemy.x, enemy.y = 8, 6
    enemy.width = enemy.height = GRID_SIZE
    enemy.health = 100
    enemy.speed = 1.0
    enemy.spawn_time = clock.time() - 3
    enemy.last_move = clock.time()
    game.enemies.append(enemy)
    return enemy


def _frost_duration(game, clock):
    enemy = _frost_target(game, clock)
    _fire_at(game, enemy)
    game.update()
    _expect(len(game.frost.zones), 1, "Ein bestätigter Feuerball erzeugt eine Zone")
    clock.advance(3.0 - 1 / 64)
    game.update()
    _expect(len(game.frost.zones), 1, "Die Frostzone bleibt knapp unter drei Sekunden aktiv")
    clock.advance(1 / 64)
    game.update()
    _expect(len(game.frost.zones), 0, "Die Frostzone endet nach drei Sekunden")


def _frost_overlap(game, clock):
    enemy = _frost_target(game, clock)
    start = clock.time()
    _fire_at(game, enemy)
    game.update()
    clock.advance(0.25)
    _fire_at(game, enemy)
    game.update()
    _expect(len(game.frost.zones), 2, "Zwei Treffer erzeugen zwei überlappende Zonen")
    clock.advance(1.15)
    game.update()
    _expect(enemy.last_move, start, "Die überlappenden Zonen verlangsamen die Bewegung")
    clock.advance(0.05)
    game.update()
    _expect(enemy.last_move, clock.time(),
            "Mit 70 Prozent Tempo folgt der nächste Bewegungsschritt bis 1,45 Sekunden")


CHECKS = (
    ("classic_body_stall", "Classic 1P – blockierter Körperzug und aktive Drei-Sekunden-Frist",
     ("1p",), _body_stall),
    ("classic_boss_damage", "Classic – Boss-HP und einmalige Prämie bei Feuerballtreffern",
     ("boss", "boss_final_fireball"), _boss_damage),
    ("classic_boss_shot_once", "Classic 2P – ein Treffer je Spieler pro Bossprojektil",
     ("2p", "boss", "projectiles"), _classic_boss_shot),
    ("frost_duration", "Frost – Zone aus bestätigtem Treffer und Ablauf nach drei Sekunden",
     ("projectiles",), _frost_duration),
    ("frost_overlap", "Frost – überlappende Zonen stapeln die Verlangsamung nicht",
     ("projectiles",), _frost_overlap),
)


def run_rule_checks(scenarios, seed, *, game_factory=None, clock_factory=None, skip_reason=None):
    """Prüft einmal pro Batch in eigenen Spielinstanzen und mit virtueller Zeit."""
    selected = set(scenarios)
    results = []
    random_state = random.getstate()
    try:
        for check_id, label, applicable, exercise in CHECKS:
            result = {"id": check_id, "label": label, "scenarios": list(applicable), "seed": seed}
            results.append(result)
            if skip_reason or selected.isdisjoint(applicable):
                result.update(status="not_run",
                              detail=skip_reason or "Passendes Szenario nicht ausgewählt.")
                continue
            if game_factory is None or clock_factory is None:
                raise TypeError("Ausgeführte Spielregelprüfungen benötigen game_factory und clock_factory.")

            try:
                random.seed(seed)
                clock = clock_factory()
                with (patch("time.time", clock.time), patch("time.monotonic", clock.monotonic),
                      patch("random.random", lambda: 1.0),
                      contextlib.redirect_stdout(io.StringIO()),
                      contextlib.redirect_stderr(io.StringIO())):
                    exercise(game_factory(headless=True), clock)
            except RuleCheckFailure as error:
                result.update(status="failed", detail=str(error))
            except Exception as error:
                result.update(status="exception", exception=type(error).__name__, detail=str(error),
                              stacktrace="".join(traceback.format_exception(error)))
            else:
                result.update(status="passed", detail="Erwartetes Spielverhalten bestätigt.")
    finally:
        random.setstate(random_state)
    return results
