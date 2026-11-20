# Irians Auge – Forschungsnotizen und technische Wissensbasis
**Stand: 20.11.2026.** Quelle: offizielles Fachmaterial, ergänzt durch
tatsächliche Dark-Snake-Codepfade und den ersten DEV+-Praxistest
`dev-round-fcd40ff2d84947a9a7fd87e6d2b21156.json`.
Dieses Dokument beschreibt Anforderungen und Grenzen, keine Abnahme.

## Was die Recherche für uns bedeutet
1. **Event-Katalog und Kontext:** OpenGameData und OpenTelemetry empfehlen
   klar definierte, zeitgestempelte Ereignisse statt unstrukturierter
   Debug-Strings. Eine Sitzung hat `session_id`, eine Classic-Runde
   `round_id`, jeder Bosskampf `boss_id` (später), jeder Eintrag
   einen Ereignistyp und ein Kontext-Objekt. Quelle:
   https://opengamedata-doc.readthedocs.io/en/latest/appendices/event_standard/index.html
   https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/events.md
2. **Sinnvolle statt laute Daten:** GameAnalytics unterscheidet
   Progression/Resource/Design Events und empfiehlt bei häufigen Events
   Aggregation. Für Dark Snake: HP-Änderungen unmittelbar und ursächlich
   protokollieren; Positionen alle 250 ms; keine Bewegung/Controller-Achse
   als Event pro Frame und keine Netzwerktelemetrie. Quellen:
   https://docs.gameanalytics.com/events-metrics-and-filtering/event-types/design-events/
   https://docs.gameanalytics.com/event-tracking-and-integrations/data-retention-and-limits/event-tracking-and-cardinality-limits/
3. **Sichere Persistenz:** Eigene `IriansAuge/`-Dateien mit
   `NamedTemporaryFile`, Flush, `os.fsync`, `os.replace`
   im selben Verzeichnis. Ein Erfolgsindikator darf erst nach
   erfolgreichem Schreiben erscheinen. Schreibfehler bleiben lokal
   sichtbar, dürfen keine Spielstände verändern. Quelle:
   https://docs.python.org/3.12/library/os.html
4. **Pygame-Eingaben:** `pygame.event.get()` muss weiterhin regelmäßig
   abgearbeitet werden; der DEV+-Button darf weder hinter anderen
   Dialogen Klicks empfangen noch Steuerungsereignisse verschlucken.
   Quelle: https://www.pygame.org/docs/ref/event.html
5. **Fehler-Breadcrumbs statt Tastenspionage:** Navigation,
   Asset-Ladefehler, Zustandswechsel, sichere benannte Aktionen,
   letzter Fehler (Kategorie/Codepfad). Keine gedrückten Texttasten,
   kompletten Dateipfade, Benutzernamen, rohen Eingabedaten oder
   automatischen Uploads. Siehe OpenGameData-Events und das allgemeine
   Breadcrumb-Konzept in Error Monitoring.

## Bestehender Code (aus echtem Repository)
- `Dark_Snake/modules/dev_recorder.py`: opt-in, lokale Rundendaten,
  atomare JSON-/HTML-Checkpoints. **Bei Game Over bereits gespeichert**,
  und nach jeder bestätigten Feedbackantwort erneut geschrieben.
- `Dark_Snake/modules/game.py`:
  `start_game`, `start_boss_fight`, `handle_death`,
  `handle_self_collision`, `_begin_respawn`, `save_settings`,
  `set_state`, `_open_level_editor`, `handle_events`.
  Diese sind die sinnvollen, zentralen Beobachtungspunkte.
- `Dark_Snake/modules/dev_analysis.py`: bisherige HTML-/SVG-Karte,
  Probleme bei Kampfzeit mit Feedback-Pausen und offenem Boss erkannt.
- `Dark_Snake/modules/dev_feedback_ui.py`: freiwillige Ratings.
  Im alten Build wurden Notizen bereits nach 180 Zeichen gekürzt.
- `Dark_Snake/modules/resources.py::developer_report_directories`:
  portable Windows- und Benutzerprofil-Fallback-Verzeichnisse.

## Beobachtungsschema (vorgeschlagen/umgesetzt in PR D/E)
**Zwei verknüpfte, lokale Ebenen:**
1. `dev-round-<round_id>.json/.html`: Boss/Items/HP/Zeit, individuelle
   Bewertungen, 250-ms-Aufenthaltsproben, unverändert lesbar.
2. `dev-session-<session_id>.json`: Hauptmenü/Optionen/Controls/
   World Studio, Marker, Fehlermeldungen, Session-Zeitleiste und
   `round_id`-Referenzen. Keine Duplikation aller Bosspositionsdaten.
   Mehrere Runden pro Sitzung möglich.

**HP und Leben:** `vitals_snapshot` (Rundenstart, Bossstart, Ende),
`vitals_change` (P1/P2 HP vorher/nachher, Quelle, gemeinsame Leben
vorher/nachher). `respawn` ist Wiederherstellung, kein zufälliges
Heil-Item. Bei fehlenden Ereignissen steht `unattributed`/unbekannt,
nicht eine erfundene Schadensursache.

**Wahrheit vor Bewertung:** `life_depleted` ist nur ein technisches
Rundenergebnis; ob ein Spieler freiwillig den Test abbrach, kann nur
ein bewusst angegebener `tester_intent` erklären. Eine Folge aus
wenig HP und kurzem Bosskampf beweist kein schlechtes Boss-Balancing.

**Zeit:** Separat `wall_elapsed_ms`, `active_fight_ms` und
`feedback_pause`; letzte Fight-Zeit spätestens am `round_finished`,
niemals am letzten GameOver-Kommentar beenden.

## Speicher-Semantik und UI
- `DEV+ AN` startet eine Sitzung; **nur freiwillig**.
- Sobald relevante Daten vorliegen: Button **SPEICHERN** im Hauptmenü.
  Der Button führt einen zusätzlichen manuellen Checkpoint aus.
  DEV+ bleibt aktiv; weitere Optionen-/Spielrundenaktivität wird
  angehängt. Grün **GESPEICHERT** nur bei erfolgreichem Flush.
- Auto-Checkpoints bei Boss-Start/-Ende, Game Over und Feedback;
  Session-Zwischensicherung an relevanten Übergängen sowie zeitgesteuert
  (nicht pro Frame). Bei normalem Quit best effort flush.
- Ein- und Aus-Schalten während einer suspendierten Runde verweigern.
  Rundenhistorie/Karriere/Skin-Inventar sind vollständig unabhängig.
- Aufbewahrung begrenzen, Fehlerausgabe sichtbar halten; Dateien dürfen
  niemals nach GitHub hochgeladen oder automatisch versendet werden.

## Prüfmatrix vor Merge
1P+2P, P1/P2 HP unabhängig / gemeinsame Leben, Heilung/DoT/Flame,
Boss-Eintritt mit 1 Leben, Self-Stall, mehrfaches Respawn,
Pause/Feedback-Timer, abgebrochener Boss, 0=Bewertung vs Skip,
Kommentar >180 Zeichen, Fenstergröße, Einstellungen, Controls,
Editor, F9-Marker, Speicherbutton bei Erfolg/Fehlschlag,
read-only Ordner, mehrere Runden, Quit/Crash-Fallback.
**Kein Auto-Merge; manuelle Windows-Abnahme erforderlich.**
