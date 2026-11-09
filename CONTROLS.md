# Steuerung

| Aktion | Standard |
| --- | --- |
| Spieler 1 bewegen | W, A, S, D |
| Spieler 1 feuern | Leertaste. Im Einzelspiel auch Enter. |
| Spieler 2 bewegen | Pfeiltasten |
| Spieler 2 feuern | Enter, Plus oder Ziffernblock-Plus |
| Pause | P |
| Spezialeffekt | Ü |

Für Spielgeräte sind standardmäßig die ersten beiden Achsen, das erste D-Pad
und die erste Taste belegt. Ein erstmals erkanntes Gerät steuert Spieler 1,
wenn gerade kein anderes Gerät verbunden ist. Weitere neue Geräte steuern
zunächst Spieler 2. Im Menü kannst du mehrere Geräte demselben Spieler zuweisen.

## Belegungen ändern

Öffne **Steuerung** im Hauptmenü. Wähle **Spieler 1**, **Spieler 2** oder
**Allgemein** für Pause und Spezialeffekt. Wähle daneben die Tastatur oder
ein Spielgerät. Die Liste zeigt die Belegungen, die vorhandenen Alternativen
und mögliche Konflikte.

1. Wähle die Aktion und dann **Zuweisen**. Drücke die neue Taste oder bewege
   die gewünschte Achse beziehungsweise D-Pad-Richtung. Mit **Esc** brichst du
   die Zuweisung ab.
2. **Entfernen** leert die Belegung für die gewählte Tastatur oder das
   gewählte Spielgerät. Das Ersetzen oder Entfernen einer Standard-Feuertaste
   ersetzt oder entfernt auch ihre Alternativen.
3. Im **Eingabetest** zeigt das Menü die erkannte Quelle und Aktion an.
   **Esc** beendet den Test.
4. **Speichern** übernimmt die Belegungen dauerhaft. **Standard** stellt die
   Vorgaben wieder her. Speichere anschließend, wenn du sie behalten möchtest.

Ohne Maus wählst du die Spielergruppe mit **Tab**, das Gerät mit **Links/Rechts**
und die Aktion mit **Hoch/Runter**. **Enter** beginnt die Zuweisung, **Entf**
entfernt die Auswahl, **T** öffnet den Eingabetest, **S** speichert und **R**
stellt den Standard wieder her. **Esc** führt zurück. Esc, Tab und F2 bleiben
für Navigation und Entwicklerwerkzeuge reserviert.

## Gamepad und HOTAS

Mit **Spieler wechseln** ordnest du das gewählte Gerät P1 oder P2 zu. Ein
T.16000M und ein TWCS können zum Beispiel beide P1 steuern. Weise jeder
gewünschten Achse ihre positive und negative Richtung getrennt zu. Stelle bei
Bedarf die **Totzone** des Geräts ein. Für die nächste Auslösung muss die
Achse erst zurück in ihren Neutralbereich.

Die Belegungen und Spielerzuordnungen liegen in
`.dark-snake/controls.json` im Benutzerprofil. Eindeutige bisherige Tasten
und Buttonnummern werden aus älteren Dateien übernommen. Geräteprofile
werden beim Wiederverbinden anhand ihrer von SDL gemeldeten Modellkennung
zugeordnet. Wenn zwei baugleiche Geräte dieselbe Kennung melden, kann die
Anschlussreihenfolge das gewählte Profil beeinflussen. Prüfe in diesem Fall
die Quelle im Eingabetest und wähle **Profil wechseln**. Die aktuelle
SDL-Instanznummer ist nur für die Erkennung im laufenden Spiel sichtbar.

## Testfolge unter Windows

1. **Tastatur:** In 1P mit WASD lenken, mit Leertaste und Enter feuern.
   In 2P beide Spieler unabhängig lenken und prüfen, dass Enter nur P2 feuern
   lässt. Pause und Ü testen. Eine Taste zuweisen, den Vorgang mit Esc
   abbrechen und nach einem Neustart die gespeicherte Belegung prüfen.
2. **DualSense:** Eine Taste, je eine positive und negative Achsrichtung und
   das D-Pad zuweisen. Eine ausgelenkte Achse halten, anschließend zentrieren
   und erneut auslenken. Abziehen, wieder anschließen und das Profil prüfen.
3. **T.16000M und TWCS:** Beide Geräte P1 zuweisen. Zum Beispiel über den Stick
   lenken und mit einer TWCS-Taste feuern. Den TWCS danach P2 zuweisen und
   im Zweispielermodus prüfen, dass er P1 nicht auslöst.
4. **Zwei baugleiche Geräte:** Zuordnung im Eingabetest prüfen, Geräte in
   anderer Reihenfolge verbinden und bei Bedarf mit **Profil wechseln** korrigieren.

## Entwicklerwerkzeuge

- **Tab** öffnet das AdminPanel, **F2** den Level-Editor.
- **R / T / Z / U / I / O** rufen im Spiel die vorhandenen Debug-Effekte auf.
