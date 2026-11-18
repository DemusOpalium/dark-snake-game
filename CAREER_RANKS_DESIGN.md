# DARK SNAKE · Karriere B – 40 Ränge und XP (Regeln V1)

**Stand: 18.11.2026 · Scope: Fortschritt aus echten Classic-Runden.**
Dies ist die zweite Schicht nach [ROUND_PROGRESS_DESIGN.md](ROUND_PROGRESS_DESIGN.md).
**Noch keine** Skin-Sperre, Belohnung, Achievements oder fertiger Karrierebildschirm.

## Quelle und Garantie

Die seit PR #208 dauerhaft gespeicherten Classic-1P-/2P-Runden unter
`~/.dark-snake/round_progress.json` bleiben **die einzige Quelle**
für tatsächlich erzielte Punkte, Gegner-, Boss- und Item-Zahlen.

Eine neue Datei `~/.dark-snake/career_progress.json` hält fest:
- `schema_version: 1` und `rules_version: 1`
- `awards`: pro tatsächlich gespeichertem `round_id` exakt ein XP-Eintrag
- `total_xp`: Summe dieser XP-Einträge
- `rank`: aus `total_xp` berechneter Karriererang

Keine Neubewertung alter, bereits gespeicherter XP, wenn künftig die
Balanceregeln geändert werden. **Eine Änderung der Regelversion erfordert
eine explizite Datenmigration**. Die alten Hochscores werden nicht erraten,
sondern nur *echte* seit dem Journal-Feature abgeschlossene Runden übernommen.

Bei finalem Game Over erfolgt erst der atomare Rundeneintrag, anschließend die
separat atomare XP-Aktualisierung. Falls die zweite Speicherung fehlschlägt,
führt der nächste echte Spielstart eine Nachholung anhand der noch nicht
gutgeschriebenen Runden-IDs durch. Die Betriebssystem-Sperrdatei schützt
auch bei zwei gleichzeitig geöffneten EXEs vor doppeltem XP.

### Versionierte XP-Regel

```text
Runden-XP = (Punkte // 10) + (besiegte Gegner × 10)
          + (besiegte Bosse × 200) + (gesammelte Items × 5)
```

Beispiel einer geprüften Spielrunde mit **3030 Punkten, 28 Feinden,
3 Bossen, 46 Relikten**: 303 + 280 + 600 + 230 = **1413 XP**.

Weder Ingame-Level noch Wanduhr-Spielzeit zählen erneut als XP,
um Doppelzählungen bzw. erfundene Pausen-Zeiten zu vermeiden. Es gibt
auch noch **keine** Extra-XP für 2P, tägliche Logins, Truhen oder Boss-IDs.
So kann alles sauber später als eigene validierte Ereignisart folgen.

### 40 Ränge, feste IDs

```text
Erforderliche Gesamt-XP für Rang n: 250 × (n - 1) × n
n = 1 bis 40
```

| Rang | Gesamt-XP ab | Rang-ID |
| ---: | ---: | --- |
| 1 | 0 | `rank_01` |
| 2 | 500 | `rank_02` |
| 3 | 1.500 | `rank_03` |
| 5 | 5.000 | `rank_05` |
| 10 | 22.500 | `rank_10` |
| 20 | 95.000 | `rank_20` |
| 30 | 217.500 | `rank_30` |
| 40 | 390.000 | `rank_40` |

Kumulative XP bleiben nach Rang 40 erhalten; der sichtbare Rang ist auf 40
begrenzt. IDs sind stabil, spätere Anzeigenamen/Icons kommen in eigener
Konfiguration, nicht über Dateinamen der Heads.

Diese Schwellen sind ein **erster Balance-Vorschlag**. Vor einem öffentlichen
Release mit regulären Speicherständen müssen wir ihre Spielbarkeit
gemeinsam anhand echter Runden und einer Langzeitsimulation prüfen.
Änderungen nach einer Freigabe benötigen eine geregelte Migration.

## Erhaltung von Funktionen und Tests

- `game.experience` und `game.level` (innerhalb der Runde) bleiben unverändert.
- Highscore-Eingabe, Dark-Abyss-Animationen, Audio, Steuerung, P1/P2,
  Respawn und Raster bleiben unverändert.
- Kein Einlesen/Schreiben oder Neuberechnen in `update()`/`draw()` oder
  Treffer-Schleifen; nur beim Spielstart und finalen Game Over.
- Headless-Entwicklersimulationen schreiben weiter keine echten Karrierewerte.
- Fremde Schema-Versionen, widersprüchliche Summen und doppelte UUIDs
  werden nicht stillschweigend überschrieben.
- Die lokalen JSON-Dateien sind kein manipulationssicherer Online-Speicher.
- Automatisierte Tests: 40 Grenzwerte, XP-Formel, Crash-Wiederherstellung,
  parallele Reconciliation, Idempotenz, 1P/2P-Ende und Headless-Isolation.
- **Windows-Sichttest: NICHT GETESTET**. Das Rang-/XP-Ergebnis ist in dieser
  Teilstufe **nur im gespeicherten JSON** sichtbar. Der FrostAge-Abschlussbildschirm
  mit Rang, Titel, XP und später Belohnung folgt im geplanten PR D.

## Nächste getrennte Arbeitspakete

**C – Skin-Inventory**: Katalog-IDs und Freischaltbedingungen mit Bestandsschutz
für bisher gewählte P1/P2-Skins. Keine kosmetischen Doppeleinträge.

**D – Dark Abyss**: Karriere-Rang, XP-Fortschritt und ggf. genau ein neuer
kosmetischer Gegenstand beim Spielende sichtbar; Highscore-Eingabe erhalten.

**E – Erfolge**: nur überprüfbare Trigger (auch individuelle Boss-/Truhen-IDs
erst dann, wenn Events existieren), höchstens ein Kosmetik-Unlock pro Runde.
