# 🐍 DARK SNAKE – Asset-Legende für Menschen und Coding-Agenten
**Bestandsprüfung:** 14.11.2026, Git-Commit `6e1e5c8e8ee6` nach PR #166. **Keine Umstrukturierung oder Grafik-Integration durch dieses Dokument.**

> **Kurzregel:** `Dark_Snake/assets/` = Spiel-/EXE-Laufzeitdaten. `GamePICs/` = Entwürfe, Originale, Uploads, Screenshots und zukünftige Spielgrafiken. Eine Datei im Repository ist **nicht automatisch im Spiel eingebunden**.

## Verbindliche Wege

| Pfad | Tatsächliche Aufgabe | Gehört derzeit zur Windows-EXE? |
| --- | --- | --- |
| `Dark_Snake/main.py` | Programmeinstieg | Code wird zur EXE gebaut |
| `Dark_Snake/modules/` | Spiellogik, Pygame-UI, World Studio, Katalog und Rendering | Ja, via PyInstaller |
| `Dark_Snake/assets/` | Laufzeitgrafiken, Levelvorlagen, Audio und Kataloge | **Ja**, `--add-data "Dark_Snake/assets;assets"` |
| `Dark_Snake/assets/graphics/frostage/` | 175 importierte FrostAge-PNGs plus `catalog.json` | **Ja** |
| `GamePICs/Incoming/Frost_Tiles/` | 175 unveränderte FrostAge-Originale + Importhinweise | **Nein**, nicht direkt |
| `GamePICs/Build/`, `File/`, `Effects/`, `Layers/` usw. | 81 **neu hochgeladene, englisch beschriftete Editor-Button-Bilder** in elf Gruppen (inkl. `EditorBigs/`) | **Nein**, noch nicht importiert |
| `GamePICs/DarkSnake-NeueHeads/` | 53 neue Head-Kandidaten / Rohentwürfe | **Nein**, noch nicht registriert |
| `GamePICs/DarkSnake-KörperNeuDesign/` | 15 Body-Kandidaten / Rohentwürfe | **Nein**, noch nicht registriert |
| `GamePICs/` (weitere Bilder) | Projekt-Screenshots, Referenzen, Konzeptgrafiken; einige in README verlinkt | Nur wenn separat in `assets/` importiert |
| `tests/` | Headless- und Funktionstests | Nein |
| `scripts/` | Build, Asset-Import, Benchmarks, Diagnose | Nein, soweit nicht separat mit eingebunden |
| `.github/workflows/` | Windows-Build, CodeQL, Release-Automation | Nein |
| `ROADMAP.md` | Verwirklicht / geplant und Reihenfolge | Nein |

**Zählbasis:** Das Repository enthält im Stand dieses Audits 344 Dateien unter `GamePICs/` (rund 119,8 MB) und 1.017 Dateien unter `Dark_Snake/assets/` (rund 125,2 MB, jeweils unkomprimierte Git-Dateigrößen). Der [JSON-Snapshot](GamePICs/asset_inventory.json) enthält **alle 81 neuen Button-Dateipfade** und **alle 68 neuen Kopf-/Körperdateipfade** samt Git-Blob-SHA und Dateigröße. Für den FrostAge-Import ist `catalog.json` das maßgebliche Laufzeitverzeichnis.

## Die 81 Editor-Buttons: elf Ordner

| Originalordner | Dateien | Einsatz |
| --- | ---: | --- |
| `Build` | 14 | Bauen, Rand links/rechts/oben/unten, Ecke, Mittelfeld, verschieben, Größe, Favoriten, Suche, Tile-Bibliothek |
| `Building Blocks` | 7 | Größere Kategorien: Ground Tile, Wall, Barrier, Roof, Lighting, Events |
| `EditorBigs` | 8 | Große Alternativdesigns: Ceiling, Collision, Damage, Events, Light, Roof, Slow, Floor Object |
| `Effects` | 5 | Damage, Slow, Effektwerte und Dachwerte |
| `File` | 9 | Neu, Öffnen, Speichern, Welten, Undo/Redo, Classic-Auswahl |
| `General` | 5 | Allgemeine Konzepte: Settings, Language, About, Exit |
| `Layers` | 9 | Boden, Objekte, Dach, Kollision, Sichtbarkeit, Layer Lock, Ebenen |
| `Learn` | 5 | Lernmodus, Beispiel, Guided Build (teilweise **geplant**) |
| `Miscellaneos` | 4 | Künftige Truhe, Coin/Item, D20 |
| `Test` | 6 | Vorschau, 1P, 2P, Dach-Demo, Test-Ende |
| `View` | 9 | Einpassen, Panel/Bibliothek, Zell-Inspektion, Overlays |

