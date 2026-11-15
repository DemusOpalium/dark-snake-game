# 👹 DARK SNAKE – BOSSFIGHT 2.0: Begegnungs- und Erlebnisdesign
**Konzeptnotiz vom 15.11.2026 · von Demus und Irian aus einem echten Classic-Spieltest abgeleitet.**  
**Status: 💡 Planung, nicht implementiert.** Maßgeblich für Termine und Häkchen bleibt die [ROADMAP.md](ROADMAP.md), Abschnitt 06. Dieses Dokument beschreibt **wie** der Bosskampf später funktionieren soll, nicht einen bereits spielbaren Funktionsumfang.

## 1. Spielerbeobachtung / Problem

Beim aktuellen Classic-Spieltest funktionieren die Boss-Schüsse und das Ausweichen bereits und machen Spaß. Der Kampf wirkt jedoch stellenweise wie gegen einen schwebenden Geist: Nach einer hörbaren Ankündigung bleibt der Boss kurz stehen; manche Begegnungen enden sehr schnell, andere dauern länger. Es fehlt vor allem eine durchgehende Inszenierung aus eindeutiger Bossidentität, vorbereiteten Angriffen, Zustandsanzeige, Sound und einem fühlbaren Sieg.

**Codeabgleich, Stand `main` vom 15.11.:**
- `Dark_Snake/modules/game.py::start_boss_fight()` wählt derzeit zufällig `Boss` oder `Boss2` und startet den Zustand `BOSS_FIGHT`.
- `damage_boss()` verarbeitet HP, Rückkehr zu `GAME`, Score, Explosion und eine kurze Achievement-Meldung. Das ist eine vorhandene Basis, aber noch keine inszenierte Bosssequenz.
- `level_up()` erhöht Level und startet aktuell eine Bossbegegnung. Das geplante Adventure-Abschnittsmodell ist **nicht** mit diesem Ablauf gleichzusetzen.
- Der normale Gegner-Spawn in `Game.update()` wirkt derzeit mit `projectile_shoot` verschachtelt. Das ist **ein separater Bug-/Designverdacht**, keine mit diesem Konzept beauftragte Gameplayänderung. Vor neuen Boss-Spawnregeln zuerst absichern und gesondert testen.
- Schwierigkeitsschwankungen können aus Bossklasse, Schaden, HP-Multiplikator oder Spielzustand kommen; **Ursache und Quantität sind noch nicht gemessen**.

## 2. Zielbild: Eine echte Bossbegegnung

```text
NORMAL GAMEPLAY
    ↓ Levelziel / Seelenschrein / Bossanlass
ANKÜNDIGUNG (Name, Silhouette, kurzer Ton, unmissverständliche Warnung)
    ↓ sichere und faire Vorbereitungszeit
BOSS ARENA (passendes Thema, Boss-Lebensleiste, kontrollierte Spawns)
    ↓ 2–3 erkennbare Angriffsmuster und HP-Phasen
FINALE (klarer letzter Treffer, dramatischer VFX-/SFX-Moment)
    ↓ Belohnung / Ergebnis / optionaler Levelübergang
NORMAL GAMEPLAY oder NÄCHSTER ADVENTURE-ABSCHNITT
```

### Start / Arena
- Boss erhält einen **festen Namen, eine eigene grafische Silhouette, Erkennungssound/optionale Sprache** und ein thematisches Hintergrund-/Arena-Profil; für hörbeeinträchtigte Nutzer stets sichtbare Ankündigung und Untertitel anbieten.
- Eintritt ohne sofortigen Schaden; Vorwarnung und kurze sichere Zeit zum Ausweichen. Boss darf nicht auf der Schlange spawnen und darf nicht alle Wege blockieren.
- Fester Rahmen für neue Bossmechaniken, aber Classic-Spielzustände, Eingabe und Rasterregeln erhalten.

### Kampf / Aktionen
- Lesbare **HP-Leiste**, Phasenanzeige und Warnhinweise vor größeren Angriffen. Optional ein Anzeige-Counter für angekündigte Sonderattacken, nicht jede Aktion muss minutengenau abgezählt werden.
- 2–3 für **diesen** Boss charakteristische Angriffe, statt zufällig wechselnder, unpassender AoE. Bewegungen, Schussmuster, Farb- und ggf. Größenwechsel dürfen Phasen erklären, nicht Kollisionen unbemerkt verändern.
- Individuelle Musik- und Sound-Ereignisse: Intro, Schuss, Treffer, Phasenwechsel, Niederlage. Audio als separater späterer Arbeitsschritt, mit deaktivierbarem Sound und fallback ohne Datei.
- Eindeutige Trefferregeln, Invulnerabilität und Schaden; keine unbeabsichtigten Mehrfachtreffer durch identische Projektile, Explosionsbilder oder überlappende AoE.

### Gegner-/Minion-Regeln
- **Normale Zufallsgegner** während einer Bossarena standardmäßig pausieren oder stark begrenzen.
- **Nur der Boss selbst** darf ausgewählte passende Minions in definierten Phasen beschwören. Minion-Anzahl, Cooldown und Lebensdauer begrenzen.
- Nach Sieg/Abbruch vorhandenes Spawnverhalten kontrolliert wiederherstellen; keine liegen gebliebenen Sonderzonen/Projektile oder vervielfachte Spawnrate.
- Die Spawn-/Update-Verschachtelung in `game.py` **zuerst in getrenntem Fix** untersuchen und als Baseline testen.

