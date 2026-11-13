# 🛣️ ROADMAP.md – Entwicklungsfahrplan

## 2025
- ✅ Q2: Finales README + Screenshot-Galerie + Dev-Kategorie GitHub
- 🔜 Q3: Prompt-System aktivieren, Debug-Doku automatisieren
- 🔜 Q4: Kivy-Portierung testen (Mobile Release optional)

## 2026
- 🔜 Q1: WebGL / Browser-Testversion
- 🔜 Q2: Feature Freeze, Vorbereitung auf Public Showcase

---

## 📚 Weitere Dokumentation

- 📦 [Modulübersicht (DEV_STRUCTURE.md)](DEV_STRUCTURE.md)
- 🎨 [Screenshot-Galerie (GALLERY.md)](GALLERY.md)
- 🎮 [Steuerung (CONTROLS.md)](CONTROLS.md)
- 🤖 [Prompt-Guide für GPT (PROMPT_GUIDE.md)](PROMPT_GUIDE.md)
- 🛣️ [Projekt-Roadmap (ROADMAP.md)](ROADMAP.md)


# 🐍 DARK SNAKE – WORLD 2 GO
## Master-Ideenliste · Entwicklungstafel · Roadmap
**Stand: 11.11.2026**

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
- ⬜ Grafiken nach Kategorien und Themen organisieren.
- ⬜ Eigene Effekt- und Grafikpakete ermöglichen.
- ⬜ Animationen über Einzelbilder oder Spritesheets verwenden.
- ⬜ Größe, Bildrate, Transparenz und Darstellungsebene einstellen.
- ⬜ Grafiken möglichst einmal laden und zwischenspeichern.
- ⬜ Wiederholte Skalierung während der Darstellung reduzieren.
- ⬜ Grafische Effekte unabhängig von Schadens- und Kollisionsberechnungen behandeln.
- ⬜ Fehlende Grafiken durch sichere Ersatzdarstellungen abfangen.
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
- 🔧 **PR 1 · FrostAge Main Menu.** Zwölf Menügrafiken mit vorhandenen Aktionen, pausierte Runden fortsetzen und den Hintergrund proportional an das Fenster anpassen.
- ⬜ **PR 2 · World Studio UI.** Vergrößerbarer Editor mit integriertem Katalog, Werkzeugleisten, rechtem Eigenschaftenpanel, Zoom, Ebenenauswahl, Tooltips und deutscher Hilfe. Stamp Builder als eigenen Schritt einplanen.
- ⬜ **PR 3 · Roof / Foreground.** Acht vorhandene Dachgrafiken auf einer eigenen Ebene platzieren und bestehende Dachobjekte gezielt verschieben können. Weiche Sichtfenster im 1P- und 2P-Leveltest prüfen.
- ⬜ **PR 4 · Lighting & Atmosphere.** Helligkeit, platzierbare und spielergebundene Lichtquellen, Flackern, Nebel und Schattenflächen speichern und laden. Darstellung und HUD mit mehreren Lichtquellen bei 1350×930 prüfen.
- ⬜ **Danach.** 13 Projektil- und 11 AoE-Grafiken über bestehende Treffer- und Effektsysteme mit Profilen und sichtbaren Beispielen im Leveltest.
- ⬜ Acht FrostAge-Gegner mit Richtungsdarstellung, konfigurierbaren Angriffen, sicheren Editor-Spawns und Tests.
- ⬜ Fünf FrostAge-Items, unter anderem Schlüssel und Truhe. Interaktionen auf deklarative Leveldaten stützen.
- ⬜ Eigene Levels mit ihren Gameplay-Ebenen im Adventure-Modus spielen. Classic separat erhalten.
- ⬜ Druckplatten, Verzögerung und Schadenszone als Trigger-Arbeitspaket.
- ⬜ Größerer Spielrahmen um das unveränderte 45×31-Raster und später eine Challenge-Zeitleiste.
- ⬜ Bestehenden Editor grundlegend erweitern.
- ⬜ Eigenen großen Editor-Bildschirm entwickeln.
- ⬜ Level Studio über die Entwicklerkonsole öffnen.
- ⬜ Übersichtliche Buttons und Werkzeugleisten erstellen.
- ⬜ Kategorien für Hintergrund, Boden, Wände, Objekte, Gegner und Effekte.
- ⬜ Vorhandene Grafiken als auswählbare Kacheln anzeigen.
- ⬜ Eigene Grafiken importieren.
- ⬜ Grafiken direkt auf der Karte platzieren.
- ⬜ Wände, Durchgänge und Labyrinthe konstruieren.
- ⬜ Objekte verschieben, löschen und verändern.
- ⬜ Verschiedene Grafik- und Spielebenen bearbeiten.
- ⬜ Animierte Objekte platzieren.
- ⬜ Boss-Spawns und Seelenschreine platzieren.
- ⬜ Spieler-Spawnpunkte festlegen.
- ⬜ Level-Eigenschaften und Spielregeln bearbeiten.
- ⬜ Benutzerfreundliche Vorschau und Werkzeugauswahl.
- ⬜ Bestehende Editorfunktionen erhalten und verbessern.

---

## 08 · WORLD DESIGN UND KOLLISIONEN

**Ziel:** Richtige Spielwelten statt ausschließlich farbiger Rasterfelder.

