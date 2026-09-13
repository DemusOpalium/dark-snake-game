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
- Das pausierende Admin-Menü bietet neun direkt ausführbare Aktionen mit
  deutschen Namen, Mouseover-Erklärungen, Status- und Fehlermeldungen.
- Admin-Menü und Level-Editor behandeln Eingaben exklusiv und können mit `ESC`
  geschlossen werden; Spiellogik und Bewegung pausieren, solange ein Werkzeug offen ist.
- Portal-Effekte können auch ohne gespeicherte Editor-Karte sicher auslaufen und
  stellen dann den normalen Spielfeldhintergrund wieder her.
- Rotierendes Laufzeitprotokoll, Ringpuffer wichtiger Ereignisse und automatische
  Crash-Reports erfassen Fehler samt sicherem Spielstatus im Benutzerdatenordner.

## Offene Risiken

- Die große historische `game.py` enthält weiterhin eng gekoppelte Debug-, Boss- und Editorlogik.
- Der Level-Editor selbst und die allgemeine Menü-Skalierung sind weiterhin für
  getrennte Folgearbeiten vorgesehen.
- Reale Controller unterscheiden sich bei Achsen- und Buttonnummern; die Totzone ist aktuell fest.
- Audio- und PyInstaller-Verhalten muss zusätzlich auf einem echten Windows-System geprüft werden.
- Änderungen an Required Checks selbst sind Repository-Einstellungen und müssen
  von einem Administrator geprüft werden; der Workflow umgeht diese Regeln nicht.

## Nächste Schritte

1. Level-Editor und allgemeines UI-Layout in getrennten Änderungen untersuchen.
2. Spielzustände in kleinere Module aufteilen und Kollisionsfälle mit Unit-Tests abdecken.
3. Controller-Totzone und Gerätezuordnung in der Oberfläche konfigurierbar machen.
4. Einen signierten Windows-Alpha-Build auf mehreren Geräten testen.
