# DARK SNAKE — Boss-/Auto-Shoot-Balance, 19.11.2026

## Anlass

Manueller Windows-Spieltest nach PR #239: Boss Phases funktionieren, Schlangenkörper
wieder solid und Auto-Shoot-Pickup schießt wieder. Dadurch wird die eigentliche
Balance sichtbar: **30 HP** frühe Bossleben bei **10 HP** je Player-Grid-Schuss,
gleichzeitig 1 + bis zu 6 Extraschüsse pro Pickup. Bereits eine Dreier-Salve
kann einen frühen Boss erledigen, bevor HP-Phasen und Verteidigung spielen.

Die zuletzt bereitgestellten `round_progress`-/`career_progress`-Daten melden
**11 abgeschlossene Runden, 20 besiegte Bosse, Karriererang 7/11.319 XP**.
Die beiden jüngsten Runden melden 2 Boss-Siege in 4:48 und 2 Boss-Siege
in 4:15 **Gesamtrundenzeit**. Sie enthalten **keine einzelnen Bosskampf-
Dauern oder Trefferzahlen**; daraus lassen sich keine exakten Killzeiten
ableiten. Direkter Spielerbeobachtung zufolge dauerte ein früher Kampf
mit Auto-Shoot teils 1–2 Sekunden. Das ist unser primärer Balancebefund.

Nutzer-Einstellungen: `auto_shoot_interval = 2 s`,
`projectile_speed_factor = 0.5`, `boss_health_multiplier = 1.0`.

## Neue Referenz (nur Auto-Shoot und Boss-HP)

| Frühere Stufe | Persönlichkeit | HP vorher | HP neu | Auto-Treffer (2 HP) | Theoretisch bei 2 s, 1P |
|---|---|---:|---:|---:|---:|
| 1 | Medusa | 30 | 64 | 32 | ~64 s |
| 2 | Jäger | 30 | 70 | 35 | ~70 s |
| 3 | Wächter | 30 | 84 | 42 | ~84 s |
| 4 | Medusa | 30 | 82 | 41 | ~82 s |

Berechnung: 64 Basis-HP + 6 pro Level nach Level 1; Wächter +8 HP;
vorhandener `boss_health_multiplier` wird danach angewendet.

| Mechanik | Bisher | Neu |
|---|---|---|
| Auto-Schuss je Kopf und Intervall | 1 + bis zu 6 gestapelte Shots | **1** |
| Auto-Schuss gegen Boss | 10 HP | **2 HP** |
| Auto-Schuss gegen normale Gegner | 1 HP | **1 HP** (unverändert) |
| Normale Gegnerleben | zufällig 1–3 HP | **1–3 HP** (unverändert) |
| Spieler-Feuerball | 3 HP, 4,5 px/Frame | **unverändert** |
| Geschwindigkeit Player-Grid-Shot | max. 4,5 px/Frame | **unverändert** |
| Auto-Intervall | Einstellung: 2 s | **unverändert** |
| Wiederholte Pickup-Items | multiplizierten Kugelanzahl | **verlängern nur Wirkungsdauer** |
| Phasenschwellen | 70 % / 35 % | **unverändert**, nun mit mehr Zeit |

**Achtung:** Die theoretischen Sekunden gelten nur bei 100 % Trefferquote,
ohne Feuerball, Spezialschaden, Schilde, Swipe, Positionswechsel und
Spielerwechsel. Treffer/Misses verlängern, Feuer/Specials verkürzen die
Zeit. Bei zwei Köpfen können 2P-Kämpfe kürzer ausfallen. Die tatsächliche
Kampfdauer muss über mehrere reale Windows-Runden gemessen werden.

## Beobachtbarkeit & Freigabe

Das bestehende Combat Event `boss_defeated` enthält jetzt zusätzlich
`boss`, `max_health`, `duration_seconds`. Über `boss_damage` sind
Trefferquellen und effektiver Schaden schon verfügbar. Ein normaler
`round_progress.json`-Datensatz speichert weiterhin nur Rundenwerte,
nicht den Ereignisstrom. Dauervergleich im Entwickler-Log vornehmen.

Automatisch prüfen: 1P/2P ein Schuss je Kopf; mehrfaches Einsammeln
erzeugt keine Extras; HP-Skalierung und Phasen bei 70/35 %; bestehende
Feuerball-/Schadens-/Boss-Defenseregeln; Windows Alpha 2 und CodeQL.

**Merge-Gate:** Erst CI grün und manueller Test (Boss-KI an,
Medusa → Jäger → Wächter; Feuerball, Auto-Shoot und HP-Phasen).
Kein Editor- oder Asset-Umbau. Später: optional separate Schusswaffen,
wenn jede ihre eigene Damage-/Cooldown-Balance besitzt.