- ⬜ Große Hintergrundbilder für vollständige Level ermöglichen.
- ⬜ Hintergrundbilder mit Grafik-Kacheln kombinieren.
- ⬜ Visuelle Boden- und Wandgrafiken unabhängig voneinander einsetzen.
- ⬜ Rasterfelder als echte Hindernisse definieren.
- ⬜ Wandkollisionen für die Schlange entwickeln.
- ⬜ Gegnerbewegung an Wände und Hindernisse anpassen.
- ⬜ Gegenstände nur auf gültigen Feldern erzeugen.
- ⬜ Durchgänge und erreichbare Bereiche überprüfen.
- ⬜ Säulen, Mauern und dekorative Elemente verwenden.
- ⬜ Wasserfälle und animierte Böden ermöglichen.
- ⬜ Optische 3D-Tiefenwirkung mit 2D-Grafiken erzeugen.
- ⬜ Löcher und Abgründe als interaktive Spielfeldelemente entwickeln.
- ⬜ Teleporter, Spezialfelder und später bewegliche Hindernisse ermöglichen.
- ⬜ Dynamisch wachsende Myzelwände für spätere Pilz-Level vorbereiten.
- ⬜ Kollision und Grafik voneinander trennen.
- ⬜ Classic-Randwechsel und neue Adventure-Wandregeln getrennt behandeln.

---

## 09 · LEVEL SPEICHERN, TESTEN UND EXPORTIEREN

**Ziel:** Levels selbst gestalten und ohne neue Programmierung verwenden.

- ⬜ Beliebig viele eigene Levels erstellen.
- ⬜ Unfertige Levels als Entwurf speichern.
- ⬜ Entwürfe jederzeit wieder öffnen und weiterbearbeiten.
- ⬜ Automatische Zwischensicherung prüfen.
- ⬜ Fertige Levels gesondert kennzeichnen.
- ⬜ Levelnamen und Beschreibungen vergeben.
- ⬜ Leveldaten automatisch als JSON speichern.
- ⬜ Hintergrund, Kollisionen, Objekte und Spawnpunkte gemeinsam speichern.
- ⬜ Verwendete Grafiken einem Level zuordnen.
- ⬜ Level direkt aus dem Editor spielbar testen.
- ⬜ Nach dem Test wieder zum Editor zurückkehren.
- ⬜ Den bisherigen Bearbeitungsstand beim Test erhalten.
- ⬜ Normale Spielstände vom Editor-Test trennen.
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
- ⬜ Nicht ausschließlich Abstürze zählen.
- ⬜ Erwartetes und tatsächliches Spielverhalten vergleichen.
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
- ⬜ Testberichte direkt im entpackten Spielordner auffindbar machen, sofern beschreibbar.
- ⬜ Alternativen für schreibgeschützte Installationsordner vorsehen.
- ⬜ TXT-/JSON-Berichte mit Datum, Version, Szenario und Fehlerdetails erzeugen.
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
- ⬜ Neue Grafiken über `Add file → Upload files` auf GitHub einreichen; aktive Assets erst nach Prüfung gezielt ersetzen.
- ⬜ Klare, sprechende Dateinamen vergeben und Kategorie, Verwendungszweck, Original-/Zielgröße und gegebenenfalls Frames dokumentieren.
- ⬜ Originalgrafiken erhalten; Skalierungen durch das Spiel beziehungsweise Build-Werkzeug vorbereiten.
- ⬜ Transparenz, Zuschnitt und Spielgrößen kontrollieren, bevor Assets live eingebaut werden.
- ⬜ Codex kann vorbereitete Bilder aus `GamePICs/Incoming/` erst nach explizitem Integrationsauftrag den passenden Ressourcen und Mechaniken zuordnen.
- 💡 Später optional HTML-Drop-in und PNG-/Paketexport; **vorerst unnötig**, da GitHub-Upload einfacher ist.

---

# 🗺️ ENTWICKLUNGSREIHENFOLGE

**PHASE 1 – AKTUELLE ARBEIT**
Frost und Simulator 2.0 Schritt 1 auf `main` bestätigt; als Nächstes Windows-Spielprobe und gezielte Grafikprüfung. Eine kleine Level-Studio-Etappe (benannte Entwürfe) darf vorgezogen werden, damit Demus selbstständig Levels gestalten kann.

**PHASE 2 – EFFECT & WEAPON SYSTEM 2.0**
Gemeinsame Effektarchitektur, Frost, Feuer, Gift, Sporen, Spezialmunition.

**PHASE 3 – INVENTAR UND SPEZIALSTEUERUNG**
Vier Slots pro Spieler, Item-Icons, frei belegbare Aktivierungstasten.

**PHASE 4 – BOSSFIGHT 2.0**
Seelenschrein, individuelle Bosstypen, feste AoE-Profile, Kampfphasen.

**PHASE 5 – WORLD STUDIO 3.0**
Weltbibliothek, Kollision, Damage/Slow und die FrostAge-Multi-Tiles sind integriert. Es folgen FrostAge-Hauptmenü, World-Studio-Oberfläche, Roof/Foreground und Lighting & Atmosphere. Projektile und AoE, Gegner, Items und Adventure folgen danach.

**PHASE 6 – LEVEL-VERWALTUNG**
Entwürfe, Level-Bibliothek, JSON, Grafikpakete, Export und Import.

**PHASE 7 – ADVENTURE & MYCELIUM AGE**
Eigene Welten, Pilzgegner, Bossarenen, neue Spielmechaniken.

**PARALLELE DESIGNARBEIT – OHNE SPIELCODE**
Grafikbibliothek sichten, Heads/Bodies/Projektile/AoE überarbeiten und als `GamePICs/Incoming/` für spätere Integration vorbereiten.

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
