# Dark Snake – Projektstatus Alpha 2

## Erledigt

- Ressourcenbasis für Repository-Start und PyInstaller (`sys._MEIPASS`) zentralisiert.
- Optionales Audio und portable Hintergrundmusik ohne Linux-spezifischen Pfad.
- Einheitlicher `InputManager` für Tastatur, Gamepad-Buttons, Hat und Achsen.
- Persistente, im Steuerungsmenü änder- und rücksetzbare Belegung.
- Frischer Zustand und getrennte Snake-Listen beim Start von Ein-/Zweispielerpartien.
- Headless-Smoke-Tests sowie Compile-/Test-Schritt im Windows-Workflow.
- Der von der Branch Protection erwartete Check `main` wird durch den stabil
  benannten Windows-CI-Job gemeldet; CodeQL analysiert Pushes, Pull Requests und
  einen wöchentlichen Zeitplan.

## Offene Risiken

- Die große historische `game.py` enthält weiterhin eng gekoppelte Debug-, Boss- und Editorlogik.
- Reale Controller unterscheiden sich bei Achsen- und Buttonnummern; die Totzone ist aktuell fest.
- Audio- und PyInstaller-Verhalten muss zusätzlich auf einem echten Windows-System geprüft werden.
- Änderungen an Required Checks selbst sind Repository-Einstellungen und müssen
  von einem Administrator geprüft werden; der Workflow umgeht diese Regeln nicht.

## Nächste Schritte

1. Spielzustände in kleinere Module aufteilen und Kollisionsfälle mit Unit-Tests abdecken.
2. Controller-Totzone und Gerätezuordnung in der Oberfläche konfigurierbar machen.
3. Einen signierten Windows-Alpha-Build auf mehreren Geräten testen.
