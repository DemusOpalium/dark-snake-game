# ❄️ DARK SNAKE – UI 2.0: Bildanalyse, Menü-Mini-Profile und Entwicklungskatalog

**Status:** 💡 Konzept/Audit – **noch keine Menü-Implementierung**.  
**Erstellt:** 15.11.2026 · Ist-Stand: `main` nach PR #176.  
**Zweck:** Die von Demus während des Spiels gezeigten Bildschirmaufnahmen und gemeinsam besprochenen Gestaltungsideen **konkret sichern**, sodass wir das UI in kleinen, nachvollziehbaren PRs erneuern können. Maßgebliche Status-/Prioritätenliste bleibt [ROADMAP.md](ROADMAP.md), Abschnitt 16.

> **Beweisgrenze:** In diesem Gespräch sind vier konkrete aktuelle Screenshots erkennbar: (A) Optionsmenü „Heads“, (B) Optionsmenü „Bodies“, (C) Vergrößerung des linken Options-/Audiobereichs mit geöffneter Musikauswahl, (D) „STEUERUNG“. **Ein fünfter eigenständiger aktueller Highscore-Screenshot ist nicht sichtbar.** Die Highscore-Beschreibung stammt deshalb aus Demus' Designidee und dem überprüften Code `Game.draw_leaderboard()`, **nicht** aus einer erfundenen Bildbeobachtung. Späteren Screenshot ergänzen, wenn er vorliegt.

## 0 · Kurzbefund und Bildreferenzen

| Bild/Quelle | Sichtbarer Ist-Stand | Bewertung / UX-Ziel |
| --- | --- | --- |
| **A – Options / Heads** · Aufnahme ungefähr 1350×963 | Violett/orange Topbar, drei Hauptspalten, **Heads**-Auswahl mit 4 Spalten von Miniaturen, rechter P1-/P2-Kasten, links Gameplay/Audio. | Funktional, aber übergroße Texte, alte Doppelrahmen, schwarze Flächen und schwache visuelle Hierarchie. |
| **B – Options / Bodies** · ungefähr 1345×948 | Gleiche Oberfläche, statt Köpfen 13 sichtbare Körpergrafiken in vier Spalten; weitere freie Fläche darunter. | Gemeinsame Galerie mit späterem Scrollen/Filtern statt starrer Grid-Ansicht. |
| **C – Audio-Detail / Dropdown** · ungefähr 480×887 | Musik/Soundeffekte und geöffnete Songliste; Sliderlabels berühren oder überdecken ihre Balken. | Klare Label-/Wert-/Slider-Zeilen; Songliste in begrenztem Bereich scrollbar; echte Dateinamen weiterhin zugänglich. |
| **D – Steuerung** · ungefähr 1339×949 | Schwarzes, schlichtes Menü mit Eingabezeilen und 6 Buttons unten; viel freier Mittelraum. | Übersichtliche FrostAge-Eingabeprofile statt leerer Fläche; bestehende Funktion und Tastenkürzel erhalten. |
| **E – Highscore** · aktuelle Aufnahme fehlt | Code zeigt eine einfache Top-10-Liste (gold/silber/bronze/weiß), „BESTENLISTE“, „ZURÜCK“. | Neues Schlangenbaum-/Totenkopf-Podest: Top 3 oben, weitere 7 unten; Score-Datei unverändert. |

**Bildhistorie:** A und B sind zwei Zustände **desselben** Menüfensters, nicht zwei getrennte Implementierungen. C ist ein Ausschnitt desselben Fensters. Das ist wichtig für ein gemeinsames UI-System.

## 1 · Optionsmenü: präzise Element- und Buttoninventur

### 1.1 Obere Aktionsleiste: **vier Buttons**

| Sichtbarer Text | Code / Aktion | Wunsch |
| --- | --- | --- |
| **Speichern** | `save_btn` → `OptionsMenu.save()` | FrostAge-Button, klare Rückmeldung „Gespeichert“. |
| **Zurück** | `back_btn` → `OptionsMenu.back()` | Einheitlicher Zurück-Button, kein versehentlicher Verlust von Änderungen. |
| **Set for P1** | `assign_p1_btn` → `assign_image(1)` | „Für Spieler 1 wählen“ oder per Sprache lokalisierbar; Auswahl und Head/Body-Typ deutlich machen. |
| **Set for P2** | `assign_p2_btn` → `assign_image(2)` | Analog Spieler 2, farblich gut unterscheidbar. |

