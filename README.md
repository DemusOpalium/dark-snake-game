<!-- Coverbild oben in der README -->
<p align="center">
  <img src="Dark_Snake/assets/graphics/2222124.png" alt="Dark Snake Game Cover" width="800px">
</p>

<hr />

# Dark Snake Game

**Ein fortschrittliches Snake-Game mit Anpassungsmöglichkeiten, Bosskämpfen, Spezialeffekten und einer modernen, modularen Architektur.**

---

## Inhaltsverzeichnis

- [Konfiguration und Globale Konstanten](#konfiguration-und-globale-konstanten)
- [Aufzählungen (Enums)](#aufzählungen-enums)
- [Grafik- und Asset-Management](#grafik--und-asset-management)
- [UI-Komponenten](#ui-komponenten)
- [Menüs für Optionen, Anpassungen und Steuerungen](#men%C3%BCs-f%C3%BCr-optionen-anpassungen-und-steuerungen)
- [Kern-Spielmechanik](#kern-spielmechanik)
- [Audio](#audio)
- [Gesamtarchitektur](#gesamtarchitektur)
- [Verwendung](#verwendung)

---

## Konfiguration und Globale Konstanten

**Datei:** `config.py`

*Zweck:*  
Diese Datei legt wesentliche Spielkonstanten (wie Bildschirmgröße, Skalierungsfaktoren, Farben, Schriftgrößen und Gameplay-Konstanten) fest. Dadurch können grundlegende Parameter an einer zentralen Stelle angepasst werden, ohne den gesamten Code durchsuchen zu müssen.

*Beispiele:*  
- **FPS:** Bilder pro Sekunde  
- **Farben:** `DARK_GREY`, `WHITE`, `GREEN`, `RED`, `PURPLE`, `ORANGE`  
- **UI-Größen:** `BORDER_SIZE`, `UI_CONTAINER_HEIGHT`  
- **Spielmechanik:** `START_SPEED`, `MAX_SPEED`, `PROJECTILE_SPEED_FACTOR`

---

## Aufzählungen (Enums)

**Datei:** `enums.py`

*Zweck:*  
Definition von Aufzählungstypen für Spielzustände und Steuerungsoptionen:

- **GameState:** z. B. `INTRO`, `GAME`, `PAUSE`, `GAME_OVER`, `BOSS_FIGHT`, `SETTINGS` etc.
- **Direction:** Bewegungsrichtungen (`UP`, `DOWN`, `LEFT`, `RIGHT`)
- **ItemType:** Verschiedene Item-Arten, wie `FOOD`, `SPEED_BOOST`, `SPEED_REDUCTION` u. a.

*Warum es nützlich ist:*  
Enums ermöglichen eine saubere, konsistente Handhabung von Status- und Steuerungswerten und reduzieren die Wahrscheinlichkeit von Tippfehlern oder inkonsistenten Werten.

---

## Grafik- und Asset-Management

**Datei:** `graphics.py`

*Zweck:*  
Lädt und skaliert sämtliche Spielbilder. Dazu gehören Schlangen-, Projektil-, Boss-, Portal- und UI-Bilder.

*Wichtige Funktionen:*  
- `load_image(filename)` – Lädt ein Bild aus dem Ordner `assets/graphics` und nutzt `convert_alpha()` für transparente Darstellungen.  
- `scale_to_thumbnail(image, factor)` – Erstellt kleine Vorschaubilder für z. B. Menüs.

*Warum es nützlich ist:*  
Ein zentrales Grafikmodul erleichtert das Vorladen und Austauschen von Bildern und sorgt für ein konsistentes Erscheinungsbild.

---

## UI-Komponenten

**Datei:** `ui.py`

*Zweck:*  
Implementiert interaktive Widgets wie Buttons, Slider, Checkboxen und Dropdown-Menüs, die in den Menüs und Optionenscreens verwendet werden.

*Beispiele:*  
- **Button:** Klickelement mit optionalem Bild, Hover-Effekten und einem Callback.  
- **Slider:** Ermöglicht die Einstellung numerischer Werte über einen Schieberegler.  
- **CheckBox und Dropdown:** Dienen zur Auswahl oder zum Umschalten von Einstellungen.

*Warum es nützlich ist:*  
Die Wiederverwendbarkeit dieser UI-Komponenten vereinfacht den Aufbau moderner Menüs und erhöht die Benutzerfreundlichkeit.

---

## Menüs für Optionen, Anpassungen und Steuerungen

### Optionsmenü

**Datei:** `options_menu.py`

*Zweck:*  
Ein modernes Menü, das Einstellungen zu Gameplay und Audio sowie die Auswahl von Grafikoptionen (z. B. Schlangendesign) bietet.

### Anpassungsmenü

**Datei:** `customization.py`

*Zweck:*  
Ermöglicht es Spielern, individuelle Schlangenköpfe und -körper auszuwählen und anzupassen.

### Steuerungsmenü

**Datei:** `controls.py`

*Zweck:*  
Zeigt die Tastenzuweisungen für Einzel- und Mehrspieler an.

*Warum diese Menüs nützlich sind:*  
Durch benutzerfreundliche Menüs kann der Spieler das Spiel individuell konfigurieren und erhält einen direkten Überblick über die Steuerung und Einstellungen.

---

## Kern-Spielmechanik

**Datei:** `game.py`

*Zweck:*  
Implementiert die zentrale Logik des Spiels, von der Schlangenbewegung über Kollisionsprüfung, Item-Management bis hin zu Gegner- und Bosskämpfen.

*Wichtige Aspekte:*

- **Spielzustände:** Steuerung des Spielablaufs (Intro, Spiel, Pause, Game Over usw.).  
- **Schlangenbewegung:** Verwaltung der Schlangen (als Liste von Segmenten) im Ein- und Mehrspielermodus.  
- **Items und Power-Ups:** Zufälliges Spawnen von Gegenständen, die verschiedene Effekte auslösen können.  
- **Kollisionsdetektion:** Überprüfung von Kollisionen mittels Pygame-Methoden.  
- **Projektile, Gegner und Bosskämpfe:** Dynamisches Gameplay durch zusätzliche Herausforderungen und Spezialeffekte.

*Warum es nützlich ist:*  
Die zentrale Spiel-Logik schafft eine klare Struktur, die zur Erweiterbarkeit und Wartbarkeit des Codes beiträgt.

---

## Audio

**Datei:** `audio.py`

*Zweck:*  
Lädt und spielt Soundeffekte sowie Hintergrundmusik ab und ermöglicht die Anpassung von Lautstärke über das Optionsmenü.

*Warum es nützlich ist:*  
Gute Audioeffekte steigern die Immersion und sorgen für ein intensiveres Spielerlebnis.

---

## Gesamtarchitektur

Das Dark Snake Game nutzt eine modulare Struktur, die folgende Vorteile bietet:

- **Klar getrennte Module:** Jede Komponente (Grafik, UI, Audio, Gameplay) ist in separate Dateien ausgelagert – dies erleichtert Wartung und Erweiterung.  
- **State-Management:** Durch den Einsatz von enums (etwa in `GameState`) werden verschiedene Spielphasen sauber voneinander getrennt.  
- **Benutzerfreundliche Menüs:** Spieler können das Spiel individuell anpassen und Einstellungen bequem über die integrierten Menüs vornehmen.

---

## Verwendung

Um das Spiel zu starten:
- **Direkt aus dem Quellcode:** Starte `main.py` in deiner Python-Umgebung.
- **Build-Artifact nutzen:** Lade die über GitHub Actions erstellte EXE herunter und führe diese auf einem Windows-System aus.

---

Diese README-Datei bietet einen umfassenden Überblick über die Struktur und Funktionsweise des Dark Snake Games und sorgt gleichzeitig für einen ansprechenden visuellen Auftritt dank des Coverbildes und der klaren Gliederung.  
Falls du weitere Anpassungen wünschst, z. B. zusätzliche Farbgestaltung oder weitere Grafikelemente, kannst du HTML-Elemente (z. B. `<hr style="border: 2px solid #FF6600;">`) in Markdown einbinden, um das Design weiter zu verfeinern.
