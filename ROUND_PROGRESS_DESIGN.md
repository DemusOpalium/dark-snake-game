# DARK SNAKE · Rundenchronik – Fundament V1

**Stand:** 18.11.2026 · **Status:** PR zur Prüfung; noch **keine** Ränge oder Skin-Freischaltungen.

## Verbindliche Datenbasis

Jede echte **Classic-Runde** bekommt unmittelbar nach `start_game(1|2)` eine neue UUID4 (`round_id`). Erst nach **finalem** Lebensverlust erfasst das Spiel eine abgeschlossene Runde. Ein einzelner Lebensverlust oder ein Respawn ist **keine neue Runde**. Vom World-Studio-Test/Headless-Entwicklertest geht standardmäßig **kein Eintrag** in die echte Karriere ein.

Bereits im Gameplay bestätigte Werte:

| JSON-Feld | Ereignis im aktuellen Spiel |
|---|---|
| `score`, `level` | bestehende Punktzahl / erreichtes Level |
| `enemies_defeated` | `round_enemies_defeated` – bestätigte Kills |
| `bosses_defeated` | `round_bosses_defeated` – `damage_boss()` nach HP=0 |
| `items_collected` | `round_items_collected` – tatsächliche Aufnahme |
| `lives_lost` | `round_death_count` – echte Todes-/Respawn-Ereignisse |
| `finished_reason` | `life_depleted` bzw. `self_stall` |
| `players` | 1 oder 2; im 2P-Classic gelten gemeinsame Leben |
| `started_at`, `finished_at` | UTC-Zeitstempel; **keine aktive Spielzeit** |

Die UTC-Zeitstempel **sind keine pausenkorrigierte Spielzeit**. Spielzeit-Erfolge erst hinzufügen, wenn eine echte, getestete Aktivzeitmessung integriert ist. Einzelne Boss-IDs, tägliche Serien, Truhen, AoE-Ketten und spezifische Trefferursachen können aktuell **nicht** als vorhandene bestätigte Werte ausgegeben werden.

## Ablage und Integrität

- Datei: `~/.dark-snake/round_progress.json` (Windows: Heimatverzeichnis unter `.dark-snake`), getrennt von `settings.json` und der `name,score`-Bestenliste.
- Struktur: `schema_version: 1`, append-only `rounds` mit `round_id`, sowie aus echten Runden berechnete `totals`.
- Abschluss: Einmalige Speicherung **nur bei Game Over**, über temporäre Datei im selben Ordner, `fsync` und `os.replace`. Kein Dateizugriff pro Frame.
- Replay-Schutz: dieselbe UUID4 mit identischem Abschluss ist ein No-Op. Dieselbe ID mit geänderten Werten wird **abgewiesen**.
- Ungültige/ältere/neuere unbekannte Versionen und widersprüchliche Summen werden **nicht ungefragt überschrieben**. Fehler im lokalen Ereignislog und `game.round_progress_error` erkennbar.
- Zwei gleichzeitig gestartete EXEs erhalten über eine **Betriebssystem-Dateisperre** auf `.lock` einen exklusiven Abschnitt für Lesen → Prüfen → Schreiben. Die Sperre wird nach einem Prozessabsturz vom Betriebssystem freigegeben; die kleine Sperrdatei bleibt absichtlich bestehen. Gleichzeitige Game-Over-Abschlüsse verlieren so keine Rundeneinträge. **Lokale JSON-Daten sind dennoch kein manipulationssicherer Online-Nachweis**.
- Der Bestand wird **nicht rückwirkend** aus alten Highscores erraten oder nachträglich vergütet. Ein Absturz vor Game Over ist kein bestätigter Abschluss.

## Vertrag für die nächsten kleinen PRs

**B · 40 Karriere-Ränge:** eigener dauerhafter XP-Wert und versionierte Rangschwellen; XP nur aus überprüften Spielwerten und einem *einmalig* bewerteten `round_id`. Spiellevel ≠ Karriere-Rang.

**C · Freischaltbare Skins:** der bestehende `skins_catalog.json` und die weiteren Legacy-Heads/Bodies bekommen stabile IDs. Startauswahl frei; Rest zunächst gesperrt. P1/P2 behalten bisher gespeicherte Outfits (Migration/Bestandsschutz). Kein Gameplay-Stat über ein Skin ohne eigene explizite Regel.

**D · Abschluss-UI:** Dark Abyss zeigt Rundensummen, Karriererang, neue Freischaltung und ggf. „heute nichts Neues“. Der bisherige Highscore-Name/Score und die Todesanimation bleiben unbeschädigt.

**E · Erfolge und Truhen:** eindeutige IDs je Boss/Truhe/Ereignis, getrennte Trigger und Prämien. **Maximal ein neues kosmetisches Element pro abgeschlossener Runde**; mehrere erfüllte Erfolge können im Journal bis zur Vergabe vorgemerkt werden. Seltenheit/Zufall erst nach Tests mit reproduzierbarer Auswahl.

**Wichtig:** In diesem PR gibt es noch **keine** XP-, Rang-, Titel- oder Skin-Vergabe. Selbst bei Score 10.000 wird nur der tatsächlich gespielte Durchlauf gespeichert. Keine automatischen Änderungen an 1P/2P-Balance, Kollisionen, Menü oder Renderpfad.

## Abnahme

- Unit/Integration: UUID, Zähler aus 1P/2P, normale Tode vs. Game Over, Stillstandstod, Mehrfachabschluss, gleichzeitige Schreibversuche, kaputte/fremde Datei, fehlgeschlagener atomarer Ersatz und Headless-Isolation.
- CI: `compileall`, `pytest -q`, Windows Alpha 2 und CodeQL.
- Manuell Windows: 1P-/2P-Game-Over, anschließend Datei im Benutzerverzeichnis und Top-10-Bestenliste getrennt prüfen. **NOT RUN** bis Demus dies bestätigt.
