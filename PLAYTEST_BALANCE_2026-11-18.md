# DARK SNAKE · Spieltest- und Fortschrittsanalyse · 18.11.2026

**Zweck:** Reproduzierbare, anonymisierte **Test-Baseline** und die nächsten
modularen Entwicklungsschritte. Grundlage: freiwillig bereitgestellte lokale
Spielstände, Screenshots und zwei ältere Entwicklerberichte, mit dem zugehörigen
Spielcode auf `main` abgeglichen. **Keine Original-Spielstände, Spieler-/Profilnamen,
UUIDs, Geräteserien, Screenshots oder persönlichen Einstellungen in dieses
öffentliche Repository übernehmen.**

## 1 · Manuell bestätigte Spielprobe (Classic, 1P)

**BEOBACHTET durch den Projektinhaber:** Dark-Abyss-Game-Over, Eintrag in die
Top-10-Anzeige, neue gedimmte Schloss-Kacheln mit Ranglabels, alte P1-/P2-Skins,
animierte 2P-Vorschau. Die neuen Skin-Sperren werden grafisch angezeigt.
Der Belohnungs-/Rangabschluss ist **noch nicht Teil des Game-Over-Bildschirms**;
ein separat gestalteter UI-Bereich folgt erst in PR D.

| Kennzahl | Runde 1 | Runde 2 | Runde 3 | Gesamt |
| --- | ---: | ---: | ---: | ---: |
| Punktzahl | 3.030 | 2.458 | 3.152 | **8.640** |
| Gegner besiegt | 28 | 30 | 44 | **102** |
| Bosse besiegt | 3 | 2 | 3 | **8** |
| Items eingesammelt | 46 | 51 | 59 | **156** |
| Ingame-Level | 4 | 4 | 4 | – |
| Endgrund | letztes Leben | letztes Leben | Selbstblockade | – |
| Lebensverluste | 3 | 3 | 3 | **9** |
| UTC-Zeitstempeldifferenz | 3:26 | 4:27 | 4:49 | **12:42** |
| Karriere-XP (V1) | 1.413 | 1.200 | 1.650 | **4.263** |

**WICHTIG:** Die 12:42 Minuten sind reine Start-/End-Zeitdifferenzen, **keine
pausenkorrigierte aktive Spielzeit**. Sie dürfen nicht unbesehen zu einem
Überlebenszeit-Achievement werden. Kein Beleg für 2P-Spieltests oder alle
späteren FrostAge-Mechaniken durch diese drei Runden.

**Mittelwerte dieser drei Runden, nicht aller Spieler:** 2.880 Punkte,
34 Gegner, 2,67 Bosse, 52 Items, 1.421 XP und 4:14 Minuten
UTC-Wanduhrdifferenz je Runde.

### XP- und Rang-Audit

XP-Regel V1 aus `career_ranks.py`:

```text
xp_runde = (score // 10) + 10 * enemies_defeated
           + 200 * bosses_defeated + 5 * items_collected
```

| Quelle | XP | Anteil der 4.263 XP |
| --- | ---: | ---: |
| Punkte (Abrundung **je Runde**) | 863 | 20,24 % |
| Gegner | 1.020 | 23,93 % |
| Bosse | 1.600 | **37,53 %** |
| Items | 780 | 18,30 % |
| **Summe** | **4.263** | **100 %** |

Die Einzelrunden-XP passen zum Karriere-Log, **drei verschiedene Runden-
kennungen** passen zum Rundenjournal und zum Skin-Inventar. Vorsicht:
`8640 // 10 = 864` ist **nicht** der Punkte-XP-Wert der drei Runden,
weil zuerst **pro Runde** abgerundet wird (303 + 245 + 315 = 863).

Karriere: **Rang 4**, **4.263 Gesamt-XP**, Rang 5 beginnt bei **5.000 XP**:
**737 XP bis Rang 5**. Laufzeit-V1-Kurve bleibt vorerst erhalten.

Bei unverändert starkem Ergebnis wäre Rang 40 (390.000 XP) rechnerisch
nach rund **275 vergleichbaren Runden bzw. 19,4 Stunden** gemessener
Start-/End-Wandzeit zu erwarten. **UNSICHERE HOCHRECHNUNG**: nur drei
überdurchschnittlich erfolgreiche echte Runden, kein repräsentatives
Balancing; Pausen, Abbrüche und neue Gegnermechaniken fehlen.
Vor Balanceänderung deutlich größere Stichprobe unterschiedlicher
Spielstärken, Classic-1P, Classic-2P und FrostAge getrennt erheben.

### Freischalt-Audit

**Anonymisierte Bestandszahlen** aus dem lokalen Inventar:

- **3** abgeschlossene Runden verarbeitet; **3** bestätigte Rang-Rewards
  (Rang 2 = Head, Rang 3 = Body, Rang 4 = Head).
