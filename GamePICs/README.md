# 📁 GamePICs – Artwork-Werkstatt / Nicht direkt die Laufzeitassets

**Hier liegen Originalgrafiken, Uploads und Referenzbilder.** Das Spiel lädt normalerweise nur die freigegebenen Dateien unter `Dark_Snake/assets/` und ist nicht von der Existenz dieses Ordners abhängig. Das Windows-Paket nimmt `GamePICs/` nicht pauschal auf.

## Neu hochgeladen am 14.11.2026

| Ordner | Dateien | Zweck | Status |
| --- | ---: | --- | --- |
| `Build/` | 14 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Building Blocks/` | 7 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `EditorBigs/` | 8 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Effects/` | 5 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `File/` | 9 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `General/` | 5 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Layers/` | 9 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Learn/` | 5 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Miscellaneos/` | 4 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `Test/` | 6 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `View/` | 9 | Beschriftete Editor-UI-/Kategorie-Buttons | **Staging; noch nicht im Editor eingebunden** |
| `DarkSnake-NeueHeads/` | 53 | Head-Entwürfe, Snips und Designvarianten | Kandidaten; nicht registriert |
| `DarkSnake-KörperNeuDesign/` | 15 | Body-Entwürfe, Snips und Designvarianten | Kandidaten; nicht registriert |

**Zusammen:** 81 Editor-Button-Grafiken (einschließlich 8 `EditorBigs`), 53 Head- und 15 Body-Dateien.

## Bestehendes FrostAge-Staging

- `Incoming/Frost_Tiles/`: 175 Original-PNGs, nach Kategorie organisiert; [Importbeschreibung](Incoming/Frost_Tiles/README.md).
- Die **bereits freigegebenen** 175 FrostAge-Bilddateien liegen separat in `../Dark_Snake/assets/graphics/frostage/` mit `catalog.json`.
- Grafikbestand allein bedeutet nicht, dass Gegner, Projektile, Items und Events bereits individuelle Spieleigenschaften besitzen.

## Für Menschen und Codex

**Vor Grafikänderungen [ASSET_GUIDE.md](../ASSET_GUIDE.md) lesen.** Ein [JSON-Inventar](asset_inventory.json) listet die vollständigen 81 Button- und 68 Head-/Body-Quelldateien samt Git-Blob-SHAs. Die Dateinamen aus dem Upload unverändert erhalten, bis geprüfte `action_id → asset`-Zuordnungen umgesetzt sind.

**Nicht** den gesamten Inhalt dieses Ordners in die Windows-EXE verpacken, nur weil die Dateien vorhanden sind. Bitte Screenshots und Konzepte auf `GamePICs/` belassen; ausgewählte Laufzeitassets nach geprüftem Import separat in `Dark_Snake/assets/` ablegen.
