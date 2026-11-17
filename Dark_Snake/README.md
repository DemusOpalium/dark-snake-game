# DARK SNAKE – Spielverzeichnis

> Diese README ersetzt eine historische Anleitung der frühen „Complete Snake Game – Dark Art Edition“. Der frühere Entwicklungsstand bleibt über die Git-Historie nachvollziehbar.

**Aktueller Projektüberblick:** [README auf Deutsch](../README.de.md) · [README in English](../README.md) · [Roadmap](../ROADMAP.md) · [Entwicklerstruktur](../DEV_STRUCTURE.md)

## Quellcode starten

Vom **Repository-Stammverzeichnis** aus (Python 3.12):

```bash
python -m pip install -r requirements.txt
python Dark_Snake/main.py
```

Unter Windows ist auch die separat veröffentlichte, entpackte [Windows-Alpha](https://github.com/DemusOpalium/dark-snake-game/releases) verfügbar. Der letzte fest veröffentlichte Tag muss nicht alle aktuellen Änderungen aus `main` enthalten.

## Hier liegt was?

| Bereich | Funktion |
| --- | --- |
| `main.py` | Initialisierung, Crash-Reporting und Spieleinstieg |
| `config.py` | Raster, Fenstergrößen, Spielkonstanten |
| `modules/game.py` | Classic-Spielablauf, Gegner, Items, Bosskämpfe und Rendering |
| `modules/input_manager.py` / `modules/controls.py` | Tastatur-/Controllerbelegung und Bedienoberfläche |
| `modules/level_editor.py` | World Studio und Editorsteuerung |
| `modules/studio_tutorial.py` | Geführtes FrostAge-Übungslevel |
| `modules/level_drafts.py` / `modules/world_library.py` | Level-JSONs und Weltverwaltung |
| `modules/resources.py` | Ressourcenpfade für Quellcode und PyInstaller |
| `assets/` | Ins Windows-Paket übernommene Laufzeitgrafiken und Audio |

**Hinweis:** `GamePICs/` im Repository-Stamm enthält auch Quell- und Konzeptbilder und wird nicht pauschal in die EXE eingebunden. [Asset-Leitfaden](../ASSET_GUIDE.md).

## Einstellungen und Benutzerdateien

Aktuelle Einstellungen, Eingabebelegungen und Levelentwürfe werden über `modules/resources.py` in einem Benutzerverzeichnis verwaltet, üblicherweise `~/.dark-snake/`. Ältere Dateien wie `settings.txt` und `leaderboard.txt` im Spielverzeichnis sind **nicht automatisch die aktive Benutzerkonfiguration**. Vor einer Löschung Verweise und Migration prüfen.

## Qualität

```bash
python -m compileall -q Dark_Snake tests
python -m pytest -q
python scripts/frostage_catalog.py --check
```

Windows-Build, Hashprüfung und Tests: [Workflow](../.github/workflows/python-app.yml) · [Windows-Anleitung](../WINDOWS_BUILD.md). Bitte neue Funktionen mit 1P-/2P-Proben und Tests absichern.

**Stand:** 17.11.2026, `main` nach World Studio PR E (#180). Kein Ersatz für die aktuelle Roadmap.
