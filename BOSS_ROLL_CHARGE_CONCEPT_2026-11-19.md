# DARK SNAKE – Boss Roll / Charge A (Konzept, noch NICHT implementiert)

**Entscheidung Demus, 19.11.2026:** Nach den erfolgreichen Portal-/
Tunnel- und Wächter-Rift-Tests **weiter an bestehenden Bossen** arbeiten.
Keine neuen Standardgegner, FrostAge-Gegner oder zusätzliche Gegnerklassen
vorzeitig einführen.

## Verifizierter technischer Bestand (GitHub main)
- `Dark_Snake/modules/game.py`: Snake-Kopf/-Körper bewegen sich per
  diskreten `GRID_SIZE`-Zellen. Logische Körperkollisionen und
  Projektil-/Boss-Treffer werden separat geprüft. Keine auf Kräften,
  Masse oder Impulsen basierende Gameplay-Physik.
- `requirements.txt`: nur `pygame==2.6.1` und `pytest==8.3.5`.
  Pymunk/Box2D sind nicht installiert und für den Vorschlag unnötig.
- `boss_swipe.py`: bereits kurze gleitende Boss-Bewegung mit
  0,18 s Dauer und einer synchron mitlaufenden Boss-Hitbox.
  `boss_teleport.py`: Warn-/Sink-/Emerge-/Recovery-Zustände,
  sichere Zielpositionen, Abbruch bei nachträglicher Belegung.
- `boss_personality.py`: drei **feste** Identitäten:
  **Wächter** = `Boss-SkullPurPurG60.png` (groß, aktuell ohne
  eigenen animierten Frameordner);
  **Medusa** = `Boss-RingG60.png` mit `Boss002`-Animation (15 Frames);
  **Jäger** = `Boss-AlexG60.png`.
  Weitere vorhandene PNGs und die `Boss001`-/`Boss003`-Ordner sind
  Asset-Vorrat, keine automatisch neuen spielbaren Boss-Persönlichkeiten.

## Prototyp A – ein vorgewarnter Roll-/Ram-Angriff

**Empfohlener erster Kandidat: Medusas Ring-Design.**
Der Roll-Effekt ist bei einer runden Sprite visuell plausibel;
wahlweise kann nach dem ersten Windows-Test der violette Schädel
stattdessen einen schweren Ram erhalten. Nicht zwei Fähigkeiten zugleich.

1. **IDLE / HUNT:** Boss bleibt normal aktiv. Roll-Trigger nur bei
   bestätigtem Sichtkontakt oder glaubwürdig beobachtetem
   Spielerprojektil; keine allwissende Suche.
2. **TELEGRAPH:** 0,7–1,0 s Warnlinie/angedeutete Zielrichtung.
   Zielzelle und Richtung **jetzt festhalten**, nicht unsichtbar
   permanent auf den neuen Kopf nachregeln.
3. **CHARGE:** ca. 2–4 Rasterzellen, ca. 0,25–0,40 s
   glatt gerendert; **echte, mitwandernde Hitbox** durch die
   gesamte Strecke, auf Wände, andere feste Objekte und beide
   Schlangen prüfen; keine Tunneling-Treffer.
   Sprite kann mit `pygame.transform.rotate` gedreht werden;
   Bewegungsvektor und Trefferprüfung bleiben unabhängig von der Optik.
4. **IMPACT:** bestehender Bosskontakt: **ein Treffer** je
   Spieler/Lauf, vorhandene Respawn- und Invincibility-Regeln
   respektieren; kein mehrfacher 60-FPS-Kontaktschaden.
   Ob Normal-Bosskontakt (10 HP) oder ein neues Damage-Profil
   genutzt wird, vor Implementierung entscheiden, nicht addieren.
5. **RECOVERY:** ca. 0,6–1,0 s, danach 6–10 s Cooldown;
   kein gleichzeitiger Swipe/Teleport/Shield-/Frost-Angriff.
   Pausen, Editor, Respawn und Phasenwechsel brechen sauber ab.

**Option B nach bestandenem Spieltest:** bestehenden NormalEnemy
höchstens einmal als begrenzte Boss-Summon-Aktion nach Abschluss
des Charges erscheinen lassen. Auf Spawn-Limit, sicheren Spawnplatz
und fehlende Spawn-Duplikate achten. Keine neue Gegnerklasse.

## Rückstoß (separat evaluieren; keine fertige Physikengine voraussetzen)

- **Stufe B1: visueller Rückstoß**: kurze Feder-/Wackelbewegung des
  **gesamten** Snake-Sprites für ca. 0,15–0,25 s. Die logischen
  Gridzellen und Schlangenkörper-Kollisionen bleiben unverändert.
  Nicht so weit animieren, dass die Hitbox sichtbar falsch wirkt.
- **Stufe B2: echter 1-Zellen-Knockback** nur wenn er wirklich
  Spielspaß gewinnt. Dann **alle** Segmente mit gleicher legaler
  Verschiebung und jeder Zwischenschritt prüfen; freie Fläche,
  Wraparound, Kollision mit eigenem Körper, 2P, Items, AoE,
  Wänden, Respawn, Self-Stall und Move-Timing absichern.
  Wenn nicht sicher: nur Schaden plus visuelles B1-Feedback.
- **Keine ungeprüfte externe Physikbibliothek** und kein Verschieben
  des Kopfes allein: sonst wird die Schlange auseinandergerissen.

## QA-Gate vor Merge eines späteren Code-PRs
- Pure Geometrie-/Zeit-Tests plus komplette headless 1P/2P-
  Regression; Catch-up mit gleitender Hitbox, Kollisionsauflösung
  bei 30/60/120 FPS, keine mehrfachen Hits.
- Roll-Unterbrechung: Bossphase, Welt-Rift, Swipe, Pause, Respawn,
  Editor; neue Attacke darf nicht auf alten Zielpunkt nachteleportieren.
- Rollbewegung darf keinen Spieler teleportieren; Abbruchgrund in
  `combat_events` loggen.
- Windows Alpha 2/CodeQL und Demus' tatsächlicher Windows-Sichttest
  entscheiden über Balance, Treffergefühl und freigegebenen Merge.

**Status dieses Dokuments: reines Konzept. Keine Umsetzung oder
Freigabe von Roll/Charge, Knockback oder Summon behaupten.**
