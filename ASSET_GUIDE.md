# 🐍 DARK SNAKE – Asset-Legende für Menschen und Coding-Agenten
**Stand vom 16.11.2026 · World Studio mit Layer Explorer, Sprachschalter und Lernmodus**

> `Dark_Snake/assets/` enthält die Spiel- und EXE-Laufzeitdaten. `GamePICs/` enthält Originale, Entwürfe und Referenzen. Die passenden Laufzeitkataloge dokumentieren die tatsächlich verwendeten Dateien.

## Verbindliche Wege

| Pfad | Tatsächliche Aufgabe | Gehört derzeit zur Windows-EXE? |
| --- | --- | --- |
| `Dark_Snake/main.py` | Programmeinstieg | Code wird zur EXE gebaut |
| `Dark_Snake/modules/` | Spiellogik, Pygame-UI, World Studio, Katalog und Rendering | Ja, via PyInstaller |
| `Dark_Snake/assets/` | Laufzeitgrafiken, Levelvorlagen, Audio und Kataloge | **Ja**, `--add-data "Dark_Snake/assets;assets"` |
| `Dark_Snake/assets/graphics/frostage/` | 175 importierte FrostAge-PNGs plus `catalog.json` | **Ja** |
| `GamePICs/Incoming/Frost_Tiles/` | 175 unveränderte FrostAge-Originale + Importhinweise | **Nein**, nicht direkt |
| `Dark_Snake/assets/graphics/editor_ui/` | 58 geprüfte Editor-Button-PNGs für 62 Action-IDs mit Herkunftsnachweis | **Ja** |
| `GamePICs/Build/`, `File/`, `Effects/`, `Layers/` usw. | Alle 81 Originale der englisch beschrifteten Editor-Button-Grafiken | 51 bytegleiche Kopien unter `editor_ui/` |
| `GamePICs/Nachtrag Fehlende Buttons/` | Sieben Originale aus #173 | Sieben bytegleiche Kopien unter `editor_ui/` |
| `GamePICs/General/De-En_Language-removebg-preview.png` | Original des Sprachschalters | Bytegleiche Kopie als `editor_ui/nav_language.png` |
| `GamePICs/DarkSnake-NeueHeads/` | 53 neue Head-Kandidaten / Rohentwürfe | **Nein**, noch nicht registriert |
| `GamePICs/DarkSnake-KörperNeuDesign/` | 15 Body-Kandidaten / Rohentwürfe | **Nein**, noch nicht registriert |
| `GamePICs/` (weitere Bilder) | Projekt-Screenshots, Referenzen, Konzeptgrafiken; einige in README verlinkt | Nur wenn separat in `assets/` importiert |
| `tests/` | Headless- und Funktionstests | Nein |
| `scripts/` | Build, Asset-Import, Benchmarks, Diagnose | Nein, soweit nicht separat mit eingebunden |
| `.github/workflows/` | Windows-Build, CodeQL, Release-Automation | Nein |
| `ROADMAP.md` | Verwirklicht / geplant und Reihenfolge | Nein |

Der datierte Staging-Snapshot enthält alle 81 Button-Dateipfade und alle 68 Kopf-/Körperdateipfade samt Git-Blob-SHA und Größe. Für den aktuellen Einsatz gelten die beiden Laufzeitkataloge. [Staging-Snapshot](GamePICs/asset_inventory.json) · [Editor-Buttons](Dark_Snake/assets/graphics/editor_ui/catalog.json) · [FrostAge](Dark_Snake/assets/graphics/frostage/catalog.json)

## Die 48 eingebundenen Editor-Grafiken

Der Katalog dokumentiert für jede Action-ID den Originalpfad, den Laufzeitdateinamen, die nativen Abmessungen, die sichtbare Fläche und den SHA-256-Wert. Die ersten 48 PNGs belegen zusammen 16.881.238 Byte. Beim Rendern kann der vollständig transparente Außenbereich ausgespart werden. Das Bild behält sein Seitenverhältnis und den englischen Schriftzug. Tooltips und Ersatzbeschriftungen folgen der gewählten Editor-Sprache. [Editor-Button-Katalog](Dark_Snake/assets/graphics/editor_ui/catalog.json)

