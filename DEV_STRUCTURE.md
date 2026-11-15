# 📦 DARK SNAKE – Entwicklerstruktur und Code-Navigation
**Standprüfung:** 15.11.2026 · `main` nach PR #173. **PR #174 ist ein separater, noch offener Draft** – nicht als Releasebestand zählen.

> Das ist eine **Orientierung zu vorhandenen Pfaden**, keine vollständig automatisch erzeugte Baumansicht. Bei Änderungen immer aktuellen Code und Tests lesen; die Quellcode-Navigation ersetzt weder [Roadmap](ROADMAP.md) noch [Asset-Legende](ASSET_GUIDE.md).

## Projektbaum und Zuständigkeiten

```text
dark-snake-game/
├─ Dark_Snake/
│  ├─ main.py                         # Python-Einstieg / Windows-EXE-Einstieg
│  ├─ config.py                       # Fenster, Raster, Takt, Basiswerte
│  ├─ developer_simulator.py          # Spielsimulation
│  ├─ modules/
│  │  ├─ game.py                      # Spielablauf, Zustände, Item- und Gegnerlogik
│  │  ├─ input_manager.py             # Tastatur, Controller, Belegungen
│  │  ├─ frame_metrics.py             # Performance- und Latenzmessung
│  │  ├─ resources.py                 # Laufzeit-Pfade und Benutzerdaten
│  │  ├─ graphics.py                  # Spielegrafiken
│  │  ├─ level_editor.py              # World Studio Hauptsteuerung
│  │  ├─ editor_layout.py             # Editorfenster / Kartenkamera
│  │  ├─ editor_sidebar.py            # Eigenschaften / Ebenen / Zellen
│  │  ├─ editor_buttons.py            # UI-PNGs / stabile Action-IDs / Cache
│  │  ├─ level_drafts.py              # JSON-Level-Format, Lesen / Schreiben
│  │  ├─ level_playtest.py            # Isolierter 1P-/2P-Leveltest
│  │  ├─ level_effects.py             # Editor-Effektfelder
│  │  ├─ frostage_assets.py           # FrostAge-Laufzeitkatalog
│  │  ├─ aoe_zones.py                 # AoE-Bausteine
│  │  ├─ simulation_checks.py         # Prüfbare Spielszenarien
│  │  └─ simulation_reports.py        # Entwicklerberichte
│  └─ assets/                          # Eingebundene EXE-Ressourcen
│     └─ graphics/
│        ├─ editor_ui/                # Derzeit 48 aktive PNG-Buttons + catalog.json
│        └─ frostage/                 # 175 FrostAge-PNGs + catalog.json
├─ GamePICs/                           # Konzeptgrafiken, Originale, Uploads
│  ├─ Incoming/Frost_Tiles/           # 175 FrostAge-Original-PNGs
│  ├─ Nachtrag Fehlende Buttons/      # 7 neue Quell-PNGs in PR #173
│  ├─ DarkSnake-NeueHeads/            # 53 Head-Kandidaten
│  ├─ DarkSnake-KörperNeuDesign/      # 15 Body-Kandidaten
│  └─ Build/, Layers/, File/, ...     # 81 ursprüngliche Editor-UI-Vorlagen
├─ scripts/
│  ├─ benchmark_game.py               # Wiederholbarer Performance-Vergleich
│  └─ frostage_catalog.py             # FrostAge-Import / Katalogcheck
├─ tests/                              # Automatisierte Tests / 1P / 2P / UI
├─ .github/workflows/                  # Windows-Build, CodeQL, Releases
├─ ROADMAP.md                          # Ziele / Status / Entwicklungsreihenfolge
├─ QUALITY_PERFORMANCE_PLAN.md         # Messprotokoll und visuelle Abnahme
└─ ASSET_GUIDE.md                      # Grafikstatus, Kataloge, Quellen
```

## Wichtigste Verbindungen

- **Spielstart → Eingabe → Update → Draw:** `main.py → Game → InputManager / Game.update() / Game.draw()`. Das Performance-Overlay `FrameMetrics` misst Ereignisannahme, Rasterwartezeit, Render-/Bildausgabe. Gerät, Monitor und der sichtbare Reaktionsweg außerhalb SDL gehören **nicht** zur internen Messung.
- **World Studio → Karte → Speichern:** `level_editor.py → editor_layout / editor_sidebar / editor_buttons → level_drafts.py`. Level-JSONs mit Grafik, Kollision, Effekten, Objekten und Roof müssen kompatibel bleiben.
- **FrostAge Original → importiert → Katalog → Spiel:** `GamePICs/Incoming/Frost_Tiles → scripts/frostage_catalog.py → Dark_Snake/assets/graphics/frostage/catalog.json → frostage_assets.py`. Ein grafischer Gegner ist **nicht automatisch** ein funktionierender Gegnertyp.
- **Eigenes Bild → Editorbutton:** `GamePICs/* → geprüfte Laufzeitkopie in assets/graphics/editor_ui → catalog.json → editor_buttons.py → UI-Action-ID`. Nicht jede Kunstdatei wird Teil der EXE.
- **Tests und Auslieferung:** `tests/ → .github/workflows/python-app.yml → PyInstaller → Windows ZIP`. Bei einem grauen/guten Testergebnis immer auch den tatsächlichen Anwendungspfad prüfen.

## Performance / Qualität

Technische Ziele und die Pflicht-Messungen stehen im [Qualitätsplan](QUALITY_PERFORMANCE_PLAN.md). Beim Einbau neuer Grafiken, Tilebibliotheken, Hintergründe und Effekte ausschließlich die beeinflusste Strecke messen. Kein „schneller“ ohne reproduzierbaren Vorher-/Nachher-Vergleich.

## Offene Architektur-Grenzen

- Die historische `game.py` enthält weiterhin eng gekoppelte Systeme; neue Mechaniken möglichst in getestete Module/Datenprofile ausgliedern. Keine großflächige Umschreibung ohne Messung und Regressionstests.
- Der neue Layer Explorer wird **in PR #174** bearbeitet. Seine noch nicht gemergten Dateien nicht vorzeitig als `main`-Bestand aufführen.
- Das vorhandene Grafik-/Levelsynchronisationssystem unterscheidet Classic, isolierten Editor-Leveltest und späteren Adventure-Modus. Nicht unbemerkt koppeln.
- Ein optionales **Mikro-Raster** war früher eine Idee. Aktuell bleibt das logische Raster unverändert. Eine spätere reine Zeicheninterpolation darf weder gespeicherte Kollisionen noch Simulatorabläufe verschieben.

**Weitere Informationen:** [Projektstatus und Pläne](ROADMAP.md) · [Performanceprüfungen](QUALITY_PERFORMANCE_PLAN.md) · [Artwork-Legende](ASSET_GUIDE.md) · [Steuerung](CONTROLS.md).
