# Irians Auge – Developer Mode Plus

## Status (20.11.2026)
**PR A – technisch implementierter Recorder, opt-in; UI/Feedback und Auswertung folgen getrennt in PR B/C.**
Nichts wird ohne ausdrückliche Aktivierung aufgezeichnet. Kein Upload, kein Tracking.
Der normale Classic-Rundenfortschritt und Karriere-Speicher bleiben unverändert.

### Entwicklerschnittstelle / Aufnahme
`Game.dev_recorder.configure(True)` vor `Game.start_game(1|2)`; nach
Rundenbeginn werden Events, Bossphasen, Teleports, Schuss-/Schadensereignisse,
Item-Aufnahmen und alle 250 ms ein begrenztes Positions-/Kampf-Sample
gepuffert. Eigene JSON pro Runde, feste `round_id`, auf Platte
**nur** bei Boss-Spawn/Boss-Ende/Runden-Ende und Feedback-Speicherung.
Berichte lokal unter `Entwicklerberichte/IriansAuge` (portables Windows)
oder `~/.dark-snake/Entwicklerberichte/IriansAuge` gespeichert.
Max. 2 MB pro Bericht, max. 20 Berichte; ältere Daten werden nur in
diesem tool-eigenen Ordner entfernt. Speicher-/Schreibfehler sind nicht fatal.

### Grenzen
Positionsproben sind **keine Pixel-Videoaufzeichnung**; 250-ms-Takt
reicht für Wege/Heatmaps, aber nicht für Frame-genaue Treffer.
Bekannte Ereignisse stammen aus `Game.log_combat_event`, nicht aus
einer neuen Spielphysik. Individuelle Item-Metadaten und spielerische
Bewertungen sind Gegenstand des nächsten PRs; Auswertungen folgen im PR C.
Vor Freigabe: 1P/2P-Windows-Build, harte Vorwarnungen/Phasen,
Boss-Teleport, Berichtspfad und Game Over prüfen.

## PR B – Freiwilliges Spielerfeedback (DEV+)
- Oben rechts im **Hauptmenü** DEV+ AUS/AN oder F8. Standardmäßig
  **AUS**, pro Prozess nicht automatisch gespeichert. Gesperrt bei
  pausierter/suspendierter Runde; kein stilles Opt-in durch bestehende Settings.
- Einmal vor dem **ersten Boss**: Zonen-Spielgefühl. Danach maximal drei
  Boss-Nachbewertungen pro Runde. **Nie bei einzelnen Phasenwechseln.**
- Nach dem Game Over (erst nach der bestehenden Todesanimation): wenn
  relevant, Portal-/Bolbu-/Item-Fragen. Nur tatsächlich erhaltene Items
  auswählen, 0–5 Snake-Heads, Freitext und anklickbare Item-Verdikte
  (hilfreich, nicht hilfreich, zu schwach/stark, inkompatibel, neue Funktion).
  Jede Frage ist überspringbar. Subjektive Daten werden ausdrücklich
  getrennt von technischen Ereignissen gespeichert.
- Bestätigte Bewertungen werden in die **gleiche lokale Runden-JSON**
  atomar geschrieben. Der Recorder kann danach Game-Over-Feedback
  ergänzen, ohne Runden-/Karrieredaten zu verändern.
- Für Items zeichnet DEV+ `item_pickup` sowie `item_applied`
  mit tatsächlichen Vorher/Nachher-Werten (Punkte, XP, Tempo,
  aktive Effekte, Boss-HP) auf. Quellort:
  `Game.handle_item_pickup` + `modules.enums.ItemType`.
- Beim Popup pausieren Updates, Eingaben und Countdown; beim Schließen
  werden die maßgeblichen Spielwelt-Timer um die Unterbrechung
  verschoben. Für diese Freeze-/Resume-Integration ist ein **echter
  Windows-Spieltest erforderlich**, insbesondere 1P/2P, erster
  Boss, Teleport und Game Over.

## PR C – Offline-Auswertung / Bossfight-Map
- Bei Boss-Ende und Game Over werden **event-basierte** Boss-Zeitachsen,
  Phasen, Warnungen, Teleport-Landungen/Abbrüche, Schadenssummen, Item-
  Effekte, Score/XP-Snapshots und die 250-ms-Positionen analysiert.
- Zusätzlich zur Entwickler-JSON entsteht eine **statische lokale HTML-Map**
  mit SVG-Raster/Heatmap (Spieler 1/2, Boss, Sichtblocker), Ereignistabelle,
  expliziten Bewertungen und Code-Wegweisern. **Kein JavaScript,
  Internet, Tracking, CDN oder Upload**.
