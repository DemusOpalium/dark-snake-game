"""Player HP and shared lives remain distinguishable in DEV+ logs."""
from types import SimpleNamespace

from modules.dev_vitals import VitalObserver, snapshot


class Recorder:
    active = True
    def __init__(self): self.events = []
    def event(self, name, **data): self.events.append((name, data))


def game(players=1):
    return SimpleNamespace(
        player_count=players, player_health=100, player_health_p1=100,
        player_health_p2=100, lives=3, level=1, speed=8, boss=None,
    )


def test_one_player_initial_boss_entry_and_recovery():
    g, r, v = game(), Recorder(), VitalObserver()
    v.observe(g, r, source="round_start", checkpoint=True)
    g.player_health = 41.5
    v.observe(g, r, source="aoe_damage")
    g.lives = 1
    g.boss = SimpleNamespace(profile_key="medusa", health=82, max_health=82)
    v.observe(g, r, source="boss_entry", checkpoint=True)
    assert r.events[-1][1]["state"]["players"]["1"]["hp"] == 41.5
    assert r.events[-1][1]["state"]["lives_remaining"] == 1
    assert r.events[-1][1]["state"]["boss"]["key"] == "medusa"
    g.player_health = 0
    v.observe(g, r, source="medusa_frost")
    g.lives = 0
    v.observe(g, r, source="life_lost")
    assert any(name == "vitals_change" and data["lives_delta"] == -1
               for name, data in r.events)


def test_shared_lives_with_two_independent_health_bars():
    g, r, v = game(2), Recorder(), VitalObserver()
    v.observe(g, r)
    g.player_health_p1 = 84
    g.player_health_p2 = 93
    v.observe(g, r, source="boss_projectile")
    change = r.events[-1][1]
    assert len(change["hp_changes"]) == 2
    assert change["hp_changes"][0]["delta_hp"] == -16
    assert change["hp_changes"][1]["delta_hp"] == -7
    assert change["lives_delta"] == 0
    g.lives = 2
    v.observe(g, r, source="life_lost")
    assert r.events[-1][1]["lives_delta"] == -1
    g.player_health_p1 = 100
    g.player_health_p2 = 100
    v.observe(g, r, source="respawn")
    assert r.events[-1][1]["hp_changes"][0]["delta_hp"] == 16


def test_only_changed_values_recorded_with_unattributed_fallback():
    g, r, v = game(), Recorder(), VitalObserver()
    v.observe(g, r)
    assert not v.observe(g, r, source="frame")
    g.player_health = 97
    v.observe(g, r, source="unattributed")
    assert r.events[-1][1]["source"] == "unattributed"
    assert snapshot(g)["lives_remaining"] == 3
