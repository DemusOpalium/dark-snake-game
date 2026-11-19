# DARK SNAKE · Enemy Vision A (19.11.2026)

**Status:** erster testbarer Wahrnehmungskern in Draft-PR. **Keine neuen FrostAge-Gegner gespawnt, keine neue Kampf-/Boss-KI aktiviert.** Der Hauptbranch `main` bleibt bis zum manuellen Review unverändert.

## Geprüfter Ausgangspunkt

- `NormalEnemy` bewegt sich bislang per Zufall, kann sprinten und verwendet weich interpolierte Rasterpositionen (`enemies.py`).
- `BolbuEnemy` erweitert `NormalEnemy` um Frame-Animation, eigene Geschosse und Würfelangriffe (`bolbu_enemy.py`).
- `Game.update()` ruft Gegnerbewegung, Angriff und gemeinsame Kollisionsauflösung auf (`game.py`); die bestehenden Classic-Regeln müssen erhalten bleiben.
- `LevelEditor.select_for_classic()` übergab bisher Grafik/Dach, aber **nicht** seine WALL-/BARRIER-Zellen an Classic. Diese Zellen werden mit diesem PR ausschließlich für das **Sichtsystem** verfügbar; physische Spielkollisionen bleiben bislang unverändert.
- `WorldLibrary` verwaltet Level-/Weltnamen und -Zuordnungen, ist noch **kein aktiver Spawn-/Enemy-Age-Router**. `LevelPlaytest` nutzt bereits eigene Kollisionsebenen, ist aber nicht dasselbe wie der Classic-Spielloop.

## Jetzt implementiert: Augen, ohne Angriffe zu verändern

- `modules/enemy_vision.py`: reine Geometrie ohne Pygame: Sichtweite in Rasterzellen, Blickwinkel 1–360°, 2D-Blickrichtung inkl. Diagonale, konservativer Supercover-Strahl durch WALL/BARRIER, deterministische Wahl der nächstgelegenen sichtbaren Schlange (1P/2P), kurze Erinnerung an die letzte **tatsächlich sichtbare** Zelle, Wahrnehmungszustände `UNAWARE`, `VISIBLE`, `SEARCHING`. Gegner können weder durch Blocker noch hinter sich schauen (außer 360°-Profile).
- `VisionSensor` prüft alle 0,15 s statt mit jeder FPS. Standardgegner: 100°, 5 Zellen, 1,5 s Gedächtnis. Bolbu: 360°, 6 Zellen, 2 s. **Versuchswerte**, kein endgültiges Balancing.
- `NormalEnemy.facing` wird nur nach wirklicher Bewegung aktualisiert. Der Sensor liegt am Gegner, nicht im PNG. Animationen sind weiterhin frei austauschbar.
- `Game.update()` aktualisiert alle echten `NormalEnemy`-Instanzen inklusive Bolbu für beide Spielerköpfe. Sichtbeobachtungen verursachen **keinen** Schaden, lösen **keinen** Sprint, keinen Teleport und keine Belohnung aus.
- Das **bestehende Hitbox-Debug-Overlay** zeichnet zusätzlich Sichtreichweite, Blicksektor, zuletzt erkannte Position und grün/gelb markierten Kontakt. Im normalen Spielbetrieb werden diese Hilfslinien nicht gezeichnet.
- Keine Änderungen an Bestandsdaten, XP, Saves, Bossmodi, Projektilgrenzen oder FPS-/Animationsregeln.

## Schnittstelle für die nächsten Vertical Slices

```python
# Beispiel rein visuelle Wahrnehmung (kein Angriff):
profile = VisionProfile(radius_cells=5, fov_degrees=90,
                        memory_seconds=1.5, scan_interval=0.15)
eyes = VisionSensor(profile)
result = eyes.observe(
    origin=(5, 5), facing=(1, 0),
    targets=[(1, (8, 5)), (2, (4, 7))],
    blockers={(6, 6)}, now=10.0,
)
# result.kind: UNAWARE | VISIBLE | SEARCHING
# result.target_player, result.last_known_cell, result.last_seen_at
```

## Folgeschritte – bewusst **nicht** in diesem PR

1. Kleine, profilgesteuerte **Wahrnehmung → Aktion**-Schnittstelle (PATROL/CHASE/SEARCH), zuerst kontrolliert aktivierbar, danach Windows-Sichtprobe.
2. `Age`-Registry und sichere separate Spawn-Pools für Classic/FrostAge/Mycelium; stabile IDs, keine Aktivierung aufgrund bloß vorhandener PNGs. Siehe [Issue #216](https://github.com/DemusOpalium/dark-snake-game/issues/216).
3. Drei FrostAge-Prototypen (Eisskelett frontal, Frostwisp Rundumsicht, Frosttitan später Boss) mit getesteter Weltzuordnung, dann DASH/TELEPORT/RETREAT/SUMMON.
4. Übertragbare Vision-Blocker auch in späteren World-Studio-Gameplay-Modi; **Wand-Kollision und Sichtblockade müssen langfristig konsistent sein**.
5. Wahrnehmungstakte und Performance mit `FrameMetrics`/Benchmark und 1P-/2P-Tests bei voller Gegnermenge prüfen; Cache und Debug-Darstellung erst nach Messungen optimieren.

**Qualitätsgrenze:** Die neuen Beobachtungszustände bedeuten nicht, dass die Gegner schon taktisch jagen. Das wird bewusst in einem getrennten, reversiblen PR umgesetzt. Für eine erste visuelle Prüfung das vorhandene Hitbox-Debug-Overlay im Classic-Spiel aktivieren.