**Weitere zwei Buttons:** `Heads` und `Bodies` sind **Tabs der mittleren Galerie**, keine zusätzlichen Aktionen der Hauptleiste. Also **4 + 2 = 6 sichtbare Haupt-/Tabbuttons**, genau die im Bild gemeinten sechs.

### 1.2 Linke Seite: **fünf Gameplay-Regler + zwei Audio-Regler + ein Dropdown**

| Gruppe | Sichtbar / Bedeutung | Ist aus Code und Screenshot | Verbesserungsprofil |
| --- | --- | --- | --- |
| Gameplay 1 | **Speed** | `initial_speed`, Bildschirm 8.0, Reglerbereich 1–15 | Wert, Einheit/Erklärung und Bereich sauber ausrichten; Veränderungen erst nach bewusstem Speichern. |
| Gameplay 2 | **Difficulty** | `difficulty`, aktuell 1.0, Bereich 0.5–2.0 | Voreinstellungen (z. B. Normal/Schwer) später **zusätzlich**, nicht statt bestehender Werte. |
| Gameplay 3 | **Projectile** | `projectile_speed_factor`, Screenshot 0.5, Bereich 0.5–2.0 | Technischen Projektil-Speed-Faktor als **Erweitert/Entwickler** einordnen; noch nicht entfernen. |
| Gameplay 4 | **Spawnrate** | `enemy_spawn_rate`, zulässig 0.001–0.005, Screenshot zeigt fälschlich **0.0** durch ein Nachkommastellen-Format | **UI-Darstellungsbug:** mindestens drei Dezimalstellen oder verständliche relative Anzeige; keine interne Null behaupten. |
| Gameplay 5 | **Boss HP** | `boss_health_multiplier`, Screenshot 1.0, Bereich 1.0–3.0 | „Boss HP ×1.0“ deutlicher benennen und Tooltip; optional Advanced. |
| Audio 1 | **Musik** | Im Ausschnitt 3 %, direkter Audio-Lautstärkeregler | Wert neben Label, barrierearme Tastaturbedienung und sichtbares Feedback. |
| Audio 2 | **Soundeffekte** | Im Ausschnitt 75 %, Preview-Sound beim Loslassen | Wie oben; Spiel-/Kampf-Sounds können später in separate Gruppen kommen. |
| Audio 3 | **Musikauswahl** | Dropdown mit aktuell ausgewähltem Dateinamen `DarkSnakeMusicIndi2.mp3` und mehreren MP3-Einträgen | Klarer Titel, lesbare scrollbare Songliste, Auswahl-Hervorhebung; nicht über andere Steuerelemente hinauszeichnen. |

**Bildfehler:** Die Sliderbeschriftung sitzt sehr dicht über dem Balken, besonders in den oberen beiden Gruppen. Dies entspricht `modules/ui.py::Slider.draw()` (Label bei `rect.y - 25`) und dem alten Abstand der Regler im Optionsmenü. Die grüne Umrandung und Innenrahmen bilden doppelte Hierarchien; Header `Heads`/`Bodies` ist für seinen Balken sichtbar zu hoch. Der schwarze Hintergrund ist kontrastreich, aber für das neue Theme zu roh.

**Designentscheidung:** Spieler sollen **Spielgefühl frei anpassen dürfen**, aber riskante/technische Balanceparameter können in einen aufklappbaren Abschnitt **Erweitert**. Speichern und bestehende Schlüssel `settings.json` unverändert, keine stillen Gameplay-Änderungen.

### 1.3 Mittlere Galerie: Heads / Bodies

