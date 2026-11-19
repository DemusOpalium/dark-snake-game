# 🛣️ ROADMAP.md – Entwicklungsfahrplan

## 🐍 Boss Intelligence 2.0 · Arbeitsstand 19.11.2026

- ✅ **Enemy Vision D (#228)** und **Smooth Movement A (#229)** – schnellere,
  ruhigere Gegnerbewegung im KI-Test; Demus-Windows-Sichttest positiv.
- ✅ **Boss Smooth Movement B (#230)** – Boss-/Boss2-Sprite-Glättung,
  bestehende Raster-/Kampf-Hitbox separat; Windows-Spielprobe positiv.
- ✅ **Medusa Eyes A (#231)** – Boss-Sicht, Memory, zwei Fernsensoren,
  ermittelte Zielzellen und begrenzte Kurzzeitvorhersage; im Admin-KI-Test.
- ✅ **Medusa Tactics B (#232, main, Windows-Sichttest 19.11.)** –
  Frostwurf aus bestätigtem Sichtkontakt oder Fernsensor-Relay, feste
  Vorwarnzone (1,35 s), kurzer Einschlag (0,65 s), 10 HP einmalig
  pro Spieler, sechs Sekunden Cooldown; Classic-AoE bleibt erhalten.
- ✅ **Boss Defense C (#233, main; Windows-Spieltest 19.11.)** –
  opt-in Sicht auf heranfliegende Projektile und kurzer Schutzschild
  (maximal ein abgewehrter Projektiltreffer, 0,8 s, 7 s Cooldown).
  Nur bestätigte Beobachtung; keine Wandsicht.
- ✅ **Boss Defense D (#234, main)** – zwei begrenzt aufladbare
  Seitwärts-Swipes, 0,18 s Animation und mitbewegte Boss-Hitbox;
  erfolgreicher Windows-Spieltest bei Demus, Ausweichen selbst
  dabei noch nicht sicher beobachtet.
- ✅ **Swipe D.1 / Player Projectile Cadence (#235, main)** –
  Spieler-Feuerball 4,5 Pixel/Frame und Pickup-/Multishots maximal gleich
  schnell, nur ein Update/Frame; Spieltest vom 19.11. bestätigt Boss-Swipes.
- 🔧 **Boss Personality A (eigener Draft-PR)** –
  fest zugeordnete Bossidentitäten **Medusa / Jäger / Wächter** mit
  unverwechselbaren, versionierten Bildern und Fähigkeiten:
  `Boss-RingG60.png` (Medusa, animiert), `Boss-AlexG60.png`
  (Jäger), `Boss-SkullPurPurG60.png` (Wächter).
  Kein `random.choice` der Bosse oder ihrer Grafiken mehr: pro
  Stufe deterministisch Medusa → Jäger → Wächter, wiederholbar
  bei gleicher Stufe. Jäger: schnell, aggressiver Fernangriff,
  Swipe; Wächter: größer, Distanzhaltung, Schild;
  Medusa: Fernaugen, Frostwurf, Schild und Swipe.
  Neuartige Prioritäten ausschließlich im KI-Test; Classic-Angriffe
  ohne KI-Test bleiben erhalten. Tests, CI/Windows und manueller
  Spieltest als Merge-Gate.
- ⬜ **Boss Phases** – Kampfphasen mit echten HP-Schwellen, Animations-
  und Vorwarnphasen, fairen Wechseln; erst nach Profil-Spieltest.
- ⬜ **FrostAge Vertical Slice** – Welt-/Spawn-Gate und drei individuelle
  Gegnerprofile einschließlich eigener Boss-Persönlichkeit, später
  eigene Frost-/Mycelium-Varianten.
- ⬜ **Boss Sensor-/Teleport-Komposition** – explizite Trigger, sichere
  freie Zielfelder, Teleport-Telegraph, keine Doppelkontakte, 1P/2P.
- ⏳ **World Studio** – Bossparameter und Event-Platzierung erst später;
  aktuell ausschließlich Code- und Windows-Spieletests.
- 📌 **Design-Referenz:** Bullet-Hell-/Bosskampf-Vielfalt (u. a.
  *The Binding of Isaac*) als allgemeine Mechanikstudie; keine fremden
  Figuren, Assets, Texte oder Bossmuster 1:1 kopieren.

---

## 📌 Aktueller Projektabgleich · 18.11.2026

> **Dieser aktuelle Abgleich ergänzt die historischen Abschnitte weiter unten.**
> [Anonymisierte Spieltest- und Balanceauswertung](PLAYTEST_BALANCE_2026-11-18.md) ·
> [Karriere-Regeln](CAREER_RANKS_DESIGN.md) ·
> [Skin-Inventar](SKIN_UNLOCK_DESIGN.md). Für den letzten Status gelten
> der tatsächliche `main`-Code, aktuelle Tests und offene PRs.

- ✅ **Progress A / A.1 / B (#208–#210):** bestätigte Runden-ID,
  atomare Speicherung/OS-Sperren, 40 versionierte Karriereränge und
  einmalige XP-Gutschriften über die Rundenchronik.
- ✅ **Inventory C (#211):** 92 Head-/Body-Bilder in der Runtime-Bibliothek,
  sechs freie Starter-Skins, Freischaltung über Rang-Rewards,
  maximal eine kosmetische Belohnung je beendeter Spielrunde,
  Bestandsschutz und Schloss-Kacheln. **Windows-Sichtprobe 18.11.:**
  Schlossanzeige und 1P-Abschluss bestätigt; vollständiger 2P-Test offen.
- ✅ **FrostAge-New-Enemy-ART (#213):** 17 neue Gegner-PNGs unter
  `GamePICs/` angenommen; **Staging, nicht im Spiel aktiv!**
  Vorgesehener erster Vertical Slice: Standardgegner, flinker
  Spezialgegner und ein Boss mit weltabhängigem Spawn-Gate.
- ✅ **Karriere-Dark-Abyss D (#215, gemergt):** bestätigte XP,
  Rang vorher/nachher und neuer Head/Body als Bild direkt im Game Over;
  Namenseingabe/Top-10 erhalten. **Manuell am 18.11. getestet:** der
  kompakte 65px-Block war noch zu gedrängt.
- 🔧 **Dark-Abyss E (#217, Draft):** eigenständiges mystisches
  violett-grünes Belohnungsfenster **unter der Namenseingabe** im
  hellen Abgrund; Titel, verifizierte Freischaltbedingung, Lobzeile,
  echte Skin-Grafik und sanfter 7+2-Sekunden-Fade. Kompaktlayout
  bleibt als Fallback für kleine Fenster. Kein neuer Achievement-Trigger.
- ⬜ **Separater Komfort-PR:** `Spielstände öffnen` öffnet per
  Klick den Nutzer-Datenordner `~/.dark-snake`, ohne JSON zu verändern.
- ⬜ **Separates UI-2D:** alte Top-10-Bestenliste optisch zu
  FrostAge umgestalten; historische `name,score`-Daten kompatibel
  beibehalten.
- ⬜ **FrostAge-Gegnerprofile:** zuerst Bilder/Kollision/Spawn-Modus/
  Balance validieren, drei ausgewählte Profile implementieren, restliche
  14 später. Classic nicht unbeabsichtigt mit FrostAge spawnen lassen.
- 💡 **Messdaten längerfristig:** Offline-/Entwicklerstatistik
  anonymisiert exportierbar machen; aktive Spielzeit erst verlässlich
  messen, anschließend geeignete Achievements planen.
  Spielbalance **nicht automatisch** aus nur drei Runden verändern.

---

## Historischer Quartalsplan (keine aktuellen Fristen)
- ✅ 2025 Q2: README und Screenshot-Galerie veröffentlicht; aktuelle Screenshots am 14.11.2026 ergänzt.
- 💡 2025 Q3: Prompt-System und automatisierte Debug-Dokumentation waren als Idee notiert; aktuellen Restbedarf separat prüfen.
- 💡 2025 Q4: Optionaler Kivy-/Mobile-Port war angedacht, bisher kein verifizierter Release.
- ⬜ Browser-/WebGL-Testversion weiterhin offen; der alte Termin 2026 Q1 ist überholt.
- ⬜ Feature Freeze / Public Showcase weiterhin offen; der alte Termin 2026 Q2 ist überholt.

---

## 📚 Weitere Dokumentation

- 📦 [Modulübersicht (DEV_STRUCTURE.md)](DEV_STRUCTURE.md)
- 🎨 [Screenshot-Galerie (GALLERY.md)](GALLERY.md)
- 🎮 [Steuerung (CONTROLS.md)](CONTROLS.md)
- 🤖 [Prompt-Guide für GPT (PROMPT_GUIDE.md)](PROMPT_GUIDE.md)
- 🛣️ [Projekt-Roadmap (ROADMAP.md)](ROADMAP.md)
- 🧪 [Messplan: Performance & Qualität (QUALITY_PERFORMANCE_PLAN.md)](QUALITY_PERFORMANCE_PLAN.md)


# 🐍 DARK SNAKE – WORLD 2 GO
## Master-Ideenliste · Entwicklungstafel · Roadmap
**Standabgleich: 17.11.2026 · geprüftes `main` nach PR #180. World Studio PR C (#174), D (#179) und E (#180) sind gemergt. UI 2.0 und Adventure-Ziele bleiben geplant.**

**Projektziel:** DARK Snake vom klassischen Arcade-Spiel zu einem modularen Spiel mit eigenen Welten, Spezialwaffen, individuellen Bossen, einem Level-Baukasten und dem späteren Adventure-Modus **Mycelium Age** weiterentwickeln.

**Statuslegende:**
- ✅ Vorhanden oder bereits umgesetzt
- 🔧 In Arbeit / vorhandenes System erweitern
- ⬜ Geplant
- 💡 Idee / Entscheidung noch offen

---

## 01 · AKTUELLE ENTWICKLUNG ABSCHLIESSEN

- ✅ Classic-Kampfregeln, Boss-Schaden und Selbstkollision überarbeitet.
- ✅ Input 2.0 und erste Performance-Messungen vorhanden.
- ✅ Frost-Prototyp programmiert und automatisiert getestet.
- ✅ Frost aus PR #117 über PR #119 in den Hauptbranch `main` übernommen (11.11.2026).
- ✅ Erste Windows-Spielprobe: blaue Frostzone sichtbar, Ablauf nach ungefähr 3 Sekunden bestätigt.
- ✅ PR #119: 223 Headless-Tests, 30 Smoke-Simulationen, Windows-CI und CodeQL grün.
- ⬜ Erweiterte manuelle Frost-Spielprobe (Standardgegner, Bolbu, Überlappung, 2P) bleibt offen.
- 🔧 Vorhandene Boss- und Kampfmechaniken überprüfen.
- ✅ Entwickler-Simulator 2.0, Schritt 1 durch PR #120 in `main` übernommen: automatische TXT/JSON-Berichte, Berichtsordner öffnen, fünf gezielte Spielregelprüfungen.
- ✅ PR #120: laut Entwicklungsbericht 249 Headless-Tests, 30 Smoke-Simulationen, Windows-CI und CodeQL erfolgreich; Windows-EXE mit Berichtsexport geprüft.
- ⬜ Erweiterte Simulatorabdeckung (Bosskörperkontakt, 2P-Sonderfälle, Bolbu-Frost, Render-Schichtung, Controller) bleibt offen.
- ⬜ Berichtsfunktion und Spielregeln zusätzlich durch Demus im entpackten Windows-Build prüfen.
- 🔧 Grafik- und Ressourcenverwaltung untersuchen.
- ⬜ Aktuelle Arbeiten abschließen, bevor größere neue Systeme beginnen.
- ⬜ Offizielles Windows-Release separat fertigstellen.

---

## 02 · EFFECT SYSTEM 2.0

**Ziel:** Ein gemeinsames System für sämtliche zukünftigen Effekte.

- ⬜ Vorhandene AoE-, Status- und Animationssysteme zusammenführen beziehungsweise sinnvoll miteinander verbinden.
- ⬜ Bestehende Funktionen erhalten, keine unnötige Neuprogrammierung.
- ⬜ Einheitliche Effektdefinitionen entwickeln.
- ⬜ Effekte über konfigurierbare Daten statt ausschließlich über Programmcode verwalten.
- ⬜ Frost, Feuer, Gift, Säure, Sporen, Myzel, Heilung und Verlangsamung unterstützen.
- ⬜ Direktschaden und Schaden über Zeit ermöglichen.
- ⬜ Heilende, schützende und schwächende Effekte ermöglichen.
- ⬜ Radius, Größe, Dauer, Schaden und Wirkungsstärke individuell einstellen.
- ⬜ Farben, Transparenz, Grafiken und Animationen austauschbar machen.
- ⬜ Auslöser definieren: Projektil, Mine, Item, Gegner, Boss oder Umgebung.
- ⬜ Wirkungen gezielt auf Spieler 1, Spieler 2, Gegner oder Bosse anwenden.
- ⬜ Effektbesitzer und Zielgruppen eindeutig unterscheiden.
- ⬜ Überlappende Effekte kontrollieren und unbeabsichtigte Mehrfachwirkungen verhindern.
- ⬜ Abklingzeiten, Immunitäten und Wirkungsgrenzen ermöglichen.
- ⬜ Einheitliche Trefferereignisse verwenden.
- ⬜ Effekte bei Spielende, Reset oder Ablauf zuverlässig entfernen.
- ⬜ Das System für spätere Pilz- und Bossmechaniken wiederverwendbar gestalten.

---

## 03 · FROST, WAFFEN UND SPEZIALMUNITION

**Ziel:** Einsammelbare Spezialfähigkeiten für beide Spieler.

- ✅ Frost-Prototyp mit Verlangsamung vorhanden.
- ✅ Testwerte: 2 Rasterfelder Radius, 3 Sekunden Dauer, 30 % Verlangsamung.
- ⬜ Frost als normalen einsammelbaren Spielgegenstand entwickeln.
- ⬜ Eigene Frostmine als Spezialgegenstand ermöglichen.
- ⬜ Weitere Spezialgegenstände: Feuer, Gift, Sporen und Myzel.
- ⬜ Unterschiedliche Projektilarten und Angriffsfunktionen entwickeln.
- 💡 **Frostburst-Idee (14.11.).** Gerade fliegende Eiskugel, die beim Ablauf oder Treffer acht gerichtete Splitter auslöst; direkter Treffer beispielsweise viermal so stark wie ein Splitter. Trefferintervalle und Mehrfachschaden sicher regeln.
- 💡 **Tornado-Idee (14.11.).** Rotierendes Projektil mit veränderlicher Größe, kurviger Bewegung, begrenzter Dauer und Kontaktschaden mit Trefferintervall; separate Soundprofile später in Ruhe ergänzen.
- ⬜ Spezialwaffen unabhängig vom normalen Schuss verwenden.
- ⬜ Verschiedene Munitionstypen für Spieler und Gegner ermöglichen.
- ⬜ Spezialwaffen auch für Bossangriffe nutzbar machen.
- ⬜ Effekt und Projektilgrafik unabhängig voneinander austauschen.
- ⬜ Minen, Flächenangriffe, direkte Treffer und zeitlich begrenzte Wirkungen unterstützen.
- 💡 Frostmine entweder hinter der Schlange ablegen oder nach vorne werfen/schießen.
- 💡 Später verschiedene Spezialfähigkeiten miteinander kombinieren.

---

## 04 · INVENTAR UND STEUERUNG

**Ziel:** Vier Spezialgegenstandsplätze pro Spieler.

- ⬜ Vier Inventarslots für Spieler 1.
- ⬜ Vier eigene Inventarslots für Spieler 2.
- ⬜ Inventaranzeige im unteren Bildschirmbereich integrieren.
- ⬜ Eingesammelte Gegenstände als Icons anzeigen.
- ⬜ Aktiven Gegenstand deutlich markieren.
- ⬜ Spezialwaffen getrennt vom normalen Schuss aktivieren.
- ⬜ Neue Spezialtaste für Spieler 1, beispielsweise **B**.
- ⬜ Neue Spezialtaste für Spieler 2, beispielsweise **I**.
- ⬜ Frei belegbare Tasten über Input 2.0 verwenden.
- ⬜ Controller-Unterstützung berücksichtigen.
- ⬜ Verbrauch, Nachladen und gegebenenfalls Abklingzeiten darstellen.
- 💡 Entscheiden: Vier einzelne Aktivierungstasten oder Slot-Auswahl plus Spezialtaste.
- 💡 Später eigene Inventargrafiken passend zur jeweiligen Spielwelt.

---

## 05 · GRAFIK- UND ANIMATIONSSYSTEM

**Ziel:** Flexible, hochwertige Darstellung bei möglichst geringer Rechenlast.

- ✅ Grafik-Loader bereits vorhanden.
- ✅ AoE-Grafiken und animierte Effekte teilweise vorhanden.
- ✅ PNG-/WebP-Animationsfolgen im EffectManager unterstützt.
- ✅ Eigene Hintergrundgrafiken können bereits als Effekt eingeblendet werden.
- ⬜ Bestehende Grafikverwaltung vereinheitlichen.
- 🔧 Grafik-Kataloge für FrostAge und Editor-Buttons vorhanden; übergreifende Vereinheitlichung weiterer Grafiksysteme weiterhin geplant.
- ⬜ Eigene Effekt- und Grafikpakete ermöglichen.
- ⬜ Animationen über Einzelbilder oder Spritesheets verwenden.
- ⬜ Größe, Bildrate, Transparenz und Darstellungsebene einstellen.
- 🔧 Laufzeit-Cache für FrostAge-Grafiken und Editor-Buttons eingeführt; weitere Bilder-/Animationspfade prüfen.
- ⬜ Wiederholte Skalierung während der Darstellung reduzieren.
- ⬜ Grafische Effekte unabhängig von Schadens- und Kollisionsberechnungen behandeln.
- 🔧 Editor-Buttons fallen auf Text zurück, andere Grafiksysteme benötigen weiterhin gesonderte Prüfung.
- ⬜ Bestehende Grafiken für neue Level und Effekte wiederverwenden.
- 💡 Animationen später selbst mit geeigneten Grafikprogrammen erstellen.
- 💡 Wasserfälle, Feuer, Pilzsporen, Portale und andere Umgebungseffekte animieren.

---

## 06 · BOSSFIGHT 2.0

**Ziel:** Individuelle Bosse mit eigenen Charakteren, Angriffen und Kampfphasen.

### Boss-Überarbeitung

- ⬜ Gegenwärtige Bossmechaniken vollständig analysieren.
- ⬜ Zufällige, ständig wechselnde AoE-Grafiken reduzieren.
- ⬜ Jeder Boss erhält ein oder zwei charakteristische AoE-Effekte.
- ⬜ Boss-Angriffe klarer und nachvollziehbarer gestalten.
- ⬜ Unnötige Effektüberlagerungen verhindern.
- ⬜ Grafiken und Fähigkeiten fest mit einem Bosstyp verbinden.
- ⬜ Doppelte beziehungsweise unnötige Boss-Grafikauswahl prüfen.
- ⬜ Bossgrafiken und Animationen effizient laden.
- ⬜ Vorhandene Bossbilder möglichst weiterverwenden.
- ⬜ Kleine Zufallsvariationen erlauben, ohne den Charakter des Bosses zu verändern.

### Seelenschrein / Boss-Erscheinung

- ⬜ Boss erscheint nicht unmittelbar als fertiger Gegner.
- ⬜ Stattdessen entsteht ein Seelenschrein, Knochenaltar oder Seelenportal.
- ⬜ Boss wird vorab ausgewählt und vorbereitet.
- ⬜ Spieler berührt den Schrein.
- ⬜ Erscheinungsanimation beginnt.
- ⬜ Nach ungefähr 1–2 Sekunden erscheint der Boss.
- ⬜ Spieler erhält ausreichend Zeit zum Ausweichen.
- ⬜ Boss darf nicht direkt auf dem Spieler erscheinen.
- ⬜ Bossmusik, Lichteffekte und Erscheinungsanimation später ergänzen.

### Individuelle Bosstypen

- ⬜ Wächter: langsam, kräftig, klassische Schüsse.
- ⬜ Jäger: schnelle Bewegungen und gezielte Angriffe.
- ⬜ Hexer: Frost-, Gift-, Sporen- oder andere Flächeneffekte.
- ⬜ Schattenboss: verschwindet und taucht an anderer Stelle auf.
- ⬜ Verfolger: jagt die Schlange und versucht, sie einzukesseln.
- ⬜ Fernkampfboss: verwendet besondere Schussmuster.
- ⬜ Weitere Bosse aus vorhandenen Grafiken entwickeln.
- 💡 **Einzigartige Bossfolge im Adventure-Modus:** Langfristig 20–40 thematisch erkennbare Bossprofile (nicht 20–40 neue Hardcode-Klassen). Pro Level/Abschnitt ein kuratierter Boss, eigene Arena, Attacken, Sound/Ansage, Belohnung. Classic darf weiterhin zufällige Bossbegegnungen verwenden.
- ⬜ **Kampfübergänge und Rückkehr:** Boss-Ankündigung → klarer Start → Kampf → deutlicher Sieg-/Belohnungsmoment → zurück ins normale Spiel samt kontrollierter Level-/Score-Fortsetzung. [Designkonzept](BOSS_ENCOUNTERS_DESIGN.md).

### Boss-Phasen

- ⬜ Bosse erhalten feste Angriffsmuster.
- ⬜ Unterschiedliche Kampfphasen abhängig von Lebenspunkten.
- ⬜ Phase 1: Grundangriffe.
- ⬜ Phase 2: zusätzliche Fähigkeiten.
- ⬜ Phase 3: gefährlichere Spezialangriffe.
- ⬜ Angriffe durch erkennbare Warnungen ankündigen.
- ⬜ Sichtbare Boss-Lebensleiste mit Phasenmarkierungen und klaren Angriffshinweisen/Cooldowns; optional stimmliche Ansagen mit Untertiteln, Audio nie als einziges Signal.
- ⬜ Bossbezogene, begrenzte Grafiken, Aura-/Farben- und Größenwechsel, Arena-Effekte und eigene Treffer-/Sieg-Sounds – keine beliebig gemischten Effekte.
- ⬜ Während eines Bosskampfs normale Zufallsgegner standardmäßig pausieren oder begrenzen; nur ausdrücklich definierte Boss-Minions erlauben. Danach normales Spawnverhalten wiederherstellen.
- ⬜ Schwierigkeit/HP/Schaden über Kapitel, verfügbare Items und Spielertempo balancieren; herausfordernd, aber ohne zufällige, praktisch unbesiegbare Ressourcen-Falle.
- ⬜ Ein Boss zuerst als vollständig spielbarer Vertical Slice (Einführung, 2–3 Phasen, Minions, Sieg, 1P/2P-Tests, Performance), danach Profile wiederverwenden.
- ⬜ Tunnel-, Loch- und Teleportmechaniken ermöglichen.
- ⬜ Schwierigkeit mit fortschreitendem Spiel erhöhen.
- ⬜ Bosse im Classic-Modus zufällig auswählen.
- ⬜ Bosse im Adventure-Modus gezielt einem Level zuordnen.
- 💡 Bossprofile später über JSON definieren.

---

## 07 · WORLD STUDIO 3.0 – FROSTAGE

**Ziel:** Ein vollständiger Level-Baukasten direkt innerhalb von DARK Snake.

- ✅ Einfacher LevelEditor bereits vorhanden.
- ✅ Grafik-Kacheln auswählen und platzieren möglich.
- ✅ Undo/Redo, benannte JSON-Entwürfe, Schutz bei ungespeicherten Änderungen und Altformat `custom_level.json` aus #121.
- ✅ Visuelle Kartenvorschau und ausdrückliche Classic-Hintergrundwahl aus #121.
- ✅ **Phase A.** Themenwelten, Level-Anzeigenamen, stabile Zuordnungen und eine getrennte, frei sortierbare Spielreihenfolge.
- ✅ **Phase A.** Aufklappbare Themen für 495 Tiles mit Suche, Vorschaubildern, Favoriten und manuell korrigierbaren Katalogeinträgen.
- ✅ **PR 1.** Separate Kollisionsebene für WALL und BARRIER mit sicherem Spielerstart im isolierten 1P-/2P-Wandtest.
- ✅ **#124.** Damage und Slow mit Trefferintervall, HP- und Tempoanzeige im isolierten Spieltest.
- ✅ **#125–#141.** Eingang der 175 FrostAge-PNGs als Originaldateien.
- ✅ **#142.** Zentraler Katalog, 175 geprüfte Laufzeitgrafiken und platzierbare Multi-Tiles mit Speichern und Undo/Redo.
- ✅ **#143 · FrostAge Main Menu.** Zwölf Menügrafiken mit vorhandenen Aktionen, pausierte Runden fortsetzen und den Hintergrund proportional an das Fenster anpassen.
- ✅ **#154 · Roof / Foreground.** Acht Dachgrafiken auf einer eigenen Ebene, Übertragen älterer Dachobjekte und spielbarer Dachbogen mit weichen Sichtfenstern in 1P und 2P.
- ✅ **#155 · PR A · Editor Layout.** Vergrößerbarer Editor mit Hauptnavigation, integriertem Baukasten, rechtem Arbeitsbereich und zoombarer Karte bei festem Spielraster.
- ✅ **#168 · Rand-Builder.** Vier Seiten und Ecken getrennt gestalten, Vorschau vor dem Anwenden, Mittelfeld weiter separat füllen.
- ✅ **#169 · Editor-Schaltflächen.** 48 von 81 eigenen PNGs über Action-IDs in World Studio integriert; fehlende Motive behalten einen Textbutton, 33 Vorlagen bleiben reserviert. 493 Headless-Tests, 30 Smoke-Simulationen und Windows-EXE-Prüfung laut PR abgeschlossen.
- ✅ **#167 · Asset-Legende.** Trennung von Laufzeitbildern und `GamePICs`-Vorlagen mit Katalogen und Agentenhinweisen dokumentiert.
- ✅ **#170 · Neue Screenshots.** Aktuelles Titelmenü und World-Studio-Ansicht für README/Galerie hochgeladen (keine neue Gameplayfunktion).
- ✅ **#173 · Sieben ergänzende Editor-Motive** als Originale hochgeladen.
- ✅ **#174 · PR C · Layer Explorer.** Sieben neue Editor-Motive als Laufzeitgrafiken zugeordnet (jetzt 55 statt 48 UI-Einträge), rechte Reiter verbessert, Ebenensichtbarkeit, Sperren, Solo-Modus und sichereres Löschen/Inspektor implementiert. **Merge bestätigt; sichtbare Windows-Gesamtabnahme nicht durch Merge ersetzt.**
- ⬜ **Ebenenvergleich.** Mehrere Ebenen mit abgestufter Deckkraft zur Orientierung anzeigen.
- ✅ **#179 · PR D · Deutsch / English und Hilfe.** Editor-Sprache im laufenden Betrieb wechseln und speichern. Hilfe und Lernen erklären Werkzeuge, Ebenen, Kollision, Dächer, Entwürfe und Leveltests.
- ⬜ **Fullscreen / Windowed · separater Folge-PR.** Die bestehende Fenstersteuerung für den Editor erweitern. Vorherige Fenstergröße speichern, beim Wechsel den sichtbaren Kartenausschnitt anpassen und beim Verlassen wiederherstellen. Spielraster, Entwurf und Verlauf erhalten. Resize-Ereignisse, DPI-Skalierung und mehrere Monitore unter Windows prüfen.
- ✅ **#180 · PR E · Learning System.** „Mein erstes FrostAge-Level“ mit fünf geprüften Schritten, eigener Übungskarte und direkter Rückkehr zum offenen Entwurf. Die Übung verwendet vorhandene Editorwerkzeuge und 1P-/2P-Leveltests. Merge bestätigt; gesonderte sichtbare Windows-Gesamtabnahme bleibt zu dokumentieren.
- ⬜ **PR F · Lighting & Atmosphere.** Helligkeit, platzierbare und spielergebundene Lichtquellen, Flackern, Nebel und Schattenflächen. Darstellung und HUD mit mehreren Lichtquellen bei 1350×930 prüfen.
- ⬜ **PR G · Trigger und Fallen.** Datenbasierte Auslöser, Bedingungen und Aktionen mit bestehenden Schadens- und Verlangsamungsregeln verbinden. Beispielkette: Druckplatte → Tor öffnet → Spezialgegner erscheint → Truhe wird freigeschaltet.
- ⬜ **Interaktive Levelobjekte.** Truhen, Fallen, Druckplatten, Schalter, Tore, Schlüssel und Portale mit eigenen Interaktionsregeln. Normale Gegner, Bosse und zufällige Items behalten die regulären Spawnmechanismen.
- ⬜ **Weitere Spielideen.** Frostburst mit acht Splittern, rotierender Tornado mit Kontaktschaden, Soundprofile und freischaltbare Schlangenköpfe und -körper.
- ✅ **#179 · PR D · Pinsel und schnelles Löschen.** FrostAge-Boden- und Wandgrafiken per Ziehen malen. Dekorationen, Dächer und frei skalierte Grafikobjekte einzeln stempeln. Rechtsklick löscht direkt auf sichtbaren, entsperrten Ebenen oder wahlweise nur auf der aktiven Ebene. Jede Ziehbewegung ist ein Undo-/Redo-Schritt.
- ⬜ **Schneller Levelbau.** Vollflächige World-Backgrounds, große Flächenfüllung, passende Tile-Übergänge, Favoriten und Design-Presets kombinieren; Benutzer soll nicht jede Bodenzelle einzeln gestalten müssen.
- ⬜ Stamp Builder als eigenen Arbeitsschritt einplanen.
- ⬜ **Danach.** 13 Projektil- und 11 AoE-Grafiken über bestehende Treffer- und Effektsysteme mit Profilen und sichtbaren Beispielen im Leveltest.
- ⬜ Acht FrostAge-Gegner mit Richtungsdarstellung, konfigurierbaren Angriffen, sicheren Editor-Spawns und Tests.
- ⬜ Fünf FrostAge-Items, unter anderem Schlüssel und Truhe. Interaktionen auf deklarative Leveldaten stützen.
- ⬜ Eigene Levels mit ihren Gameplay-Ebenen im Adventure-Modus spielen. Classic separat erhalten.
- ⬜ Druckplatten, Verzögerung und Schadenszone als Trigger-Arbeitspaket.
- ⬜ Größerer Spielrahmen um das unveränderte 45×31-Raster und später eine Challenge-Zeitleiste.
- ⬜ **PR H · World Backgrounds.** Dauerhaft gespeicherte Landschaften unter den Tiles mit Galerie und Vorschau. Themen sind Gothic Graveyard, Mystic Forest, FrostAge, Desert, Volcano und Galaxy. Der Spezialbild-Effekt über `Ü` bleibt ein zeitlich begrenzter Spieleffekt.
- 💡 **Sichtweiten-Mechanik.** Später Nebel- und Dunkelheitsmasken mit spielerbezogenem Radius; Items können die Sichtweite verändern, analog zur bestehenden Dach-Sichtfenster-Idee, aber mit eigenem Rendering.
- ⬜ Bestehenden Editor grundlegend erweitern.
- ✅ Eigenen großen, größenveränderbaren Editor-Bildschirm durch PR #155 umgesetzt.
- ⬜ Level Studio über die Entwicklerkonsole öffnen.
- ✅ Werkzeugleisten und 48 Bild-Buttons für vorhandene Aktionen durch PR #155/#169 umgesetzt; Restmotive und spätere Funktionen offen.
- ⬜ Kategorien für Hintergrund, Boden, Wände, Objekte, Gegner und Effekte.
- ✅ 495 Classic-Tiles und 175 FrostAge-Grafiken im Editor-Baukasten auswählbar.
- ⬜ Eigene Grafiken importieren.
- ✅ Grafikobjekte und FrostAge-Multi-Tiles direkt im Editor platzieren.
- ✅ Wände, Barrieren, Durchgänge und Randseiten im isolierten Editor-Leveltest mit Vorschau gestalten.
- ⬜ Objekte verschieben, löschen und verändern.
- ✅ Boden, Objekte, Roof/Foreground, Kollision und Effektfelder getrennt bearbeiten. Solo und Sperren sind Bestandteil von PR C.
- ⬜ Animierte Objekte platzieren.
- ⬜ Boss-Spawns und Seelenschreine platzieren.
- ⬜ Spieler-Spawnpunkte festlegen.
- ⬜ Level-Eigenschaften und Spielregeln bearbeiten.
- ✅ Editor-Kartenvorschau, 1P/2P-Leveltests und Werkzeuge vorhanden; weiteres Polishing geplant.
- ⬜ Bestehende Editorfunktionen erhalten und verbessern.

---

## 08 · WORLD DESIGN UND KOLLISIONEN

**Ziel:** Richtige Spielwelten statt ausschließlich farbiger Rasterfelder.

- ⬜ Große Hintergrundbilder für vollständige Level ermöglichen.
- ⬜ Hintergrundbilder mit Grafik-Kacheln kombinieren.
- ✅ Boden/Objekt-/Dachgrafik und WALL/BARRIER-Kollision im Editor getrennt, nicht automatisch gekoppelt.
- ✅ WALL/BARRIER-Zellen blockieren im **isolierten Editor-Leveltest**; nicht als vollständige Classic-Adventure-Kollision ausgeben.
- ✅ Im isolierten 1P/2P-Leveltest haben WALL/BARRIER eigene Kollisionsregeln; Classic bleibt getrennt.
- ⬜ Gegnerbewegung an Wände und Hindernisse anpassen.
- ⬜ Gegenstände nur auf gültigen Feldern erzeugen.
- ⬜ Durchgänge und erreichbare Bereiche überprüfen.
- ✅ Säulen, Mauern und Dachelemente als grafische Objekte verfügbar; Dachbogen-Demo ist spielbar.
- ⬜ Wasserfälle und animierte Böden ermöglichen.
- ⬜ Optische 3D-Tiefenwirkung mit 2D-Grafiken erzeugen.
- ⬜ Löcher und Abgründe als interaktive Spielfeldelemente entwickeln.
- ⬜ Teleporter, Spezialfelder und später bewegliche Hindernisse ermöglichen.
- ⬜ Dynamisch wachsende Myzelwände für spätere Pilz-Level vorbereiten.
- ✅ Grafik-/Kollisionsebenen in World Studio getrennt.
- ✅ Classic-Randwechsel und isolierter Editor-Wandtest getrennt; zukünftige Adventure-Regeln weiterhin geplant.

---

## 09 · LEVEL SPEICHERN, TESTEN UND EXPORTIEREN

**Ziel:** Levels selbst gestalten und ohne neue Programmierung verwenden.

- ⬜ Beliebig viele eigene Levels erstellen.
- ✅ Unfertige Levels als benannte JSON-Entwürfe speichern.
- ✅ Levelentwürfe wieder öffnen und weiterbearbeiten.
- ⬜ Automatische Zwischensicherung prüfen.
- ⬜ Fertige Levels gesondert kennzeichnen.
- ⬜ Levelnamen und Beschreibungen vergeben.
- ✅ Levelentwürfe werden im versionsgeprüften JSON-Format gespeichert.
- ⬜ Hintergrund, Kollisionen, Objekte und Spawnpunkte gemeinsam speichern.
- ✅ Grafik-Katalog-IDs und platzierte Objekte mit Levelentwürfen speichern.
- ✅ Isolierte Leveltests direkt aus World Studio für 1P/2P starten.
- ✅ Vom isolierten Leveltest zum Editor zurückkehren.
- ✅ Beim Leveltest bleiben die Editor-Entwurfsdaten erhalten.
- ✅ Isolierter Leveltest und reguläre Classic-Runde getrennt.
- ⬜ Fehlerhafte oder unspielbare Karten erkennen.
- ⬜ Fertige Level als Paket exportieren.
- ⬜ JSON und benötigte Grafiken an Codex oder Irian übergeben können.
- ⬜ Level später direkt durch das Spiel laden lassen.
- ⬜ Eigene Level ohne Programmänderung hinzufügen können.

### Level-Bibliothek

- ✅ Übersicht gespeicherter Entwürfe in Themenwelten.
- ⬜ Vorschaubilder anzeigen.
- ⬜ Status: Entwurf / Fertig.
- ⬜ Level bearbeiten, testen, kopieren und exportieren.
- ⬜ Beispielsweise 20 eigene Levels für den Adventure-Modus vorbereiten.

---

## 10 · ADVENTURE-MODUS & MYCELIUM AGE

**Ziel:** DARK Snake bekommt eigene Welten und Level-Abfolgen.

- ⬜ Classic Arcade bleibt als eigenständiger Modus erhalten.
- ⬜ Adventure als zusätzlicher Spielmodus.
- ⬜ Mehrere fest gestaltete Level nacheinander spielen.
- ⬜ Unterschiedliche Hintergrundwelten.
- ⬜ Unterschiedliche Hindernisse und Labyrinthe.
- ⬜ Spezielle Gegner abhängig vom Level.
- ⬜ Festgelegte Bossarenen.
- ⬜ Seelenschreine als mögliche Bossauslöser.
- ⬜ Spezialwaffen und Inventar in den Adventure-Modus integrieren.
- ⬜ Pilzwelt mit Sporen, Myzel, Gift und Frost.
- ⬜ Animierte Pilzlandschaften und interaktive Umgebung.
- ⬜ Neue Pilzgegner und individuelle Pilz-Bosse.
- ⬜ Später eigene Themenwelten und Grafikpakete ermöglichen.

---

## 11 · ENTWICKLER-SIMULATOR 2.0

**Ziel:** Tests sollen echte Spielfehler erkennen, nicht nur erfolgreiche Programmabläufe melden.

- ✅ Entwickler-Simulator bereits vorhanden.
- ✅ Automatisierte Spielsimulationen möglich.
- 🔧 Bestehende Tests auf Aussagekraft überprüfen.
- ✅ Entwickler-Simulator prüft seit #120 auch definierte Spielregeln statt nur Abstürze; weitere Szenarien offen.
- ✅ Erste fünf gezielte Spielregelprüfungen seit PR #120; vollständige Szenarioabdeckung weiterhin offen.
- ⬜ Fehlerhafte Kollisionen erkennen.
- ⬜ Spieler- und Gegnerverhalten prüfen.
- ⬜ Bossangriffe und Bossphasen testen.
- ⬜ Frost und andere Statuseffekte überprüfen.
- ⬜ Effektüberlagerungen und Schadensberechnung prüfen.
- ⬜ Level mit Wänden und Hindernissen simulieren.
- ⬜ 1P- und 2P-Szenarien getrennt untersuchen.
- ⬜ Normale Spieltests und Stresstests unterscheiden.
- ⬜ Fehlende Prüfungen erkennbar ausweisen.
- ⬜ Tests mit reproduzierbaren Zufallswerten durchführen.
- ⬜ Simulator gegen absichtlich eingebaute Testfehler prüfen.
- ⬜ Entwicklerberichte verständlicher und ausführlicher gestalten.
- ✅ Berichtsexport in den entpackten Spielordner mit Fallback nach User-Datenverzeichnis seit #120 vorgesehen.
- ✅ Fallback in Benutzer-Datenverzeichnis für nicht beschreibbare Installationsordner vorhanden.
- ✅ TXT-/JSON-Entwicklerberichte mit Prüfdetails seit PR #120 vorhanden.
- ⬜ Erfolgreiche, fehlgeschlagene und nicht ausgeführte Prüfungen unterscheiden.

---

## 12 · PERFORMANCE UND QUALITÄT

**Ziel:** Schnelle, direkte Steuerung und stabile Darstellung.

- 🎯 **Ziel 60 FPS**: pro Frame circa 16,67 ms Budget. **Zielwert, kein gemessener Ist-Stand**.
- ✅ `FrameMetrics` misst Bildabstand und Event-/Update-/Draw-/Present-Phasen, Eingabeannahme, Rasterwartezeit und Event→Bild (p50, p95, Max; Schwelle >33,3 ms).
- ✅ `scripts/benchmark_game.py` bietet reproduzierbare `1p`, `2p` und `load`-Lasten sowie `--uncapped` und `--overlay`. Das belegt **noch keine** echte Windows-FPS-Referenz.
- ⬜ **Erste dokumentierte Windows-Referenzmessung**: 1P, 2P, Boss/Projektile, Editor-Zoom/Dach, 900×620, 1350×930, maximiert; Commit, Rechner, Treiber, Szenario, Framezahl, p95/Max/Spikes festhalten.
- ⬜ **Laufende Regressionserkennung**: vor/nach Grafik- und Gameplay-PRs vergleichbare Benchmarks ausführen; reproduzierbare Verschlechterungen untersuchen statt automatische Erfolgsmeldungen.
- ⬜ Eingabeverzögerung **getrennt** von absichtlich späteren Rasterzügen bewerten; keine künstliche „16-ms-Gesamtlatenz“ verlangen.
- 🔧 UI-/FrostAge-Grafiken verwenden teils Cache; übrige Animations-/Bildpfade auf wiederholte Loads, Scaling, Alpha-Konversion und unnötige Zeichenaufrufe prüfen.
- ⬜ Bei vielen Gegnern, 24+ Projektilen, Bossen, Nebel, Roof-Masken und AoE **Bilder >33,3 ms** auswerten und Ursache bestimmen.
- ⬜ Beim späteren World-Background-, Light- und Layer-Ausbau Cache-Invalidierung, Render-Reihenfolge, RAM/EXE-Asset-Zuwachs und Zoom-Stress kontrollieren.
- ⬜ Simulator/Testergebnisse klar als **PASS / FAIL / NOT RUN** ausweisen; Soll-/Ist-Verhalten und reproduzierbare Fehlerbeispiele verlangen.
- ✅ Windows-CI kompiliert, prüft pytest und Asset-Kataloge, baut EXE + SHA-256-geprüftes ZIP; **sichtbarer Windows-Spieltest bleibt zusätzlich nötig**.
- ⬜ Nach jedem bedeutenden PR einen **Qualitätsnachweis** hinterlegen: Tests, realer Klicktest, 1P/2P soweit betroffen, Performancevergleich oder begründetes „nicht gemessen“.

**Messmethodik, vorläufige Schwellenwerte, Abnahmeprotokolle und spätere Classic-Tile-Pflege:** [QUALITY_PERFORMANCE_PLAN.md](QUALITY_PERFORMANCE_PLAN.md). **Keine tatsächlich gemessenen FPS-Werte erfinden.**

---

## 13 · TITELMENÜ 2.0 – GOTHIC ARCADE

**Ziel:** Das neue DARK-Snake-Titelmotiv wird zum hochwertigen, gut bedienbaren Hauptmenü (Flipper-/Gothic-Design).

- ⬜ Neues Titelbild als Hintergrund verwenden, sobald die Datei im Repository vorliegt.
- ⬜ Grafik und interaktive Buttons strikt trennen (keine fest eingebrannten Schaltflächen).
- ⬜ Große, deutlich sichtbare Hauptaktionen **1 Spieler** und **2 Spieler**.
- ⬜ Weitere Aktionen wie Optionen, Steuerung, Simulation und Zurück/Beenden sinnvoll auf dem Motiv verteilen.
- ⬜ Einheitliche verzierte Gothic-Rahmen, ausreichend Kontrast und gut lesbare Beschriftungen.
- ⬜ Maus-Hover, Tastatur-/Controller-Fokus und gedrückten Zustand sichtbar unterscheiden.
- ⬜ Kurzes Aufleuchten beim Aktivieren; Eingaben nicht mehrfach auslösen.
- ⬜ Neue Menüoberfläche weiterhin mit Input 2.0, Maus und Controllern nutzbar halten.
- ⬜ Menü erst nach echter Spielprobe übernehmen; bestehende Menünavigation erhalten.

---

## 14 · GO IN GAME – ÜBERGANGS- UND LEVEL-STARTBILDSCHIRM

**Ziel:** Eine bewusst gestaltete Tür zwischen Menü, Level, Bosskampf und Spielwelt.

- ⬜ Separaten Übergangszustand mit frei wählbarem Themenbild und optionaler Animation schaffen.
- ⬜ Levelname, kurze Einleitung, Hinweise oder Bossinformationen anzeigen.
- ⬜ Während des Übergangs Spielbewegung, Schaden und aktive Kampfzeit sicher anhalten.
- ⬜ Auf Spielerfreigabe warten (z. B. **Spiel starten / Weiter**), inklusive Tastatur und Controller.
- ⬜ Übergang für Spielstart und Levelwechsel wiederverwenden; Bossintro optional später.
- ⬜ Benötigte Assets und Leveldaten möglichst vor Spielbeginn vorbereiten; Ladefortschritt nur bei real messbarem Fortschritt anzeigen.
- ⬜ Keine blockierende Dauerschleife und kein eingefrorenes Fenster; UI bleibt bedienbar.
- ⬜ Themenbilder und Infotexte später über Leveldaten zuordnen, ohne Codeänderung pro Welt.

---

## 15 · GRAFIKWERKSTATT, ASSET-BIBLIOTHEK UND INTEGRATION

**Ziel:** Das grafische Erbe systematisch prüfen und neue Spielgrafiken unabhängig vom Codex-Budget vorbereiten.

- ✅ Grafikbestand aus GitHub erfasst: 907 PNG-Dateien, darunter 55 AoE-Grafiken, 495 Tiles und Animationsframes (Stand 11.11.2026).
- ✅ Externe HTML-Grafikbibliothek V2 zur Sichtung und Code-Referenzprüfung vorbereitet (noch kein Spielmodul).
- ⬜ Grafikstatus sorgfältig unterscheiden: **direkte Codeverknüpfung**, **dynamisch geladen**, **Archiv/Vorlage**, **Verwendung nicht nachgewiesen**.
- ⬜ Eine Code-Referenz nicht automatisch mit einer tatsächlich sichtbaren Laufzeitverwendung verwechseln.
- ⬜ Vorhandene AoE-Einzelbilder kontrollieren; neue Frost-, Feuer-, Gift-, Sporen- und Myzelgrafiken optional vorbereiten.
- ⬜ Projektilvarianten für Spieler 1 und 2 entwerfen; spätere Zuordnung erst durch Codeintegration.
- ⬜ Boss001/Boss002/Boss003, FlameExplosion und Bolbu als **Animationsframes**, nicht als Einzelbosse zählen.
- ⬜ Alte Kopf- und Körperdesigns sichten, Originalgrößen erhalten und Lesbarkeit im 30-Pixel-Spielraster testen.
- 💡 **Spätere Classic-Tile-Kuration:** Die 495 älteren Tiles auf Kombinierbarkeit, Stil, Nahtlosigkeit und Bedienbarkeit prüfen; eine kleinere empfohlene Standardpalette und einen Legacy-Bereich planen, bestehende Tile-IDs und gespeicherte Level erhalten. Nach dem Layer-Explorer-Merge weiterhin ausdrücklich **keine** Löschung oder Umbenennung im laufenden Betrieb.
- ⬜ Classic-Tile-Audit erst nach den wichtigeren Editor-/Gameplay-Arbeiten: Sichtprüfung, ID-/Nutzungsübersicht, Beispielkarten und Vorher-/Nachher-Messung von Ladezeit und Scrollen. Details im [Qualitätsplan](QUALITY_PERFORMANCE_PLAN.md).
- ⬜ Vorhandene zusätzliche Heads/Bodies nach Tests über die Skin-Auswahl verfügbar machen; **53 Head- und 15 Body-Kandidaten** aus `GamePICs` einzeln auf Dubletten/Qualität prüfen, stabile IDs und kreative Anzeigenamen vergeben. Umfang und visuelle Anforderungen: [UI-2.0-Bildprüfung](UI_2_0_SCREEN_AUDIT.md).
- 💡 Freischaltbare Schlangenköpfe/Körper und charakterbezogene Sounds für Treffer, Levelwechsel und Game Over.
- ✅ `titel2.png` ist bereits als Fenster-Icon eingebunden; EXE-Dateiicon gesondert prüfen.
- ⬜ Neue, unfertige PNG-Dateien zunächst in `GamePICs/Incoming/` nach Projektilen, Bossen, Gegnern, AoE, Heads, Bodies, Hintergründen und Animationen ablegen.
- ✅ Neue Bilder über GitHub-Uploads gesammelt; 48 geeignete Editorbilder nach Prüfung in separate Runtime-Assets übernommen.
- ✅ Stabile Katalog-IDs und Herkunft für derzeit **58 Editor-PNGs / 62 Action-IDs** sowie 175 FrostAge-Grafiken dokumentiert; weitere Rohbilder teils mit `ksnip_`-Namen noch nicht vollständig geprüft.
- ✅ Originalbilder bleiben in `GamePICs`; 48 Editor-Grafiken als Laufzeitkopien und skalierte Cache-Darstellung integriert.
- ✅ PNG-Abmessungen, transparente Bildbereiche und Original-Hashes der 48 integrierten Buttons durch Katalog und Tests geprüft.
- ✅ FrostAge- und Editorgrafiken über explizite Integrations-PRs eingebunden; neue Gegner-/Projektilmechaniken bleiben offen.
- 💡 Später optional HTML-Drop-in und PNG-/Paketexport; **vorerst unnötig**, da GitHub-Upload einfacher ist.

---

## 16 · UI 2.0 – OPTIONEN, SNAKE-GALERIE, STEUERUNG & BESTENLISTE

**Ziel:** Die historischen Alpha-Menüs funktionserhaltend in eine gemeinsame FrostAge-/Gothic-Arkade-Oberfläche überführen. **Planung und Bildprüfung:** [UI_2_0_SCREEN_AUDIT.md](UI_2_0_SCREEN_AUDIT.md) (Screenshots 15.11.2026, aktuelle Codepfade, einzelne Mini-Profile, Akzeptanzkriterien).

- ✅ Aktuell vorhanden: Optionen mit **4 oberen Aktionsbuttons**, **2 Tabs**, **5 Gameplay-Reglern**, **2 Audio-Reglern**, **Musik-Dropdown** und P1/P2-Vorschau; Auswahl und Speichern existieren.
- ✅ Aktuell vorhanden: Eingabemenü mit Spieler-/Gerätewahl, Aktionen, **6 unteren Befehlen** und Speicher-/Testfunktion; einfache Top-10-Bestenliste mit Rückkehrknopf.
- 🔧 **Beobachteter UI-Rückstand, kein Gameplay-Ausfall:** Überlappende Sliderlabels, große schwarze Leerflächen, uneinheitlich skalierte Schriften, alte grüne Doppelrahmen und unruhiger Audio-Dropdown.
- ⬜ **UI-2A · Options-FrostAge-Stil:** eigene ruhige Hintergrundgrafik, neue Buttons/Rahmen, klare Gruppierung, funktionierende Slider und gut bedienbarer Musik-Dropdown; **Spawnrate nicht als 0.0 anzeigen**, da interne Werte kleiner als 0,01 sind.
- ⬜ **UI-2B · Snake-Galerie:** bestehende Runtime-Skins und 53 neue Head-/15 Body-Kandidaten sichten, Dubletten/Artwork unterscheiden, katalogisieren, skalierte **und gecachte** Thumbnails sowie scrollbare Suche und kreative Namen. Separate tatsächliche 30×30-Spielgrößen-Vorschau für P1/P2 beibehalten.
- ⬜ **UI-2C · Steuerung:** bestehendes Input-2.0-/Geräte-/Rebinding-/Test-/Speicherverhalten erhalten, aber Lesbarkeit und Navigation an neues Menüschema anpassen.
- ⬜ **UI-2D · Bestenliste:** Rang 1–3 als aufwendig gestaltetes Podest mit Totenkopf-/Schlangenbaum-Thema, Rang 4–10 gut lesbar darunter; Elite/Legendär/Episch nur als **visuelle Auszeichnung**, solange keine geprüften Gameplay-Rangstufen bestehen. Bestehendes `name,score`-Format kompatibel erhalten.
- ⬜ **Einstellungen für alle vs. Entwickler:** Speed, Difficulty, Spawnrate und Boss-HP zunächst erhalten; Projectile-Speed und experimentelle Balanceparameter bei Bedarf in aufklappbaren Advanced-/Developer-Bereich verschieben, aber **nicht** vorzeitig entfernen.
- ⬜ **Performance & Qualität:** Bilder vorladen und skaliert cachen, fehlende Assets abfangen, Scroll-/Dropdown-Clipping, Fenstergrößen, 1P/2P, Keyboard/Controller, Save/Reload sowie FPS-Regressionen explizit prüfen.
- 💡 **Gestalterische Grundregel:** Dekorative, neue Grafiken und ruhige FrostAge-Farben dürfen Bedienbarkeit und tatsächlich angezeigte Original-Spritegröße nicht überdecken. Menü-Grafik und übersetzbarer UI-Text getrennt halten, wo möglich.
- ⬜ Alle UI-Bereiche **in separaten kleinen Draft-PRs** umsetzen; nach jedem Schritt sichtbare Windows-Abnahme. Bestehende Startmenü-/Editor-/Boss-/Highscore-Logik nicht ungeprüft umbauen.

---

# 🗺️ ENTWICKLUNGSREIHENFOLGE

**PHASE 1 – AKTUELLE ARBEIT**
✅ Frost, Simulator 2.0 und World Studio nach PR #180 auf `main`: 1P-/2P-Test, Roof/Foreground, Rand-Builder, Layer Explorer, DE/EN im Editor, Frost-Pinsel und interaktiver Lernkurs. Laufzeitkatalog: **58 Editor-PNGs für 62 Action-IDs**.
⬜ **Nächster Kontrollpunkt:** Sichtbare Windows-Abnahme des PR-E-Lernkurses und erste reproduzierbare Performance-Baseline. Qualitätswartung: [Classic-Regeln #181](https://github.com/DemusOpalium/dark-snake-game/issues/181), [Security #183](https://github.com/DemusOpalium/dark-snake-game/issues/183), [Code-/Dokumentationspflege #184](https://github.com/DemusOpalium/dark-snake-game/issues/184). [Messplan](QUALITY_PERFORMANCE_PLAN.md).
💡 **Neue Testbeobachtungen (15.11.):** FrostAge-Objekte sind einzeln zu stempeln, Classic-Ground-Tiles lassen sich durch Ziehen malen; langfristig UX vereinfachen, World Backgrounds vor einzelner Massen-Kachelkunst priorisieren. Bossfight 2.0 als gesondertes datenbasiertes Spielsystem planen.

**PHASE 2 – EFFECT & WEAPON SYSTEM 2.0**
Gemeinsame Effektarchitektur, Frost, Feuer, Gift, Sporen, Spezialmunition.

**PHASE 3 – INVENTAR UND SPEZIALSTEUERUNG**
Vier Slots pro Spieler, Item-Icons, frei belegbare Aktivierungstasten.

**PHASE 4 – BOSSFIGHT 2.0**
Seelenschrein, klar lesbare individuelle Bossprofile und Phasen; kontrolliertes Boss-Spawn-Verhalten, UI/Audio, Boss-Minions, Belohnung und heroischer Siegübergang. Im Adventure-Modus später eine kuratierte Folge von bis zu 20–40 thematischen Bossen; zuerst **einen vollständigen Vertical Slice** entwickeln. Konzept: [BOSS_ENCOUNTERS_DESIGN.md](BOSS_ENCOUNTERS_DESIGN.md).

**PHASE 5 – WORLD STUDIO 3.0**
Weltbibliothek, Kollision, Damage/Slow, FrostAge-Multi-Tiles, Hauptmenü, Roof / Foreground, Editor-Layout, Rand-Builder und **55 zugeordnete Editor-Bildaktionen** sind auf `main` integriert (#155, #168, #169, #174). Es folgen vollständige Sprache/Hilfe, Lernmodus, Licht/Nebel und Trigger in einzelnen PRs. Der **World-Background-Ansatz (PR H, Konzept)** erlaubt später dauerhaft gespeicherte Landschaften unter Tiles. Projektile/AoE/Gegner/Items, Freischalt-Skins und Adventure bleiben separate Arbeitspakete.

**PHASE 6 – LEVEL-VERWALTUNG**
Entwürfe, Level-Bibliothek, JSON, Grafikpakete, Export und Import.

**PHASE 7 – ADVENTURE & MYCELIUM AGE**
Eigene Welten, Pilzgegner, Bossarenen, neue Spielmechaniken.

**PARALLELE DESIGNARBEIT – OHNE SPIELCODE**
53 neue Head- und 15 Body-Kandidaten sowie 175 FrostAge-Originale bleiben als vorbereitete Quellen unter `GamePICs/`; Laufzeitkopien nur nach Prüfung in `Dark_Snake/assets`. Separater Skin-Galerie-PR mit scrollbarer Vorschau und späteren Freischaltungen bleibt offen.

**GEPLANTE UI-ERGÄNZUNGEN – IN KLEINEN PRs**
Titelmenü 2.0 (Gothic Arcade), GO IN GAME und **UI 2.0** (Options, Skins, Steuerung, Bestenliste) als getrennte, funktionserhaltende Arbeitspakete. Screenshots, Mini-Profile und Abnahmeplan: [UI_2_0_SCREEN_AUDIT.md](UI_2_0_SCREEN_AUDIT.md).

*Die Phasen sind eine vorläufige Reihenfolge. Gemeinsame technische Grundlagen können früher vorbereitet werden.*

---

# 🧠 GRUNDREGELN UNSERER ENTWICKLUNG

1. Bestehende funktionierende Systeme möglichst erhalten.
2. Neue Systeme modular und erweiterbar entwickeln.
3. Keine unnötigen Doppelentwicklungen.
4. Grafiken, Kollisionen und Spielregeln sauber trennen.
5. Classic Arcade nicht durch Adventure-Änderungen beschädigen.
6. Neue Funktionen zuerst testen, dann erweitern.
7. Performance bei jeder größeren Änderung berücksichtigen.
8. Neue Grafiken möglichst ohne tiefgreifende Codeänderungen einfügen können.
9. Boss- und Level-Design sollen später weitgehend über Daten konfigurierbar sein.
10. Kleine, überprüfbare Entwicklungsschritte statt eines unkontrollierten Komplettumbaus.

---

## 🐍 PROJEKTLEITGEDANKE

**DARK Snake soll nicht nur ein Spiel sein.**

Es soll ein Spiel werden, in dem wir eigene Welten, Bosse, Effekte und Spielmechaniken gestalten können.

Das langfristige Ziel ist ein modularer Spielebaukasten, in dem kreative Ideen zunehmend direkt umgesetzt werden können, ohne jedes Mal große Teile des Programmcodes verändern zu müssen.

**DARK SNAKE – WORLD 2 GO**

*Gemeinsame Entwicklungs- und Ideentafel von Demus & Irian.*

**Version der Ideenliste: 1.2 – jederzeit erweiterbar.**
