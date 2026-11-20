# 👁️ DARK SNAKE – Irians Auge: Windows-Playtest-Protokoll
**Stand:** 20.11.2026 · **Quelle:** Spielerbeobachtung plus lokal ausgewertete Berichte, Fortschrittsdateien und überprüfte GitHub-Quellstellen. **Art:** Erfahrungs-/Entwicklungswissen; kein automatischer Balancebeschluss.

> Zweck: Nächste Entwickler und KI-Kollegen sollen später rasch erkennen,
> **was tatsächlich beobachtet**, **was bereits korrigiert**, **was nur eine Idee**
> und **was noch nicht getestet** ist.
>
> **Datenschutz:** Dieser öffentliche Bericht enthält bewusst nur abstrahierte
> Kennzahlen und zusammengefasste Bewertungen. **Keine Roh-JSONs, Spieler-
> Kommentare im Wortlaut, Namen, absoluten Windows-Pfade, Session-IDs oder
> persönlichen Spieldaten in GitHub einchecken.** Die vollständigen lokalen
> `dev-round-*.json/.html` und `dev-session-*.json` bleiben beim Tester.

## 1 · Testumfang und Datenlage

| Fenster | Modus | Resultat | DEV+-Details verfügbar? | Befund |
|---|---|---|---|---|
| 20.11. vormittags | Classic 1P | 2.235 Punkte, Level 4; 30 Gegner, 2 Bosse, 38 Items | **Ja:** 602 Events / 1.250 Positionsproben; 0 Verlust | Recorder/HTML/Feedback funktionieren grundsätzlich. Bosszeiten und Spieler-HP-Beginn sollten getrennt interpretiert werden. |
| 20.11. mittags | Classic 2P | 2.265 Punkte, Level 3; 47 Gegner, 2 Bosse, 28 Items | **Ja:** 1.144 Events / 1.206 Positionsproben; 0 Verlust | Session-Recorder und Bewertungen gespeichert. In **diesem alten Build** HP-Snapshot und Analyse defekt; Game-Over-Menü-Crash beim späteren Rendern des F10-Hinweises. |
| 20.11. nach Hotfix | Classic 1P | 1.810 Punkte, Level 3; 29 Gegner, 1 Boss, 29 Items; 816 Karriere-XP | **Nein:** Fortschritts-/Karriere-/Bestenlisten-Dateien liegen vor; neuer detaillierter DEV+-Report **nicht** zur Prüfung vor | Spieler meldet **keinen erneuten Absturz** nach Highscore-Eingabe. Dies bestätigt den 1P-Pfad, **nicht** automatisch alle 2P- oder DEV+-Exportpfade. |

Die Spielerabsicht war **bewusstes Funktionstesten**: Zonen betreten,
Schaden/Heilung beobachten, Menüs öffnen, Bewertungen eingeben, die Runde
ggf. absichtlich beenden. Ein kurzes Bossüberleben ist **kein Beweis für
übermächtigen Boss**. Das Ende `life_depleted` beschreibt lediglich das
technische Ergebnis.

### Zusätzlicher Dateiabgleich (18 gespeicherte Classic-Runden)
- Rundenjournal: **18 Runden**, **33.437 Punkte**, **500 Gegner**,
  **30 Bosse**, **585 Items**, **54 verlorene Leben**; ausgewiesene Totale
  stimmen mit den Einzelrunden überein.
- Karriere: **17.264 XP**, **Rang 8**; einmalige XP-Awards folgen den
  im Journal enthaltenen Runden. Das Skin-Register enthält dieselben
  verarbeiteten Runden. Bei diesem Dateiabgleich keine Dubletten gefunden.
- Bestenliste: neuer 1P-Eintrag nach dem Hotfix tatsächlich vorhanden.
  **Zwei ältere leere Namen** fallen auf; Eingabevalidierung später prüfen,
  historische Einträge nicht ohne Einwilligung verändern.
- `settings.json`: Beispielsweise Snake-/Musik-/Schwierigkeits- und
  Projektileinstellungen vorhanden, Speichern bei früherer DEV+-Sitzung
  als erfolgreich gemeldet.
- Persistente `*.lock`-Dateien: im Code der Journale **absichtlich**
  vorhanden; Sperren werden systemseitig freigegeben. **Nicht löschen.**
