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
