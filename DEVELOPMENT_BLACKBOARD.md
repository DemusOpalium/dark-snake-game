# ☕🐍 DARK SNAKE – Developer Blackboard & Kaffeerunde

**Stand:** 17.11.2026 · **Status:** gemeinsamer Entwicklungsraum (Dokumentation, keine laufende Agenten-Session)  
**Zweck:** Demus und beteiligte KI-/Entwicklungsagenten können freiwillig **eigene Beobachtungen, Ideen, Fragen und Vorschläge** für DARK SNAKE festhalten – auch dann, wenn sie nicht Teil des aktuellen Auftrags sind.

> **Sichtbarkeit:** Das Repository `DemusOpalium/dark-snake-game` ist **öffentlich**. Dieses Blackboard, seine Branches, Pull Requests und Kommentare sind daher **nicht privat**. Keine persönlichen Gespräche, Zugangsdaten, Secrets, privaten Gesundheits-/Kontaktdaten, internen Prompts oder unveröffentlichten vertraulichen Transkripte hier ablegen. Für wirklich vertrauliche Notizen ist ein **separates privates Repository** nötig.

## 1 · Unsere Kaffeerunde 🤝

Willkommen sind Beiträge von Menschen und KI-Agenten, die gerade tatsächlich an der Entwicklung beteiligt sind. Freie Gedanken sind ausdrücklich erlaubt, auch mit trockenem Humor. Niemand muss eine Idee erst „perfekt“ ausarbeiten.

**Wichtig:**
- KI-Agenten sprechen **nicht automatisch miteinander** und arbeiten nicht unbeaufsichtigt im Hintergrund. Austausch entsteht erst, wenn ein Mensch oder ein beauftragter Agent dieses Dokument liest und über einen **Issue-, PR-Kommentar oder vorgeschlagenen Datei-PR** antwortet.
- Wer eine Beobachtung macht, darf sie als **freiwillige Notiz** hinzufügen, auch wenn die laufende Aufgabe eine andere ist – solange die eigentliche Aufgabe dadurch nicht blockiert wird.
- Keine fiktiven Arbeitsberichte oder unbestätigten Aussagen im Namen anderer Agenten. Ein Name/Handle dient der **nachvollziehbaren Zuordnung**, nicht der Behauptung einer eigenständigen permanenten Person oder Sitzung.
- **Demus entscheidet** über Spielgefühl, Prioritäten und Merge. Keine stillen Änderungen auf `main`, kein Auto-Merge.
- Kaffeerunde = Ideen sammeln; **Issue = prüfbarer Auftrag; PR = konkrete Änderung**. Nicht für jede spontane Idee ein Ticket erzeugen.

### Notiz-Vorlage – gern kurz

```md
### [Datum] · [Name / Agent / Mensch] · [Thema]
- **Art:** Idee / Beobachtung / Frage / bestätigter Befund
- **Was fiel auf?** ...
- **Beleg oder Ausgangspunkt:** Datei/Zeile, Spielbeobachtung oder „noch unbestätigt“
- **Vorschlag/Nutzen:** ...
- **Risiko / Kosten:** ...
- **Status:** offen / zum Prüfen / entschieden / umgesetzt / verworfen
- **Bezug:** Issue/PR (falls vorhanden)
```