**Ist:** vier Vorschaubilder pro Zeile, Anklicken wählt ein Bild, „Set for P1/P2“ ordnet es einem Spieler zu; der Bildschirm zeigt viele dunkle und farbige Kopf-/Körperkunstwerke. Die Thumbnails sind relativ groß, die finale Spielfigur rechts dagegen sehr klein. `OptionsMenu.load_options()` lädt die alten Runtime-Verzeichnisse und erzeugt starre 60×60-Vorschauen; `draw_inventory_grid()` skaliert sie erneut beim Zeichnen, `inventory_scroll_offset` besitzt derzeit keine offensichtliche Begrenzung in diesem Pfad. **Das sind technische Prüfpunkte, nicht automatisch nachgewiesene Abstürze.**

**Soll:**
1. Galerie mit Tabs **Heads**, **Bodies**, später **Sets**, dazu Suche, Kategorie, Filter, Favoriten (optional später) und sichtbarem Scrollbalken.
2. Auswahlkarten mit **kreativem Namen**, Spritevorschau, kurzer Herkunft und optionaler Seltenheit (nur kosmetisch).
3. Größenverhältnis und Alpha sauber behandeln: **Seitenverhältnis erhalten**, transparente Ränder/zu große Leerflächen vorab prüfen, **nicht** das Original dauerhaft kleinrechnen.
4. Durch Scrollen, Mausrad, Controller/Tastatur und Maus navigierbar; bei 53+ Kandidaten keine endlose starre Spalte.
5. Ausgewähltes Bild vor Zuweisung klar markieren. P1 und P2 unabhängig zuweisen; belegte Skins beim Wiedereinstieg korrekt markieren.
6. Geeignete Bilder **lazy laden**, Thumbnails je Größe cachen; kein `pygame.transform.scale()` sämtlicher Karten in jedem Frame.
7. Jedes akzeptierte Kopf-/Körpermotiv erhält eine **stabile ID**; Dateiname und Anzeigename sind getrennt. Umbenennung in der UI darf `settings.json` nicht brechen.
8. Später Freischaltungen/Erfolge möglich, in der ersten Überarbeitung **alle geeigneten Sprites auswählbar** lassen.

**Quellen:** `Dark_Snake/assets/graphics/SnakeHeadsbibliothek/` und `SnakeBodysBibliothek/` (alte Runtime) sowie `GamePICs/DarkSnake-NeueHeads/` (**53 Kandidaten**) und `GamePICs/DarkSnake-KörperNeuDesign/` (**15 Kandidaten**). Kandidaten sind teils Roh-Snips, Referenzen oder Dubletten: **nicht 68 ungeprüft spielbare Einzel-Skins versprechen**. Geeignetes Artwork erst sichten/prüfen und in Runtime kopieren, übrige Quellen erhalten.

### 1.4 Rechte Seite: P1/P2-Final-Vorschau

**Im Screenshot:** Zwei große, gerahmte Kästen `Player 1 Final` / `Player 2 Final`, darin pro Spieler sehr kleine Head-/Body-Symbole; die Kästen wirken ansonsten leer.

**Wichtigster Wunsch von Demus:** **Die reale Spielgröße bleibt identisch.** Im Code werden Kopf und Körper in `GRID_SIZE×GRID_SIZE` gezeichnet. Nicht die gesamte Demonstration vergrößern.

**Verbesserung:** In jedem Kasten eine kleine **„In-Game 1:1“**-Bühne mit passendem FrostAge-Boden, Gitter/Skalierungsmarke und realen Head-/Body-Grafiken in tatsächlich verwendeter Rastergröße. Darüber oder daneben eine **separate vergrößerte Detailvorschau**, explizit als Zoom beschriftet, wenn sie hilfreich ist. Dadurch zugleich schöne Präsentation **und** ehrliche Größenkontrolle.

**Sicherheitsregel:** Wenn eine Datei fehlt oder ein Sprite unpassend ist, klaren Fallback zeigen; niemals alte P1/P2-Auswahl löschen. Vorschau und tatsächlich im Spiel verwendete Bilder müssen übereinstimmen.

### 1.5 Neue Oberfläche / Art Direction