**Bildstatus:** Diese Button-Grafiken sind **benannte, gestaltete, ausgeschnittene Entwürfe mit teils englischem Schriftzug**. Es sind **keine** reinen textfreien `icon_id`-Icons. Die ältere Blueprint-JSON beschreibt abstrakte Icon-IDs; diese Namen dürfen **nicht ohne geprüfte Zuordnung** als Dateipfade interpretiert werden.

**Beispiele für überprüfbare Kandidaten** (Mapping nur geplant, **keine** aktuelle Spiel-Verknüpfung):

| Funktion / action id | Bildquelle |
| --- | --- |
| Speichern / `file_save` | `GamePICs/File/Save-removebg-preview.png` |
| Boden / `layer_ground` | `GamePICs/Layers/Ground-removebg-preview.png` |
| Objekte / `layer_objects` | `GamePICs/Layers/Objects-removebg-preview.png` |
| Dach / `layer_roof` | `GamePICs/Layers/Roof-removebg-preview.png` |
| WALL / `collision_wall` | `GamePICs/Building Blocks/Wall-removebg-preview.png` |
| BARRIER / `collision_barrier` | `GamePICs/Building Blocks/Barrier-removebg-preview.png` |
| Schaden / `effect_damage` | `GamePICs/Effects/Damage-removebg-preview.png` |
| Slow / `effect_slow` | `GamePICs/Effects/Slow-removebg-preview.png` |
| Rand links / `border_left` | `GamePICs/Build/Border_Left-removebg-preview.png` (**Rand-Builder noch geplant**) |
| Rand oben / `border_top` | `GamePICs/Build/Border_Top-removebg-preview.png` (**Rand-Builder noch geplant**) |
| Dachwerte / `roof_settings` | `GamePICs/Effects/Roof_Value-removebg-preview.png` |
| Test 1P / `test_player_1` | `GamePICs/Test/Test_1P-removebg-preview.png` |
| Karte einpassen / `view_fit_map` | `GamePICs/View/Fit_Map-removebg-preview.png` |

Die **vollständige** Zuordnung zwischen tatsächlichen Menüaktionen und Grafiken gehört in einen **separaten Integrations-PR**. Ein rein ähnlicher Name reicht nicht als Prüfung. `EditorBigs` sind große Kategoriegrafiken und nicht automatisch Ersatz für kleine Aktionsbuttons.

## FrostAge: Bereits integriert ≠ voll spielmechanisch aktiviert

- `GamePICs/Incoming/Frost_Tiles/`: **175 ursprüngliche PNGs**, darunter 126 Flächen-/Objekt-/Dachgrafiken, 11 AoE, 12 Menübuttons, 8 Gegner, 5 Items und 13 Projektile. Der Ordner ist **Staging**.
- `scripts/frostage_catalog.py --write` baut das Laufzeitpaket `Dark_Snake/assets/graphics/frostage/` aus dem Originalbestand; `--check` kontrolliert die Zuordnung. **Nicht manuell per Drag-and-drop Originale in die Laufzeitbibliothek umbenennen.**
- `Dark_Snake/modules/frostage_assets.py` lädt Asset-Metadaten aus `catalog.json` und Grafiken bei Bedarf. **Das ist der maßgebliche Katalog.**
- World Studio kann Grafikobjekte platzieren; **Roof/Foreground und Dach-Sichtfenster sind seit PR #154 spielbar**. Das Hauptmenü nutzt FrostAge-Buttonassets.
- Die neuen FrostAge-Gegner/Items/Projektile/AoE sind **nicht allein durch den PNG-Import als individuelle neue Spielmechanik implementiert**. Datenprofile, Spawns, Kollisionen, Treffer und Tests sind eigene Arbeitspakete.
- Grafik, Render-Ebene, Kollision und Schaden sind **vier getrennte Eigenschaften**. Ein Feuerbild löst nicht automatisch einen Damage-Effekt aus.

## Neue Snake-Heads und Bodies: Noch keine freischaltbaren Skins

- 53 Dateien liegen unter `GamePICs/DarkSnake-NeueHeads/`, 15 unter `GamePICs/DarkSnake-KörperNeuDesign/`; darunter Roh-Snips und andere Designreferenzen. Noch keine Freigabe aller Dateien als einzelne 30×30-Sprites.
- `Dark_Snake/modules/customization.py` bietet derzeit **vier fest verdrahtete Kopfoptionen**. Für Bodies liest es `assets/graphics/SnakeBodysBibliothek` per relativem Arbeitsverzeichnis; dieser Pfad ist **nicht** über `modules.resources` aufgelöst und sollte in einem eigenen Fix aktualisiert werden.
- Nächster **getrennter** Character-/Customization-PR: Quellen sichten, gültige Heads/Bodies auswählen, stabile Skin-IDs vergeben, portable Pfade und Liste/Katalog verwenden, scrollbares responsives Auswahlraster, Live-Vorschau bei Spielgröße und Head/Body-Kombinationsprüfung. Erst danach optional Unlocks über Spielziele; Freischaltungen **noch nicht aktiv**.