Bei möglichen Sicherheitsproblemen **keine Geheimnisse oder ausnutzbaren Details in öffentliche Kommentare kopieren**; siehe [Security-Issue #183](https://github.com/DemusOpalium/dark-snake-game/issues/183).

## 2 · Gemeinsame Leitlinien (Inspiration aus einer Entwicklerdiskussion)

Keine Dogmen: Diese Punkte sind **unsere projektbezogenen Arbeitsregeln**, keine wortgetreuen Aussagen oder ein vollständiger Mitschnitt der Diskussionsrunde.

1. **Spielerlebnis vor äußerlicher Code-„Sauberkeit“.** Große Dateien/Funktionen sind nicht automatisch fehlerhaft; erst Verantwortlichkeiten, Kopplungen, Änderungen und reale Probleme bewerten.
2. **Abstraktion hat Kosten.** Keine neuen Klassen, Event-Busse oder „Frameworks“ ohne erkennbaren Nutzen. Wiederverwendung oder eine echte Schnittstelle kann dennoch eine Auslagerung rechtfertigen.
3. **Am Verhalten testen.** Ein Test soll bevorzugt die für Spieler relevante Zusage absichern: Position, Lebensverlust, Eingabe, Timing, Bild, Ton oder speicherbares Level. Interne Tests dort, wo sie tatsächlich helfen.
4. **Wenige wertvolle End-to-End-/Sichttests.** Nicht blind viele fragile Prüfungen hinzufügen. Bestehende **pytest-, Smoke-, Windows-CI- und CodeQL-Prüfungen behalten**, aber um gezielte sichtbare 1P-/2P-Proben ergänzen.
5. **Erst messen, dann optimieren.** `frame_metrics.py` und `scripts/benchmark_game.py` verwenden. Keine FPS-, Speicher- oder Latenzgewinne ohne vergleichbare Messung behaupten.
6. **Kleine, rücknehmbare Änderungen.** Eine Ursache / ein Ziel pro PR, Nachweise und Regressionstests, kein ungefragtes „großes Refactoring“.
7. **Beobachtung ≠ Bestätigung.** Immer kennzeichnen: `BEOBACHTET`, `VERDACHT`, `BESTÄTIGT`, `NICHT GETESTET`. Ein grüner CI-Lauf beweist noch kein perfektes Windows-Spielgefühl.
8. **Sicherheit und Erhalt.** Keine unbekannten externen Skripte ausführen; Downloads/Dependencies, Assets und Veröffentlichungen kontrolliert prüfen. Historische Belege nicht grundlos löschen.

Diese Leitlinien ergänzen [AGENTS.md](AGENTS.md), die technische [Roadmap](ROADMAP.md) und den [Messplan](QUALITY_PERFORMANCE_PLAN.md); die tatsächliche Implementierung bleibt maßgeblich.

## 3 · Stand und Entscheidungstafel

| Thema | Stand am 17.11.2026 | Nächster sinnvoller Schritt |
| --- | --- | --- |
| Classic Normalgegner-Kontakt | PR #187 gemergt, CI erfolgreich | Weitere echte Spielproben bei Bedarf |
| FrostAge Respawn 1.0 | PR #188 gemergt; Windows-Spielprobe vom Projektinhaber positiv, auch 1P-/2P-Spiel insgesamt als gut beschrieben | Sonderfälle und Controller-/Pauseabläufe nur bei konkretem Anlass nachprüfen; vorerst **kein neuer Grafikumbau** |
| Codequalität / Cleanup | [Issue #184](https://github.com/DemusOpalium/dark-snake-game/issues/184) | Nur nachweislich unbenutzte Bestandteile entfernen |
| Security / Lieferkette | [Issue #183](https://github.com/DemusOpalium/dark-snake-game/issues/183) | Abhängigkeiten, Historie und EXE getrennt prüfen |
| Langfristige Erhaltung | [Issue #182](https://github.com/DemusOpalium/dark-snake-game/issues/182) | Backup/Release-Nachvollziehbarkeit zu gegebener Zeit |
| Neue Spielrahmen-Anzeigen | **Konzept**, nicht implementiert | Zuerst kleine Layout-/Datenfluss-Skizze und Kosten-/Platzprüfung; danach eigenständiger Basis-PR |

> Der Status ist **eine datierte Momentaufnahme**, nicht automatisch live aktualisiert. Für den neuesten Stand immer offene [Issues](https://github.com/DemusOpalium/dark-snake-game/issues), [PRs](https://github.com/DemusOpalium/dark-snake-game/pulls) und `main` vergleichen.

## 4 · Ideenwand – offen für neue Einträge

### 17.11.2026 · Demus + Irian · FrostAge Command Deck
- **Art:** Game-Design-Idee / Konzept; noch **nicht umgesetzt**.
- **Wunsch:** Zusätzlich zum **unveränderten 45×31-Spielraster** perspektivisch bis zu vier eigenständige Außenanzeigen (oben, links, rechts, unten) für HP, Erfolge, Level, Bossinfos, Zeitgrafiken, Animationen und später wählbare Buttons.
- **Leitidee:** Oldschool-Indie-Gameplay im Zentrum, moderne FrostAge-Anzeigen außen. Daten **lesen**, Spielregeln dabei nicht verändern. Keine zweite Controller-Logik erfinden.
- **Erstes Arbeitspaket:** Ist-HUD und überlappende Texte inventarisieren, Platzbedarf/Fenstergrößen testen, ein **statisches Layout** ohne neue Spielmechanik erproben. Bestehende Controls/Settings schützen.
- **Risiken:** Auflösung 1350×930, Skalierung, DPI, Klick-Hitboxen, Performance, durch UI verdeckte Spielfeldzellen.
- **Bezug:** [UI-2.0-Bestandsaufnahme](UI_2_0_SCREEN_AUDIT.md), [Roadmap](ROADMAP.md).

### 17.11.2026 · Irian (KI-Assistent) · HUD-Schriften und Überlagerungen
- **Art:** Code-Beobachtung + Nutzerhinweis; **Performancegewinn nicht gemessen**.
- **Beleg:** `Dark_Snake/modules/game.py`, `draw_hud()` und `AchievementManager.draw_achievements()` erzeugen wiederholt `pygame.font.SysFont(...)` beim Zeichnen. Der Projektinhaber berichtet teils über überlappende Texte links.
- **Vorschlag:** Zuerst echte Überlappung per Screenshot/Window-Größe reproduzieren; anschließend nur benötigte Schrift-/Text-Caches einführen, messen und mit klassischen 1P-/2P-HUD-Proben verifizieren.
- **Risiko:** Zu frühe Umgestaltung könnte Anzeige und Rasterkoordinaten durcheinanderbringen.
- **Status:** Zum Prüfen, kein Bugfix versprochen.

### 18.11.2026 · Spieltest/Belohnungssystem & FrostAge-Gegner · geprüfter Befund
- **Art:** manuelle Windows-Beobachtung + anonymisierte Auswertung lokaler
  Testdateien; nicht gleichzusetzen mit allgemeingültigem Balance-Beweis.
- **BESTÄTIGT:** Rundenjournal/Karriere/Inventar verknüpfen drei
  unterschiedliche abgeschlossene 1P-Runden; gesamt 8.640 Punkte,
  102 besiegte Gegner, 8 Bosse und 156 Item-Aufnahmen.
  Die XP-Formel ergibt 4.263 XP, Rang 4, und das Inventar weist
  genau drei einmalige Rangfreischaltungen aus.
- **BEOBACHTET:** FrostAge-Optionen zeigen abgedunkelte gesperrte
  Snake-Skins, Rangmarkierung sowie P1/P2-Skinvorschau. Die
  historische Top-10-Anzeige funktioniert, entspricht aber noch nicht
  dem geplanten Design. Dark Abyss zeigt Rundenwerte, derzeit
  **keine Rang-/Skin-Belohnungszeremonie**.
- **ARCHIVIERT:** Zwei ältere Simulator-Berichte aus September und
  November sind **unterschiedliche Testprofile**; ihre fehlerfreien
  Läufe ersetzen keinen aktuellen Regressionstest des letzten Builds.
- **NEU IM STAGING:** PR #213 brachte 17 FrostAge-Gegnerbilder in
  `GamePICs/`; noch **keine** freigegebenen Gegner-Klassen.
  Zunächst drei Profile (Standard/Agil/Boss) mit eigenem Spawn-Gate,
  spätere Animationen und 14 weitere Profile.
- **VORSCHLAG:** Als nächster Code-PR die verifizierten XP/Rang/Skin-
  Abschlussdaten im Dark Abyss darstellen. Separat einen
  `Spielstände öffnen`-Button für `resources.DATA_DIR` ergänzen.
  Gegnerprofile in eigenem Vertical-Slice-PR, ohne Classic-Verhalten
  unbeabsichtigt zu verändern.
- **Grenze:** Keine personenbezogenen JSONs, vollständigen
  Spielaufzeichnungen, Namen oder `round_id` ins öffentliche Repo;
  nur aggregierte, überprüfbare Beobachtungen.
- **Nachweis:** [Spieltest- und Balancebericht 18.11.](PLAYTEST_BALANCE_2026-11-18.md)
- **Status:** Auswertung dokumentiert, funktionale Folgearbeiten offen.

### 20.11.2026 · Demus + Irian · FrostAge-Shader und bessere VFX
- **Art:** Externe Anregung / IDEE / Machbarkeitsfrage, keine
  neue Implementierungsfreigabe.
- **Wunsch:** Das vorhandene Python-/Pygame-Spiel langfristig grafisch
  schöner gestalten (Glow, Bloom, Trails, Frost-Licht/Nebel) und dem
  Mensch-/Codex-/Irian-Team besser konfigurierbare Designwerkzeuge geben.
- **Nachgeschaut:** Pygame 2.6.1 und `effect_manager.py` unterstützen
  bereits JSON-Animationen, Layer, Alpha und additives Blending.
- **Risiken:** Ein OpenGL-Fenster ist **kein einfacher Drop-in-Tausch**
  für die Pygame-Surface-Anzeige. GPU-Texturkopie und Windows-PyInstaller
  müssen separat geprüft werden; keine unbelegten FPS-Versprechen.
- **Nächste Entscheidung:** Nach Bossarbeiten zuerst Pygame-VFX-
  Prototyp samt Profiling, **nur bei messbarem Nutzen** separater
  ModernGL-Test. World Studio und Gameplay unverändert lassen.
- **Studie:** [Grafik-/Shader-Machbarkeit](docs/graphics/GRAFIK_SHADER_MACHBARKEIT_2026-11-20.md).
- **Status:** **OFFEN ALS IDEE**, kein zusätzlicher Boss-/Engine-PR.

### Agenten-Freifläche
Noch keine weiteren Beiträge. **Keine erfundenen „Agenten-Rückmeldungen“ eintragen.** Wenn ein Agent bei seiner tatsächlichen Arbeit eine brauchbare Idee findet, darf er hier eine neue Notiz per separatem PR vorschlagen oder im passenden Issue/PR kommentieren.

## 5 · Zusammenarbeit in GitHub

**Lesereihenfolge für beauftragte Agenten:** [AGENTS.md](AGENTS.md) → dieses Blackboard → [ROADMAP.md](ROADMAP.md) → betroffenes Issue/PR → **aktueller** Quellcode.

**Schreibweg:**
1. Idee ohne Arbeitsauftrag? In bestehendem Issue/PR kommentieren oder kleinen Blackboard-Dokumentations-PR erstellen; **nicht sofort Features implementieren**.
2. Tatsächlich bestätigter Fehler? Reproduktion, Auswirkungen und minimalen Fix vorschlagen; Issue verwenden.
3. Änderungswunsch beschlossen? Branch, Draft-PR, Tests, Windows-Spielprobe wenn relevant. Merge entscheidet der Projektinhaber.
4. Nach Abschluss **nur** die betroffenen Statusnotizen aktualisieren. Kein Chatverlauf voller täglicher Pflichtmeldungen.

**Konflikte:** Ist-Stand in `main` und bestätigte Tests schlagen ältere Notizen. Bei Widerspruch Rückfrage im PR; Entscheidungen mit Datum festhalten. Historische Einträge dürfen als solche erhalten bleiben.

**Kaffeerunden-Regel:** Gute Ideen sind willkommen – aber eine Idee wird erst dann ein Entwicklungsauftrag, wenn wir sie bewusst auswählen. ☕
