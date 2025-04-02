Complete Snake Game – Dark Art Edition
Willkommen zum Complete Snake Game – Dark Art Edition! Dieses Snake-Spiel vereint klassische Spielmechaniken mit einem düsteren, künstlerischen Look. Entwickelt mit Pygame unter Linux Mint, bietet es nicht nur ein nostalgisches Snake-Erlebnis, sondern auch einzigartige Features wie Totenschädel-Elemente, Spezial-Level mit Portalen und Bosskämpfen, eine erweiterte, flipperartige UI und eine funktionierende Bestenliste.

Projektstruktur
Das Projekt folgt einer modularen Architektur, die eine einfache Erweiterung und Wartung ermöglicht. Die wichtigsten Bestandteile sind:

bash
Kopieren
complete-snake-game/
├── main.py                # Einstiegspunkt und Spiel-Loop
├── config.py              # Konfiguration, Konstanten und Farbdefinitionen
├── assets/
│   ├── sounds/            # Sounddateien (z. B. eat.wav, powerup.wav, boss.wav, gameover.wav, dice.wav)
│   └── graphics/          # Grafiken, Sprites, Animationen und Icons
├── modules/
│   ├── game.py            # Zentrale Spiel-Logik (Level, Quests, Gegner, Spezial-Level)
│   ├── ui.py              # UI-Komponenten (Buttons, Slider, HUD)
│   ├── graphics.py        # Grafik-Rendering und Spriteladen
│   ├── controls.py        # Steuerungslogik (Tastatur, Touch, ggf. Gamepad)
│   └── audio.py           # Soundmanagement
└── leaderboard.txt        # Speicherung der Bestenliste

Installation & Anforderungen
Python 3.12 (oder höher)

Pygame – installiere es über:

bash
Kopieren
python3 -m pip install pygame
Es wird empfohlen, Linux Mint zu verwenden. Für den Android-Port können zusätzlich pygame_sdl2 oder Kivy/Buildozer zum Einsatz kommen.

Um das Spiel zu starten, navigiere in den Projektordner und führe aus:

bash
Kopieren
cd complete-snake-game
python3 main.py
Features
Grafikstil: Dark Art
Das Spiel besticht durch einen düsteren, kontrastreichen Look – Totenschädel und dunkle, atmosphärische Grafiken verleihen dem Snake-Klassiker eine ganz neue Dimension.

Spezial-Level
Zusätzliche Portale öffnen zeitlich begrenzte Level, in denen besondere Herausforderungen warten. Bosskämpfe und vermehrter Loot sorgen für zusätzlichen Nervenkitzel.

Erweiterte UI
Eine extra Anzeige im oberen Bereich (ähnlich einem Flipper) präsentiert Effekte, Animationen und Spezialereignisse und macht das Spielerlebnis dynamischer.

Bestenliste
Nach Spielende kann der Spieler seinen Namen eingeben. Die Bestenliste verfügt über eine einfache Navigation (inklusive „Zurück“-Button).

Steuerung
Das Spiel unterstützt sowohl Tastatur (WASD und Pfeiltasten) als auch Touch-Eingaben – ideal auch für mobile Geräte.

Modulare Architektur
Die klare Trennung der Funktionalitäten ermöglicht es, dass unterschiedliche Entwicklerbereiche unabhängig voneinander erweitert werden können:

main.py – Einstiegspunkt und Hauptspiel-Loop.
config.py – Alle Konstanten, Variablen und Farbdefinitionen.
modules/audio.py – Laden und Abspielen der Sounddateien.
modules/controls.py – Steuerungslogik für Tastatur, Touch und Gamepad.
modules/graphics.py & modules/ui.py – Rendering der Grafiken, Sprites, Animationen sowie die UI-Komponenten.
modules/game.py – Zentrale Spiel-Logik: Level, Quests, Gegner und Spezial-Level.
Entwicklung & Erweiterungsmöglichkeiten
Dank der modularen Struktur kannst du den Code leicht in einzelne Bereiche aufteilen und weiterentwickeln – sei es durch zusätzliche Level, neue Gegner, verbesserte Grafiken oder eine erweiterte Benutzeroberfläche.

Lizenz
Dieses Projekt steht unter der MIT-Lizenz. Details dazu findest du in der Datei LICENSE.

Hinweise
Sounddateien:
Stelle sicher, dass alle benötigten Sounddateien im Ordner assets/sounds/ vorhanden sind. Bei fehlenden Dateien kannst du Dummy-WAV-Dateien verwenden.

Grafiken:
Platziere deine Grafiken und Sprites (z. B. Totenschädel, Portale) im Ordner assets/graphics/ und passe ggf. die Pfade in den entsprechenden Modulen an.

Android-Port:
Für den Port auf Android schaue dir pygame_sdl2 oder Kivy mit Buildozer an.

Viel Spaß beim Spielen und Weiterentwickeln des Complete Snake Game – Dark Art Edition!
