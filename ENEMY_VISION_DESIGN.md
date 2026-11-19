# DARK SNAKE · Enemy Vision A/B/C (19.11.2026)

**Bestätigt unter Windows:** Phase A (#225) und Phase B (#226) sind gemergt und vom Projektinhaber mit mehreren Gegnern und `KI-Test an/aus` positiv geprüft. Phase C wird in einem **separaten Draft-PR** erprobt. **Keine neuen FrostAge-Gegner gespawnt; Boss-/Angriffsregeln unverändert.**

## Phase C · Feste Stellschrauben für die existierenden Gegner

**Kein zusätzlicher Enemy Creator, kein Gegner-Zufallsgenerator.** Hier wird der bereits verwendete `VisionProfile` erweitert:
- `radius_cells` = kleiner **Entdeckungsradius**;
- `alert_radius_cells` = größerer **Sicht-/Verfolgungsradius erst NACH bestätigter Entdeckung**, wahlweise `None` für bisheriges Classic-Verhalten;
- `reaction_seconds` = wie lange der Kopf innerhalb eines echten Sichtkegels vor dem ersten Erkennen sichtbar bleiben muss (kontinuierlich über mehrere Sensor-Ticks);
- `memory_seconds` = wie lange die **letzte bestätigte** Position nach Sichtverlust gesucht werden darf, danach Reset zum kleinen Entdeckungsradius;
- `scan_interval` = gedrosselter, fest einstellbarer Sensor-Takt (kein Frame-Zähler);
- `BehaviorProfile` erhält getrennte feste `patrol_speed`-, `chase_speed`- und `search_speed`-Faktoren. Einheit: Faktor zum jeweiligen existierenden Gegnertempo, kein neues Bewegungssystem.

Bei aktivem `KI-Test` bekommen **bereits vorhandene** Gegner zwei unterschiedliche **feste** Beispiele: `NormalEnemy` (100°, 5→11 Felder, 0,25 s Entdeckung, 3 s Gedächtnis, CHASE 1,30× / SEARCH 0,78×) und `BolbuEnemy` (360°, 6→12 Felder, 0,55 s Entdeckung, 5 s Gedächtnis, GUARD, ruhiger PATROL). Alle Werte sind **Prototyp-Balancing**, nicht endgültige Spielregeln.

**Keine magische Ortung:** Sowohl innerer als auch äußerer Kreis prüfen Blickwinkel und Supercover-Wände; während des Suchens steht nur die zuletzt **wirklich beobachtete** Position zur Verfügung. Nach Ablauf der Gedächtniszeit muss der Gegner den Spieler im kleinen Radius erneut entdecken. Auch im Zweispielermodus bleiben die Zielwahl und die Kontinuität der Entdeckung definiert.

**KI-Test aus** stellt sofort das alte `SIGHT_PROFILE` und ursprüngliche Classic-Bewegungs-/Sprintverhalten wieder her; der neue Alarmzustand wird beim Wechsel zurückgesetzt. Das übrige Spiel, HP, Bossphasen, Schadens-, Projektil- und Speicherregeln bleiben unangetastet.

**Windows-Probe:** Tab → `KI-Test` + `Hitboxen`. Im Grundzustand kleinerer Ring; nach echter Entdeckung zeichnen wir einen dezenten größeren violetten Ring. Sichtverlust an einer Wand → Suche nach letzter Stelle → nach wenigen Sekunden wieder kleiner Ring. `KI-Test` abschalten → alte Classic-Bewegung. Erst nach manuellem Windows-Test Folgeschritt "weitere Classic-Gegnerprofile / Boss-System-Adapter" und später FrostAge (#216).


## Phase B · Wahrnehmung wird zu Bewegung (Opt-in)

- `modules/enemy_behavior.py`: minimale, isolierte Reaktionsplanung ohne Pygame. `PATROL` bei fehlendem Kontakt, `CHASE` bei Sichtkontakt, `SEARCH` zur letzten tatsächlich gesehenen Position; zusätzlich `GUARD` und `RETREAT` als kompatible Profile für spätere Feinde.
- Classic-Normalgegner folgen der Schlange nur, wenn **Admin-Menü → KI-Test** ausdrücklich aktiviert wurde. Bolbu bleibt bei Sichtkontakt stationär (`GUARD`), feuert und würfelt aber weiterhin nach bestehenden Regeln.
- Die Bewegungsentscheidung verwendet die bereits vorhandene `VisionSensor`-Messung, vermeidet WALL/BARRIER-Zellen sowie diagonales Abkürzen durch Wandecken und verwendet das **bestehende** Rasterbewegungs-/Animationssystem. Lokaler nächster Schritt, **noch kein A*-Pathfinding** und keine feste Flanken-/Boss-KI.
- Debugmodus **Hitboxen** zeigt zusätzlich einen kleinen Buchstaben (`P/C/S/G/R`) für den aktuellen Zustand. Das ist ein Entwicklertest, keine neue Spieler-HUD-Fläche.
- Drei **inaktive künftige** FrostAge-Verhaltensprofile sind vorbereitet:
  - `frostage_eisskelett` = CHASE / Verfolgung,
  - `frostage_frostwisp` = RETREAT bei Nähe / Distanzverteidigung,
  - `frostage_frosttitan` = GUARD / schwerer Wächter.
  **Wichtig:** Profile alleine sind keine FrostAge-Runtime-Assets, kein Spawn-System und keine spielbaren Gegner. Die grafische Einbindung folgt getrennt unter Issue #216.
- Standard Classic bleibt **exakt beim bisherigen Zufallsverhalten**. Der Schalter ist nicht dauerhaft gespeichert und wird bei jeder neuen Runde auf `aus` gesetzt.
- Nur Wahrnehmungs- und Bewegungsabsichten geändert, **keine** neue Auslösung von Schaden, Projektilen, Belohnungen, Teleport oder Spawn. Der bestehende Bolbu-Dice-Sprint bleibt bei Aktivierung weiterhin möglich.

### Windows-Spielprobe für Demus

1. Neuen Windows-Build starten, Classic **1P** wählen und mit `Tab` das Admin-Menü öffnen.
2. **KI-Test** aktivieren, danach das Menü schließen. Optional die bereits vorhandenen **Hitboxen** einschalten.
3. Bei einem normalen Gegner vor dessen Blickrichtung laufen: der Buchstabe `C` steht für `CHASE`; hinter ihm bleibt er auf `P` (PATROL), bis er sich zu dir dreht.
4. Hinter Sichtblockern wird der Sichtkontakt unterbrochen: `S` für kurzes SEARCHING, dann `P`. Bolbu zeigt bei Rundumsicht `G` und bleibt bei Sichtkontakt als Schütze stehen (Würfel-/Schussaktionen bleiben erhalten).
5. **KI-Test** ausschalten: sofort wieder altes Classic-Verhalten. Mit neuem Run ist der KI-Test automatisch aus. Danach gern 2P-Spielprobe mit beiden Köpfen.

Die Bewegung wird nur dann clever, wenn der Entwickler den Test einschaltet. Alle Werte sind **Prototyp-Balancing**, kein geplanter automatischer Classic-Release.

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