### Sieg / Übergang
- Sichtbar und hörbar bestätigter Sieg: Boss zerfällt, besondere aber begrenzte Explosion, Arena beruhigt sich, Erfolgstext mit Bossname/Ergebnis, Score/Item-Belohnung.
- **Heldenerlebnis** ohne erzwungenes langes Warten: kurzer Effekt, überspringbar oder in Optionen reduzierbar, danach wieder flüssiges Gameplay.
- Belohnung genau einmal ausgeben. Reset, Pause, 2P und gleichzeitige Treffer dürfen den Sieg nicht mehrfach auslösen.

## 3. Classic und Adventure strikt unterscheiden

| System | Classic | Geplanter Adventure-/Roguelite-Modus |
| --- | --- | --- |
| Bossauswahl | Wiederverwendbarer Pool, zufällig unter gültigen Bossprofilen | Kuratierter, thematisch passender Boss pro Level/Kapitel |
| Anzahl | Kleiner getesteter Pool | **Langfristige Vision: 20–40 einzigartige Bossprofile** (kein unmittelbarer Umfang eines PRs) |
| Ort / Zeitpunkt | An aktuelle Spielregeln angepasst, keine Levelmigration erzwingen | Levelziel, Portal/Seelenschrein oder definierter Event-Trigger |
| Schwierigkeit | An vorhandene Level-/HP-Regeln angepasst und gemessen | Progression mit Items, Upgrades, klaren Anforderungen |
| Gegner | Spawnregeln ausdrücklich während Bosskampf definieren | Normale Spawns pausieren, Boss-Minions auf bestimmte Phasen begrenzen |
| Sieg | Rückkehr zum normalen Classic-Spiel | Dramatischer Levelabschluss und nächster Abschnitt |

**Fairness:** Spätere Bosse dürfen mächtig sein und durch vorherige Ausrüstung vorbereitet werden. Der Spieler darf aber nicht allein wegen unglücklicher zufälliger Itemdrops mathematisch chancenlos sein. Benötigte Schlüssel-Upgrades im Abschnitt erreichbar machen, Mindestschaden/Alternative berücksichtigen und Fortschritt überprüfen.

## 4. Datengetriebene Bossprofile

Keine 40 einzeln hardcodierten Bossklassen. Zuerst ein **stabiles, versioniertes Bossprofil** mit zulässigen Parametern und Animation-/Asset-Referenzen entwerfen:

- `boss_id`, Anzeigename, Thema/Welt, zulässige Spielmodi;
- Sprite-/Animations-/Sound-IDs (fehlertolerant), Hitbox, HP/Damage/Speed;
- Intro-Text, Warnsignal und Phase-Trigger anhand von HP/Zeit;
- Anzahl und Eigenschaften charakteristischer Projektile/AoE, Angriffscooldowns;
- mögliche Boss-Minions (Typ, Limit, Trigger), Arena-Regeln;
- Belohnungsprofil, Sieg-Effekt und nächster Spielzustand.

Datenprofile müssen **validiert** werden: keine negativen HP, keine unbekannten Grafikpfade, keine ungültigen Spawnpositionen und keine beliebige Ausführung von Code durch Leveldateien.

**Abnahme pro Boss:** Einzigartig erkennbar, nicht unfair, in 1P/2P spielbar, klare HP-/Phasenrückmeldung, keine Mehrfachbelohnung, keine unkontrollierten Gegner, stabile 60-FPS-Zielmessung und protokollierte Ausnahmen.

## 5. Entwicklungsstrategie

1. **Zuerst echten Ist-Stand messen und Bugs einzeln beheben:** Bossdauer, HP/Damage und Ursache sehr kurzer Kämpfe; normalen Gegner-Spawn in `Game.update()` isoliert untersuchen.
2. **Boss Encounter Vertical Slice:** **einen** Boss vollständig neu inszenieren (Intro, HP-Leiste, 2 Phasen, telegraphierter Angriff, limitierte Minions, Sieg, Rückkehr). Keine neuen 20 Bosse in einem PR.
3. **Profilkatalog und Tests:** Vorhandene `Boss`/`Boss2` nicht aus Versehen unspielbar machen; Classic behält Zufallspool.
4. **Audioprofile und optional Stimme/Untertitel** später separat, wenn die Spielmechanik stabil ist.
5. **Adventure-Kampagne:** Ein Boss pro kuratiertem Abschnitt, skalierende Itemprogression und Belohnungen. Erst nach funktionsfähiger Level-/Event-Integration.
6. **Erweiterung um viele Bossidentitäten** nach Spieltests und Messungen. Gleiche Engine, unterschiedliche Designs; nicht dieselbe Mechanik bloß umfärben.

## 6. Qualitätsnachweis / Regressionsprüfung

- Unit-Tests: HP und Schaden, genau-einmal-Sieg, Spawn-Limit, Arena-Sicherheit, Phasen, Warnung vor Angriff, Reset und Rückkehr.
- Simulation: 1P/2P, schwache und starke Ausrüstung, ungünstige Itemdrops, schwere Bosse und kombinierte Frost-/AoE-Effekte. `PASS/FAIL/NOT RUN`, Soll/Ist und reproduzierbarer Seed.
- Echte Windows-EXE: Inputgefühl, Lesbarkeit, Animation-/Soundsynchronisierung, klare Sicht ohne HUD-Überdeckung, Übergang zurück zum Classic-Spiel.
- Performance: `scripts/benchmark_game.py` und `FrameMetrics` als Basis, zusätzliche reale Bossprofil-/Minion-Lasten vergleichen. Neue grafische Effekte dürfen keine Lade-/Frame-Spikes unbemerkt verursachen. [Messplan](QUALITY_PERFORMANCE_PLAN.md).

**Nicht Teil der Dokumentation:** Es werden keine Bosse, Projektile, Sounds, Spawnregeln oder Level jetzt geändert. Die aktuelle Priorität bleiben die bereits gemergte Editorarbeit, Windows-Prüfung, Performance-Baseline und die geplanten Folge-PRs.