- **6** kostenlose Starter-Skins, **4** vor dem Upgrade aus den bestehenden
  Einstellungen übernommene Skins, **3** neue Rang-Rewards:
  **13 / 92** im lokalen Besitz (79 nicht besessen).
- Alle drei Rewards haben jeweils eine **andere bestätigte Rundenkennung**:
  bisher keine Doppelbelohnung; das `maximal 1 Skin pro Runde`-Prinzip
  ist für **diese Stichprobe** erfüllt.
- Gesperrte Optionen wurden im Screenshot sichtbar bestätigt.
  Ein vollständiger manueller 2P-Spieltest mit tatsächlich gesperrter
  und freigeschalteter Ausrüstung steht weiterhin aus.
- `.lock`-Dateien mit einem einzelnen Byte sind die erwarteten
  Sperrdatei-Platzhalter und **keine** Belohnung oder beschädigte JSON.

## 2 · Bestandsabgleich weiterer Testdateien

- **Leaderboard:** 25 historische Einträge in der lokalen Textdatei;
  die Spielanzeige sortiert und zeichnet die besten 10. Namen im Screenshot
  sind **freie Highscore-Eingaben, keine Achievement-Titel**.
  Plain-Black-Gestaltung = offener **UI-2D-Auftrag**, kein fehlender XP-Commit.
- **Settings:** P1/P2-Kopf- und Körperwahl sind jeweils gespeichert.
  Alte gewählte Outfits wurden im Inventar als Bestandsschutz übernommen.
- **World-Library:** 1 Welt, 3 benannte Level und 2 Level-IDs in der
  Reihenfolge. Das ist **noch keine** Freigabe der neuen FrostAge-Gegner.
- **Controls:** Schema-Version 2, 13 Tastenaktionen, 2 erkannte
  Geräte-Konfigurationen. Keine Auswertung oder Veröffentlichung von
  Gerätekennungen.
- **Entwicklerbericht 11.11.2026:** 30/30 ausgeführte Szenarioläufe,
  20 bis zum Zeitlimit, 7 natürliche Game Overs, 3 erwartete Game Overs,
  **0 technische Fehler**, 0 Timeouts, 10 unterschiedliche Szenarien.
  Es gab 26 Kollisionen, 37 Projektiltreffer, 21 Gegner-Tode und
  29 Item-Aufnahmen in diesem Simulatorprofil.
- **Historischer Bericht 13.09.2026:** 225/225 ausgeführte Szenarioläufe,
  200 reguläre Abschlüsse und 25 Game-Over-Läufe, **0 technische Fehler**.
  Testprofil: 120 Ticks / 2 virtuelle Sekunden, anders als die Novembersimulation
  mit bis zu 3.600 Ticks / 60 Sekunden. **Nicht direkt als gleicher
  Erfolgsmaßstab vergleichen** und nicht als Prüfung der neuen Skin-PRs ausgeben.
- Die oben genannten Simulationsberichte sind historische Entwicklungs-
  stichproben, **keine** Benchmark-Messung des aktuellen Builds.

## 3 · Nächster sinnvoller, separater Produkt-Schritt: Game Over / Karriere D

**Ziel:** Im bestehenden Dark Abyss, **nach finalem Game Over und
nach bestätigtem Journal-/Karriere-/Inventar-Abschluss**, anzeigen:
Punkte/Level/Gegner/Bosse/Items (bereits vorhanden), **XP dieser Runde**,
**Karriere-Rang vorher → nachher**, Gesamt-XP, XP bis nächsten Rang,
und falls vorhanden den **einen tatsächlich gespeicherten neuen Skin**
mit Bild/Name. Wenn keine Freischaltung: ehrliches `Heute kein neuer Skin`
bzw. `Nächstes Ziel: Rang X`. **Keine erfundenen Achievements**.

- Keine nachträglichen Rewards aus bloßem UI-Klick; nur aus
  `career_progress.json` / `skin_inventory.json` und bestätigter
  `round_id`.
- Bereits vergebene Runden beim Neustart nicht erneut als neue Gewinne
  inszenieren; Wiederherstellung der Daten bleibt möglich.
- **Highscore-Eingabe muss weiter benutzbar bleiben**; Game-Over-Layout
  ausreichend Platz für kleine Fenster und Fullscreen (mind. 900×620,
  1350×930). Kein Zeichnen über die Namenseingabe.
- Keine Dateioperationen pro Frame; vorbereitete Anzeigeobjekte/Caches.
  Ohne gültige Speicherstände muss ein ehrlicher Status erscheinen.
- Separate Tests 1P/2P, Rangwechsel / kein Rangwechsel, 0/1 Unlock,
  Legacy-Bestand und unlesbare Dateien. Manuelle Windows-Sichtabnahme.

### Kleine UX-Nachfolge: Spielstand-Ordner öffnen