- Eigenes **FrostAge-/Gothic-Arcade-Hintergrundbild**, aber gedimmt und in der Mitte ruhig, damit Slider und Miniaturen nicht untergehen.
- Lesbare Panels in dunklem Blau/Graphit, feine Eiskanten statt neon-grüner Doppelrahmen; dezente orange/bernsteinfarbene Aktivmarkierungen für Kontrast.
- Einheitliche Buttonhöhe, sinnvolle Schriftgrößen und ausreichende Innenabstände.
- Fenster-/Rastergröße weiterhin kompatibel. UI-Layout proportional anpassen oder kontrolliert scrollen; hit targets müssen der sichtbaren Grafik entsprechen.
- Keine eingebrannten interaktiven Buttons im Hintergrundartwork. DE/EN-lokalisierbare Texte getrennt von Grafiken, soweit sinnvoll.

## 2 · Steuerung: Elementinventur und Mini-Profil

**Sichtbare Aufnahme:** Überschrift **STEUERUNG**; oben 2 Auswahlbereiche `Spieler 1 ›` und `Tastatur ›`, darunter eine Anleitung. Aktionszeilen: `Hoch → W`, `Runter → S`, `Links → A`, `Rechts → D`, `Feuerball → Leertaste / Enter (1P)`.

**Unten genau sechs Befehle:** `Zuweisen`, `Entfernen`, `Eingabetest`, `Speichern`, `Standard`, `Zurück`. Im unteren Bereich stehen Hinweise zu Tastenwahl, Speichern und Navigation.

**Bildkritik:** Viel ungenutzter schwarzer Raum zwischen Aktionsliste und Status/Buttons unten. Funktional und lesbar, aber nicht auf FrostAge-Stil gebracht. Rechts-/linksseitige Aufteilung könnte vorhandenen freien Raum besser für aktuelle Geräte-/Spielerinfos, belegte Tasten und Eingabetest verwenden.

**Muss erhalten bleiben:** Input-2.0-Verhalten aus `modules/controls.py` und `input_manager.py`; Spieler-/Gerätewahl, Tastatur/Controller, Konfliktprüfung, Testmodus, Zurück, Speichern, Standardbelegung und sichere laufende Erfassung. Keine Standardtasten verlieren oder beim Menü-Redesign versehentlich überschreiben. Keyboard-first und Controller-Fokus ausdrücklich testen.

**Späterer Layoutvorschlag:** Links Spieler/Gerät/Aktionsliste, rechts aktives Eingabeprofil, Tastensymbole und Teststatus; unten die sechs originalen Befehle mit konsistenten FrostAge-Buttons. Keine bloß dekorativen Schaltflächen.

## 3 · Bestenliste / Highscore: Konzeptprofil mit überprüftem Code

**Nicht mit eigenem aktuellem Screenshot belegt.** Der Code `Game.draw_leaderboard()` zeigt `BESTENLISTE`, höchstens zehn Datensätze, Gold/Silber/Bronze für 1–3, Weiß für 4–10, und **ZURÜCK**. `Game.load_leaderboard()` liest historisch Zeilen mit `name,score`; es sind **Ränge**, nicht drei verschiedene reale Spieler-Profile. Es darf nicht ohne neue Datenbasis fälschlich getrennte Player-1-/Player-2-/Player-3-Highscores anzeigen.

**Demus' visuelle Vision:** Eine epische Ruhmeshalle mit verflochtenen Schlangen, Totenschädeln, Eis, Feuer und einer baumartigen Rangliste.

- **Top 3 als Monument/Podest:** **Rang 1** zentral und prächtig (Gold, „Legendär“), **Rang 2** und **3** seitlich (Silber/Bronze; „Elite“, „Episch“ nur Design-Badges, noch keine Spielklasse). Große Namen und Score gut lesbar vor dekorativem Hintergrund.
- **Ränge 4–10** darunter als ordentliches, scrollbar/gestalterisch ruhiges 7er-Segment; die Werte sollen nicht hinter Schlangenwurzeln verschwinden.
- **Leerzustand** als schöne „Ruhmeshalle wartet auf ihren ersten Champion“-Grafik/Titel, falls keine Scores gespeichert sind; Rückkehr immer bedienbar.
- **Daten unverändert:** bestehende Sortierung, Dateiformat, Eintragslogik und Namen erhalten. Keine neuen Onlinedaten, Seasons oder Rang-Vergaben ohne separates Konzept.
- **Performant:** Dekoratives Bild/Schlangenbaum als **eine gecachte Hintergrundebene**, Score-Texte überlagert; nicht pro Frame Schriftarten/PNG-Dateien neu laden.
- **Optional später:** Spielmodus, Zeitpunkt, Schwierigkeitsgrad, Siege und eigene 1P-/2P-Wertungen **nur mit versioniertem Schema und Migration**.

