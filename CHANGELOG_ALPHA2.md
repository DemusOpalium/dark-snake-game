# Changelog – Alpha 2

## Stabilität
- Start aus dem Repository-Hauptordner und aus einem PyInstaller-Bundle unterstützt.
- Fest codierter Linux-Musikpfad entfernt; fehlendes Audiogerät ist nicht fatal.
- Laufzeitdaten für Belegung außerhalb gebündelter Ressourcen gespeichert.

## Eingabe und Mehrspieler
- WASD plus Leertaste/Enter für Spieler 1, Pfeile plus Enter/Plus für Spieler 2.
- Tastaturstart im Hauptmenü und grundlegende Joystick-Unterstützung ergänzt.
- Steuerungsbelegung kann erfasst, gespeichert und zurückgesetzt werden.
- Inaktive Snake-Listen und transiente Projektilzustände werden beim Neustart geleert.

## Qualität
- UTF-8-Texte wie `HAUPTMENÜ`, `ZURÜCK` und `ü` geprüft.
- Headless-Smoke-Suite für Menü, Zeichnen, beide Spielmodi und Gamepad-Ereignisse ergänzt.
- CI kompiliert Python-Quellen und führt pytest vor dem Windows-EXE-Build aus.
- Windows-CI meldet den stabilen Required Check `main`; ein CodeQL-Workflow führt
  Python-Code-Scanning für Pull Requests, `main` und wöchentlich aus.