Optionalen Button **`Spielstände öffnen`** in einem vorhandenen
Entwickler-/Optionen-Bereich anbieten. Zielverzeichnis **ausschließlich**
`modules.resources.DATA_DIR` (normalerweise `~/.dark-snake`), in dem
`round_progress.json`, `career_progress.json`,
`skin_inventory.json` sowie Einstellungen liegen. Ordner nur über
ein bestehendes, ausdrücklich angeklicktes UI-Ereignis öffnen;
Pfade plattformverträglich, Fehler sichtbar behandeln. **Kein**
Kopieren persönlicher Daten ins Repository, kein direkter Speicherdatei-
Editor und keine zweite Persistenzdatenbank.

### Spätere Balancing-Werkzeuge

- Einen **lokalen, anonymisierten Statistikexport** mit Anzahl/Rundenwerten,
  Schema-/Spielversion, Testprofil und verlässlicher Aktivzeitmessung vorsehen,
  bevor weitere zeitbasierte Erfolge freigegeben werden.
- Datenanalyse/Schwellenberechnung **offline** bzw. nach Game Over;
  nicht aus `draw()`, nicht pro Tick, keine ungefragten Selbständerungen
  an Spieldaten oder XP-Formel. Vorschläge aus echten Messungen erhalten
  Tests, Versionshinweise und werden **erst nach Review** umgesetzt.
- Schwierigkeitsgrade, Classic/FrostAge und 1P/2P **getrennt** auswerten.
  Gegnerstatistiken künftig mit stabilen Gegnertyp-IDs statt nur
  einem globalen Kill-Zähler erfassen.

## 4 · 17 neue FrostAge-Gegnerbilder (PR #213)

**BELEGT:** 17 neue einzelne PNGs wurden in `GamePICs/` auf `main`
eingeliefert (PR #213). Sie sind **Quelldateien**, noch **keine** neuen
spielbaren Gegner, nicht automatisch in der PyInstaller-EXE. Dateinamen
allein belegen weder Größe/Transparenz noch Kampfeigenschaften.
Vor Import jedes Motiv per Sichtprüfung, Alpha-/Maß-/Duplikatprüfung
und getesteter Runtime-Kopie abnehmen.

**Konzeptvorschlag, nicht freigegeben:**
- `frostage_eisskelett` · Standardgegner (Quelle: `Eisskelett`).
- `frostage_frostwisp` · flinker Spezialgegner (Quelle: `Frostwisp`).
- `frostage_frosttitan` · einzelner Boss-Prototyp (Quelle: `Frosttitan`).

Die restlichen **14** Motive bleiben im inventarisierten Staging, mit
späteren Profilen statt 14 neuen hardcodierten Klassen.

**Für jeden Gegner später eigene Datenfelder:** stabile Typ-ID, Welt/
Modus, Mindestlevel, Boss-/Normal-Rolle, maximale gleichzeitige Anzahl,
HP, Bewegung, Angriff, Schaden, Kollision, Hit-Intervalle, Projektil,
Drop-Tabelle, Animation (`idle`, `move`, `hit`, `death`; zunächst
Einzelbild), Grafikpfad und Schwierigkeits-Skalierung.

**Spawn-Gate ist Pflicht:** Ab FrostAge-Level 4 oder 5 **nur FrostAge-Pool**
in ausdrücklich aktivierter FrostAge-Welt/Modus, **nicht** einfach globale
Classic-Gegner ersetzen. Alte Classic-/Bosskampfregeln, 1P/2P,
Intro/Respawn, Levelwechsel und Performance durch Tests schützen.
FrostAge-Bossfight: normale Zufallsgegner pausieren bzw. nur ausdrücklich
zugewiesene Minions aktiv. Drei Prototypen zuerst getrennt nach Rolle
testen, dann den Pool stufenweise erweitern.

## 5 · Belegqualität / nächster Kontrollpunkt

| Bereich | Ergebnis | Status |
| --- | --- | --- |
| Round-/Career-/Inventory-V1 | Drei unterschiedliche Runden / XP / drei Grants passen zusammen | **DATEIEN GEPRÜFT** |
| FrostAge Skin-Galerie | Schlösser sichtbar, P1/P2-Auswahl fotografiert | **MANUELL BEOBACHTET** |
| XP & neuer Head im Dark Abyss | Auf Screenshots noch nicht sichtbar | **NOCH NICHT IMPLEMENTIERT** |
| Bestenlisten-Layout | Funktionale Top 10, alter Stil | **UI-2D OFFEN** |
| Ordnerzugriff | Benutzerverzeichnis derzeit manuell gesucht | **KOMFORTWUNSCH** |
| FrostAge 17 Gegner | Staging-PNGs eingecheckt | **NOCH NICHT SPIELBAR** |
| Aktuelle 1P/2P-Regressionssimulation mit neuen Gegnern | Neue Gegner nicht aktiv | **NICHT GETESTET** |

**Leitsatz:** Rohdaten privat halten, bestätigte Spielereignisse zentral
bewahren, auswertbare Statistiken versionssicher ableiten und neue Mechaniken
nur mit reproduzierbaren Tests + Windows-Spielprobe übernehmen.