| Bereich | Zuordnung der vorhandenen Aktionen zu den Grafik-IDs |
| --- | --- |
| Hauptnavigation (7) | Datei `nav_file`, Bauen `nav_build`, Ebenen `nav_layers`, Effekte `nav_effects`, Ansicht `nav_view`, Testen `nav_test`, Lernen `nav_learn` |
| Datei (8) | Neu `file_new`, Öffnen `file_open`, Speichern `file_save`, Welten `file_worlds`, Undo `file_undo`, Redo `file_redo`, Für Classic wählen `file_use_classic`, Classic-Standard `file_classic_default` |
| Bauen (4) | Mittelfeld `build_middle`, Objekt verschieben `build_move_objects`, Objektgröße `build_object_size`, Tile-Bibliothek `build_tile_library` |
| Rand-Builder (6) | Linke, rechte, obere und untere Seite `border_left`, `border_right`, `border_top`, `border_bottom`, Gesamter Rand `border_all`, Eckgrafiken `border_corner` |
| Ebenen und Kollision (7) | Boden `layer_ground`, Objekte `layer_objects`, Dach `layer_roof`, Kollision `layer_collision`, Effekte `layer_effects`, WALL `collision_wall`, BARRIER `collision_barrier` |
| Effekt- und Dachwerkzeuge (4) | Schaden `effect_damage`, Slow `effect_slow`, Effektwerte `effect_values`, Dachwerte `roof_settings` |
| Ansicht (7) | Karte einpassen `view_fit_map`, Bibliothek `view_library`, Arbeitsbereich `view_panel`, Zelle untersuchen `view_cell`, Kollision `view_collision`, Effekte `view_effects`, Dachansicht `view_roof` |
| Testen (5) | Vorschau starten `test_preview`, Test 1P `test_player_1`, Test 2P `test_player_2`, Dach-Demo `test_roof_demo`, Test beenden `test_stop` |

**Border (All)** befindet sich bei der Auswahl aller Seiten im Rand-Builder. **Lernen** öffnet den geführten Kurs und die Dach-Demo.

## Die sieben Motive aus PR #173

| Original | Action-ID |
| --- | --- |
| `Help.png` | `nav_help` |
| `Border_Builder.png` | `build_border` |
| `Move_to_Roof.png` | `build_transfer_roof` |
| `Graphics_Only.png` | `tool_graphics` |
| `Graphics_Collision.png` | `tool_combined` |
| `Properties.png` | `sidebar_properties` |
| `Stop.png` | `preview_stop` |

Die Seitenreiter `sidebar_layers`, `sidebar_cell`, `sidebar_help` und `sidebar_learn` verwenden die vorhandenen Bilder für Ebenen, Zellinspektion, Hilfe und Lernen. Ihre eigenen Action-IDs teilen sich die vorhandenen Laufzeitdateien. [Laufzeitkatalog](Dark_Snake/assets/graphics/editor_ui/catalog.json)

## Sprachschalter aus PR D

Der Schalter `nav_language` übernimmt das vorhandene DE/EN-Motiv aus `GamePICs/General/`. Die RGBA-Datei misst 1085 × 230 Pixel. Beide Sprachzustände nutzen dieselbe Kopie und denselben Grafik-Cache. Der Sprachwechsel lokalisiert die UI-Texte, während der Schriftzug Teil der Grafik bleibt. [Laufzeitkatalog](Dark_Snake/assets/graphics/editor_ui/catalog.json)

## Lernmodus aus PR E

