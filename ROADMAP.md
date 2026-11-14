# 🛣️ ROADMAP.md – Entwicklungsfahrplan

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


# 🐍 DARK SNAKE – WORLD 2 GO
## Master-Ideenliste · Entwicklungstafel · Roadmap
**Stand: 14.11.2026 · aktueller `main` nach PR #170**

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

### Boss-Phasen

- ⬜ Bosse erhalten feste Angriffsmuster.
- ⬜ Unterschiedliche Kampfphasen abhängig von Lebenspunkten.
- ⬜ Phase 1: Grundangriffe.
- ⬜ Phase 2: zusätzliche Fähigkeiten.
- ⬜ Phase 3: gefährlichere Spezialangriffe.
- ⬜ Angriffe durch erkennbare Warnungen ankündigen.
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
- ⬜ **PR C · Layer Explorer.** Ebenenfarben, Sichtbarkeit, Sperren und Vergleich, Zellen-Inspektor mit Objektauswahl, Effektbearbeitung und sicheres Löschen samt Radierer.
- ⬜ **PR D · Deutsch / English und Hilfe.** Gespeicherte Sprachwahl, vollständige Übersetzung, Tooltips und Werkzeugbeschreibungen.
- ⬜ **PR E · Learning System.** „Mein erstes FrostAge-Level“ mit geprüften Schritten in einer eigenen Übungskarte.
- ⬜ **PR F · Lighting & Atmosphere.** Helligkeit, platzierbare und spielergebundene Lichtquellen, Flackern, Nebel und Schattenflächen. Darstellung und HUD mit mehreren Lichtquellen bei 1350×930 prüfen.
- ⬜ **PR G · Trigger und Fallen.** Auslöser, Bedingungen und Aktionen mit bestehenden Schadens- und Verlangsamungsregeln verbinden.
- ⬜ Stamp Builder als eigenen Arbeitsschritt einplanen.
- ⬜ **Danach.** 13 Projektil- und 11 AoE-Grafiken über bestehende Treffer- und Effektsysteme mit Profilen und sichtbaren Beispielen im Leveltest.
- ⬜ Acht FrostAge-Gegner mit Richtungsdarstellung, konfigurierbaren Angriffen, sicheren Editor-Spawns und Tests.
- ⬜ Fünf FrostAge-Items, unter anderem Schlüssel und Truhe. Interaktionen auf deklarative Leveldaten stützen.
- ⬜ Eigene Levels mit ihren Gameplay-Ebenen im Adventure-Modus spielen. Classic separat erhalten.
- ⬜ Druckplatten, Verzögerung und Schadenszone als Trigger-Arbeitspaket.
- ⬜ Größerer Spielrahmen um das unveränderte 45×31-Raster und später eine Challenge-Zeitleiste.
- ⬜ **PR H – World Backgrounds (neue Idee 14.11.).** Vollflächige, dauerhaft gespeicherte Landschaftsbilder unter Boden/Objekten/Kollisionen/Dächern; Galerie, Vorschau, geordnete Render-Ebenen, auswählbare Themen wie Friedhof, Wald, Eis, Wüste, Vulkan und Weltraum. Bestehenden kurzlebigen Spezialbild-Effekt über `Ü` nicht mit der permanenten Hintergrundebene verwechseln.
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
- ✅ Boden, Objekte, Roof/Foreground, Kollision und Effektfelder getrennt bearbeiten; Solo/Lock/Vergleich bleiben PR C.
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

