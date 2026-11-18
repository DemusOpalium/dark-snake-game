# DARK SNAKE · Snake Inventory C – Heads & Bodies (Version 1)

**Status (18.11.2026):** PR #211 ist gemergt. Der Projektinhaber
hat die gedimmten Skin-Schlösser und die P1/P2-Vorschau unter Windows
sichtbar geprüft. Drei echte Classic-Runden haben drei eindeutige
Rang-Skin-Vergaben erzeugt. **Nicht getestet:** vollständiger neuer
2P-Durchlauf mit freigeschalteten/gesperrten Skins. Auswertung:
[Spieltest-Baseline](PLAYTEST_BALANCE_2026-11-18.md).

Diese Stufe baut auf
[ROUND_PROGRESS_DESIGN.md](ROUND_PROGRESS_DESIGN.md) und
[CAREER_RANKS_DESIGN.md](CAREER_RANKS_DESIGN.md) auf.

## Grundlage

Das Runtime-Verzeichnis besitzt exakt **72 Heads** und **20 Bodies** (92 PNGs).
Eine einzige versionierte Datei `Dark_Snake/assets/graphics/skin_registry.json`
führt sie mit stabilen, eindeutigen IDs, Typ, Dateinamen und Freischaltgruppe.
**Keine Laufzeitpfade nach `GamePICs`!** Der bestehende provenienzbasierte
`skins_catalog.json` bleibt unangetastet.

| Gruppe | Heads | Bodies | Berechtigung jetzt |
| --- | ---: | ---: | --- |
| Kostenlos (Starter) | 4 | 2 | sofort |
| Karriere-Ränge 2 bis 39 | 30 | 8 | über echte Karriere-XP |
| Achievements | 18 | 5 | reserviert / gesperrt |
| Bosse | 8 | 3 | reserviert / gesperrt |
| Truhen/spätere Inhalte | 12 | 2 | reserviert / gesperrt |
| **Gesamt** | **72** | **20** | **92** |

Rang 2 = erster neuer Head; Rang 3 = erster neuer Body. Weitere 36 Ränge
erhalten jeweils ein kosmetisches Item. Für Rang 40 ist ein künftiger
besonderer Titel/Effekt vorgesehen; keine künstliche Head-Vergabe.
Diese Anfangszuordnung ist ein getesteter technischer Vorschlag. Seltenheits-
und Set-Zuordnungen lassen sich später ausdrücklich im neuen Katalog versionieren.

## Verarbeitung und Sicherheit

- Freischaltquelle sind ausschließlich bereits bestätigte
  `career_progress.json.awards` (selbst aus `round_progress.json` erzeugt).
- **Pro `round_id` maximal ein kosmetisches Item**. Mehrere gleichzeitig
  erreichte Rangstufen bleiben offen und werden jeweils in späteren
  tatsächlich abgeschlossenen Runden ausgegeben. Keine RNG-Überraschungen.
- Stabiler JSON-Bestand `~/.dark-snake/skin_inventory.json`:
  `legacy_unlocked`, `processed_rounds`, `grants`, `unlocked`.
  Jedes Element der Liste `grants` enthält `round_id`, `skin_id`,
  `required_rank`. Die Liste `unlocked` wird aus tatsächlich vorhandenen
  Starter-/Altbestand-/Reward-IDs abgeleitet.
- **Einmalige Bestandsübernahme:** Die bis zum ersten Start gespeicherten
  P1/P2-Kopf- und Körperdateinamen werden als schon besessen markiert.
  Bei späterer manueller Änderung der `settings.json` erzeugt der Bestand
  **keine weiteren Freischaltungen**.
- Seriennummer/Schema-Versionen, doppelte/grants fremder IDs, unmögliche
  Karriere-Ränge und beschädigte Dateien werden zurückgewiesen. Alte Datei
  wird nicht überschrieben. Lokale Offline-JSON-Dateien bieten weiterhin
  **keinen kryptografischen Manipulationsschutz**.
- OS-Dateisperre und atomarer Replace verhindern doppelte Vergaben und
  Datenverlust beim normalen Commit. Wenn Karriere zwar gespeichert,
  Inventar aber nicht gespeichert wurde, erfolgt beim nächsten realen
  Spielstart die **idempotente Nachvergabe** nach der vorhandenen Runden-UUID.
- **Kein Journalzugriff und keine Freischaltprüfung in Gameplay-Updates**;
  nur beim Programmstart und nach finalem Game Over. Für die Bildergalerie
  wird ein im Speicher gehaltener Besitzstand verwendet.

## UI und Rückwärtskompatibilität

- Das bestehende FrostAge-Optionsmenü zeigt gesperrte Kacheln abgedunkelt mit
  Schloss, Rangkennzeichen (`R2` usw.) oder `SPÄTER`. Auswahl darf den
  Status eines Skins zeigen, **zuweisen oder speichern** darf nur Besitzer.
- Bereits zugewiesene alte Skins bleiben im Besitz und für P1/P2 verwendbar.
  Kein Eingriff in die Bilddateien, das neue Preview-Caching, die beiden
  Playervorschauen, Soundregler, Buttons, Top-10-Highscore oder Classic-Regeln.
- Fehlende/kaputte Inventardatei führt nicht zum Überschreiben fremder Daten.
  Bei gültigem Karrierebestand wird die Datei erzeugt bzw. nachgetragen.
  Bei beschädigter Inventardatei werden bis zur Reparatur nur freie Starter
  angeboten, mit Fehlerprotokoll. Eine ungültig bearbeitete `settings.json`
  wird nicht als Berechtigung anerkannt.

## Beispiele aus reproduzierbaren Testdaten

- Runde mit 1.413 XP: Rang 2, **genau ein Head**.
- Nächste Runde mit 1.200 XP: Gesamt 2.613 XP, Rang 3, **genau ein Body**.
- Extremrunde mit vielen Rangaufstiegen: trotzdem **ein** Item. Unbelohnte
  erreichte Ränge bleiben für die kommenden Runden im Pool.
- Wiederholter Finalisierungsaufruf, Neustart, zweite EXE: **keine Duplikate**.

## Abnahme und weitere Pakete

- Tests: ID-/Bildkatalog, alle 92 und Starter-Gruppen, selbstständiger
  1P/2P-Abschluss, Sperren/Save-Guard, P1/P2-Legacy-Migration, Zwischenabsturz,
  parallele Instanzen, idempotente Backlogs, korrupte Dateien, UI bei 900×620 /
  1350×930 und Windows-Bundle-Prüfung.
- Pflicht: `python -m compileall -q Dark_Snake tests`, `python -m pytest -q`,
  Windows Alpha 2 + CodeQL.
- **Manueller Windows-UI-Test: TEILWEISE BESTÄTIGT (18.11.2026).**
  Gesperrte Heads und P1/P2-Vorschauen sichtbar; 1P-Spielrunde und
  drei Rang-Rewards mit lokalem JSON-Abgleich geprüft. Ein gezielter
  2P-Gameplay-/Save-Reload-Test bleibt offen.
- **Nächstes PR D**: Sichtbare XP/Rang-/Belohnungsübersicht im Dark Abyss.
  Der neue Inventarbestand ist bereits maschinenlesbar, jedoch gibt es in C
  noch keine Belohnungszeremonie im Spielende.
- **PR E** erst bei echten, validierten Boss-, Truhen-/Achievement-Events.