## Agenten-Regeln für jede künftige Asset-Aufgabe

1. **Status zuerst bestimmen:** `runtime`, `staged`, `reference`, `candidate` oder `planned`. Einen geplanten Button nie als funktionierende Spielmechanik ausgeben.
2. **Originale erhalten.** Aus `GamePICs/` ausgewählte, geprüfte PNGs nach `Dark_Snake/assets/` **kopieren** bzw. aus dortigem Staging katalogisieren; Originale und Screenshots nicht löschen oder verschieben, solange sie referenziert sind.
3. Vor jeder Nutzung **Datei und Inhalt** kontrollieren: Name, Schriftzug, Transparenz, Bildabmessungen, Blickrichtung, 24–48-Pixel-Lesbarkeit. Dateiname allein beweist nicht korrekte Zuordnung.
4. Eine **eindeutige stabile Action-ID → bestehende PNG-Datei**-Zuordnung anlegen, statt Buttonfunktionen über den deutschen/englischen Beschriftungstext zu steuern.
5. Die neuen Button-PNGs enthalten teilweise **englischen Text**; eine allgemeine DE/EN-Umschaltung übersetzt diesen Text nicht. Für eine vollständig deutsche Oberfläche alternative DE-Grafiken oder separaten UI-Text planen.
6. Runtime-Assets über `modules.resources.find_asset(...)` / `find_asset_directory(...)` auflösen. **Keine cwd-abhängigen Pfade** und keine `GamePICs/`-Pfade zur Laufzeit.
7. Große Bilder **erst nach Bedarf laden und skalierte Varianten cachen**. Originale nicht zerstörend verkleinern. Nur tatsächlich aktive Assets in die EXE übernehmen.
8. Die Spiel-Koordinaten, Level-JSON-Versionen 1–3, Classic, Spieltests und Dachmaske dürfen bei Grafikarbeiten nicht stillschweigend verändert werden.
9. Staged Assets ändern **nicht unmittelbar** die Laufzeitgeschwindigkeit. GitHub-Ordner umbenennen bringt keine Frame-Millisekunden; Ladevorgänge, Caching und Renderkosten müssen getrennt gemessen werden.
10. Änderungen in **separaten PRs** durchführen: (a) UI-Button-Mapping, (b) Snake-Skins, (c) FrostAge-Gegner/Projektile/Items. Compile, Headless-Tests, CI, Paketinhalte und sichtbaren Windows-Test liefern.

## Repository- und Download-Größen

- **Windows-Build:** Das Workflow-Skript `.github/workflows/python-app.yml` bündelt explizit `Dark_Snake/assets` (und Python-/Modulcode), **nicht den Ordner `GamePICs`**. Staging/Referenzbilder gelangen deshalb nicht allein durch das Hochladen in die EXE.
- **GitHub-Quellcode-Download / Clone:** Hier bleiben `GamePICs`-Originale dagegen Teil des Repositorys. **Nur Verschieben in einen anderen Ordner desselben Repositorys spart keinen Clone-/ZIP-Speicher.** Erst eine bewusste Trennung in externe Quelldaten, sparsamen Checkout oder Git-LFS-Konzept kann langfristig helfen. Kein Git-Verlauf-Rewrite ohne separate Planung.
- **Praktischer Beschluss:** Erst **Dokumentation und Kennzeichnung**, nicht sofort massenhaft umbenennen/löschen. Nach bestätigter Integration mit Messungen über echte Paketgröße oder Ladezeit sprechen.

## Projektstatus und nächste Arbeiten

✅ PR #154: Roof/Foreground. ✅ PR #155: neue Editorfenster-/Sidebar-/Kartenkamera-Struktur.  
✅ PRs #156–#166: neu hochgeladene Grafiken im Repository. **Noch keine Einbindung der 81 Bilder in die Editorsteuerung.**  
⬜ Rand-Builder, vollständige Ebenensteuerung und Undo-sicheres Löschen.  
⬜ DE/EN-Hilfe und interaktiver Lernmodus.  
⬜ Lighting, Events/Trigger, erweiterte FrostAge-Profile, Snake-Skin-Galerie.

**Hinweis:** Ältere `PROJECT_STATE.md` / `DEV_STRUCTURE.md` enthalten Aussagen aus früheren Alpha-Ständen. Für eine Änderung immer **aktuellen Code, Tests und PRs** prüfen, statt alte Statusangaben ungeprüft zu übernehmen.

[📁 Staging-Übersicht](GamePICs/README.md) · [⚙️ Maschinenlesbarer Bestands-Snapshot](GamePICs/asset_inventory.json) · [🛣️ ROADMAP](ROADMAP.md)