- ⬜ 60 FPS als wichtiges Mindestziel für flüssiges Spiel.
- ⬜ Bildbudget von ungefähr 16,67 ms berücksichtigen.
- ⬜ Eingabeverzögerung getrennt von der Rasterbewegung messen.
- ⬜ Effekte dürfen keine unnötigen Ruckler verursachen.
- ⬜ Animationen nicht ständig neu laden oder berechnen.
- ⬜ Grafik- und Effekt-Caching verbessern.
- ⬜ Unnötige doppelte Berechnungen vermeiden.
- ⬜ Grenzen für gleichzeitig aktive Effekte festlegen.
- ⬜ Leistung bei vielen Gegnern und Projektilen messen.
- ⬜ Bosskämpfe besonders intensiv testen.
- ⬜ Level-Editor und Testmodus dürfen die normalen Spielregeln nicht beschädigen.
- ⬜ Windows-EXE und ZIP regelmäßig überprüfen.
- ⬜ Automatisierte Tests durch echte Windows-Spieltests ergänzen.

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
- ⬜ Vorhandene zusätzliche Heads/Bodies nach Tests über die Skin-Auswahl verfügbar machen.
- 💡 Freischaltbare Schlangenköpfe/Körper und charakterbezogene Sounds für Treffer, Levelwechsel und Game Over.
- ✅ `titel2.png` ist bereits als Fenster-Icon eingebunden; EXE-Dateiicon gesondert prüfen.
- ⬜ Neue, unfertige PNG-Dateien zunächst in `GamePICs/Incoming/` nach Projektilen, Bossen, Gegnern, AoE, Heads, Bodies, Hintergründen und Animationen ablegen.
- ✅ Neue Bilder über GitHub-Uploads gesammelt; 48 geeignete Editorbilder nach Prüfung in separate Runtime-Assets übernommen.
- 🔧 Stabile Katalog-IDs und Herkunft für 48 Editor-Buttons sowie 175 FrostAge-Grafiken dokumentiert; weitere Rohbilder teils mit `ksnip_`-Namen, noch nicht vollständig geprüft.
- ✅ Originalbilder bleiben in `GamePICs`; 48 Editor-Grafiken als Laufzeitkopien und skalierte Cache-Darstellung integriert.
- ✅ PNG-Abmessungen, transparente Bildbereiche und Original-Hashes der 48 integrierten Buttons durch Katalog und Tests geprüft.
- ✅ FrostAge- und Editorgrafiken über explizite Integrations-PRs eingebunden; neue Gegner-/Projektilmechaniken bleiben offen.
- 💡 Später optional HTML-Drop-in und PNG-/Paketexport; **vorerst unnötig**, da GitHub-Upload einfacher ist.

---

# 🗺️ ENTWICKLUNGSREIHENFOLGE

**PHASE 1 – AKTUELLE ARBEIT**
✅ Frost und Simulator 2.0 Schritt 1 sowie World Studio nach PR #169 auf `main`: benannte Entwürfe, 1P/2P-Leveltest, Roof/Foreground, Rand-Builder, 48 grafische Buttons. Nächster eigenständiger PR: Layer Explorer (Solo, Sperren, Inspektor, sicheres Löschen). Für die weitere Grafikarbeit gelten die Kataloge; neue Gameplay-Profile werden separat entwickelt.

**PHASE 2 – EFFECT & WEAPON SYSTEM 2.0**
Gemeinsame Effektarchitektur, Frost, Feuer, Gift, Sporen, Spezialmunition.

**PHASE 3 – INVENTAR UND SPEZIALSTEUERUNG**
Vier Slots pro Spieler, Item-Icons, frei belegbare Aktivierungstasten.

**PHASE 4 – BOSSFIGHT 2.0**
Seelenschrein, individuelle Bosstypen, feste AoE-Profile, Kampfphasen.

**PHASE 5 – WORLD STUDIO 3.0**
Weltbibliothek, Kollision, Damage/Slow, FrostAge-Multi-Tiles, Hauptmenü, Roof / Foreground, Editor-Layout, Rand-Builder und **48 grafische Editor-Buttons** sind integriert (#155, #168, #169). Es folgen Layer Explorer (PR C), vollständige Sprache/Hilfe, Lernmodus, Licht/Nebel und Trigger in einzelnen PRs. Der neue **World-Background-Ansatz (PR H, Konzept)** erlaubt später dauerhaft gespeicherte Vollbildlandschaften unter Tiles. Projektile/AoE/Gegner/Items, Freischalt-Skins und Adventure bleiben separate Arbeitspakete.

**PHASE 6 – LEVEL-VERWALTUNG**
Entwürfe, Level-Bibliothek, JSON, Grafikpakete, Export und Import.

**PHASE 7 – ADVENTURE & MYCELIUM AGE**
Eigene Welten, Pilzgegner, Bossarenen, neue Spielmechaniken.

**PARALLELE DESIGNARBEIT – OHNE SPIELCODE**
53 neue Head- und 15 Body-Kandidaten sowie 175 FrostAge-Originale bleiben als vorbereitete Quellen unter `GamePICs/`; Laufzeitkopien nur nach Prüfung in `Dark_Snake/assets`. Separater Skin-Galerie-PR mit scrollbarer Vorschau und späteren Freischaltungen bleibt offen.

**GEPLANTE UI-ERGÄNZUNGEN – IN KLEINEN PRs**
Titelmenü 2.0 (Gothic Arcade) und GO IN GAME als wiederverwendbaren Übergangsbildschirm entwickeln, sobald Bilder und technische Grundlagen bereitstehen.

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
