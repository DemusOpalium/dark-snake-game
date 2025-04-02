# Complete Snake Game – Dark Art Edition

Welcome to the Complete Snake Game – Dark Art Edition!  
Willkommen beim Complete Snake Game – Dark Art Edition!

---

## Description / Beschreibung

**English:**  
This Snake game combines classic gameplay with a dark, artistic look. Developed with Pygame on Linux, it offers not only a nostalgic snake experience but also unique features such as skull-themed graphics, special levels with portals and boss battles, an enhanced, pinball-like UI, and a functional leaderboard.  
  
**Deutsch:**  
Dieses Snake-Spiel vereint klassische Spielmechaniken mit einem düsteren, künstlerischen Look. Entwickelt mit Pygame unter Linux, bietet es nicht nur ein nostalgisches Snake-Erlebnis, sondern auch einzigartige Features wie Totenschädel-Grafiken, Spezial-Level mit Portalen und Bosskämpfen, eine erweiterte, flipperartige Benutzeroberfläche und eine funktionierende Bestenliste.

---

## Project Structure / Projektstruktur

Dark_Snake/ ├── main.py # Entry point and game loop / Einstiegspunkt und Spiel-Loop ├── config.py # Configuration, constants, and color definitions / Konfiguration, Konstanten und Farbdefinitionen ├── assets/ # All external resources / Alle externen Ressourcen │ ├── graphics/ # Graphics, sprites, animations, and icons / Grafiken, Sprites, Animationen und Icons │ │ ├── Boss001/ # Animation frames for Boss 001 │ │ ├── Boss002/ # Animation frames for Boss 002 │ │ ├── Boss003/ # Animation frames for Boss 003 │ │ └── ... # Additional images for snake head, body, items, portals, etc. │ └── sounds/ # Sound files and music / Sounddateien und Musik │ ├── boss.wav │ ├── dice.wav │ ├── gameover.wav │ ├── eat.wav │ ├── gegner.wav │ ├── powerup.wav │ └── music/ # Music files (e.g., DarkSnakeMusicIndi1.mp3, DarkSnakeMusicIndi2.mp3, etc.) ├── modules/ # Modular game code / Modulare Spiel-Logik │ ├── audio.py # Audio functions / Soundverwaltung │ ├── customization.py # Customization options / Anpassungsfunktionen │ ├── enums.py # Enumerations (game states, directions, item types, etc.) / Enumerationen │ ├── graphics.py # Rendering and sprite handling / Grafik-Rendering und Spriteladen │ ├── ui.py # UI components (buttons, sliders, HUD) / Benutzeroberfläche │ ├── controls.py # Input handling (keyboard, touch, etc.) / Steuerungslogik │ ├── enemies.py # Enemy classes and behavior / Gegner-Logik │ └── game.py # Core game logic (levels, collisions, upgrades, etc.) / Zentrale Spiel-Logik ├── leaderboard.txt # Leaderboard data / Bestenliste ├── settings.txt # User settings / Benutzereinstellungen ├── GameStarter.desktop # Desktop file for starting the game under Linux / Startverknüpfung für Linux ├── README.md # Project documentation / Projektdokumentation └── (Other files may include licenses, etc.)


---

## Installation & Requirements / Installation & Anforderungen

**English:**  
- **Requirements:** Python 3.12 or higher, Pygame, and other dependencies.  
- Install Pygame via:  
  ```bash
  python3 -m pip install pygame

    To run the game, navigate to the project directory and execute:

    cd Dark_Snake
    python3 main.py

Deutsch:

    Voraussetzungen: Python 3.12 (oder höher), Pygame und weitere Abhängigkeiten.

    Installiere Pygame über:

python3 -m pip install pygame

Um das Spiel zu starten, wechsle in den Projektordner und führe aus:

    cd Dark_Snake
    python3 main.py

Features / Features

English:

    Dark Art Style:
    The game features a dark, high-contrast look with skull graphics and atmospheric designs, giving a new twist to the classic snake game.

    Special Levels:
    Timed portal levels, boss battles, and extra loot provide additional challenges and excitement.

    Enhanced UI:
    A dynamic, pinball-inspired user interface displays effects, animations, and special events during gameplay.

    Leaderboard:
    A simple and intuitive leaderboard allows players to save and view high scores.

    Controls:
    Supports keyboard input (WASD and arrow keys) and touch controls for mobile devices.

Deutsch:

    Dark Art Stil:
    Das Spiel besticht durch einen düsteren, kontrastreichen Look mit Totenschädel-Grafiken und atmosphärischen Designs, der dem klassischen Snake-Spiel eine neue Dimension verleiht.

    Spezial-Level:
    Zeitlich begrenzte Portale, Bosskämpfe und zusätzlicher Loot sorgen für zusätzliche Herausforderungen und Nervenkitzel.

    Erweiterte UI:
    Eine dynamische, flipperartige Benutzeroberfläche zeigt Effekte, Animationen und Spezialereignisse während des Spiels an.

    Bestenliste:
    Eine einfache und intuitive Bestenliste ermöglicht es den Spielern, Highscores zu speichern und anzuzeigen.

    Steuerung:
    Unterstützt Tastatureingaben (WASD und Pfeiltasten) sowie Touch-Steuerung – ideal auch für mobile Geräte.

Development & Contributions / Entwicklung & Beiträge

English:
This project is open source and welcomes contributions!
Feel free to fork the repository, submit pull requests, or open issues for any bugs or feature requests.
All contributions will be acknowledged.

Deutsch:
Dieses Projekt ist Open Source und Beiträge sind willkommen!
Du kannst das Repository forken, Pull Requests einreichen oder Issues für Fehler oder neue Features öffnen.
Alle Beiträge werden gewürdigt.
License / Lizenz

This project is licensed under the MIT License.
Dieses Projekt steht unter der MIT-Lizenz.
(See the LICENSE file for details.)
Notes / Hinweise

    Resources:
    Ensure that all required resource files (graphics and sounds) remain in their respective folders as the game loads them during runtime.

    Platform:
    The game has been developed and tested on Linux Mint with Python and Pygame.

    Future Enhancements:
    Ideas for future updates include additional levels, new enemy types, improved UI effects, and potential mobile adaptations.