- `Level_001.json`: 45×31, absichtlich ohne platzierte Objekte/Grafiken.
  **Nur World-Studio-Knöpfe, Laden und Speichern getestet.**
  **Kein Editor-Speicherfehler nachgewiesen.** World Studio-/Level-Design
  ausdrücklich **nicht** Teil des aktuellen Entwicklungsziels.

## 2 · Technische Befunde und Historie

| Beobachtung | Evidenz / Status | Folge |
|---|---|---|
| Rückkehr von Game Over/Highscore ins Hauptmenü führte zu `AttributeError: pygame.Rect.topcenter`. | Windows-Traceback + Quellstelle `Game._draw_dev_indicator`. **Behoben:** `midtop` in **PR #256**; CI/CodeQL grün; 1P-Praxistest danach ohne Wiederholung. | 2P/F10-Hinweis, Highscore und Button-Reihenfolge weiter regressionsprüfen. |
| 2P-`vitals_snapshot` enthielt `players: {"1":"dict","2":"dict"}`. | Echte lokale 2P-Datei; Rekursionsgrenze im sicheren JSON-Serializer. `analysis_error: 'str' object does not support item assignment`. **Fix in #256**. | **Neue** 1P/2P-Runden mit numerischen Start-HP validieren; in **alten** Dateien sind diese Werte **unbekannt**, nicht rückwirkend rekonstruieren. |
| Wiederholte Heil-Events mit +0,3 HP pro Update, stellenweise **P1 bis 142,8 HP**. | 2P-`vitals_change`, `aoe_hp_effect`; Snapshot deklarierte `max_hp=100`. | **Ungeklärte Semantik**: Overheal gewollt? HUD max? Wertebegrenzung? Nichts ohne Game-Designentscheidung ändern. |
| 2P-Datenvolumen: 1.144 Events, davon 227 separate AoE-HP-Effekte und 286 Vital-Änderungen. | Echte Debug-Datei; **0** verworfene Events/Samples. | Ggf. Heil-Ticks pro Zone zusammenfassen; nicht schon pauschal optimieren, da Schaden/Hilfsdaten sonst verloren gehen könnten. |
| Individuelle UI-Aktionen sind nicht sämtlich aufgezeichnet. | Aktuelle Session sieht Navigation, Options-Speicherung, Editor-Toggle, Boss- und Feedback-Events. | Ergänzende **opt-in Breadcrumbs** für relevante Buttons, Asset-Load-Fehler, UI-Sackgassen und Exceptions erst in einem späteren separaten PR. |
| Manuelle DEV+-Speicherung, F9/F10 und mehrere Runden. | Code/Session-JSON vorhanden, aber nicht alle realen Windows-Pfade manuell geprüft. | Sicherstellen, dass die Anzeige **GESPEICHERT** ausschließlich auf erfolgreichem Flush beruht und weitere Aufzeichnung weiterläuft. |

## 3 · Spielgefühl: Rückmeldungen aus echten Runden
Diese Aussagen sind **Testerurteile und Vorschläge**, keine bewiesenen Fehler.

**1P (2.235 Punkte)**
- Startzone **4/5**: Anzahl der Gegner und AoE-Zonen grundsätzlich in Ordnung.
- Jäger **4/5**: guter Kampf; längere/lesbarere Phasenübergänge,
  dezente Farbwechsel und mehr Bewegungsdynamik erwägenswert.
- Wächter **3/5**: Phase III im Verhältnis zur schnellen Snake
  ggf. zu langsam/zu passiv; Angriffsdruck und Spieler-Speed gemeinsam messen.
- Portal **4/5**. `PROJECTILE_SHOOT` **3/5**, als **„Zu schwach“**
  bewertet – später an realen Schadenswerten überprüfen.

**2P (2.265 Punkte)**
- Startzone **3/5**: `SPEED_REDUCTION`/Slow-Pickup wirkt störend; über
  zeitliches Verschwinden, alternatives Auftreten und Itemvielfalt nachdenken.
- Jäger **3/5**: im 2P möglicherweise zu schnell besiegt; Boss-HP und
  erhaltenen Schaden **messen**, bevor 2P-Skalierung erwogen wird.
  Optik bei Bossbeginn/-ende und eigenständiges Boss-Arenadesign gewünscht.
- Wächter **3/5**: deutlicher unterscheidbare Phasen und Visuals;
  Idee für **klar begrenzte** beschworene Gegner/Schutzphasen, nicht
  als bereits freigegebene Mechanik behandeln.
