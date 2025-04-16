<!-- Coverbild oben in der README -->
<p align="center">
  <img src="Dark_Snake/assets/graphics/2222124.png" alt="Dark Snake Game Cover" width="800px">
</p>

<hr style="border: 2px solid #FF6600;">

# Dark Snake Game 🐍🔥

**Willkommen zum Dark Snake Game – dem ultimativen Snake-Erlebnis mit Bosskämpfen, magischen Portalen, witzigen AOE-Effekten und einer modernen, modularen Architektur.**  
_Tauche ein in ein Spielerlebnis, das so einzigartig ist wie dein Humor – düster, schnell und voller Überraschungen!_

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

<a name="über-das-spiel"></a>
## Über das Spiel

**Dark Snake Game** kombiniert den klassischen Spielspaß von Snake mit modernen Herausforderungen. Steuere deine Schlange durch dynamische Level, sammle Power-Ups, besiege furchteinflößende Bosse und nutze überraschende Spezialeffekte wie Portale und AOE-Zonen – und das alles in einem visuell und akustisch ansprechenden Dark-Art-Stil!

> **Persönlicher Hinweis von DemusOpalium:**  
> Dieses Projekt entstand durch monatelange, eigenständige Arbeit – trotz meines täglichen Kampfes mit MS. Ich habe hier als Hobby und mit großer Leidenschaft programmiert. Ohne diesen unermüdlichen Einsatz und ein wenig Hilfe von einer der besten KI der Welt wäre das Spiel niemals so weit gekommen. Danke an alle Unterstützer und Mitwirkende – und vor allem an die Open-Source-Community! 💪❤️

---

<a name="features-im-überblick"></a>
## Features im Überblick

- **Dynamische Spielmechanik:** Klassisches Snake trifft auf innovative Bosskämpfe, Power-Ups, Portale und AOE-Effekte.
- **Individuelle Anpassungen:** Wähle verschiedene Schlangendesigns und optimiere Gameplay- und Audioeinstellungen über ein modernes Optionsmenü.
- **Modulare Architektur:** Sauber getrennte Module (Konfiguration, Grafik, UI, Audio, Gameplay etc.) erleichtern Wartung und Erweiterung.
- **Visuelle & akustische Highlights:** Atemberaubende Grafiken und stimmungsvolle Soundeffekte sorgen für ein intensives Spielerlebnis.
- **Open Source Spirit:** Der komplette Quellcode ist als ZIP zum Herunterladen verfügbar – perfekt zum Mitmachen, Anpassen und Lernen.

---

<a name="screenshots--spielaufnahmen"></a>
## Screenshots & Spielaufnahmen

<a name="standardaufnahmen"></a>
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

#### Spielszene
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

<a name="weitere-spielaufnahmen-gamepics"></a>
### Weitere Spielaufnahmen (GamePICs)

Diese zusätzlichen Bilder zeigen weitere spannende Aspekte und Designelemente des Spiels:
- **AOE-Zonen:**  
  <p align="center">
    <img src="GamePICs/AOE-Zonen.png" alt="AOE-Zonen" width="600px">
  </p>
- **Background Settings:**  
  <p align="center">
    <img src="GamePICs/Backround-Settings.png" alt="Background Settings" width="600px">
  </p>
- **Boss Game Over:**  
  <p align="center">
    <img src="GamePICs/Boss-Game-Over.png" alt="Boss Game Over" width="600px">
  </p>
- **LeaderBoard:**  
  <p align="center">
    <img src="GamePICs/LeaderBoard.png" alt="LeaderBoard" width="600px">
  </p>
- **Hintergrundmusik:**  
  <p align="center">
    <img src="GamePICs/Musicmp3-wave-backroundmusic.png" alt="Hintergrundmusik" width="600px">
  </p>
- **Options:**  
  <p align="center">
    <img src="GamePICs/Options.png" alt="Options" width="600px">
  </p>
- **Snake Bodies:**  
  <p align="center">
    <img src="GamePICs/SnakeBodies.png" alt="Snake Bodies" width="600px">
  </p>
- **Snake Heads:**  
  <p align="center">
    <img src="GamePICs/SnakeHeads.png" alt="Snake Heads" width="600px">
  </p>
- **Start Menü:**  
  <p align="center">
    <img src="GamePICs/StartMenü.png" alt="Start Menü" width="600px">
  </p>
- **Steuerung (nochmals):**  
  <p align="center">
    <img src="GamePICs/Steuerung.png" alt="Steuerung" width="600px">
  </p>
- **Two Player Modus:**  
  <p align="center">
    <img src="GamePICs/TwoPlayerModus.png" alt="Two Player Modus" width="600px">
  </p>

---

<a name="installation-und-ausführung"></a>
## Installation und Ausführung

