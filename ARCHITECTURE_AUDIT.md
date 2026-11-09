# DARK Snake · Architektur-Audit

Ausgangsstand ist `main` bei `5f7b206`. Die folgenden Befunde beziehen sich auf diesen Stand.

## Ablauf eines Frames

1. [`main.py`](Dark_Snake/main.py) initialisiert Absturzprotokoll, Pygame und Mixer. Ein kleines Display steht schon vor dem Import von `Game` bereit, damit die Grafiken beim Laden `convert_alpha()` verwenden können. `Game()` öffnet anschließend das Spielfenster. Der PyInstaller-Build verwendet denselben Einstieg.
2. [`Game.run()`](Dark_Snake/modules/game.py) ruft `handle_events()` auf. Dort werden Pygame-Events ausgelesen, Belegungen über `InputManager` aufgelöst und je nach Spielzustand an Menüs, Entwicklerwerkzeuge oder Spielaktionen weitergegeben.
3. `Game.update()` läuft in `GAME` und `BOSS_FIGHT`, solange Admin-Menü und Editor geschlossen sind. Update umfasst unter anderem Cooldowns, Gegner, Projektile, Kollisionen, Portale, Effekte und Rasterzüge. Die Spielrichtung wird erst beim Rasterzug wirksam. Kopf und Körper bleiben für die Kollision auf Rasterkoordinaten.
4. `Game.draw()` wählt die Szene, zeichnet Welt, HUD und Overlays und übergibt die Fläche mit `pygame.display.update()` an SDL. `Clock.tick(FPS)` begrenzt danach den Takt. Das Ende dieses Aufrufs zur Bildausgabe ist als interne Messgrenze beobachtbar. Geräteabfrage, Systemwarteschlangen und sichtbare Monitorreaktion liegen außerhalb dieser Messung.

## Aufrufer und Abhängigkeiten

| Bereich | Bestehende Abhängigkeiten | Grenze für diesen Umbau |
| --- | --- | --- |
| `InputManager` | Tastatur- und Joystick-Events, Benutzerprofil für `controls.json`, Belegungsdaten für Menü und Simulator | Geräte erkennen und zuordnen, Events in benannte Aktionen übersetzen, Belegungen migrieren und speichern |
| `ControlsMenu` | Arbeitet über `game.input` und wechselt über `Game.set_state()` zurück ins Hauptmenü | Anzeige, Erfassung und Eingabetest. `Game` leitet Events während der Erfassung exklusiv an das Menü. |
| `Game` | Besitzt Spielzustand, Raster, Leben, Gesundheit, Effekte und Entitäten. Verwendet Pygame, Ressourcen, Audio und die Menümodule. | Aktionen anhand von Spielmodus und Zustand annehmen oder verwerfen und am richtigen Spielpunkt anwenden |
| `AdminPanel` | Liest Kopf und Richtung von Spieler 1, ändert Gesundheit und Effekte und ruft u. a. `Game.spawn_item_at()` und `Game.start_boss_fight()` auf | Die bestehenden Aktionsaufrufe bleiben überprüfbar. Das Menü schaltet die getrennte Zeitmessung um. |
| Entwicklersimulator | `SimulationBot.act()` liest `game.input.bindings[action]["key"]` und sendet Pygame-Tastenevents an `Game.handle_events()`. Batch-Läufe erzeugen `Game(headless=True)`, nutzen eine virtuelle Uhr und rufen `Game.update()` direkt auf. | Den Tastaturzugriff und den Eventpfad mitdenken. Ein reiner Umbau des Dateiformats reicht dafür nicht aus. Headless-Läufe bleiben ohne eigenes Spielfenster. |
| Zeitmessung | Zeitmarken an Eingabeannahme, Rasterzug beziehungsweise Projektilerzeugung und Bildausgabe | `FrameMetrics` verwaltet die Messwerte und das Overlay. Entscheidungen über Kollisionen und Eingaben bleiben beim Spiel. |

## Befunde am Ausgangsstand

- `Game.update()` zeichnet AoE-Zonen, Explosionen und Gesundheitsleisten. `draw_game()` zeichnet Zonen und Explosionen erneut. Der Simulator führt das Update ebenfalls aus und muss diese Zeichenarbeit am Offscreen-Surface bezahlen.
- `draw_game()` ruft `draw_hud()` auf, danach ruft `Game.draw()` das HUD ein zweites Mal auf. `test_windows_runtime.py` ruft `draw_game()` auch direkt auf. Die Änderung muss den Weltaufbau in diesem Aufruf erhalten.
- `ControlsMenu.draw()` und `CustomizationMenu.draw()` geben das Bild selbst aus. Im regulären Frame gibt anschließend auch `Game.draw()` das Bild aus. `draw_leaderboard()` liest außerdem eine zweite Eventliste und vermischt Zeichnen und Eingabe. `confirm_back_to_main()` gibt die Bestätigungsanzeige separat aus und wartet blockierend.
- Unter `if __name__ == "__main__"` folgen nach der laufenden Spielschleife und einer Terminal-Eingabe fünf Moduldefinitionen. `spawn_item_at`, `create_damage_zone`, `create_slow_zone`, `spawn_explosive_projectile` und `start_boss_fight` gehören dort zur Modulebene. Beim normalen Import werden sie nicht definiert, und die Spielschleife kehrt im regulären Ablauf nicht dorthin zurück. Die gleichnamigen **Methoden** `Game.spawn_item_at()` und `Game.start_boss_fight()` stehen weiter oben in der Klasse. Admin-Menü, Simulator und Boss-/Portalübergänge verwenden diese aktiven Methoden.
- In 2P ist `self.snake` leer. Die Kurzbefehle R, T und Z lasen trotzdem `self.snake[0]`. Die Debug-Zonen brauchen dieselbe Auswahl des aktiven Spielerkopfs wie die übrigen Effekte.
- Der 1P-Rasterzug prüft den eigenen Körper ohne das letzte Segment. 2P prüft den Körper einschließlich des Schwanzes. Im Ausgangsstand ruft der Rasterzug bei einer festgestellten Selbstkollision `handle_death()` auf. Die Methode kehrt bei positiver Gesundheit zurück, sodass die Kollision ohne Lebensverlust als stehengebliebener Zug enden kann.
- `update_projectiles()` wird in `update()` vor dem Rasterzug und innerhalb eines fälligen Rasterzugs aufgerufen. Dabei werden auch einige bereits weiter oben aktualisierte Projektile erneut fortgeschrieben. Vor einer Änderung der Kadenz brauchen Geschwindigkeit und Trefferreihenfolge eine feste Spielregel mit Test.

