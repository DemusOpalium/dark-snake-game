# FrostAge / Frost World — Asset-Eingang

**Status: Quellgrafiken, noch NICHT in den Laufzeit-Loader integriert.**

Dieser Ordner ist der Import-Stagingbereich für das von Demus vorbereitete FrostTiles-Paket vom 13.11.2026. Vorhandene PNG-Dateien unverändert erhalten; keine automatische 30×30-Konvertierung im Repository.

## Erwartete Originalordner

| Ordner | Bilder im gelieferten ZIP | Transparente PNGs | Vollständig deckende PNGs |
| --- | ---: | ---: | ---: |
| `1x1` | 35 | 9 | 26 |
| `2x1` | 11 | 11 | 0 |
| `2x2` | 17 | 7 | 10 |
| `4x4` | 21 | 7 | 14 |
| `5x5` | 4 | 4 | 0 |
| `6x6` | 3 | 3 | 0 |
| `8x8` | 17 | 9 | 8 |
| `10x1` | 5 | 0 | 5 |
| `1x10` | 5 | 0 | 5 |
| `Dach` | 8 | 8 | 0 |
| **Summe** | **126** | **58** | **68** |

Die Ordnerbezeichnungen sind zunächst nur Autor-Angaben, **keine** technisch validierten Raster-Footprints. Prüfen: Die gelieferten fünf `10x1`-PNG sind im Original hochformatig (ca. 295×1110 px), die fünf `1x10`-PNG querformatig (ca. 2000×220 px). Auch die `2x1`-PNG sind überwiegend hochformatig. **Nicht stillschweigend drehen oder stauchen.** Vor Verwendung Rasterausrichtung mit Demus klären bzw. anhand der tatsächlichen Grafiken im Editor bestätigen.

## Codex-Import

- Das aktuell bestehende `Dark_Snake/modules/graphics.py` liest nur direkte Dateien aus `assets/graphics/tiles/` und skaliert sie auf ein Rasterfeld (zurzeit 30×30 px). **Die PNGs hier nicht einfach direkt in diesen Ordner kopieren.**
- Künftiger Multi-Tile-Loader: Bilder unverändert als Original speichern, im Spiel mit separat spezifiziertem Raster-Footprint proportional bzw. per transparentem Canvas zeichnen, keine Verzerrung.
- `Dach` ist als späterer **Roof / Foreground**-Layer gedacht: über Spieler, Gegner und Bosse, aber unter dem HUD; weiche lokale Transparenz um die Schlange folgt in eigenem PR.
- Grafik/Kollision/Effekt/Objekt/Foreground voneinander unabhängig halten; alte benannte JSON-Level weiter unterstützen.
- Diese Upload-Arbeit ist **nur Quellgrafikverwaltung**, keine Änderung an Spielmechanik, Renderpipeline oder Tests.

## Herkunft

Die PNGs wurden vom Projektinhaber manuell zugeschnitten, benannt und in `FrostTiles.zip` bereitgestellt. Die Kategorie `Dach` ist ein erster Entwurf, noch keine im Spiel benutzbare Foreground-Ebene.