**Visuelle Beschreibung für spätere Artwork-Anfertigung:** 16:9 oder anpassbare FrostAge-Ruhmeshalle; Oben großer gotischer **DARK SNAKE HALL OF LEGENDS**-Schriftzug als separate UI-Textebene; links/rechts Totenkopf-Schlangen, silberne/bernsteinene Flammen, mittig ein gewaltiger verschnörkelter Schlangenbaum, der drei Podeste umfasst. **Wichtig:** Freie ruhige Textfelder für Namen und Zahlen, kein fest eingebrannter Text im Artwork.

## 4 · Namenskonzept für 53 Heads und 15 Bodies

Ziel: **jedes nach visueller Prüfung freigegebene Motiv** bekommt einen merkbaren, möglichst einzigartigen Namen, eine stabile ID und eine kurze Charakterbeschreibung. Keine Dateiumbenennung der Rohkunstwerke erzwingen.

**Beispielnamen als kreative Platzhalter, noch keinem konkreten PNG zugeordnet:**

| Kategorie | Namensidee | Atmosphäre |
| --- | --- | --- |
| Head | **Frostfang** | blauer Eisjäger |
| Head | **Grave Whisper** | Friedhofsgeist / dunkles Gesicht |
| Head | **Mycelis** | Pilz-/Sporenwesen |
| Head | **Ember Viper** | glühend und feurig |
| Head | **Void Oracle** | mystisches Auge / Kosmos |
| Head | **Obsidian Crown** | schwere schwarze Rüstung |
| Body | **Glacier Coil** | gefrorene Segmente |
| Body | **Ashbone Chain** | Knochen / Glut |
| Body | **Moonsteel Scales** | metallische Schuppen |
| Body | **Spore Circuit** | leuchtendes Myzel |
| Body | **Wraith Spine** | geisterhafte Wirbelsäule |
| Body | **Royal Serpent** | goldene Runen |

**Vorschlag für späteren Skin-Katalog (Schema, noch nicht umgesetzt):**

```json
{
  "id": "head_frostfang",
  "type": "head",
  "display_name": {"en": "Frostfang", "de": "Frostzahn"},
  "source_path": "GamePICs/DarkSnake-NeueHeads/<nach_pruefung>.png",
  "runtime_asset": "graphics/skins/<freigegebenes_bild>.png",
  "theme": "frostage",
  "status": "candidate",
  "description": {"de": "Eisiger Schlangenkopf", "en": "Icy serpent head"}
}
```

**Mini-Profil-Checkliste pro Skin:** Original-ID/Pfad, Duplikatprüfung/Hash, Bildinhalt, Name DE/EN, Head oder Body, Stil, Alpha/Kanten, Größe, 30px-Lesbarkeit, Spielerzuordnung, Freigabestatus. **Sofort alle 68 hochladen** ist nicht gleichbedeutend mit **sofort alle 68 ohne Prüfung einbauen**.

## 5 · Kleine, getrennte Umsetzungspakete (Priorität und Akzeptanz)

### UI-2A – Optionsmenü / Grundstil (zuerst bei diesem UI-Thema)
- Optionen/Audio/Credits nicht mit World Studio in einem riesigen PR koppeln.
- Vier Kopfaktionen + zwei Tabs + sieben Slider + Musik-Dropdown erhalten; Labels/Abstände verbessern.
- Spawnrate **nicht** irreführend auf `0.0` runden.
- FrostAge-Hintergrund und Buttons, klare Container ohne grüne Doppelrahmen, intuitive P1/P2-Vorschau.
- Funktionstests für Speichern/Laden, Mausdrag, Dropdownwechsel, SFX-Vorschau, P1/P2, Preview bei 30px und Resize.
- Windows-Sichttest: keine Überschneidungen bei 900×620, 1350×930 und maximiert.