| Original in `GamePICs/Learn/` | Aktion | Abmessungen |
| --- | --- | --- |
| `My_FIrst_LvL-removebg-preview.png` | Kurs starten (`learn_start`) | 1222 × 204 |
| `Examples-removebg-preview.png` | Beispiel ein- und ausblenden (`learn_example`) | 1235 × 202 |

Die beiden RGBA-Grafiken werden bytegleich übernommen. Für `learn_previous`, `learn_next` und `learn_retry` gibt es lokalisierte Textschaltflächen. Falls eine zugeordnete PNG fehlt, zeigt der Renderer die lokalisierte Beschriftung der Aktion an. [Laufzeitkatalog](Dark_Snake/assets/graphics/editor_ui/catalog.json)

## Die 30 reservierten Editor-Grafiken

Die Dateinamen stehen ohne den gemeinsamen Suffix `-removebg-preview.png` in der Tabelle. Die Quelldateien und ihre exakten Pfade stehen im Inventar. [Staging-Snapshot](GamePICs/asset_inventory.json)

| Ordner | Reserviert | Grund |
| --- | --- | --- |
| `Build` (3) | `Build_Symbol_Text`, `Favorite`, `Search` | Alternative Navigation. Favoriten und Suche haben bereits eine Kategorieliste und ein Eingabefeld. |
| `Building Blocks` (5) | `Building_Blocks`, `Event_-_Triggers`, `Ground_Tile`, `Lighting`, `Roof_-_Foreground` | Kategorietitel, zusätzliche Entwürfe für vorhandene Ebenen und geplante Werkzeuge für Licht und Trigger. |
| `EditorBigs` (8) | `Ceiling`, `Collision`, `Damage`, `Events`, `floor_object`, `Light`, `Roof`, `Slow` | Alternative Großformate für eine spätere Gestaltung. |
| `General` (4) | `About`, `Exit`, `General`, `Settings` | Konzepte für eigene Studio-Aktionen. Der Editor verwendet seine bestehenden Dialoge sowie F2 und Esc zum Schließen. |
| `Layers` (3) | `All_Layers`, `Lock_layers`, `Show_Hide` | Reservierte Motive. Der Layer Explorer verwendet kompakte Textschaltflächen, die den aktuellen Zustand der einzelnen Ebenen anzeigen. |
| `Learn` (2) | `Guided_Build`, `Learn_Tutorial` | Alternative Entwürfe für künftige Lernfunktionen. |
| `Miscellaneos` (4) | `Chest`, `Coin_-_Item`, `Miscellaneous`, `Random_D20` | Konzepte für spätere platzierbare Interaktionen und Events. |
| `View` (1) | `View_Map` | Die vorhandenen Aktionen heißen Karte einpassen und Vorschau starten. |

## FrostAge-Laufzeitkatalog und nächste Spielprofile

- `GamePICs/Incoming/Frost_Tiles/` enthält **175 ursprüngliche PNGs**, darunter 126 Flächen-/Objekt-/Dachgrafiken, 11 AoE, 12 Menübuttons, 8 Gegner, 5 Items und 13 Projektile.
- `scripts/frostage_catalog.py --write` baut das Laufzeitpaket `Dark_Snake/assets/graphics/frostage/` aus dem Originalbestand; `--check` kontrolliert die Zuordnung. **Nicht manuell per Drag-and-drop Originale in die Laufzeitbibliothek umbenennen.**
- `Dark_Snake/modules/frostage_assets.py` lädt Asset-Metadaten aus `catalog.json` und Grafiken bei Bedarf. **Das ist der maßgebliche Katalog.**
- World Studio kann Grafikobjekte platzieren. Roof/Foreground und Dach-Sichtfenster sind seit PR #154 spielbar. Das Hauptmenü nutzt FrostAge-Buttons.
- **8 Gegnerbilder** können eigene Profile mit stabiler ID, Ausrichtung, Bewegung, HP, Schaden, Projektil und Spawn erhalten. Die vorhandenen Regeln von `NormalEnemy` und `BolbuEnemy` sowie die Boss-Klassen sind Ausgangspunkte.
- **13 Projektilbilder** brauchen Profile für Tempo, Lebensdauer, Richtung, Schaden und Trefferverhalten. Dafür die vorhandenen Rasterprojektile sowie Feuerball-, Boss- und Bolbu-Projektile wiederverwenden. Eine Animation braucht ausdrücklich definierte Einzelbilder und Reihenfolge.
- **11 AoE-Bilder** lassen sich gezielt Schadens-, Heilungs- und Debuffzonen zuordnen. Laufzeit, Intervalle und Wirkung kommen aus einem ausdrücklichen Profil auf Basis der bestehenden `AoEZone`-Klassen, des Frost-Prototyps oder der Editor-Effektfelder.
- **5 Itembilder** brauchen geprüfte Zuordnungen zu `ItemType` und `ITEM_IMAGES` sowie eigene Aufnahme- und Interaktionsregeln. Schlüssel, Truhen und Belohnungen werden bei entsprechender Eignung der Motive in getrennten Gameplay-PRs umgesetzt.
- Grafik, Render-Ebene, Kollision und Schaden sind getrennte Eigenschaften. Ein reines Grafikobjekt hat die Wirkung seiner Ebene.

