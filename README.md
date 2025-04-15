<!-- Coverbild oben in der README -->
<p align="center">
  <img src="Dark_Snake/assets/graphics/2222124.png" alt="Dark Snake Game Cover" width="800px">
</p>

<hr style="border: 2px solid #FF6600;">

# Dark Snake Game

**Willkommen zum Dark Snake Game – dem ultimativen Snake-Erlebnis mit Bosskämpfen, magischen Portalen, witzigen AOE-Effekten und einer modernen, modularen Architektur.**  
_Tauche ein in ein Spielerlebnis, das so einzigartig ist wie dein Humor – dunkler, schneller und überraschender, als man es sich je vorgestellt hat!_

---

## Inhaltsverzeichnis

- [Über das Spiel](#über-das-spiel)
- [Features im Überblick](#features-im-überblick)
- [Screenshots & Spielaufnahmen](#screenshots--spielaufnahmen)
  - [Standardaufnahmen](#standardaufnahmen)
  - [Weitere Spielaufnahmen (GamePICs)](#weitere-spielaufnahmen-gamepics)
- [Installation und Ausführung](#installation-und-ausführung)
- [Modulare Architektur](#modulare-architektur)
  - [Konfiguration (config.py)](#konfiguration-configpy)
  - [Main-Startpunkt (main.py)](#main-startpunkt-mainpy)
  - [AOE-Zonen (aoe_zones.py)](#aoe-zonen-aoe_zonespy)
  - [Audio (audio.py)](#audio-audiopy)
  - [Steuerung (controls.py)](#steuerung-controlspy)
  - [Anpassungs-Menü (customization.py)](#anpassungs-menü-customizationpy)
  - [Gegner (enemies.py)](#gegner-enemiespy)
  - [Aufzählungen (enums.py)](#aufzählungen-enumspy)
  - [Spiel-Logik (game.py)](#spiel-logik-gamepy)
  - [Options-Menü (options_menu.py)](#options-menü-options_menupy)
- [Bereitstellung des Quellcodes als ZIP](#bereitstellung-des-quellcodes-als-zip)
- [Lizenz](#lizenz)
- [Kontakt & Feedback](#kontakt--feedback)

---

## Über das Spiel

**Dark Snake Game** kombiniert den klassischen Spielspaß von Snake mit modernen Herausforderungen. Steuere deine Schlange durch dynamische Level, sammle Power-Ups, besiege furchteinflößende Bosse und nutze überraschende Spezialeffekte wie Portale und AOE-Zonen – und das alles in einem visuell und akustisch ansprechenden Dark-Art-Stil!

---

## Features im Überblick

- **Dynamische Spielmechanik:** Klassisches Snake trifft auf innovative Bosskämpfe, Power-Ups, Portale und AOE-Effekte.
- **Individuelle Anpassungen:** Wähle verschiedene Schlangendesigns und passe Gameplay-Einstellungen sowie Audio über ein modernes Optionsmenü an.
- **Modulare Architektur:** Sauber getrennte Module (Konfiguration, Grafik, UI, Audio, Gameplay usw.) erleichtern Wartung und Erweiterung.
- **Visuelle und akustische Highlights:** Atemberaubende Grafiken und passende Soundeffekte sorgen für ein intensives Spielerlebnis.
- **Bereit als ZIP:** Den kompletten Quellcode findest du als ZIP zum Herunterladen – perfekt für alle, die tiefer einsteigen oder das Spiel anpassen möchten.

---

## Screenshots & Spielaufnahmen

### Standardaufnahmen

#### Titelbild
<p align="center">
  <img src="Dark_Snake/assets/graphics/2222124.png" alt="Spiel Titelbild" width="500px">
</p>

#### Options- und Profilbilder
<p align="center">
   <img src="GamePICs/SnakeHeads.png" alt="Snake Heads" width="600px">
</p>

#### Steuerung
<p align="center">
   <img src="GamePICs/Steuerung.png" alt="Steuerung" width="600px">
</p>

#### Spielszene (Aufnahmen)
- **Spiel Szene 1:**
  <p align="center">
    <img src="GamePICs/TwoPlayerModus.png" alt="Two Player Modus" width="600px">
  </p>
  
- **Boss Fight 1:**
  <p align="center">
    <img src="Dark_Snake/assets/graphics/Boss-DemusG60.png" alt="Boss Fight 1" width="200px">
  </p>
  
- **Portal Event:**
  <p align="center">
    <img src="Dark_Snake/assets/graphics/PortalTempelG60.png" alt="Portal Event" width="150px">
  </p>
  
- **AOE Effekte:**
  <p align="center">
    <img src="Dark_Snake/assets/graphics/AOEEffekte/DungeonAOE.png" alt="AOE Effekt" width="600px">
  </p>

### Weitere Spielaufnahmen (GamePICs)

Diese zusätzlichen Bilder zeigen weitere spannende Aspekte und Designelemente des Spiels:
- **AOE-Zonen:**  
  <p align="center">
    <img src="GamePICs/AOE-Zonen.png" alt="AOE-Zonen" width="600px">
  </p>
- **Backround Settings:**  
  <p align="center">
    <img src="GamePICs/Backround-Settings.png" alt="Backround Settings" width="600px">
  </p>
- **Boss Game Over:**  
  <p align="center">
    <img src="GamePICs/Boss-Game-Over.png" alt="Boss Game Over" width="600px">
  </p>
- **LeaderBoard:**  
  <p align="center">
    <img src="GamePICs/LeaderBoard.png" alt="LeaderBoard" width="600px">
  </p>
- **Musicmp3-wave-backroundmusic:**  
  <p align="center">
    <img src="GamePICs/Musicmp3-wave-backroundmusic.png" alt="Hintergrundmusik" width="600px">
  </p>
- **Options:**  
  <p align="center">
    <img src="GamePICs/Options.png" alt="Options" width="600px">
  </p>
- **SnakeBodies:**  
  <p align="center">
    <img src="GamePICs/SnakeBodies.png" alt="Snake Bodies" width="600px">
  </p>
- **SnakeHeads:**  
  <p align="center">
    <img src="GamePICs/SnakeHeads.png" alt="Snake Heads" width="600px">
  </p>
- **StartMenü:**  
  <p align="center">
    <img src="GamePICs/StartMenü.png" alt="Start Menü" width="600px">
  </p>
- **Steuerung:**  
  <p align="center">
    <img src="GamePICs/Steuerung.png" alt="Steuerung" width="600px">
  </p>
- **TwoPlayerModus:**  
  <p align="center">
    <img src="GamePICs/TwoPlayerModus.png" alt="Two Player Modus" width="600px">
  </p>

---

## Installation und Ausführung

### Voraussetzungen
- [Python 3.12](https://www.python.org/downloads/)
- [Pygame](https://www.pygame.org/news)
- Weitere Abhängigkeiten können über `pip install -r requirements.txt` installiert werden (falls vorhanden).

### Spiel starten
- **Über den Quellcode:**  
  Starte das Spiel mit:
  ```bash
  python Dark_Snake/main.py

    Als EXE:
    Lade das über GitHub Actions erstellte Build-Artefakt (ZIP-Datei) herunter und führe die EXE-Datei auf einem Windows-System aus.

Modulare Architektur

Das Dark Snake Game ist in mehrere Module unterteilt, um Wartung und Erweiterung zu erleichtern:
Konfiguration (config.py)

Definiert globale Einstellungen – von Bildschirmgröße und Skalierungsfaktor bis zu Farben, Schriftarten und Gameplay-Konstanten.
Main-Startpunkt (main.py)

Initialisiert Pygame, Fonts, Mixer und startet die Hauptspiel-Logik.
AOE-Zonen (aoe_zones.py)

Implementiert verschiedene AOE-Effekte (Schaden, Heilung, Debuff, vollflächiger Hintergrund) und lädt zufällige Effektbilder.
Audio (audio.py)

Lädt und spielt Soundeffekte sowie Hintergrundmusik ab und erlaubt die Anpassung der Lautstärke.
Steuerung (controls.py)

Stellt die Steuerungsoptionen sowie Tastenzuweisungen für Einzel- und Mehrspielermodus grafisch dar.
Anpassungs-Menü (customization.py)

Ermöglicht dem Spieler, individuelle Schlangenköpfe und -körper auszuwählen – inklusive dynamischer Thumbnails.
Gegner (enemies.py)

Verwaltet das Spawnen und die Bewegung von Gegnern, mit zufälligen Eigenschaften wie Geschwindigkeit und Gesundheit.
Aufzählungen (enums.py)

Definiert alle relevanten Enums, wie GameState, Direction und ItemType, für konsistente Werte im Code.
Spiel-Logik (game.py)

Das Herzstück des Spiels – verwaltet Spielzustände, Schlangenbewegung, Kollisionsprüfung, Bosskämpfe, Items, Power-Ups und mehr.
Options-Menü (options_menu.py)

Bietet ein modernes Menü für Gameplay- und Audio-Einstellungen sowie ein Image Inventory zur Auswahl von Schlangendesigns.
Bereitstellung des Quellcodes als ZIP

Du kannst den kompletten Quellcode des Dark Snake Games auch als ZIP-Datei herunterladen. Der Build-Prozess via GitHub Actions erstellt automatisch ein Build-Artefakt, das du in der Actions-Übersicht unter „Build Artifact“ findest.
So kannst du jederzeit die aktuelle Version des Quellcodes sichern – ideal, wenn du selbst Hand anlegen oder einfach nur stöbern möchtest.
Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details findest du in der LICENSE Datei.
Kontakt & Feedback

Hast du Fragen, Ideen oder witzige Vorschläge für Dark Snake Game?
Öffne ein GitHub Issue oder schreib mir direkt eine E-Mail an deine.email@domain.de.
Und denk daran: Auch Schlangen haben ihren Humor – also behalte immer ein Lächeln auf den Lippen!

Vielen Dank, dass du Dark Snake Game ausprobierst – viel Spaß beim Spielen und Programmieren!


---

### Hinweise zur Umsetzung

1. **Bildpfade prüfen:**  
   Stelle sicher, dass die relativen Pfade zu deinen Bildern stimmen. In diesem Beispiel werden die Bilder aus `Dark_Snake/assets/graphics/` bzw. `GamePICs/` eingebunden. Passe die Pfade ggf. an, falls deine Repository-Struktur anders aufgebaut ist.

2. **Persönlicher Touch:**  
   Die README-Datei enthält humorvolle, persönliche Hinweise und einen lockeren Ton – so wird sie nicht nur informativ, sondern auch sympathisch.

3. **Modulübersicht:**  
   Alle wichtigen Module werden kurz vorgestellt, sodass Besucher sofort wissen, welche Funktionen hinter deinem Spiel stecken.

Diese README-Datei bietet einen vollständigen, informativen und ansprechenden Überblick, der deinem Dark Snake Game sowohl technischen als auch emotionalen Kontext verleiht. Viel Erfolg und Spaß beim Spielen – und denk daran, auch die Schlangen mögen mal einen guten Witz!
