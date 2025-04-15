<!-- Coverbild oben in der README -->
<p align="center">
  <img src="Dark_Snake/assets/graphics/2222124.png" alt="Dark Snake Game Cover" width="800px">
</p>

<hr />

# Dark Snake Game

**Ein fortschrittliches Snake-Game mit Anpassungsmöglichkeiten, Bosskämpfen, Spezialeffekten und einem modernen, modularen Aufbau.**

---

## Inhaltsverzeichnis

- [Konfiguration und Globale Konstanten](#konfiguration-und-globale-konstanten)
- [Aufzählungen (Enums)](#aufzählungen-enums)
- [Grafik- und Asset-Management](#grafik--und-asset-management)
- [UI-Komponenten](#ui-komponenten)
- [Menüs (Optionen, Anpassung, Steuerung)](#menüs-optionen-anpassung-steuerung)
- [Kern-Spielmechanik](#kern-spielmechanik)
- [Audio](#audio)
- [Gesamtarchitektur](#gesamtarchitektur)
- [Verwendung](#verwendung)

---

## Konfiguration und Globale Konstanten

**Datei:** `config.py`

*Zweck:*  
Diese Datei legt die wesentlichen Konstanten für das Spiel fest – von der Bildschirmanzeige über Skalierungsfaktoren bis hin zu grundlegenden Parametern für Gameplay, Farben, UI-Größen und Schriftarten.  
**Beispiele:**

- **FPS** – Bilder pro Sekunde
- **Farben:** `DARK_GREY`, `WHITE`, `GREEN`, `RED`, `PURPLE`, `ORANGE`
- **UI-Größen:** `BORDER_SIZE`, `UI_CONTAINER_HEIGHT`
- **Schriftgrößen:** `FONT_SMALL`, `FONT_MEDIUM`, `FONT_LARGE`, `FONT_TITLE`
- **Spielmechanik:** `START_SPEED`, `MAX_SPEED`, `PROJECTILE_SPEED_FACTOR`
- **Leaderboard:** Dateiname für die Bestenliste

*Warum es nützlich ist:*  
Die zentrale Ablage dieser Werte ermöglicht es, das Erscheinungsbild und die Grundmechanik des Spiels schnell anzupassen, ohne den gesamten Code durchsuchen zu müssen.

---

## Aufzählungen (Enums)

**Datei:** `enums.py`

*Zweck:*  
Definition von Aufzählungstypen (Enums) für den Spielstatus und andere Werte, z. B.:

- **GameState:** Zustände wie `INTRO`, `GAME`, `PAUSE`, `GAME_OVER`, `BOSS_FIGHT`, `SETTINGS`, `LEADERBOARD`, `CONTROLS`, `CUSTOMIZATION`
- **Direction:** Bewegungsrichtungen (`UP`, `DOWN`, `LEFT`, `RIGHT`)
- **ItemType:** Verschiedene Gegenstände wie `FOOD`, `SPEED_BOOST`, `SPEED_REDUCTION`, usw.

*Warum es nützlich ist:*  
Enums sorgen für eine konsistente und leicht verständliche Codebasis, reduzieren Fehler und erleichtern die Steuerung des Spielflusses.

---

## Grafik- und Asset-Management

**Datei:** `graphics.py`

*Zweck:*  
Lädt und skaliert sämtliche Spielbilder.  

**Schlüssel-Funktionen:**

- `load_image(filename)` – Lädt Bilder aus dem Ordner `assets/graphics` unter Anwendung von `convert_alpha()` für Transparenz.
- `scale_to_thumbnail(image, factor)` – Erstellt kleinere Vorschaubilder, z. B. für Menüs.

**Wichtige Assets:**

- Snake-Grafiken (Kopf und Körper)
- Projektilbilder
- Titel- und Bossbilder
- Portal-Bilder
- Item-Bilder (über ein Dictionary zugeordnet)
- UI-Elemente (Buttons u. Ä.)

*Warum es nützlich ist:*  
Ein zentrales Grafikmodul erleichtert das Vorladen und Austauschen von Bildern, falls das visuelle Design aktualisiert werden soll.

---

## UI-Komponenten

**Datei:** `ui.py`

*Zweck:*  
Implementiert interaktive Elemente wie Buttons, Slider, Checkboxen und Dropdown-Menüs.  
**Beispielklassen:**

- **Button:** Klickelement mit optionalem Bild, Hover-Effekten und Rückruffunktion.
- **Slider:** Regler zur Einstellung numerischer Werte.
- **CheckBox:** Einfache Umschaltfunktion.
- **Dropdown:** Ausklappbare Listen zur Auswahl (z. B. für Musikauswahl).

*Warum es nützlich ist:*  
Diese Widgets trennen die Eingabelogik von der Spiel-Logik und sorgen so für eine saubere, wiederverwendbare Codebasis.

---

## Menüs: Optionen, Anpassung und Steuerung

### Optionsmenü

**Datei:** `options_menu.py`

*Zweck:*  
Ein modernes Menü, das Gameplay- und Audioeinstellungen sowie ein Grafik-Inventar für Schlangendesigns anzeigt.

**Features:**

- Einstellungen für Gameplay (Geschwindigkeit, Schwierigkeitsgrad, Spawn-Rate)
- Bildvorschau und Auswahl (Thumbnail-Ansicht)
- Globale Steuerungsbuttons oben im Menü

### Anpassungsmenü

**Datei:** `customization.py`

*Zweck:*  
Ermöglicht es den Spielern, individuelle Schlangenköpfe und -körper auszuwählen.  
**Features:**

- Vorher definierte Optionen mit Thumbnails
- Dynamisches Laden weiterer Bilder aus Ordnern
- Rückkehr-Möglichkeit ins vorherige Menü

### Steuerungsmenü

**Datei:** `controls.py`

*Zweck:*  
Zeigt Tastenzuweisungen für Einzel- und Mehrspieler-Modi an und beinhaltet eine Rück-Taste.

*Warum diese Menüs nützlich sind:*  
Sie verbessern die Benutzerfreundlichkeit, indem sie den Spielern erlauben, das Spiel individuell anzupassen und sich schnell mit den Steuerungen vertraut zu machen.

---

## Kern-Spielmechanik

**Datei:** `game.py`

*Zweck:*  
Zentrale Spiel-Logik, die Spielzustände (State Management), Schlangenbewegung, Kollisionsprüfung, Power-Ups, Gegner und Bosskämpfe koordiniert.

**Wichtige Aspekte:**

- **Spielzustände:** Wechsel zwischen Intro, Spiel, Pause, Game Over, Boss-Fight, etc.
- **Schlangen-Handling:** Verwaltung der Schlangen (als Liste von Segmenten) für ein- und Mehrspielermodus.
- **Item-Handling:** Zufälliges Spawnen von Items und deren Auswirkungen auf das Spiel.
- **Gegner-Logik:** Dynamisches Spawnen und Aktualisieren von Gegnern und Bossen.
- **AoE-Zonen:** Temporäre Flächen, die bestimmte Effekte (Schaden, Heilung, Verlangsamung) auslösen.
- **Collision Detection:** Einfache Kollisionsabfrage mittels Pygame-Rect
- **Punktesystem und Level:** Zählt Punkte und Erfahrung, löst Level-Aufstiege und Bosskämpfe aus.
- **UI und HUD:** Anzeige von Lebensbalken, Punkten, und Achievements.

*Warum es nützlich ist:*  
Die zentrale Spiel-Logik bündelt alle Mechanismen in einer kohärenten Struktur, was die Erweiterbarkeit und Wartbarkeit des Projekts verbessert.

---

## Audio

**Datei:** `audio.py`

*Zweck:*  
Laden und Abspielen von Soundeffekten und Hintergrundmusik.  
**Features:**

- Verwaltung der Soundeffekte (z. B. Essen, Schaden, Boss-Ereignisse)
- Anpassung der Lautstärke über das Optionsmenü

*Warum es nützlich ist:*  
Gute Audioeffekte erhöhen die Immersion und bieten dem Spieler ein vollständigeres Erlebnis.

---

## Gesamtarchitektur

Das "Dark Snake Game" ist ein komplexes Pygame-Projekt, das eine klare, modulare Struktur aufweist:

- **Modulare Struktur:**  
  Getrennte Module für Konfiguration, Grafik, UI, Audio, Gameplay und Menüs.
  
- **Zustandsverwaltung:**  
  Ein sauber implementiertes State-Management sorgt für reibungslose Übergänge zwischen verschiedenen Spielmodi.
  
- **Erweiterbarkeit:**  
  Durch die Trennung in logische Module und Klassen können neue Features (z. B. zusätzliche Power-Ups oder Gegnerarten) einfach integriert werden.
  
- **Anpassung:**  
  Die Menüs für Options- und Anpassungen bieten dem Spieler umfangreiche Individualisierungsmöglichkeiten.

---

## Verwendung

Um das Spiel zu spielen, lade die neueste Build-Artifact (EXE) herunter oder führe das Spiel direkt aus dem Quellcode aus.  
Weitere Informationen und Anleitungen findest du in den folgenden Dateien:

- **`config.py`** – Spielkonfiguration
- **`enums.py`** – Definition von Aufzählungstypen
- **`graphics.py`** – Grafikmanagement
- **`ui.py`** – Benutzeroberfläche
- **`game.py`** – Hauptspiel-Logik

---

> **Hinweis:**  
> Für weitere Anpassungen (z. B. Farben, Trennlinien, Schriften) kannst du auch HTML in Markdown nutzen.  
> Beispiel:
> ```html
> <hr style="border: 2px solid #FF6600;">
> ```
> Mit solchen Mitteln kannst du die README-Datei weiter individualisieren.

---

Ich hoffe, diese Version hilft dir dabei, dein Spiel ansprechend zu präsentieren! Bei weiteren Fragen stehe ich dir gern zur Verfügung.
