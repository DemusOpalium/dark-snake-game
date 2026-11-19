# DARK SNAKE – Windows-Boss-Teleport-Spieltest, 19.11.2026

## Ergänzung: Spielerabnahme Boss Rift Search B

- **PR #242 Boss Teleport A:** gemergt und im Windows-Spieltest visuell
  erfolgreich (schwarze Bodenlöcher, sink/emerge, Verlagerung).
- **PR #243 Wächter Rift Search B:** gemergt; Demus hat die
  Ganzkarten-Suche, den Schatten-/Tunneleffekt und das Auftauchen
  im Spiel bewusst getestet und als **gut spielbar** bestätigt.
  Seine Einstufung: **Tunnel-Fertigkeit auf Beta-Niveau**, nicht
  das gesamte Spiel auf Beta-Release-Level hochstufen.
- **Abnahmeentscheidung:** Beide Fertigkeiten als spielerisch
  akzeptiert markieren, ohne derzeit neue Balance- oder Effekt-
  Umbauten vorzunehmen.
- **Restbeobachtung:** Manchmal abgebrochener Ortswechsel.
  Die aktuelle Sicherheitslogik kann das absichtlich auslösen,
  wenn sich während der Ankunftsvorwarnung ein Objekt in die
  Landefläche bewegt. Keine verifizierte Fehlfunktion, aber
  künftige 1P-/2P-Langzeittests sollten den Abbruchgrund aus
  dem Kampfereignislog, die Framerate sowie die optische
  Ankunfts-/Hitbox-Synchronität bei Bedarf prüfen.
- **Technischer Audit (kein unmittelbarer Fix):** Zielwahl und
  AoE-Kollisionsmaske werden nur bei Teleportversuchen berechnet.
  Der globale Suchring ist ein weiterer reiner Render-Effekt.
  Erst mit Framezeit-Messungen entscheiden, ob eine Optimierung
  sinnvoll wird; aktuell keine spürbaren Probleme gemeldet.
- **Aktueller `main`:** Windows Alpha 2, CodeQL und Pages grün.
  Manuelle 2P-Validierung bleibt offen.
- **Nächster Roadmap-Fokus:** FrostAge-Gegner als isolierter,
  weltgebundener Vertikalschnitt; bestehende Teleports, Bossphase,
  Boss-HP und Auto-Shoot nicht anfassen.

---

## Spielerrückmeldung
- **Boss Teleport A / schwarze Bodenlöcher** sehen gut aus und
  funktionieren im realen Windows-Test mit etwa drei gezielt
  provozierten Ortswechseln.
- Ein weiterer Versuch wurde nicht vollständig ausgeführt.
  **Das ist noch kein nachgewiesener Bug**: Die aktuelle
  Landeprüfung bricht gezielt ab, wenn in der Vorwarnung Spieler,
  Gegner, Items oder andere Hindernisse das Zielfeld blockieren.
  Das vorhandene Event `boss_teleport_aborted` enthält den
  Abbruchgrund; der Runden-Speicherstand enthält solche Events
  leider nicht.
- Wunsch: Wächter/Ritter soll in einer späten Phase mit einem
  schwarzen Loch **das ganze Spielfeld nach Snake absuchen** und
  sich dann mit sichtbarer Vorwarnung näher heran teleportieren.
  Als eigenständige Phase-III-KI-Test-Fähigkeit umgesetzt.

## Neu hochgeladene Dateien
`round_progress(9).json`, `career_progress(9).json`,
`skin_inventory(8).json`, `settings(7).json`. Verglichen mit
dem unmittelbar vorherigen 12-Runden-Datensatz.

| Kennzahl | Vorher | Jetzt | Änderung |
|---|---:|---:|---:|
| Runden | 12 | 13 | +1 |
| Punkte gesamt | 23.167 | 24.027 | +860 |
| Besiegte Gegner | 333 | 347 | +14 |
| Besiegte Bosse | 21 | 22 | +1 |
| Items | 433 | 449 | +16 |
| Karriere-XP | 12.008 | 12.514 | +506 |
| Karriererang | 7 | 7 | unverändert |
| Freigeschaltete Skins | 12 | 12 | unverändert |

Neuester Lauf: `5944f41cc89b44ad8320587a8dc069c6`,
Classic 1P, vom 19.11.2026 21:21:13 bis 21:23:27 UTC
(22:21:13 bis 22:23:27 Berlin), **2:14 Minuten**,
Ebene 2, **860 Punkte**, **14 Gegner**, **1 Boss**,
**16 Items**, 3 Leben verloren, `finished_reason=life_depleted`.
`career_progress` bestätigt dazu +506 XP, Rang 7.

Benutzereinstellungen blieben vergleichbar:
`initial_speed=8`, `difficulty=1.0`,
`auto_shoot_interval=2`, `projectile_speed_factor=0.5`,
`boss_health_multiplier=1.0`.

Die Dateien beweisen, dass Spielrunde, Karriere und Skin-Verarbeitung
weiterhin funktionieren. Sie **enthalten keine** konkreten
Teleport-Positionen, Abbruchursachen, Phasenfolgen,
Trefferzahlen oder individuellen Bosskampfzeiten. Der visuelle
Teleport-Test ist daher durch die direkte Spielerrückmeldung,
nicht durch diese JSON-Dateien, bestätigt.

## Verbesserungen aus PR #243 (inzwischen gemergt)
1. **Wächter Phase III:** 1,45 s sichtbar über die ganze Karte
   wandernder Suchkreis aus schwarzem Loch, auch ohne lokale Sicht.
   Andere Boss-Typen und Wächter Phase II bleiben an ihre normale
   Sicht gebunden.
2. **Zielsuche am Scan-Ende:** aktuelle 1P/2P-Köpfe;
   danach getrennte 1,1-s-Landezielwarnung. Kein
   unmittelbarer Sprung auf den Spieler, mind. 3 Zellen Abstand.
3. **Abbruch-Rückmeldung:** 0,55 s schließender Schattenring,
   wenn die berechnete Landung neu belegt wird, statt eines
   abrupten visuellen Verschwindens.
4. Vorhandene Regeln erhalten: feste Sprites, Boss-HP,
   Projektilschaden, Snake-Kollision und Teleport-Sicherheitsmasken.

### Ursprünglicher QA-Plan (erste Spielerabnahme erfüllt)
Admin-KI-Test aktiviert, Level 3 Wächter in Phase III (<35 % HP)
bringen, Kopf weit vom Boss wegbewegen: globaler Ring, Suchdauer,
aktuelle Kopfposition und zusätzliche Lande-Vorwarnung prüfen.
In der Zielzone stehen bleiben oder hineinziehen:
Abbruch sichtbar, kein Schaden/Telefrag. Zweiten Spieler testen,
KI-Test abschalten und einmal Pause/Respawn durchführen.
Dann erst Draft-PR mergen.
