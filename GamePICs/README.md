# 📁 GamePICs – Artwork-Werkstatt

Hier liegen Originalgrafiken, Uploads und Referenzbilder. Das Windows-Paket bündelt die freigegebenen Laufzeitdateien unter `Dark_Snake/assets/`.

## Editor-Grafiken vom 14.11.2026

| Originalordner | Originale | In World Studio | Reserviert |
| --- | ---: | ---: | ---: |
| `Build/` | 14 | 11 | 3 |
| `Building Blocks/` | 7 | 2 | 5 |
| `EditorBigs/` | 8 | 0 | 8 |
| `Effects/` | 5 | 5 | 0 |
| `File/` | 9 | 9 | 0 |
| `General/` | 5 | 1 | 4 |
| `Layers/` | 9 | 6 | 3 |
| `Learn/` | 5 | 3 | 2 |
| `Miscellaneos/` | 4 | 0 | 4 |
| `Test/` | 6 | 6 | 0 |
| `View/` | 9 | 8 | 1 |
| **Gesamt** | **81** | **51** | **30** |

Die 51 eingebundenen PNGs aus diesem Bestand liegen bytegleich in `Dark_Snake/assets/graphics/editor_ui/`. Alle 81 Originale behalten ihren Pfad. Der Laufzeitkatalog verbindet die verwendeten Dateien über Action-IDs mit den Editoraktionen. Die Asset-Legende listet die reservierten Grafiken und ihre geplante Verwendung. [Laufzeitkatalog](../Dark_Snake/assets/graphics/editor_ui/catalog.json) · [Asset-Legende](../ASSET_GUIDE.md)

## Nachtrag vom 15.11.2026

Die sieben RGBA-Dateien unter [Nachtrag Fehlende Buttons](Nachtrag%20Fehlende%20Buttons/) wurden in PR #173 hochgeladen. World Studio verwendet sie für Hilfe, Rand-Builder, Dachübertragung, Grafikmodus, kombinierten Grafik-/Kollisionsmodus, Eigenschaften und Vorschau-Ende. Vier Reiter im rechten Arbeitsbereich verwenden dieselben Dateien wie die zugehörigen Hauptaktionen und behalten eigene Action-IDs. [Zuordnung im Laufzeitkatalog](../Dark_Snake/assets/graphics/editor_ui/catalog.json)

PR D verwendet zusätzlich das vorhandene DE/EN-Motiv für den Sprachschalter `nav_language`. [Originalgrafik](General/De-En_Language-removebg-preview.png)

PR E verwendet die Motive **My First Level** und **Examples** für den Kursstart und das Beispiel im Learn-Reiter. **Zurück**, **Weiter** und **Wiederholen** verwenden übersetzte Textschaltflächen. Der Laufzeitkatalog umfasst damit 58 PNGs für 62 Action-IDs. [My First Level](Learn/My_FIrst_LvL-removebg-preview.png) · [Examples](Learn/Examples-removebg-preview.png)

## Skin-Entwürfe

In `DarkSnake-NeueHeads/` liegen 53 Kopfdesigns, in `DarkSnake-KörperNeuDesign/` 15 Körperdesigns. Geeignete Einzelbilder sollen in einem eigenen PR für die geplante Galerie ausgewählt werden.

## Bestehendes FrostAge-Staging

- `Incoming/Frost_Tiles/`: 175 Original-PNGs, nach Kategorie organisiert; [Importbeschreibung](Incoming/Frost_Tiles/README.md).
- Die **bereits freigegebenen** 175 FrostAge-Bilddateien liegen separat in `../Dark_Snake/assets/graphics/frostage/` mit `catalog.json`.
- Grafikbestand allein bedeutet nicht, dass Gegner, Projektile, Items und Events bereits individuelle Spieleigenschaften besitzen.

## Für Menschen und Codex

Der datierte Snapshot enthält alle 81 Button- und 68 Head-/Body-Quelldateien samt Git-Blob-SHAs. Der Laufzeitkatalog hält den aktuellen Einsatz fest. [Staging-Snapshot](asset_inventory.json) · [Laufzeitkatalog](../Dark_Snake/assets/graphics/editor_ui/catalog.json)

**Nicht** den gesamten Inhalt dieses Ordners in die Windows-EXE verpacken, nur weil die Dateien vorhanden sind. Bitte Screenshots und Konzepte auf `GamePICs/` belassen; ausgewählte Laufzeitassets nach geprüftem Import separat in `Dark_Snake/assets/` ablegen.
