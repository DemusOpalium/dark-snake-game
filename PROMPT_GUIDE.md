# 🤖 DARK SNAKE – Prompts und Agentenleitfaden

Dieser Leitfaden enthält **Beispiele** für die Zusammenarbeit mit GPT/Codex. Verbindliche Regeln für Codeänderungen stehen in [AGENTS.md](AGENTS.md); technische Architektur und aktuelle Aufgaben in [DEV_STRUCTURE.md](DEV_STRUCTURE.md), [ROADMAP.md](ROADMAP.md) und [GitHub Issues](https://github.com/DemusOpalium/dark-snake-game/issues).

## Gute Fragen an den Code

- „Was macht `Dark_Snake/modules/bolbu_enemy.py` und wo wird das Modul tatsächlich verwendet?“
- „Wie wirken D20-Items auf das Classic-Spiel? Bitte die echten Aufrufpfade nennen.“
- „Welche Komponenten verwenden `level_drafts.py`? Welche Tests schützen das Levelformat?“
- „Zeige für eine vermutete tote Funktion alle Referenzen: Imports, Callbacks, Action-IDs, Tests und PyInstaller.“

## Vorlage für einen kleinen Entwicklungsauftrag

1. **Basis:** aktuellen `main`-SHA und bestehende Issues/PRs prüfen.
2. **Ziel:** genau eine Änderung, erwartetes Verhalten und Nicht-Ziele nennen.
3. **Belege:** konkrete Pfade, Aufrufer und eine reproduzierbare Fehlerprobe.
4. **Umsetzung:** minimale Änderung, bestehende Schnittstellen und Savegames erhalten.
5. **Prüfen:** betroffene Unit-/Regressionstests, vollständiges pytest, Assetcheck und bei Laufzeitänderungen Windows-EXE/1P-/2P-Test.
6. **Ergebnis:** Draft-PR, Testprotokoll, Risiken, kein Auto-Merge.

## Wichtig bei Aufräumaufträgen

**Nicht allein aufgrund eines Suchtreffers löschen.** Pygame-Callbacks, dynamische Importpfade, Asset-Katalog-IDs und UI-Actions können ohne direkte Funktionsaufrufe benutzt werden. Alte Dokumente können historische Messwerte belegen: lieber klar als „historisch“ kennzeichnen, bevor Informationen verloren gehen. Siehe [Wartungs-Issue #184](https://github.com/DemusOpalium/dark-snake-game/issues/184) und [Security-Issue #183](https://github.com/DemusOpalium/dark-snake-game/issues/183).

Weitere Links: [Steuerung](CONTROLS.md) · [Asset-Guide](ASSET_GUIDE.md) · [Windows-Build](WINDOWS_BUILD.md) · [Qualitätsplan](QUALITY_PERFORMANCE_PLAN.md).