### UI-2B – Große Head-/Body-Galerie
- Kandidaten zuerst inventarisieren, Dubletten und Reference Images ermitteln; nur nutzbare einzelne Sprites ins Runtime-Verzeichnis kopieren.
- Lazy-Load + Thumbnail-Cache, sanftes Scrollen, 4-Spalten-Grid nur wenn breit genug, Suche und Namensanzeige.
- Auswahl für P1/P2 bleibt getrennt; 30px-Referenz plus optionales 2–4x vergrößertes Detail, eindeutig gekennzeichnet.
- Der alte Speicherwert muss weiterhin auf dasselbe Bild zeigen; Migrationslogik bei neuer ID.

### UI-2C – Steuerung / Input 2.0
- FrostAge-Panels, bessere Nutzung der Fläche, Fokus/Highlight, klare Bindings, alle sechs unteren Befehle erhalten.
- Tests für 1P/2P, Tastatur/Controller/Joysticks, Escape, Rebinding, Konflikte, Reset, Speichern und Re-Load.

### UI-2D – Highscore / Ruhmeshalle
- Art/Rank-Panel erstellen, Top-3-Podest mit Platz 1 in der Mitte, 4–10 darunter, Datenfluss unverändert.
- Liste und Leerzustand, lange Namen/Zahlen, Skalierung, Keyboard/Controller-Rücknavigation, Versionskompatibilität testen.
- Optional spätere Score-Metadaten **nicht** gleichzeitig einführen.

### Prüfregel für alle vier PRs
`python -m compileall -q Dark_Snake tests`, `python -m pytest -q`, Windows-Build + CodeQL, sichtbare Probe im echten Windows-Fenster; 1P/2P-Gameplay und gespeicherte Einstellungen dürfen nicht regressieren. Vorher/nachher FPS/p95 und Ladevorgänge gemäß [QUALITY_PERFORMANCE_PLAN.md](QUALITY_PERFORMANCE_PLAN.md) vergleichen oder ausdrücklich **NOT MEASURED** angeben.

## 6 · Für spätere Gestaltung vorbereitete Grafiken (noch keine Assetanforderung)

1. **Options-Backdrop:** ruhiger dunkler FrostAge-Innenraum, eisige Architektur und dezentes Myzel, im Panelzentrum geringe Detailfrequenz.
2. **UI-Panel-/Rahmenset:** einheitliche Frost-/Metallflächen für Gameplay, Audio, Galerie, P1/P2 und Steuerung; Zustände normal/hover/focus/disabled.
3. **Buttonset:** Save, Back, Assign P1, Assign P2, Heads, Bodies, Musik-Dropdown, optional Advanced. Keine frei erfundenen toten Buttons.
4. **Galerie-Status:** Auswahl, Sperre (später), Favoriten (später), Scrollleiste, Einzel-Skin-Karte ohne eingebrannten Namen.
5. **Highscore-Backdrop:** „Hall of Legends“ mit Schlangenbaum/Skulls/Eis/Feuer und drei Podestflächen; separate, textfreie Liste für Ränge 4–10.
6. **Steuerung:** tastatur-/controllerfreundliche Rahmen und Fokus-Layer; keine Änderung an tatsächlich belegten Tasten.

**Erst passende Grafiken erzeugen/hochladen, dann gezielt den nächsten Runtime-PR eröffnen.** Artwork-Originale bleiben in `GamePICs`; nur die freigegebenen Bilder werden unter `Dark_Snake/assets` gebündelt.

## 7 · Was dieses Audit nicht behauptet

- Dass der aktuelle Highscore-Screenshot bereits vorliegt: **nein**.
- Dass alle 53+15 Rohdateien fertige, kompatible Einzel-Skins sind: **nein**.
- Dass UI 2.0 oder die legendäre Ruhmeshalle bereits implementiert sind: **nein**.
- Dass das vollständige Menü-Redesign in einem PR erledigt werden soll: **nein**.
- Dass eine schönere Oberfläche ohne Messung schneller läuft: **nein**.

**Leitsatz:** Das Menü soll sich so hochwertig anfühlen wie FrostAge – mit echten Funktionen, ohne verlorene Optionen, ohne Bildruckler und mit einer ehrlichen 30×30-Snake-Vorschau.