## Neue Köpfe und Körper für die geplante Skin-Galerie

- `GamePICs/DarkSnake-NeueHeads/` enthält 53 Kopfdesigns und `GamePICs/DarkSnake-KörperNeuDesign/` 15 Körperdesigns, darunter Roh-Snips und Referenzen. Die Auswahl geeigneter 30×30-Sprites gehört in einen eigenen PR.
- Die aktuelle Grafikoption verwendet `ExtendedOptionsMenu`. Sie sucht Ressourcen über `find_asset_directory` und speichert die Auswahl je Spieler. Das ältere `CustomizationMenu` hat vier feste Kopfoptionen und lädt Körperbilder aus einem relativen Pfad.
- Die geplante Galerie übernimmt geprüfte Sprites mit stabilen Skin-IDs, portablen Pfaden, Scrollen und Vorschau in Spielgröße. Kombinationsprüfung und mögliche Freischaltungen durch Spielerfolge folgen mit eigenen Tests. **UI-2.0-Bildanalyse, kreatives Skin-Namensschema und Abnahme: [UI_2_0_SCREEN_AUDIT.md](UI_2_0_SCREEN_AUDIT.md).**

## Agenten-Regeln für jede künftige Asset-Aufgabe

1. **Status zuerst bestimmen:** `runtime`, `staged`, `reference`, `candidate` oder `planned`. Einen geplanten Button nie als funktionierende Spielmechanik ausgeben.
2. **Originale erhalten.** Aus `GamePICs/` ausgewählte, geprüfte PNGs nach `Dark_Snake/assets/` **kopieren** bzw. aus dortigem Staging katalogisieren; Originale und Screenshots nicht löschen oder verschieben, solange sie referenziert sind.
3. Vor jeder Nutzung **Datei und Inhalt** kontrollieren: Name, Schriftzug, Transparenz, Bildabmessungen, Blickrichtung, 24–48-Pixel-Lesbarkeit. Dateiname allein beweist nicht korrekte Zuordnung.
4. Eine **eindeutige stabile Action-ID → bestehende PNG-Datei**-Zuordnung anlegen, statt Buttonfunktionen über den deutschen/englischen Beschriftungstext zu steuern.
5. Die Button-PNGs behalten ihren **englischen Schriftzug**. Tooltips, Hilfetexte und Ersatzbeschriftungen verwenden die gewählte Editor-Sprache.
6. Runtime-Assets über `modules.resources.find_asset(...)` / `find_asset_directory(...)` auflösen. **Keine cwd-abhängigen Pfade** und keine `GamePICs/`-Pfade zur Laufzeit.
7. Große Bilder **erst nach Bedarf laden und skalierte Varianten cachen**. Originale nicht zerstörend verkleinern. Nur tatsächlich aktive Assets in die EXE übernehmen.
8. Die Spiel-Koordinaten, Level-JSON-Versionen 1–3, Classic, Spieltests und Dachmaske dürfen bei Grafikarbeiten nicht stillschweigend verändert werden.
9. Staged Assets ändern **nicht unmittelbar** die Laufzeitgeschwindigkeit. GitHub-Ordner umbenennen bringt keine Frame-Millisekunden; Ladevorgänge, Caching und Renderkosten müssen getrennt gemessen werden.
10. Änderungen in **separaten PRs** durchführen: (a) UI-Button-Mapping, (b) Snake-Skins, (c) FrostAge-Gegner/Projektile/Items. Compile, Headless-Tests, CI, Paketinhalte und sichtbaren Windows-Test liefern.

