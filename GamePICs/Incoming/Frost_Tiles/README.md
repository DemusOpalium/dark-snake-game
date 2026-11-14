# FrostAge / Frost World — Asset-Eingang

**Status.** Die 175 Originalgrafiken bilden die Quelle des FrostAge-Laufzeitkatalogs. Im F2-Editor sind sie als Grafikobjekte auswählbar.

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

Zusätzlich liegen hier 11 AoE-Grafiken, 12 Menübuttons, 8 Gegner, 5 Items und 13 Projektile. Die Ordner `10x1`, `1x10` und `2x1` sind nach der tatsächlichen Ausrichtung als 1×10, 10×1 und 1×2 im Katalog erfasst. Der Editor zeichnet die Bilder proportional.

## Laufzeitkatalog

- `python scripts/frostage_catalog.py --write` erzeugt den Katalog und identische Laufzeitdateien unter `Dark_Snake/assets/graphics/frostage/`. `--check` prüft den Bestand, die Bildmetadaten und die unveränderten Bytes.
- Der Katalog unterscheidet Ground, Walls, Objects, Roof, AoE, Enemies, Projectiles, Items und Menu. Diese Zuordnungen steuern die Bibliothek. Die Roof-/Foreground-Ebene mit Sichtfenstern ist seit PR #154 spielbar; individuelle Gameplay-Profile für FrostAge-Gegner, Projektile und Items folgen in eigenen PRs.
- Die Laufzeitkopien belegen rund 72,2 MiB vor dem Verpacken. Die Windows-CI prüft die Prüfsummen der tatsächlich in der EXE enthaltenen PNGs.

## Herkunft

Die PNGs wurden vom Projektinhaber manuell zugeschnitten, benannt und in `FrostTiles.zip` bereitgestellt. Die Kategorie `Dach` wurde in PR #154 als spielbare Roof-/Foreground-Ebene mit sichtbaren Fenstern für die Spieler umgesetzt.
