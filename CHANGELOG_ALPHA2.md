# Changelog – Alpha 2

## Stabilität
- Start aus dem Repository-Hauptordner und aus einem PyInstaller-Bundle unterstützt.
- Fest codierter Linux-Musikpfad entfernt; fehlendes Audiogerät ist nicht fatal.
- Laufzeitdaten für Belegung außerhalb gebündelter Ressourcen gespeichert.
- Der Ablauf eines Portal-Effekts stellt ohne Editor-Karte sicher den normalen
  Hintergrund wieder her; vorhandene Editor-Karten werden weiterhin neu aufgebaut.
- Ein fehlertolerantes, rotierendes Laufzeitprotokoll und automatische Crash-Reports
  mit Stacktrace, Spielstatus, Objektanzahlen und letzten Ereignissen ergänzt.

## Eingabe und Mehrspieler
- WASD plus Leertaste/Enter für Spieler 1, Pfeile plus Enter/Plus für Spieler 2.
- Tastaturstart im Hauptmenü und grundlegende Joystick-Unterstützung ergänzt.
- Steuerungsbelegung kann erfasst, gespeichert und zurückgesetzt werden.
- Inaktive Snake-Listen und transiente Projektilzustände werden beim Neustart geleert.

## Qualität
- UTF-8-Texte wie `HAUPTMENÜ`, `ZURÜCK` und `ü` geprüft.
- CI und Tests lehnen nicht aufgelöste Git-Konfliktmarkierungen in getrackten
  Quell-, Konfigurations- und Dokumentationsdateien ausdrücklich ab.
- Headless-Smoke-Suite für Menü, Zeichnen, beide Spielmodi und Gamepad-Ereignisse ergänzt.
- CI kompiliert Python-Quellen und führt pytest vor dem Windows-EXE-Build aus.
- Windows-CI meldet den stabilen Required Check `main`; ein CodeQL-Workflow führt
  Python-Code-Scanning für Pull Requests, `main` und wöchentlich aus.

## Admin-Menü
- Neun stabile Sofortaktionen für Feuerball, Bosskampf, Heilung, Multi-Schuss,
  Hitboxen, Bolbu-Item, Explosion sowie Schadens- und Zufallszonen umgesetzt.
- Titel, deutsche Icon-Namen, Mouseover-Beschreibungen und sichtbare Status- bzw.
  abgefangene Fehlermeldungen ergänzt.
- `TAB` und `ESC` schließen das Admin-Menü; Admin-Menü und Level-Editor pausieren
  die Partie und erhalten Eingaben exklusiv.
- Ein- und Zweispieleraktionen sowie Werkzeug-Pause durch Headless-Tests abgedeckt.

## Bekannte Einschränkungen
- Der Level-Editor und die allgemeine UI-Skalierung bleiben Gegenstand eigener
  Folgearbeiten; diese Änderung implementiert sie bewusst nicht neu.
- Ein unsignierter privater Windows-Build kann weiterhin eine SmartScreen-Warnung zeigen.