## Prüfbasis

Die 61 Headless-Tests auf `main` decken Menüs und Tastaturstart, 2P-Reset, simulierte Gamepad-Events und Speichern, Admin- und Editor-Routing, Grafikressourcen und Editor-Dateien, normale Schlangeninterpolation, Portalhintergründe, Boss-Niederlage und Projektil-Hitboxen, Effekte sowie deterministische Simulator-Szenarien ab. Die Tests zur Interpolation vergleichen Raster und Darstellung getrennt. Sie belegten noch keine Randmatrix für alle Kanten, Spieler und Skalierungen. Die 2P-Gerätezuordnung bei Hotplug und die Verzögerung bis zur Bildausgabe brauchten eigene Tests.

Das [Messskript](scripts/benchmark_game.py) verwendet Seed `16000`, je 60 Aufwärm- und 360 Messframes und ein Limit von 60 FPS. Die Lastprobe startet 2P mit Boss, 24 zusätzlichen Rasterprojektilen pro Frame und zwölf zusätzlichen Effekten. Die Spieluhr wird in festen Schritten simuliert. Die Phasen werden mit `perf_counter_ns()` auf der echten Uhr gemessen. Tastenevents werden erzeugt, SDL läuft mit dem Dummy-Treiber. Die Vergleichsprobe erfasst für den Ausgangsstand die Richtungsannahme am Setzen der nächsten Richtung und Feuer am Eintritt in den Projektilkonstruktor. Die Live-Messung verwendet nach dem Umbau eigene Zeitmarken am Annahme- und Anwendungspunkt.

| Ausgangsstand | 1P | 2P | Last |
| --- | ---: | ---: | ---: |
| p95 Event → Richtungsannahme | 0,029 ms | 0,051 ms | 0,062 ms |
| p95 Event → Feuergate | 0,050 ms | 0,095 ms | 0,058 ms |
| p95 Arbeit pro Frame | 4,96 ms | 5,66 ms | 8,14 ms |
| p95 Abstand zwischen Ausgaben | 17,75 ms | 17,92 ms | 18,89 ms |
| Abstände über 33,3 ms | 0 | 0 | 1 |

Die Richtungsprobe hat 30, 60 und 60 Stichproben, die Feuerprobe wegen des Cooldowns 3, 6 und 6. Die Lastprobe erreichte im längsten Frame 57,00 ms Rechenzeit und 65,54 ms Abstand zur vorigen Ausgabe. Rechenzeit und Abstand zwischen Ausgaben müssen getrennt beurteilt werden, weil der Abstand auch das Warten im Frame-Takt enthält.

## Sichere Reihenfolge für weitere Auslagerungen

1. **Darstellung und Ausgabe.** Zeichenfunktionen auf einem bereitgestellten Surface halten, doppelte Präsentation beseitigen und Menü-Events außerhalb der Zeichenfunktionen verarbeiten. Einen Test für genau eine Ausgabe pro regulärem Frame und die Offscreen-Prüfungen erhalten. Erst danach die Spielwelt, den HUD und die Debug-Overlays in ein Render-Modul verschieben.
2. **Rasterbewegung.** Einen Rasterzug mit alter Zelle, neuer Zelle, Richtung und Grund für einen Sprung beschreiben. Normalen Zug, Randwechsel, Portal und Respawn getrennt absichern, damit die Darstellung keinen falschen Zwischenstand an die Kollision weitergibt.
3. **Kollisionen und Lebensverlust.** Körper und freiziehende Schwanzfelder pro Spieler einheitlich prüfen und Item-Aufnahme im selben Zug berücksichtigen. Eine Strukturkollision und das Aufbrauchen von HP als unterschiedliche Auslöser testen. Noch zu entscheiden ist, ob beide Spieler beim gleichzeitigen Einfahren in dieselbe Zelle verlieren und ob sie sich gegenseitig durchqueren dürfen. Beide Fälle lassen sich in 2P mit vorgegebenen Köpfen, Richtungen und einem einzelnen Rasterzug reproduzieren.
4. **Boss und Projektile.** Konfigurationswerte, Sprites und Effekte von der Trefferauflösung trennen. Vor dem Verschieben die Aufrufer in Admin-Menü, Simulator und Portalpfad sowie die Trefferreihenfolge absichern. Boss-Schaden, Projektil-Lebensdauer und Effekte jeweils an einer Stelle pro Spielschritt aktualisieren. Die Verteilung der Zuständigkeiten soll die gemessenen Lastspitzen nachprüfbar machen.