## Repository- und Download-Größen

- **Windows-Build:** Das Workflow-Skript `.github/workflows/python-app.yml` bündelt explizit `Dark_Snake/assets` (und Python-/Modulcode), **nicht den Ordner `GamePICs`**. Staging/Referenzbilder gelangen deshalb nicht allein durch das Hochladen in die EXE.
- **GitHub-Quellcode-Download / Clone:** Hier bleiben `GamePICs`-Originale dagegen Teil des Repositorys. **Nur Verschieben in einen anderen Ordner desselben Repositorys spart keinen Clone-/ZIP-Speicher.** Erst eine bewusste Trennung in externe Quelldaten, sparsamen Checkout oder Git-LFS-Konzept kann langfristig helfen. Kein Git-Verlauf-Rewrite ohne separate Planung.
- Für die 48 Editor-Buttons kommen rund 16,1 MiB an PNG-Dateien zum Laufzeitbestand hinzu. Beim Laden und Skalieren werden die verwendeten Varianten im Speicher vorgehalten.

## Projektstatus und nächste Arbeiten

- ✅ PR #154 · Roof/Foreground. ✅ PR #155 · Editorfenster, Seitenleisten und Kartenkamera.
- ✅ PRs #156–#166 · Originale der Editor-Buttons. ✅ PR #168 · Rand-Builder.
- ✅ PR #169 · Editor-Button-Integration: 48 Grafiken mit echten Aktionen verbunden, 33 Entwürfe reserviert.
- ✅ PR #170 · Neue Titelbildschirm- und World-Studio-Screenshots unter `GamePICs/`; in README und Galerie verwendet.
- ⬜ Nacharbeiten: reale Ansicht der beiden Roof-Buttons `layer_roof` und `view_roof` im Windows-Fenster prüfen; beide Action-IDs stehen bereits im Runtime-Katalog, eine noch fehlende Bildzuordnung ist durch die Dateiliste nicht belegt.
- ⬜ Neue volle **World-Background-Ebene** nach PR H als separates Konzept, nicht mit dem temporären Hintergrund-Spezialeffekt verwechseln.
- ✅ PR #174 · Sieben ergänzende Editorbilder, grafische Seitenreiter und Layer Explorer.
- ✅ PR #179 · Sprachschalter mit vorhandener DE/EN-Grafik und zweisprachiger Hilfe.
- 🔧 PR E · Interaktiver Lernmodus mit Grafiken für Start und Beispiele.
- ⬜ Lighting, Events/Trigger, erweiterte FrostAge-Profile, Snake-Skin-Galerie.

**Hinweis:** Ältere `PROJECT_STATE.md` / `DEV_STRUCTURE.md` enthalten Aussagen aus früheren Alpha-Ständen. Für eine Änderung immer **aktuellen Code, Tests und PRs** prüfen, statt alte Statusangaben ungeprüft zu übernehmen.

[📁 Staging-Übersicht](GamePICs/README.md) · [⚙️ Maschinenlesbarer Bestands-Snapshot](GamePICs/asset_inventory.json) · [🛣️ ROADMAP](ROADMAP.md)