- Bei Schreibfehlern oder HTML-Fehlern bleiben Spielergebnis und
  Original-JSON maßgeblich. Die Reportdateien im eigenen Verzeichnis
  sind auf maximal 20 abgeschlossene/zwischengespeicherte Runden begrenzt.
- Offline kann die Kartenansicht auch später neu erzeugt werden:
  `python scripts/analyze_dev_report.py PFAD/ZUM/dev-round-xxx.json`.
- Heatmap zeigt **Besuchsproben**, keine vollständigen Einzelbild-
  Bewegungsbahnen. Alle Werte folgen protokollierten Ereignissen,
  keine behaupteten Gefühlsanalysen oder erdachten Boss-Attacken.

## QA und Freigabe
Die PRs sind **gestapelt**: A → B → C. Erst A nach Review,
Windows-/2P-Spieltest und grünem CI mergen, dann B und C jeweils
gegen `main` aktualisieren und getrennt abnehmen. Test mit
1P/2P, erster Boss und zweiter Boss, Phase III Wächter/Rift,
Portal/Itembewertungen, GameOver-Feedback, Berichtskorruption,
schreibgeschütztem Ordner, Menü-Rückkehr, Pausen und
verschiedenen Bildschirmgrößen. Keine automatische Veröffentlichung
von Daten auf GitHub.

## Laufzeitmessung (PR C)
Im DEV+-Modus werden nur während echter laufender Spiel-Frames
die **Abstände lokaler Bildübergaben** gemessen (maximal die letzten
6.000 Intervalle für p50/p95/Maximum, langsame Intervalle >33,3 ms
für die ganze Runde gezählt). UI-Feedback-Standbilder werden nicht
als normale Gameplay-Intervalle gewertet. Diese Werte sind kein
Monitor-Feedback, keine echte Input-Latenz und kein Ersatz für
vergleichbare Windows-Benchmarks nach `QUALITY_PERFORMANCE_PLAN.md`.


## DEV+-Sitzung und manueller Speicherknopf (PR E)
- **Einmal DEV+ AN** startet eine lokale `dev-session-<session_id>.json`.
  Diese Sitzung läuft über Hauptmenü, Optionen, Steuerung, Level Studio
  und beliebig viele Classic-Runden weiter, bis DEV+ AUS oder Quit.
- Im Hauptmenü erscheint **SPEICHERN**, sobald relevante Sitzungsdaten
  gesammelt wurden (z. B. einmal Optionen aufgerufen oder eine Runde
  gespielt). Ein Klick schreibt einen zusätzlichen atomaren Checkpoint,
  **beendet die Sitzung nicht**. **GESPEICHERT** bedeutet, dass die
  Sitzungsdatei geschrieben wurde; **SPEICHERFEHLER** bedeutet, dass
  der Speicherstatus nicht bestätigt werden konnte.
- Session-Zwischensicherung: bei Beginn/Ende jeder Runde, beim Speichern
  von Einstellungen, beim Editor-Aufruf, bei Spielerfeedback, nach F9,
  außerdem alle ca. 90 Sekunden bei Änderungen und best effort beim Quit.
- **F9** setzt einen Entwickler-Marker (Bereich/Level/Boss/Runden-ID),
  ohne rohe Tastatureingaben zu protokollieren.
- **F10** markiert nach einer beendeten Runde freiwillig
  `intentional_test_end`. Der technische Endgrund (`life_depleted`,
  `self_stall`) bleibt unverändert. Im Hauptmenü ist die Funktion
  nach dem ersten abgeschlossenen Run sichtbar.
- Die Sitzungsdatei speichert nur Verweise auf die
  `dev-round-<round_id>.json/.html`-Einzelberichte und eine kleine
  zeitliche Liste von Navigation, Einstellungen (nur geänderte
  **Schlüsselnamen**, keine rohen Eingaben), Editor-Status und Markern.
  **Keine Datei wird hochgeladen.** Die einzelnen Boss-/HP-Daten
  bleiben in den pro-Runde-Dateien; 20 Sitzungen und 20 Rundenberichte
  werden jeweils in eigenen Namensräumen begrenzt.
- Wenn der Datenträger schreibgeschützt oder voll ist, darf eine
  fehlerhafte Sicherung nicht als erfolgreich angezeigt werden und
  DEV+ nicht stillschweigend ausgeschaltet werden.
- Mehr zum Recherchestand, den exakten Quellen und der Testmatrix:
  [Forschungs-/Testkonzept](docs/IRIANS_AUGE_RESEARCH_2026-11-20.md).

**PR D + E sind Entwürfe; ohne Gameplay-Abnahme und Windows-CI nicht mergen.**
