# 🧪 DARK SNAKE – Qualitäts- und Performanceplan
**Erstellt:** 15.11.2026 · **Verifizierte Codebasis:** `main` `de66d0676d3b` (nach PR #173).  
**Offener Entwurf:** PR #174 (World Studio Layer Explorer und sieben zusätzliche UI-Bilder) – Stand dieser Bestandsaufnahme **nicht gemergt**.

> Dies ist das **Mess- und Prüfprotokoll** zur [zentralen Roadmap](ROADMAP.md), **keine zweite Aufgabenliste**. Alle Spielziele, Entwicklungsphasen und Prioritäten werden in der Roadmap gepflegt. Werte werden **erst nach Messung** als bestanden markiert.

## 1 · Bereits vorhanden und überprüfbar

| Funktion / Bereich | Stand im Repository | Was noch fehlt |
| --- | --- | --- |
| Performanceinstrumentierung | `Dark_Snake/modules/frame_metrics.py`: getrennte Events, Update, Draw, Present, Bildabstand, Eingabeannahme, Rasterwartezeit und Event→Bild mit Median/p95/Max; Zähler für Bildabstände >33,3 ms. | Dauerhaftes, vergleichbares Windows-Referenzprotokoll und Alertschwellen. |
| Wiederholbarer Benchmark | `scripts/benchmark_game.py`: 1P, 2P, `load` (Boss + 12 Effekte + 24 Projektile), feste Seeds, Warmup, JSON-Ausgabe, optional `--uncapped` und `--overlay`. | Nach jedem relevanten PR mit **gleichem Testsystem** vorher/nachher ausführen, Diff und Interpretation dokumentieren. |
| Basis-Qualitätstests | `tests/test_frame_metrics.py`, `tests/test_smoke.py`, Simulatorprüfungen, Python-Tests im Windows-CI. | Spielnahe Szenarien, die Fehlverhalten **und** Messregressionen sichtbar machen, erweitern. |
| Windows-Auslieferung | `.github/workflows/python-app.yml`: Compile, pytest, FrostAge-Katalogprüfung, PyInstaller-EXE, Archiv und SHA-256. | Bildqualität, Eingabegefühl, tatsächliche Frametimes und subjektive Bedienbarkeit im geöffneten Windows-Spiel zusätzlich testen. |
| Assetverwaltung | Runtime unter `Dark_Snake/assets`, Konzeptbilder unter `GamePICs`; nach PR #169 48 aktive Editor-PNGs, 33 Altvorlagen reserviert. | Neue PR-#174-Grafiken erst **nach Merge** als aktive Runtimegrafiken zählen; weitere Assets immer auf sichtbaren Nutzen und Größe prüfen. |

**Wichtig:** Grüne Unit-Tests und CI beweisen **nicht** konstante 60 FPS, geringe Latenz oder einen flüssigen Windows-Build. Bis zur ersten Vergleichsmessung lautet der Leistungsstatus **NICHT GEMESSEN**.

## 2 · Messwerte und Zielkorridor

| Kennzahl | Warum | Ziel / Eskalationsregel (zunächst **vorläufig**, keine vorhandene Messung) |
| --- | --- | --- |
| 60 FPS | Ziel-Takt für die Anzeige | **16,67 ms pro Frame** als Orientierung. Die Render- und Simulationskosten dürfen das Budget im normalen Spiel möglichst nicht überschreiten. |
| Bildabstand p50 / p95 / Maximum | Ruckler und längere Einzelbilder erkennen | In vergleichbaren Windows-Läufen **p95 möglichst ≤16,67 ms**; bildschirm- und vsyncbedingte Abweichungen erklären. |
| Bilder >33,3 ms | Sichtbare Frame-Spikes | Ziel langfristig **≤1 %** der Messbilder, idealerweise 0; **nicht** ohne Windows-Baseline als CI-Fehlschlag definieren. |
| Events → Annahme p95 | Echte Programmlatenz der Eingabeverarbeitung | **≤5 ms als zu prüfender Entwicklungsrichtwert**; Gerät und Betriebssystem sind nicht Teil der internen Messung. |
| Richtung: Annahme → Rasterzug → Bild | Rasterbewegung von Eingabe-Lag trennen | Getrennt messen. **Nicht** „Event→Bild ≤16 ms“ fordern, wenn ein geplanter Rasterzug erst später stattfindet. |
| Update / Draw / Present p95 | Ursache von Rucklern finden | Phasen getrennt vor/nach Änderung vergleichen; erst danach spezifische Budgets festlegen. |
| 1P / 2P / Boss + viele Projektile / World Studio | Unterschiedliche Belastung | Jeder relevante PR nennt wenigstens die betroffenen Szenarien; kein Gameplay-Szenario durch einen Headless-Test ersetzen. |
| Assets / Start / Zoom | Laderuckler und Grafik-Speicher | Größen, Ladehäufigkeit und Skalierungen protokollieren; nach Möglichkeit nur bei Änderungen am Artworkprofil erneut laden. |

**Vergleichsregel:** Mindestens drei vergleichbare Läufe nach Warmup mit gleichem Rechner, Treibern, Spielversion, SDL/Pygame, Auflösung, Overlaystatus, Seed, Szenario und Framezahl. Regressionsverdacht: p95/Median reproduzierbar mehr als etwa **10 %** schlechter bei unveränderter Last. **Nicht** automatisch sperren, sondern Ursache erklären, Messung wiederholen und gegebenenfalls eigenes Performance-Fix-Ticket erstellen. Die Prozentgrenze ist **ein Review-Auslöser**, kein universelles Erfolgsversprechen.

## 3 · Konkreter reproduzierbarer Benchmark

Aus dem Repository-Root:

```bash
python -m compileall -q Dark_Snake tests
python -m pytest -q
python scripts/benchmark_game.py --frames 1200 --warmup 120 --seed 16000 --uncapped
python scripts/benchmark_game.py --frames 1200 --warmup 120 --seed 16000 --overlay
```

- `--uncapped` misst eher **Arbeitskosten ohne 60-FPS-Drosselung**, kein realistisches Display-FPS-Erlebnis.
- Ohne `--uncapped` sind OS-Scheduling, `Clock.tick(60)` und Dummy-SDL beteiligt. **Auch das ersetzt keinen echten Windows-Bildschirmtest.**
- Die **bereits implementierten** Szenarien heißen **1p, 2p und load**. Editor-Zoom, Dachmaske und große Assetbibliotheken werden mit dem bestehenden Skript **noch nicht vollständig** abgedeckt; dafür sind zusätzliche Messungen nötig.
- Optional vor/nach jeder größeren Änderung JSON-Ergebnisse als PR-Anhang ablegen, mitsamt Commit-SHA, Auflösung, Gerät, Datum und Testkommando. Nicht große temporäre Benchmark-Dateien in Git einchecken, wenn ein PR-Artefakt ausreicht.
- Zurzeit wurden für diesen Dokumentations-PR **keine neuen Frametimes gemessen**. **Keinen „grünen Performance-Status“ ohne Daten behaupten.**

## 4 · Manuelle Windows-Spielprobe: ausfüllen, nicht raten

| Szenario | Eingaben / Bildschirmlage | Beobachtung | p95 / Spitzen | Ergebnis |
| --- | --- | --- | --- | --- |
| Classic 1P | Richtungswechsel, Schuss, normaler Gegner- und Item-Spawn | *Noch nicht gemessen* | – | ⬜ |
| Classic 2P | Zwei verschiedene Controller-/Tastaturprofile, gleichzeitig schießen | *Noch nicht gemessen* | – | ⬜ |
| Boss / Frost / Stress | Hohe Projektilzahl, mehrere AoE, Dach-/Frosteffekte wo anwendbar | *Noch nicht gemessen* | – | ⬜ |
| World Studio 900×620 | Bilderbuttons, Seitenteile, Scrollen, Layerwechsel, Undo/Redo | *Noch nicht gemessen* | – | ⬜ |
| World Studio 1350×930 | Tile-Palette, Zoom, Pan, Roof-Sichtmaske, Test 1P/2P | *Noch nicht gemessen* | – | ⬜ |
| Fenster maximiert | Resize, Tooltips, Wechsel zurück zu Classic, UI-Hitboxen | *Noch nicht gemessen* | – | ⬜ |
| Neues Grafikpaket | Start, Katalogauswahl, erstes Laden, mehrfacher Wechsel, EXE-Größe | *Noch nicht gemessen* | – | ⬜ |

**Pro Zeile angeben:** `PASS / FAIL / NOT RUN`, EXE-Build/SHA, Windows und GPU, Bildschirmauflösung, FPS/Bildabstand, auffällige Ruckler, reproduzierbare Schritte. Nicht getestete Sachen ausdrücklich als **NOT RUN** führen. Einmalige Lade-Ruckler von dauerhaften Frame-Spikes unterscheiden.

## 5 · Performance-Regeln für jede Gameplay-/Grafikänderung

1. **Erst Profiling, dann Optimierung:** Kein Umbau allein aufgrund der Vermutung, dass Python „zu langsam“ sei.
2. PNGs, Sound und Katalogdaten **nicht in der Frame-Schleife neu einlesen**. `convert_alpha()` nach dem Laden; passende skalierte Versionen cachen, Cache begrenzen.
3. Große Karten- und Hintergrundbilder **bei Änderung/Zoomstufe** neu skalieren, nicht bei jedem Draw. Dirty-Region-/Cache-Strategien nach messbarem Bedarf.
4. Deckende Hintergrundebene, Ground, Objects, Collision-/Effects-Overlay, Roof, Fog und HUD in definierter Reihenfolge rendern. Versteckte Ebenen möglichst nicht zeichnen; Spielregeln davon nicht abhängig machen.
5. Boss-/AoE-/Projektilzahlen unter repräsentativer Last prüfen. Doppelte Updates/Zeichenaufrufe vermeiden, aber Kollisionen und Schaden nicht wegoptimieren.
6. Eingabeannahme **zeitnah** behandeln, Rasterkadenz separat. Keine Simulationstakte verkürzen, um einen Grafik-Lag zu verstecken.
7. Mit gleicher Testsequenz, identischen Settings und reproduzierbarem Seed vor/nachher vergleichen. Änderungen der VSync-/SDL-Optionen und der Zielhardware dokumentieren.
8. Assets nur dann in die Windows-EXE übernehmen, wenn sie wirklich benötigt werden. Staging-/Artwork-Dateien unter `GamePICs` belassen.
9. Jede bedeutende Funktion verlangt: korrekte Spielregel, aussagekräftigen Negativtest, sichtbare Bedienprobe, Messvergleich und separaten Change-Log-Eintrag.

## 6 · Entwickler-Simulator: bessere Aussagekraft

Die automatische Simulation soll **erwartetes vs. tatsächliches Verhalten** prüfen, nicht nur `0 Exceptions` melden. Dazu gehören zunächst:
- 1P/2P-Richtungswechsel, Selbstkollision, Wand/Barrier und freie Durchfahrt.
- Gegner-/Item-Spawn bei belegtem Feld, Cooldowns, Bossphasen, Schaden/Slow/Frost, Projektil-Doppeltreffer.
- Roof-Sichtfenster mit 1P/2P, Grafik→Kollision getrennt, Locks/Solo-Ansicht und Undo/Redo in World Studio.
- Wiederholbare Seeds, aussagekräftige Fehler mit Soll/Ist, Fehlerszenario und Screenshot/Log nach Möglichkeit.
- Entwicklerbericht: **Pass / Fail / Not Run**, Commit-SHA, Zeitstempel, Testname, Windows-Build und reproduzierbare Schritte. Berichte bevorzugt im **entpackten Spielordner**, falls beschreibbar, sonst über bekannten Benutzerdatenpfad; keine Berechtigungstricks.

Zukünftig für Timing **auch** Frame- und Eingabestatistiken im Bericht verfügbar machen, falls Messung aktiviert ist. Das ist **noch nicht umgesetzt**.

## 7 · Classic-Tiles: spätere Qualitätsrunde, ohne jetzt Altlevel zu zerstören

**Ausgangslage:** Es gibt eine Bibliothek mit **495 Classic-Tiles**. Demus berichtet, dass viele davon schwer zu kombinieren, uneinheitlich oder grafisch nicht mehr zeitgemäß sind. Das ist eine **gestalterische Prüfung**, kein heute bestätigter Laufzeitfehler.

**Ziel für späteren eigenen PR:** Eine kleinere, klar strukturierte **empfohlene** Palette mit guten Übergängen und gutem Kachelverhalten. Die vollständigen Legacy-Assets bleiben zunächst in einer **erweiterten/Legacy-Ansicht** erreichbar.

Prüfschritte:
1. Kacheln visuell sichten: Nahtlosigkeit (oben/unten/links/rechts), Skalierung, Lesbarkeit und gemeinsame Themes.
2. Pro Tile stabile ID, Quelle, Dimension, Alpha, mögliche Nachbarn und Nutzungsstatus dokumentieren; Lieblings-/Standard-/Legacy-Status anbieten.
3. Nicht passende Varianten zunächst **aus der Standardpalette ausblenden**, nicht löschen. Eine Beispielkarte aus empfohlenen Tiles zum realen Vergleich gestalten.
4. Alte Level-JSONs, Tile-IDs, Classic-Spielkarten und gespeicherte Entwürfe weiter öffnen können. Kein automatisches Umnummerieren von Bildern.
5. Alte Referenzen und reale Abhängigkeiten vor jeder eventuellen späteren Löschung prüfen; nur mit eigenem Migrationsplan und Tests.
6. Vorher/nachher Ladezeit, Scrollgeschwindigkeit, belegten RAM und EXE-Zuwachs messen. Weniger sichtbare Kacheln allein garantiert keine Performanceverbesserung.

**Priorität:** bewusst **späterer Feinschliff**, nicht in PR #174 und nicht vor den wichtigen Gameplay-/Editorfunktionen.

## 8 · Was wann abgeschlossen ist

| Arbeitspaket | Voraussetzung / Abnahme | Stand am 15.11.2026 |
| --- | --- | --- |
| PR #174 Layer Explorer + sieben UI-Grafiken | CI, Test der Locks/Solo und Windows-Grafikprüfung, danach Merge | 🔧 Draft offen, nicht in `main` |
| Performance-Referenz erfassen | Gleiche 1P/2P/`load`-Tests + echte Windows-Tests mit dokumentierten Messwerten | ⬜ |
| DE/EN, Hilfe, sichtbares Fenster-Vollbild | Vollständige Tooltip-Übersetzung, UI-Klicks, gespeicherte Sprache, Resize | ⬜ |
| World Backgrounds | Dauerhafte Landschaft unter Tiles, gespeicherte Levelreferenz, Zoom, EXE-Bundle, Legacy-Leser | ⬜ |
| Interaktive Objekte | Truhe/Falle/Tor als Datenprofile, getrennt von zufälligen Spawns; sichere Zustandsübergänge | ⬜ |
| Trigger / Events | Kette Druckplatte→Tor→Spezialspawn→Truhe, im Spieltest reproduzierbar | ⬜ |
| Spezial-Projektile / AoE | Frostburst, Tornado, Effekte, Richtungsbilder, getrennte Hit-Intervalle | ⬜ |
| Legacy-Tile-Kuration | Gute Default-Palette bei weiterhin lesbaren Altlevels | ⬜ (später) |

**Keine** Aufgabe als ✅ markieren, nur weil ein PNG vorhanden, ein PR offen oder ein CI-Test grün ist.