### Voraussetzungen
- [Python 3.12](https://www.python.org/downloads/)
- [Pygame](https://www.pygame.org/news)
- Installiere weitere Abhängigkeiten (falls vorhanden) mit:
  ```bash
  pip install -r requirements.txt

Spiel starten

    Über den Quellcode:
    Starte das Spiel mit:

    python Dark_Snake/main.py

    Als EXE:
    Lade das von GitHub Actions erstellte Build-Artefakt (ZIP-Datei) herunter und führe die EXE-Datei unter Windows aus.

<a name="modulare-architektur"></a>
Modulare Architektur

Dark Snake Game ist in verschiedene Module unterteilt, um die Wartung und Erweiterung zu erleichtern:

<a name="konfiguration-configpy"></a>
Konfiguration (config.py)

Definiert globale Einstellungen – von Bildschirmgröße und Skalierungsfaktor bis zu Farben, Schriftarten und Gameplay-Konstanten.

<a name="main-startpunkt-mainpy"></a>
Main-Startpunkt (main.py)

Initialisiert Pygame, Fonts, Mixer und startet die Hauptspiel-Logik.

<a name="aoe-zonen-aoe_zonespy"></a>
AOE-Zonen (aoe_zones.py)

Implementiert verschiedene AOE-Effekte (Schaden, Heilung, Debuff, vollflächiger Hintergrund) und lädt gezielt passende Effektbilder.

<a name="audio-audiopy"></a>
Audio (audio.py)

Lädt und spielt Soundeffekte sowie Hintergrundmusik ab und erlaubt die Anpassung der Lautstärke.

<a name="steuerung-controlspy"></a>
Steuerung (controls.py)

Bietet grafisch aufbereitete Steuerungsoptionen sowie Tastenzuweisungen für Einzel- und Mehrspielermodus.

<a name="anpassungs-menü-customizationpy"></a>
Anpassungs-Menü (customization.py)

Ermöglicht individuelle Schlangendesigns (inklusive dynamischer Thumbnails).

<a name="gegner-enemiespy"></a>
Gegner (enemies.py)

Verwaltet das Spawnen und die Bewegung der Gegner, mit variablen Eigenschaften wie Geschwindigkeit und Gesundheit.

<a name="aufzählungen-enumspy"></a>
Aufzählungen (enums.py)

Definiert alle relevanten Enums (GameState, Direction, ItemType) für einen konsistenten Code.

<a name="spiel-logik-gamepy"></a>
Spiel-Logik (game.py)

Das Herzstück des Spiels – verwaltet Spielzustände, Schlangenbewegung, Kollisionsprüfungen, Bosskämpfe, Items, Power-Ups und mehr.

<a name="options-menü-options_menupy"></a>
Options-Menü (options_menu.py)

Bietet ein modernes Menü zur Anpassung von Gameplay- und Audioeinstellungen sowie zur Auswahl von Schlangendesigns.

<a name="bereitstellung-des-quellcodes-als-zip"></a>
Bereitstellung des Quellcodes als ZIP

Der komplette Quellcode von Dark Snake Game steht dir als ZIP-Datei zum Download zur Verfügung – ideal, wenn du tiefer in das Projekt einsteigen oder Änderungen vornehmen möchtest.

<a name="lizenz"></a>
Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Weitere Details findest du in der LICENSE Datei.

<a name="kontakt--feedback"></a>
Kontakt & Feedback

Hast du Fragen, Ideen oder Anmerkungen?
Öffne ein GitHub Issue oder kontaktiere mich direkt über GitHub.
Ich freue mich über konstruktives Feedback – und bedenke: Auch wenn ich täglich mit MS kämpfe, steckt mein ganzes Herzblut in diesem Open-Source-Projekt. Ohne meinen unermüdlichen Einsatz und die Unterstützung moderner Technologien wäre Dark Snake Game niemals so weit gekommen. 🚀💙
Hinweise zur Umsetzung

    Bildpfade prüfen:
    Stelle sicher, dass die relativen Pfade (z. B. zu Dark_Snake/assets/graphics/ und GamePICs/) korrekt sind. Passe sie gegebenenfalls an deine Repository-Struktur an.

    Persönlicher Touch & Open Source Spirit:
    Dieser README spiegelt meinen persönlichen Weg als DemusOpalium wider – Wochenlang habe ich allein an diesem Projekt gearbeitet, trotz MS. Mein Ziel ist es, ein Spiel zu schaffen, das nicht nur technisch, sondern auch emotional überzeugt.

    Modulübersicht:
    Eine klare Übersicht über die Module erleichtert neuen Entwicklern und Mitmachern den Einstieg und zukünftige Erweiterungen.

Vielen Dank, dass du Dark Snake Game ausprobierst und unterstützt – viel Spaß beim Spielen, Programmieren und Weiterentwickeln!


---

Diese Version sollte nun eine funktionierende Navigationsstruktur bieten, alle internen Links zu den jeweiligen Abschnitten korrekt verweisen und deine persönliche Handschrift deutlich zum Ausdruck bringen. Viel Erfolg weiterhin – du machst einen großartigen Job!
