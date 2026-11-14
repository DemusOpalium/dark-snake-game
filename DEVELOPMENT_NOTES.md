# DARK Snake · Bestandsaufnahme und nächste Entwicklung

Ausgangsstand ist `main` bei `b8b4377` (PR #112). Das [Architektur-Audit](ARCHITECTURE_AUDIT.md) beschreibt die Zuständigkeiten und den Frame-Ablauf. Die folgenden Erweiterungen sind Vorschläge für eine spätere Prüfung.

## Audio · nachgewiesener Ausgangsstand

Unter Windows 11 mit Pygame 2.6.1 und SDL-Dummy meldeten `pygame.init()`, der anschließende explizite Mixer-Aufruf und der Import von `config` jeweils 44.100 Hz, 16 Bit und zwei Kanäle. Die Aufrufe waren redundant. Die Messung weist keine erneute Öffnung eines physischen Geräts nach. Die sechs WAV-Effekte sind ebenfalls 44.100 Hz, 16 Bit und Stereo. Alle Musikdateien sind 48.000 Hz und Stereo. Damit musste der alte Mixer die Musik umrechnen.

Im Ausgangsstand änderte das Ziehen der Regler zunächst die angezeigten Werte. Beim Speichern wurden Musik- und Effektpegel angewandt, bei der Titelauswahl zusätzlich der Musikpegel. Der gewählte Titel wurde beim Neustart durch den Standardtitel ersetzt. Das sind reproduzierbare Fehler im Bedien- und Startpfad. Gerätespezifisches Knacken, Aussetzer und Übersteuerung lassen sich mit SDL-Dummy nicht beurteilen.

Alle fünf MP3-Pfade wurden mit FFmpeg vollständig und strikt in Float32 dekodiert (`-xerror -err_detect explode -f f32le -acodec pcm_f32le`). `ebur128=peak=true` ermittelte integrierte Lautheit und True Peak. Keine Dekodierfehler und keine dekodierten Samples bei oder über Vollaussteuerung. Die zweite Datei im übergeordneten Sound-Ordner ist bytegleich mit `FürAndreTeil2.mp3`.

| Musikdatei unter `assets/sounds/music` | Lautheit | True Peak |
| --- | ---: | ---: |
| `ChillFürAndre.mp3` | −12,4 LUFS | −1,8 dBTP |
| `DarkSnakeMusicIndi1.mp3` | −11,9 LUFS | −0,8 dBTP |
| `DarkSnakeMusicIndi2.mp3` | −12,1 LUFS | −1,0 dBTP |
| `FürAndreTeil2.mp3` | −12,2 LUFS | −1,1 dBTP |

Die Originale bleiben unverändert. Die Werte belegen weder den Pegel nach dem Mischen mehrerer Spielsounds noch die Ausgabequalität des Audiogeräts. Für die Hörprobe unter Windows denselben Track bei derselben Lautstärke und demselben Ausgabegerät vor und nach dem Fix vergleichen. Regler während der Wiedergabe bewegen, Musik auf null ziehen und Effekte prüfen, dann die Probe umgekehrt wiederholen. Einstellungen speichern und nach dem Neustart beide Pegel und den Titel prüfen. Bosskampf und überlappende Soundeffekte separat anhören.

### Audio nach dem Fix

Der normale Start öffnet den Mixer über einen zentralen Einstieg mit 48.000 Hz, 16 Bit, Stereo und 1.024 Samples Puffer. Damit stimmen Musikformat und Mixer-Rate überein. Der Puffer bietet mehr Reserve bei unregelmäßiger Bedienung durch das System. 1.024 Samples entsprechen bei 48 kHz rund 21 ms Pufferdauer. Das ist keine Messung der gesamten Audiolatenz.

Im SDL-Dummy liefen alle vier Titel im Musikordner mit der neuen Mixer-Rate an. Musik und Soundeffekte reagieren getrennt auf Reglerbewegungen. Die Effektvorschau beim Loslassen macht die Einstellung im Menü prüfbar. Eine Reglerbewegung lädt den laufenden Track nicht neu. Beim Speichern werden die beiden Pegel und die Titelauswahl übernommen. Das Spiel kann bei einem nicht verfügbaren Mixer weiter starten. Die vorhandene Zuordnung für den Gegner-Sound ist jetzt mit der bereits enthaltenen WAV-Datei belegt. Die überzählige Musikdatei wird beim Start nicht mehr zusätzlich als langer Soundeffekt in den Speicher geladen.

## AoE · Zeichnung und Reproduktion

Die regulären `AoEZone`-Objekte lagen bereits unter dem Boss. Die wachsende Warnung wurde dagegen innerhalb von `Boss.draw()` nach Sprite und Lebensbalken geblittet. Zwei weitere Pfade, die Boss-Aura des `EffectManager` und die Feuerexplosion, zeichneten nach den normalen Gegnern. `Game.update()` zeichnete die Zonen und Explosionen zusätzlich auf die Spielfläche, bevor der eigentliche Frame den Hintergrund aufbaute.

Der Renderpfad zeichnet diese Welt-Effekte vor den Figuren. `update()` schreibt dafür keine Pixel mehr. In der Regression überlappen vorbereitete Effekte die Boss- und Gegnersprites. Der Test vergleicht die unverdeckten Sprite-Pixel, einen sichtbaren Effektbereich neben der Figur und das HUD über der Welt. Ein Update-Test prüft zusätzlich, dass Radius und Animation weiterlaufen.

## Kampfregeln im klassischen Modus

Die bisherigen Geschwindigkeiten und Bewegungsabläufe sind die Referenz für die folgenden Entscheidungen. Die Reproduktionen liefen unter Windows 11 mit Pygame 2.6.1 und dem SDL-Dummy-Treiber. Ein reproduzierbarer Prüfaufbau friert die Spielzeit bei 100 Sekunden ein, verwendet Seed `20261109`, unterdrückt spontane Zufallsspawns und erzwingt bei Bedarf genau einen Rasterzug.

| Fall | Bestehendes Verhalten | Entscheidung oder nächster Schritt |
| --- | --- | --- |
| Klassisches Bossprojektil | Ein Projektil zieht jedem getroffenen Spieler über seine gesamte Flugzeit einmal 10 HP ab. Zwei getrennte Projektile können denselben Spieler treffen. Das Projektil fliegt nach dem Treffer mit derselben Kadenz, Geschwindigkeit und Raster-Trefferfläche weiter. | Tests prüfen anhaltende Überlappung, getrennte Spieler und Projektile, den normalen Update-Schritt und den zusätzlichen Schritt beim Rasterzug. |
| Bosskörper | Kontakt kostet 10 HP mit einer Sekunde Trefferpause pro Spieler. Die Schutzphasen beim Boss-Spawn und Spieler-Respawn gelten weiterhin. Der Boss kann während des Kontakts agieren. Ein tödlicher Kontakt in 2P verbraucht einmal das gemeinsame Leben. | Tests prüfen 1P, P2 allein, gleichzeitigen Kontakt, die Schutzphasen und den gemeinsamen Lebensverlust. |
| Eigenkörper | Ein weiterhin belegtes eigenes Feld blockiert den Zug. Kopf, Körper, HP und Leben behalten beim Blockieren ihren Wert. Eine freiziehende Schwanzzelle ist begehbar. Bei Wachstum bleibt sie belegt. Unverwundbarkeit erlaubt den Zug durch den eigenen Körper. | Nach drei Sekunden aktiver Spielzeit im Stillstand wird einmal ein gemeinsames Leben abgezogen. In 2P läuft der Timer pro Schlange. Die andere Schlange und der Kampf laufen während der Blockade weiter. |
| Andere Schlange | P1 (4, 4) nach rechts und P2 (6, 4) nach links dürfen beide auf (5, 4) landen. Benachbarte Köpfe dürfen ihre Zellen tauschen. | Beide Fälle sind als Classic-Regel getestet. |
| Bossflamme | Der vorhandene Regressionstest sichert ab, dass eine Bossflamme auf überlappenden 2P-Köpfen beide Spieler einmal trifft und nur einmal entfernt wird. | Bestehende Regel für dieses Flächenereignis beibehalten und von klassischen Projektilen trennen. |
| Spezialschadens-Item | `SPECIAL_DAMAGE` richtet bei aktivem Boss und abgelaufener Abklingzeit `5 × Level` Schaden über `damage_boss()` an und gibt 100 Item-Punkte. Ein tödlicher Treffer setzt die HP auf null, beendet den Bosskampf und vergibt zusätzlich einmal die normale Bossprämie von `100 × Level`. Das Kampfprotokoll führt die Quelle als `special_damage_item`. | Tests prüfen nicht tödlichen Schaden, Abklingzeit und einmalige Prämien. Die Projektilstatistik zählt das Item nicht als Projektiltreffer. |
| Boss-Aura | Der Sieg beendet die konkrete Aura-Instanz des besiegten Bosses. Die Siegexplosion und andere aktive Effekte laufen weiter. | Der Test mit zwei aufeinanderfolgenden Bosskämpfen prüft, dass sich keine Bossauren ansammeln. |
| Multischuss | Ein `PROJECTILE_SHOOT`-Item setzt einen zusätzlichen Schuss und verlängert die Laufzeit um 900 Sekunden. Bis zu sechs zusätzliche Schüsse sind möglich. Im Test blieben nach HP-Tod und Respawn mit Restleben der zusätzliche Schuss und die Laufzeit erhalten. `reset_game()` setzt beide auf null. Die automatische Zielsuche wählt den nächstgelegenen Gegner ab drei Sekunden Spawndauer und schießt sonst entlang der Blickrichtung. | Beim Waffenentwurf zwischen Lebensverlust und vollständigem Rundenreset unterscheiden. Die bestehende Zielsuche und den begrenzten Multischuss erhalten. |

Die Trefferauflösung ist von Bewegung und Darstellung abgegrenzt. Ein bestätigter Treffer ist der Einstiegspunkt für spätere Zusatzeffekte. Normale Updates und Rasterzüge behalten ihre getestete Bewegungskadenz. Bossprämie und Aura-Abschluss sind durch die Regressionen aus PR #115 abgesichert.

### Manuelle Classic-Spielprobe

1. Ein 1P-Spiel starten und über **Tab → Bosskampf** einen Boss erzeugen. Das AdminPanel schließen. Während der Spawn-Schutzphase und danach durch den Bosskörper lenken. Nach dem Schutz soll ein Kontakt 10 HP kosten. Bei wiederholtem Kontakt innerhalb einer Sekunde bleibt der Balken zunächst stehen, während der Boss weiter angreift.
2. In 2P zuerst nur P2 durch den Bosskörper lenken, dann beide Spieler. Die zwei Balken getrennt beobachten. Bei gleichzeitig tödlichem Kontakt soll der gemeinsame Lebenszähler einmal sinken. Direkt nach dem Respawn gilt die Schutzphase.
3. Ein klassisches Bossprojektil über mehrere Updates beobachten. Der getroffene Spieler verliert dafür einmal 10 HP. Ein weiterer Schuss kann erneut treffen. Danach zwei Spieler auf dasselbe freie Feld beziehungsweise direkt aneinander vorbeilenken und prüfen, dass beide Rasterzüge ausgeführt werden.
4. Eine längere Schlange gegen ihren eigenen Körper lenken. Innerhalb von drei aktiven Sekunden in ein freies Feld lenken und mit denselben HP und Leben weiterfahren. Danach einen blockierten Zug halten und zwischendurch Pause, AdminPanel oder Editor öffnen. Erst nach drei aktiven Sekunden folgt ein Respawn oder Game Over. In 2P dabei mit der anderen Schlange weiterfahren.

Der Stillstands-Timer beginnt beim ersten blockierten Rasterzug. Bewegung, Teleport, Respawn und Rundenwechsel setzen ihn zurück. Pause, AdminPanel und Editor zählen nicht zur aktiven Spielzeit. Laufen zwei Timer im selben Update ab, verarbeitet das Spiel einen gemeinsamen Lebensverlust.

## Schwierigkeit und Spawn-Budget

| Einstellung oder Quelle | Tatsächliche Wirkung im aktuellen Stand |
| --- | --- |
| Schwierigkeit 0,5–2,0 | Ändert die Chance auf ein gewöhnliches Zufallsitem pro Rasterzug zu `0.005 × difficulty`, also 0,25–1 %. Der normale Zufallspfad stoppt ab fünf Items. Bossstart, Bossportal, Admin und Lebensmittelersatz können zusätzliche Items erzeugen. |
| Spawnrate 0,001–0,005 | Normalgegner werden nur bei aktivem `projectile_shoot` ausgewürfelt. Die Chance gilt pro Spielupdate. Bei 60 Updates/s entspräche das im Mittel 3,6–18 neuen Gegnern pro aktiver Minute, ohne Abzug getöteter Gegner. Der Standardwert 0,002 entspricht 7,2. Es gibt keine gemeinsame Gegnerobergrenze. |
| Bolbu-Item | Erzeugt separat ein bis drei Bolbu. Der normale Gegnerspawn und Bolbu teilen sich die Gegnerliste, aber kein gemeinsames Budget. Bolbu kann einen Fächerschuss mit drei Projektilen erzeugen. |
| Tempo und Boss-HP | Das Starttempo bestimmt die Rasterzugfrequenz. Level erhöhen sie in Schritten von 0,5 bis `MAX_SPEED`. Die Boss-HP-Einstellung multipliziert die Bossgesundheit. Bossstarts kommen aus Levelaufstieg, Portal und Admin. `boss_spawn_timer` zeigt einen Countdown an, löst aber keinen Bossstart aus. |
| Neutrale AoE-Zonen | Pro Update gilt eine Chance von 0,1 %, wenn insgesamt weniger als fünf Zonen aktiv sind. Boss- und Admin-/Debug-Pfade hängen eigene Zonen unabhängig davon an. |
| Visuelle Effekte und Projektile | `EffectManager` ist getrennt von den schädigenden Zonen. Schleifen benötigen einen expliziten Abschluss. Die Aura jedes Bosses endet bei dessen Niederlage. Reguläre Rasterprojektile verschwinden primär am Spielfeldrand. Feuerball, Bossflamme und Bolbu-Projektile haben eigene Lebensdauern. Die Erzeugerbudgets stehen im Nachtrag. |

Ein Stresstest mit erzwungenen erfolgreichen Spawnwürfen bestätigte die Trennung. Zehn Updates bei inaktivem Autoschuss ergaben 0 Normalgegner und fünf neutrale Zonen. Vierzig weitere Updates mit aktivem Autoschuss ergaben 40 Normalgegner und weiterhin fünf neutrale Zonen. Das ist ein Kapazitätsnachweis unter erzwungener Zufallsfolge, keine Prognose für eine normale Runde.

### Vorschlag für eine spätere Balancephase

1. Pro Erzeuger die Zahl aktiver Gegner, Projektile und Zonen, höchste gleichzeitige Belastung sowie verworfene Spawnversuche erfassen. Dieselben Seeds in 1P und 2P sowie einen Bosskampf unter Last verwenden.
2. Zuerst harte Grenzen und faire Platzierung testen. Als **Versuchswerte** eignen sich 8 Gegner in 1P und 12 in 2P, 5 neutrale Zonen plus eine klar angekündigte Bosszone und ein separates Budget für feindliche Projektile. Neue zufällige Gegner außerhalb der unmittelbaren Kopfbereiche platzieren und eine kurze Kontaktwarnung prüfen. Obergrenzen nie durch schnelleres Nachspawnen kompensieren.
3. Einen angekündigten Bossangriff und garantierte Lebensmittel von Zufallsspawns unterscheiden. Ein volles Budget soll weitere Zufallsspawns auslassen, statt bestehende Projektile oder Angriffe unsichtbar zu löschen. Für belegte Spielfelder die Platzsuche begrenzen. Die heutigen `while True`-Schleifen für freie Itemzellen können auf einem vollständig belegten Raster keinen Kandidaten finden.
4. Erst nach diesen Schutzmaßnahmen einen langsamen Anstieg mit Spielzeit oder Level erproben. Spawnrate und Schwierigkeit im Menü passend zu ihrer tatsächlichen Wirkung beschriften. Für einen Classic-Preset die bisherigen Mechaniken als Vergleichsgruppe behalten und erst nach Testspiel-Freigabe neue Standardwerte wählen.

## Würfel im klassischen Spiel

- **Würfel-Item.** Ein zufällig erzeugtes Item hat unter den elf gleich gewichteten Item-Typen eine Chance von 1/11 auf `DICE_EVENT`. Die Beutekiste kann denselben Effekt auslösen. Bei einer Kiste wählt das Spiel aus zehn Typen, also mit 1/10 Wahrscheinlichkeit für den Würfeleffekt.
- **Portal.** Ein neu angelegtes Portal wählt gleichmäßig aus fünf Ereignissen. Davon ist eines ein Würfelwurf. Bei einem Ergebnis von 11–20 gibt es `5 × Wurf` Punkte, bei 1–10 keine Belohnung. Der Portalwurf vergibt keine Erfahrung. Die Würfelanzeige erscheint jeweils für fünf Sekunden.
- **Bolbu würfelt separat.** Der Gegner verwendet beim Angriffsintervall einen W6. Die 6 startet einen Sprint (1/6), 4–5 erzeugen drei Schüsse (2/6), 1–3 einen Schuss (3/6). Das gehört zur Gegner-KI und verwendet keine D20-Spielerbelohnungen.

Der D20 zieht mit `random.randint(1, 20)` gleichverteilt. Jedes einzelne Ergebnis hat 5 % Wahrscheinlichkeit. Die Tabelle beschreibt die direkten Item-Effekte. Eine erreichte Erfahrungsschwelle löst anschließend das normale Level-up aus, das zusätzliche Punkte vergeben und einen Bosskampf starten kann.

| Wurf | Wahrscheinlichkeit | Punkte | Erfahrung |
| --- | ---: | ---: | ---: |
| 1 · Kritischer Fehlschlag | 5 % | 1 | 0 |
| 2–5 · Fehlschlag | 20 % | Wurf | 0 |
| 6–10 · Kleiner Erfolg | 25 % | 2 × Wurf | Wurf / 2, abgerundet |
| 11–15 · Erfolg | 25 % | 3 × Wurf | Wurf |
| 16–19 · Großer Erfolg | 20 % | 5 × Wurf | 2 × Wurf |
| 20 · Kritischer Erfolg | 5 % | 300 | Setzt Erfahrung auf die nächste Levelschwelle |

### Optionale Erweiterung zur Freigabe

Klassisch bleibt der Standard. Ein optionales Profil könnte eine reine Auswertung `roll → Ergebnis` pro Quelle (Item, Portal oder später Myzel) verwenden. Der Wurf erhält eine injizierbare Zufallsquelle für feste Seeds. Jede Ergebnistabelle ist separat über alle 20 Werte prüfbar. Die UI zeigt eine Belohnung anhand der tatsächlichen Quelle an. Im Moment benutzt das Portal dieselben Textstufen wie das Item, obwohl es anders belohnt.

Eine niedrige Zahl kann eine kleine Belohnung geben. Eine hohe Zahl kann ein gut sichtbares Bonus-Item oder ein seltenes, angekündigtes Ereignis auslösen. Keine zufälligen Verluste von Leben, Steuerung oder sicherem Platz. Abklingzeit und Mengenlimit sollen verhindern, dass ein Bonus weitere Würfe in einer Kette erzeugt. Pilz- und Sporenereignisse bekommen später eigene Ergebnistabellen.

## Waffen und Effekte zur Freigabe


| Baustein | Vorschlag |
| --- | --- |
| Waffenprofil | Deklarative Daten für Projektilbild, Schadensquelle, Trefferaktion und optionales Zonenprofil. Die bestehende Projektillogik behält Tempo, Takt und Zielwahl. |
| Trefferereignis | Ein bestätigter Treffer enthält Position, Quelle und Ziel. Eine optionale Trefferaktion erzeugt höchstens eine Zone pro Projektil. Direktschaden und Zonenschaden erhalten getrennte Tests. |
| Frost | Der Entwickler-Test erzeugt auf bestätigte Feuerballtreffer eine sichtbare Zone hinter den Figuren. Überlappende Zonen verlangsamen Gegner mit demselben Faktor wie eine einzelne Zone. |
| Feuer | Ein sichtbarer Radius mit getaktetem Schaden und einem Abklingintervall je Ziel. Ein Gegner erhält maximal einen Schaden pro Tick und Zone. Vor einem Prototyp Grenzwerte für Überlappung und Lebensdauer festlegen. |
| Multischuss | Bestehendes Auto-Ziel und bestehende Zusatzschüsse als eigene Auflösung beibehalten. Den Zeitpunkt des Zurücksetzens vor einem Umbau ausdrücklich mit Tests festschreiben. |

Das vorhandene AoE-System liefert Radius, Lebensdauer und Darstellung. Die vorhandene Wirkung ist überwiegend auf Spielfiguren ausgelegt. Vor dem ersten Waffenprototyp Zielgruppe und Schadensintervall klar abtrennen. `EffectManager` erhält die sichtbare Wirkung, während die Spiellogik Treffer und Status entscheidet. Dieses Modell erlaubt später Sporenwolken, Frostmyzel und Pilzgegner. Dynamische Wände und Myzel-Netzwerke gehören zur Raster- und Kollisionslogik. Bossmechaniken können dieselben Trefferereignisse verwenden. Es ist kein zusätzlicher Spielmodus erforderlich, um diese Schnittstellen zu testen.

### Frost-Prototyp im Entwickler-Test

Der Schalter **Frost-Test** im Admin-Menü startet bei jedem Programmstart ausgeschaltet. Jeder bestätigte Feuerballtreffer kann bei eingeschaltetem Test eine Zone am Einschlag erzeugen. Die **Spieltestwerte** sind zwei Rasterzellen Radius, drei Sekunden Dauer und 30 Prozent langsamere Rasterbewegung für Standardgegner und Bolbu. Der Faktor ist auch bei mehreren gleichzeitig aktiven Zonen 0,7. Die Zone folgt der Zeitbasis der Welteffekte. Abgelaufene Zonen verschwinden beim nächsten Spiel-Update, auch nach einer Pause. Das Ausschalten des Tests und ein Rundenneustart räumen die Zonen auf.

1. Im Einzelspiel mit ausgeschaltetem Frost einen Gegner per Feuerball treffen. Beim Treffer erscheint die gewohnte Explosion. Die Gegner bewegen sich wie im Classic-Modus.
2. Mit **Tab** das Admin-Menü öffnen und **Frost-Test** einschalten. Optional dort ein **Bolbu-Item** ablegen, das Menü schließen und das Item einsammeln. Einen Gegner mit der Feuerballtaste treffen, standardmäßig mit **Leertaste**. Am Einschlag sollte eine blaue Zone hinter den Figuren erscheinen. Ein Fehlschuss lässt die Spielfläche frei.
3. Einen Standardgegner und Bolbu innerhalb und außerhalb der Zone beobachten. Zwei Treffer in kurzer Folge nahe beieinander erzeugen überlappende Zonen. Im Überlappungsbereich gilt derselbe Bewegungsfaktor wie in einer einzelnen Zone. Nach ungefähr drei Sekunden endet die Verlangsamung, sobald keine aktive Zone den Gegner mehr erfasst.

## Entwickler-Simulator 2.0 – Schritt 1

Der bestehende Simulator steuert zehn Szenarien mit einem reproduzierbaren Seed und 60 Spiel-Updates pro virtueller Sekunde. Die Oberfläche startet dafür einen eigenen Prozess mit Pause, Fortschritt und Abbruch. Die bisherigen Berichte erfassen Läufe, Spielzeit, Ereignisse und Ausnahmen. Das Speichern in der Oberfläche erforderte einen Klick, und die erfassten Ereignisse waren keine Spielregelprüfungen.

Die Oberfläche speichert jetzt nach Abschluss automatisch ein TXT/JSON-Paar und zeigt den letzten Bericht sowie seinen Ordner an. **Berichtsordner öffnen** öffnet diesen Ordner unter Windows. Die entpackte EXE bevorzugt `Entwicklerberichte` neben sich. Bei fehlenden Schreibrechten und beim Start aus dem Quellcode liegen die Berichte in `~/.dark-snake/Entwicklerberichte`. Das temporäre PyInstaller-Verzeichnis wird beim Speichern ausgeschlossen. Zeitstempel, Seed und bei Bedarf eine laufende Nummer halten die Dateinamen eindeutig.

Pro Batch laufen die passenden Prüfungen in kurzen eigenen Spielinstanzen mit virtueller Zeit:

| Ausgewählte Szenarien | Spielregelprüfung |
| --- | --- |
| `1p` | Ein blockierter Eigenkörperzug kostet zunächst keine HP und kein Leben. Pause zählt nicht mit. Nach drei aktiven Sekunden folgt ein Lebensverlust mit Respawn. |
| `boss`, `boss_final_fireball` | Feuerballschaden senkt die Boss-HP. Der tödliche Treffer beendet den Kampf und vergibt die normale Prämie einmal. |
| `2p`, `boss`, `projectiles` | Ein klassisches Bossprojektil verursacht einmal 10 HP Schaden pro getroffenem Spieler. |
| `projectiles` | Ein bestätigter Feuerballtreffer erzeugt eine Frostzone, die nach drei Sekunden endet. Überlappende Zonen verstärken die Verlangsamung eines Standardgegners nicht. |

Der Bericht trennt bestandene, fehlgeschlagene und nicht ausgeführte Spielregelprüfungen von technischen Ausnahmen, Zeitüberschreitungen und Abbrüchen. Die Probe mit `--scenario portal` führt alle fünf Spielregelprüfungen als nicht ausgeführt auf. Die gezielten Simulatorprüfungen decken unter anderem Bosskontakt, simultanen Lebensverlust, Bolbus Bewegung im Frost, visuelle Schichtung und Controller-Eingaben noch nicht ab. Bestehende separate Regressionstests bleiben dafür relevant.

### Windows-Spielprobe für die Berichtsverwaltung

1. Die ZIP entpacken, die EXE öffnen und im Hauptmenü **Entwickler** wählen. Das Profil **Smoke** auswählen und einen Batch starten.
2. Nach Abschluss den letzten Bericht und den angezeigten Pfad prüfen. **Berichtsordner öffnen** wählen und das gleichnamige TXT/JSON-Paar im Explorer prüfen.
3. Einen zweiten Batch ausführen und beide Paare prüfen. Einen laufenden Batch abbrechen und den Abbruchgrund im Bericht prüfen.

## Level Studio 1.1 – Bestandsaufnahme

Auf `main` bei `2feda6b` öffnet F2 den vorhandenen Rastereditor. Er bietet 495 Tile-Grafiken, Favoriten, Füllwerkzeuge sowie Rückgängig und Wiederholen. Die Dateiauswahl besteht aus Speichern und Laden einer einzigen `custom_level.json`. Das bestehende Format ist ein Raster mit Kachelnamen oder `null`.

- Speichern überschreibt dieselbe Datei sofort. Laden prüft das Raster, fragt bei Änderungen aber nicht nach und vermischt die Historie zweier Karten. F2 und Tab schließen den Editor ohne Schutz.
- **Sim Start** speichert die Karte und übergibt dieselbe Liste als Hintergrund an Classic. **Sim Stop** setzt nur ein Flag. Im Editor läuft kein Spieltest. Ein späterer Classic-Start lädt die Datei automatisch.
- Die Tile-Auswahl ändert sich beim Zeichnen anhand gehaltener Maustasten. Ein Klick außerhalb der sichtbaren Palette kann eine verdeckte Kachel auswählen. Die Scrollgrenze lässt am Ende viel Leerraum. Rechtsklick malt auf der Karte, und die Randfüllung hat keinen eigenen Undo-Schritt. Transparente Flächen werden beim Zeichnen nicht vollständig erneuert.

## Level Studio 1.1 – Entwürfe bearbeiten

1. **F2** öffnet die Werkstatt. Über **Neu** einen eindeutigen Namen wie `Pilzwelt_01` vergeben. Gespeicherte Entwürfe lassen sich über **Öffnen** auswählen. **Speichern** schreibt ausschließlich den aktuellen benannten Entwurf. **Strg+N**, **Strg+O** und **Strg+S** führen dieselben Befehle aus.
2. Mit dem Mausrad über der linken Palette scrollen. Eine Kachel links anklicken, auf der Karte mit Links platzieren oder über Felder ziehen. Rechts auf der Karte löscht. Rand, Mittelfeld und Mausstriche lassen sich rückgängig machen und wiederholen.
3. Ein Stern beim Namen kennzeichnet ungespeicherte Änderungen. Vor dem Verwerfen beim Laden, Anlegen oder Schließen fragt der Editor nach. Ein fehlgeschlagener Ladevorgang lässt den bisherigen Entwurf und seine Historie im Editor.
4. **Vorschau starten** zeigt den aktuellen Hintergrundentwurf. **Esc** oder **Vorschau beenden** führt zurück zur Bearbeitung. Der Spieltest mit eigener Runde ist ein späterer Schritt.
5. **Für Classic wählen** übernimmt die gespeicherte Fassung als Hintergrund für kommende Runden in dieser Sitzung. Nach weiteren Änderungen die Karte speichern und erneut auswählen. **Classic-Standard** wählt wieder den Standardhintergrund. Nach einem Programmneustart beginnt Classic mit dem Standardhintergrund.

Die Entwürfe liegen unter `~/.dark-snake/levels/`, unter Windows im Benutzerordner unter `.dark-snake\levels`. Die bisherige `custom_level.json` lässt sich im Editor laden. Zum Weiterbearbeiten und Speichern erhält sie einen eigenen Entwurfsnamen. Die Originaldatei bleibt erhalten.

## World Studio 2.0 – Phase A

### Welten und Spielreihenfolge

1. Mit **F2** den Editor öffnen und über **Welten** in die Entwurfsbibliothek wechseln. Gespeicherte Karten erscheinen zunächst unter **Freie Level**. Eine Themenzeile klappt die Gruppe auf oder zu. Mit **Öffnen** in der Levelzeile geht es in die Karte. Bei ungespeicherten Änderungen greift die Verwerfungsabfrage.
2. Mit **Welt neu** eine Themenwelt anlegen. Zum Verschieben zuerst das Level markieren, dann die Zielwelt anklicken und **Zuordnen** wählen. **Freie Level** löst die Zuordnung. **Welt umbenennen** und **Level umbenennen** ändern die Anzeigenamen.
3. Ein markiertes Level über **Zur Reihenfolge** aufnehmen. Rechts die Reihenfolge per Ziehen oder mit **Nach oben** und **Nach unten** ändern. **Entfernen** streicht den Eintrag aus der Reihenfolge. Der Entwurf bleibt in der Bibliothek.

Der Index `~/.dark-snake/world-library.json` hat Formatversion 1 und speichert stabile Welt- und Level-IDs. Karten behalten Dateinamen und Inhalt beim Umbenennen in der Bibliothek. Entwürfe unter `~/.dark-snake/levels/` und das Altformat `custom_level.json` bleiben lesbar. Das Altformat lässt sich nach dem Öffnen als benannter Entwurf für die Weltbibliothek speichern. Die Spielreihenfolge wird für den späteren Adventure-Modus gepflegt. Für Classic gilt weiterhin die bewusste Auswahl im Editor.

### Tile-Bibliothek

**Tile-Bibliothek** öffnet die Kategorien. Dort lassen sich Themen und Untergruppen auf- und zuklappen. Die Suche akzeptiert Dateinamen, Themen und Untergruppen. Linksklick übernimmt die Kachel zum Malen. Rechtsklick fügt sie zu den Favoriten hinzu oder entfernt sie. Die Schnellpalette links bleibt für direktes Malen verfügbar.

Die 495 vorhandenen PNGs wurden anhand ihrer Präfixe zugeordnet. Gebündelte Ausnahmen stehen in `Dark_Snake/assets/graphics/tile_catalog.json`. Für eigene Korrekturen die Datei `~/.dark-snake/tile_catalog.json` anlegen und die Bibliothek erneut öffnen.

```json
{
  "version": 1,
  "overrides": {
    "bone_corner_tl.png": {"category": "frost", "group": "single"}
  }
}
```

Die Kategorie-IDs sind `bones`, `frost`, `galaxy`, `dungeon`, `nature`, `poison`, `fire`, `gothic` und `other`. Unbekannte Präfixe erscheinen unter **Sonstige**. `multi`, `walls` und `stamps` sind bereits als Anzeigegruppen neben `single` vorgesehen. In Phase A setzen alle Einträge einzelne Grafikkacheln. Die Katalogzuordnung hat keine Spielwirkung.

### Classic-Regeln und Randwechsel

Der Bosskörperkontakt zieht im bestehenden Trefferpfad Spieler-HP ab. Regressionen prüfen P1, P2 und gleichzeitigen Kontakt und halten die Boss-HP dabei fest. Der Kopf erhält keinen eigenen Kontaktangriff.

Bei vier Randrichtungen und beiden Köpfen bleibt der Rastertakt gleich. Bei einer kontrollierten Folge mit 60 Bildern pro Sekunde und Geschwindigkeit 8 lagen die Züge vor, beim und nach dem Wechsel jeweils acht Frames auseinander, also 133,3 ms. Die Regression verwendet zusätzlich einen 64-Hz-Takt mit gleichmäßigen 125 ms pro Zug und prüft die tatsächlich gerenderten Pixel, einschließlich des folgenden Körpersegments. Die Interpolation setzt den Kopf beim Randwechsel direkt ans Ziel und hält ihn dort bis zum nächsten Rasterzug. Mit einem deckenden Test-Körpersprite kann der Kopf im ersten Bild des Folgezuges kurz überdeckt sein. Ein zusätzlicher logischer Stillstand wurde nicht beobachtet. Die Spiellogik wurde für Phase A beibehalten. Schwankungen auf einzelnen Rechnern waren nicht Teil der kontrollierten Messung.

### Entwurf für den späteren Aufbau aus Phase A

- **B.** Ein großes Bild bekommt eine Rastergröße und einen Ankerpunkt. Ein Stempel bekommt ein rechteckiges Raster aus bestehenden Grafik-IDs. Die Platzierung und Undo/Redo sollen jeweils das gesamte Objekt bearbeiten. Das ursprüngliche Bild bleibt erhalten.
- **C.** Für Karten ein versioniertes Dokument mit Abmessungen und getrennten Ebenen für Grafik, Kollision, Effekte und Ereignisse vorsehen. Bisherige Raster werden beim Lesen als reine Grafikebene interpretiert. Zuerst `WALL` und `BARRIER` umsetzen. Eine Grafikplatzierung schreibt nur ihre Ebene. Ein kombinierter Befehl schreibt zusätzlich eine ausdrückliche Kollisionsmaske. Grafik und Kollision lassen sich getrennt oder gemeinsam löschen. Undo speichert die betroffenen Ebenen als einen Schritt.
- **C.** Fest gesetzte Spawns anhand von Grenzen, Kollision, Belegung und Ausweichraum validieren. Beim Boss die gesamte Grundfläche prüfen. Bei einer ungültigen festen Position eine geeignete freie Position suchen oder den Spawn mit Begründung auslassen. Die bestehende Zufallsauswahl bleibt für gültige freie Flächen verwendbar.
- **D.** Effektfelder und Trigger erhalten definierte Typen und geprüfte Parameter. 90 Prozent Slow lässt 10 Prozent des Bewegungstempos übrig. Schaden bekommt ein Intervall pro Ziel. Ereignisse verwenden zugelassene Aktionen aus Daten. Später folgt ein eigener Spieltest mit isoliertem Zustand, danach eine Rückkehr zum Entwurf.

## World Studio – Wände malen und testen

1. Mit **F2** einen Entwurf öffnen. Oben **Nur Grafik**, **Grafik + Kollision** oder **Nur Kollision** und bei Bedarf **WALL** oder **BARRIER** wählen. Linksklick malt die gewählten Ebenen. Rechtsklick löscht die Ebenen des aktuellen Werkzeugs. Im Modus **Nur Grafik** bleibt eine übermalte oder freigeräumte Wand erhalten.
2. **Kollision ein/aus** steuert die sichtbaren Umrisse. Orange zeigt WALL, Blau zeigt BARRIER. Das Umschalten ändert nur die Anzeige. Undo/Redo nimmt einen zusammenhängenden Mausstrich auf den bearbeiteten Ebenen gemeinsam zurück.
3. **Test 1P** oder **Test 2P** startet den Wandtest mit dem aktuellen Entwurf im Speicher. Die Schlangen beginnen auf freien Feldern mit einem freien Nachbarfeld. Die normale Belegung für Richtungen gilt, standardmäßig WASD für P1 und Pfeiltasten für P2. Vor WALL und BARRIER bleibt die Schlange auf ihrer Zelle und kann in eine freie Richtung abbiegen.
4. Mit **Esc**, **F2** oder **Test beenden** zur Bearbeitung zurückkehren. Der Test verwendet kurze Testschlangen für Rasterbewegung und Kollision. Entwurfsänderungen und Undo/Redo bleiben im Editor. **Speichern** schreibt die Karte ausdrücklich auf die Festplatte.

Formatversion 1 speichert Grafik und Kollision als getrennte Felder. Die Kollisionsliste enthält Koordinaten mit dem Typ WALL oder BARRIER. Ältere JSON-Raster öffnen sich als Grafikkarten mit leerer Kollisionsebene. **Für Classic wählen** übernimmt weiterhin den grafischen Hintergrund. WALL und BARRIER wirken im isolierten Editor-Test.

## World Studio – Damage und Slow testen

1. Mit **F2** einen Entwurf öffnen. Über **Effektwerte** den Schaden (1–100 HP), das Trefferintervall (0,1–60 s) und optional die maximale Dauer eines Kontakts (0,1–600 s) einstellen. Ein leeres Dauerfeld bedeutet, dass der Schaden bei dauerhaftem Kontakt weiter wiederholt wird. Für Slow stehen 10, 25, 50, 75 und 90 Prozent zur Wahl.
2. **Schaden** oder **Slow** auswählen und mit Linksklick auf dem Raster malen. Rechtsklick löscht den gewählten Effekt. Beide Effekte können dieselbe Zelle belegen. Grafik, Kollision und der jeweils andere Effekt bleiben beim Löschen erhalten. **Effekte ein/aus** steuert die Editor-Markierungen. Undo/Redo und **Speichern** erfassen die Effektfelder.
3. Ein Schadensfeld eine Zelle rechts vom Start malen und zwei Felder rechts eine WALL setzen. **Test 1P** starten. Beim Betreten sinken die HP um den eingestellten Betrag. Vor der Wand stehen bleiben, um das Intervall und die optionale Dauer zu beobachten. Mit WASD ausweichen und erneut auf das Feld fahren. In **Test 2P** gilt derselbe Ablauf getrennt für beide Spieler.
4. Eine Reihe Slow-Felder neben den Start malen. Der Test zeigt die HP und das verbleibende Tempo je Spieler. 75 Prozent Slow lässt 25 Prozent Tempo übrig. Sobald der Kopf das Feld verlässt, gilt wieder das normale Tempo. Eine Zelle hat einen Slow-Wert. Erneutes Malen ersetzt ihn.

Schaden wirkt beim Betreten und nach Ablauf des jeweiligen Trefferintervalls, solange der Kopf auf der Zelle bleibt. Am Ende der eingestellten Kontaktdauer trifft das Feld nicht erneut. Ein Verlassen beendet den Kontakt. Beim erneuten Betreten beginnt er neu. Bei null HP bleibt nur der betroffene Testspieler stehen. Mit **Esc** zum Entwurf zurückkehren und den Test bei Bedarf neu starten.

Formatversion 2 speichert Grafik, Kollision und Effekte getrennt. Ältere Grafik- und Wandkarten bleiben lesbar. Damage und Slow gelten im isolierten Editor-Test. Für Classic lässt sich weiterhin nur die Grafik des Entwurfs auswählen.

### World Studio V3 – Folgeaufträge

3. **Multi-Tiles und Stamp Builder.** Zusammenhängende Grafiken mit frei wählbarer Rastergröße und wiederverwendbare Stempel aus vorhandenen Kacheln. Platzierung, Löschen und Undo/Redo bearbeiten jeweils das gesamte Objekt.
4. **Roof und Foreground.** Transparente Objekte über den Figuren und unter dem HUD. Optional öffnet sich um jeden Schlangenkopf ein weicher transparenter Bereich mit einstellbarem Radius und Stärke.
5. **Lighting 1.0.** Konfigurierbare Lichtquellen mit weichen, wiederverwendbaren Verläufen, Farbe, Radius, Intensität und Flackern. Darstellung bei 1350×930 messen.
6. **Druckplatten und Trigger.** Ein isolierter Spieltest prüft die Druckplatte, das Warnsignal, den Timer und eine zeitlich begrenzte Schadenszone. Leveldateien beschreiben feste Ereignistypen.
7. **Editor-Bedienung bei Bedarf.** Tile-Gruppen und Favoriten links sowie Auswahl und Sichtbarkeit der Ebenen näher an die Arbeitsfläche rücken.

## FrostAge – Grafikobjekte im Editor

1. **F2 → Tile-Bibliothek** öffnen und nach **FrostAge**, einer Kategorie oder dem Originaldateinamen suchen. Die Bibliothek zeigt das Motiv und die Rastergröße an.
2. Eine Grafik wählen und den Mauszeiger aufs Raster setzen. Die Vorschau zeigt die Fläche des Objekts. Linksklick platziert das Motiv als ein Objekt. Über **Objektgröße** die Rastergröße für die nächste Platzierung wählen, etwa `6x6`. Das Seitenverhältnis bleibt beim Skalieren erhalten.
3. Über **Objekt verschieben** ein platziertes Objekt anklicken und an einer freien Stelle ablegen. Ein Rechtsklick mit dem Grafikwerkzeug löscht das ganze Objekt, auch wenn du es an einer anderen Zelle als dem Anker triffst. Platzierung, Verschieben und Löschen lassen sich rückgängig machen. Außerhalb des Rasters oder über einem anderen Objekt wird die Platzierung abgelehnt.
4. **Speichern** und **Öffnen** prüfen. Über **Test 1P** und **Test 2P** erscheint die aktuelle Anordnung im isolierten Leveltest. Die Objekte sind Dekoration. Wände und Effekte werden weiterhin mit ihren eigenen Werkzeugen gesetzt. Im ausdrücklich kombinierten Grafik-/Kollisionsmodus betrifft die Kollisionsänderung nur das angeklickte Rasterfeld.

Leveldateien in Version 3 speichern Grafikobjekte separat von Hintergrundkacheln, Kollision und Effekten. Jeder Eintrag enthält die Grafik-ID, die Ankerkoordinate und die Rastergröße. Bisherige Grafik-, Kollisions- und Effektkarten bleiben lesbar.

Alle 175 Quellen bleiben unter `GamePICs/Incoming/Frost_Tiles/` erhalten. Der Katalog ordnet ihnen stabile IDs und Laufzeitpfade zu. Er erfasst Pixelmaße, Alpha, tatsächliche Ausrichtung, Rastergröße und SHA-256. Alle PNGs besitzen einen Alphakanal, 107 enthalten nicht vollständig deckende Pixel. Die Ordner `10x1` und `2x1` enthalten Hochformate, `1x10` Querformate. Die Metadaten verwenden 1×10, 1×2 beziehungsweise 10×1. Ähnliche AoE- und Projektilvarianten wurden als Einzelbilder erfasst, da sich aus den Quellen keine verlässliche Framefolge ableiten lässt.

PR #142 hat die Multi-Tiles als dekorative Objekte eingeführt. Das FrostAge-Hauptmenü verwendet die zwölf Menügrafiken als Schaltflächen. Bereits platzierte Menügrafiken in älteren Entwürfen bleiben als Grafikobjekte lesbar. Licht, Gegner-, Projektil- und Itemprofile und der Stamp Builder folgen in den in der Roadmap aufgeführten Etappen.

## FrostAge-Hauptmenü unter Windows prüfen

1. Die Windows-ZIP entpacken und `DARK-Snake.exe` starten. Hintergrund, Seitenränder und die zwölf FrostAge-Bilder prüfen. Mit der Maus über aktive Schaltflächen fahren. Mit Pfeiltasten oder Steuerkreuz den Fokus wechseln und mit Enter oder der zugewiesenen Bestätigungstaste auswählen.
2. **Single Player** und **Multiplayer** getrennt starten. Ein paar Felder fahren, mit P oder der zugewiesenen Pausentaste pausieren und **Hauptmenü** wählen. **Continue** muss dieselbe laufende Runde mit dem bisherigen Spielstand aufnehmen. Das gilt auch mitten im Bosskampf. Nach einem frischen Programmstart oder einem Game Over ist **Continue** ausgegraut. Esc schließt das Pausenmenü und kehrt zur Runde zurück.
3. **Options**, **Highscore**, **Steuerung** und **Entwickler-Simulation** öffnen und jeweils zurückgehen. **Level Studio** öffnet denselben Editor wie F2. In der Tile-Bibliothek nach `frostage_menu_single_player` suchen. Die Menügrafik ist dort nicht mehr auswählbar.
4. **Workshop**, **Boss Rush**, **Inventory**, **Statistics** und **Credits** tragen den Hinweis **Nicht verfügbar**. Ein Klick bleibt ohne Aktion. **Quit** schließt das Spiel.

**Continue** hält die Runde im Arbeitsspeicher und folgt den bestehenden Pausenregeln für laufende Effekte. Während eine Runde im Hauptmenü zur Fortsetzung bereitsteht, lässt sich das AdminPanel dort nicht per Tab öffnen. Nach der Fortsetzung ist es wieder erreichbar.

## FrostAge-Dachbogen unter Windows ausprobieren

1. `DARK-Snake.exe` starten, **Level Studio** öffnen und auf **Dach-Demo** klicken. Die mitgelieferte Karte öffnet sich als Entwurf. Mit **Speichern** lässt sich eine eigene Kopie anlegen.
2. **Test 1P** wählen. Die Schlange steht zwischen zwei Säulen. Bei Standardbelegung fährt **W** nach oben durch den mittleren Durchgang. **Test 2P** wiederholt den Versuch mit **W** für Spieler 1 und **↑** für Spieler 2. Über **Esc** geht es zurück zur Karte.
3. Im Durchgang verdeckt der Bogen die Schlangenköpfe teilweise. Unter **Dachwerte** lassen sich Sichtfenster, Radius, Transparenz und Randweichheit ändern. Für den Vergleich das Sichtfenster ausschalten und den Leveltest erneut starten. Die Säulen blockieren weiterhin nur ihre eigenen Kollisionsfelder.
4. Für einen eigenen Bogen **Dach / Foreground** wählen, in der **Tile-Bibliothek** nach **FrostAge Dach** suchen und das Motiv mit Linksklick platzieren. **Objekt verschieben** wählt ein Dach und anschließend sein Ziel. Rechtsklick entfernt das Dach. Mit **Auf Dachebene** und einem Klick auf ein bereits unter **Objekte** liegendes Dach kann man es gezielt übertragen. Undo und Redo erfassen Platzierung, Verschieben, Löschen, Ebenenwechsel und Dachwerte.

Der isolierte 1P-/2P-Leveltest verwendet die Kollisionsfelder der Karte. Im regulären Classic-Spiel zeigt **Für Classic wählen** beim nächsten Start die Bodenkacheln und die Dachebene eines gespeicherten Entwurfs. Dort wirkt das Dach auch über Gegnern, Bossen und Projektilen. Classic verwendet seine üblichen Kollisions- und Effektregeln. **Classic-Standard** kehrt zur Standardkarte zurück.

Levelformat 3 speichert Dächer und Sichtfenster-Einstellungen getrennt von Grafikobjekten, Kollisionen und Effekten. Bestehende Entwürfe bleiben lesbar. Ältere Dachgrafiken behalten ihren Platz auf der Objektebene, bis sie im Editor gezielt übertragen werden.

## Vorgeschlagene nächste Phase

1. Audio und Ebenen unter Windows 11 mit echten Ausgabegeräten prüfen.
2. Die Classic-Regeln zu Bosskontakt, Trefferschaden und 2P-Feldbelegung anhand der manuellen Spielprobe prüfen.
3. Mit festen Seeds Spawn-Spitzen messen und erst danach Obergrenzen für Gegner, Projektile und Zonen festlegen. Einen optionalen Frost-Prototyp erst nach Prüfung dieser Grenzen freigeben.

## Nachtrag zum Windows- und Arcade-PR

PR #114 beseitigte die doppelte Trefferprüfung im selben Update. Die Classic-Regel weiter oben begrenzt den Treffer über die gesamte Flugzeit.

Normalgegner und Bolbu teilen sich nun ein Limit von 12 aktiven Gegnern in 1P und 16 in 2P. Bolbu-Punkte richten sich nach tatsächlich erzeugten Gegnern. Die Grenzen für neue Schüsse liegen getrennt bei 96 Spieler-Rasterprojektilen, 24 klassischen Bossprojektilen, 16 Bossflammen und 64 Gegnerprojektilen. Bereits sichtbare Schüsse bleiben im Spiel. Für zufällige Items und die Boss-Aufnahme versucht die Platzsuche zuerst die bisherige Zufallsauswahl. Bei dicht belegtem Raster wechselt sie zur Liste der freien Zellen und kehrt bei vollem Raster zurück. Spawn-Wahrscheinlichkeiten, Schwierigkeitsregler und Leveltempo behalten ihre Wirkung. Die Grenzen sind Startwerte für eine Spielprobe. Eine neue Schwierigkeitskurve und ein globales Zonenlimit sind offene Punkte.

Die Regressionstests prüfen alle 20 D20-Ergebnisse sowohl beim Item als auch beim Portal. Auf der Basis bleiben Bonus-Items, seltene angekündigte Ereignisse und quellenspezifische Erfolgsanzeigen die nächsten optionalen Schritte. Die aktuellen Würfelregeln sind davon unabhängig.

Für die weitere Zerlegung von `game.py` dienen die getrennte Trefferauflösung und ihre Tests als Ausgangspunkt. Als Nächstes können Trefferquelle, Ziel, Trefferzeitpunkt und Statuswirkung in einem gemeinsamen Ereignisformat beschrieben werden. Die bestehende AoE-Geometrie und visuelle Ebene sind die Basis für optionale Freeze-, Slow- und Burning-Profile. Multischuss behält seine Zielwahl und seinen Rundenreset. Mycelium Age kann diese Schnittstellen später mit eigenen Daten verwenden.

## Separat · Firefox-Downloadwarnung

Die Ursache der Firefox-Warnung bleibt offen. Die Prüfung der beanstandeten Download-URL und Datei ist in [WINDOWS_BUILD.md](WINDOWS_BUILD.md) beschrieben.