- Portal **4/5**: funktionierend und positiv, mit Ausbaupotenzial.
- Bolbu **3/5**: brauchbarer Gegner, später etwas schärfere Sicht/Verfolgung
  untersuchen, **nicht** vor den aktuellen Boss-Prioritäten.
- `SPEED_REDUCTION` **1/5**, Verdikte: nicht hilfreich, neue Funktion
  gewünscht, nicht kompatibel. Später eigenständiges Item-Balance-Ticket.

## 4 · Priorisierte Arbeitsfolge
1. **Jetzt:** Boss-Entwicklung gemäß
   `BOSS_ROLL_CHARGE_CONCEPT_2026-11-19.md`; Medusa Roll/Charge A
   isoliert umsetzen. Vorher vorhandene Regressionstests/Status prüfen.
2. **Gleichzeitig als Messinstrument erhalten:** Irians Auge mit den
   bereits korrigierten JSON-/UI-Fehlern; für *nächste* Windows-Runden
   vollständige Vital-Snapshots, Bosszeit inkl. Pausen, Ratings und
   F10-Bewusst-Testende prüfen. **Keine ungetestete Masseninstrumentierung.**
3. **Danach:** Bossfähigkeiten/2P-Balance anhand mehrerer vergleichbarer
   **aktiver** Kampfzeiten, HP vor Boss, gemeinsamer Leben, Schadensquellen,
   Spieler-Speed und tatsächlicher subjektiver Bewertung untersuchen.
   Jeder neue Bossmechanismus mit eigenem PR und 1P/2P-Spieltest.
4. **Später:** Slow-Item, Bolbu, UI-Aktions-Breadcrumbs/Asset-Erkennung,
   leere Highscore-Namen und World-Studio-Level-Design.
   **Keinen World-Studio-Bug aus der absichtlich leeren Map ableiten.**

## 5 · Wiederverwendbare Testmatrix
- [ ] Windows 1P + 2P: Start → Boss → Treffer/Heilung → Respawn →
      letzter Tod → Name → zurück ins Hauptmenü **ohne Crash**.
- [ ] **Boss-Eintritts-HP P1/P2 und gemeinsame Leben** sind echte
      numerische Werte; Round-End-Datei enthält keine `analysis_error`.
- [ ] Aufzeichnung zeigt Schaden/Heilung getrennt (bei AoE ggf.
      Aggregation mit präzisem Endwert), kein falsches doppelt gezähltes HP.
- [ ] Feedback-Pause ist nicht Boss-Spielzeit; F10-Testabsicht ändert
      nicht den technischen Game-Over-Grund.
- [ ] DEV+ **AN → SPEICHERN → GESPEICHERT** bei tatsächlichem Flush;
      weitere Runde bleibt in derselben Session; Test von Speicherfehlern.
- [ ] Einzelberichte + Session-JSON referenzieren passende Runden und
      erhalten ältere Dateien (innerhalb definierter Aufbewahrung).
- [ ] Menü/Optionen/Steuerung/Editor nur auf Anwesenheit und Navigation
      prüfen, **keine ungeplante Level-/Editor-Entwicklung**.
- [ ] Medusa Roll/Charge A: 1P/2P, Boss-Pause, Phasen, Teleport,
      Warnrichtung, sichere Trefferhitbox und Recovery.

## 6 · Tracking auf GitHub
- **Boss-Ideen und 1P/2P-Balancing-Hypothesen:** Issue [#257](../../issues/257).
- **Irians Auge / Heilzone / Hotfix-Nachtest / Highscore-Namen:** Issue [#258](../../issues/258).
- **DEV+ Entwicklungsfolge:** PRs #248–#255;
  **Post-GameOver-/HP-Hotfix:** PR [#256](../../pull/256), bereits
  gemergt (CI/CodeQL grün). Neue Release-/Spielabnahme bleibt getrennt
  von CI.
- **Boss-Prototyp-Konzept:** [BOSS_ROLL_CHARGE_CONCEPT_2026-11-19.md](../../BOSS_ROLL_CHARGE_CONCEPT_2026-11-19.md).

Dieses Protokoll wird durch künftige *verifizierte* Runs aktualisiert,
ohne historische Bewertungen als heutige Wahrheiten umzuschreiben.
