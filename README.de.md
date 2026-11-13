<p align="center">
  <img src="Dark_Snake/assets/graphics/titel1.png" alt="DARK SNAKE Titelgrafik" width="240">
</p>

<h1 align="center">🐍 DARK SNAKE</h1>

<p align="center">
  <strong>Klassisches Snake trifft auf düsteres Arcade-Chaos.</strong><br>
  Bosskämpfe · Zwei Spieler · Portale · Elementare Effekte · World Studio
</p>

<p align="center">
  <a href="README.md">English 🇬🇧</a> · <strong>Deutsch</strong> ·
  <a href="https://github.com/DemusOpalium/dark-snake-game/discussions">Community & Feedback</a> ·
  <a href="ROADMAP.md">Roadmap</a>
</p>

> 🚧 **Aktives Hobbyprojekt / Alpha.** Entwickelt von DemusOpalium mit KI-Unterstützung, Neugier und Freude an Spielen. Kostenlos zum Entdecken und Testen; noch keine fertige kommerzielle Veröffentlichung.

## 🎮 So sieht das Spiel aus

<p align="center">
  <img src="GamePICs/Spiel%2BAdminPanel-open22.4.2025.png" alt="DARK SNAKE im Spiel mit geöffnetem Entwickler-Panel (älterer Stand)" width="740">
</p>
<p align="center"><em>Echter Spiel-Screenshot aus einem älteren Build, mit geöffnetem Entwickler-Panel.</em></p>

**Was steckt drin?** Ein schnelles Snake-Arcade-Spiel mit Bossen, Gegnern, Projektilen, Portalen, Items und Zwei-Spieler-Steuerung. Dazu kommen eigene Snake-Designs und Hintergrundmusik.

<p align="center">
  <img src="GamePICs/LvLEDITOR.png" alt="Der integrierte DARK SNAKE Level-Editor (älterer Screenshot)" width="640">
</p>
<p align="center"><em>World Studio: eigene Karten gestalten und speichern. Die Werkstatt wird weiterentwickelt.</em></p>

## ❄️ World Studio & FrostAge

**Schon nutzbar:** Mit **F2** den Editor öffnen, **495 bisherige Tiles** auswählen, benannte JSON-Entwürfe speichern, Themenwelten verwalten und **WALL/BARRIER**, **Schaden** sowie **Slow** im isolierten 1P-/2P-Leveltest ausprobieren.

**Wichtig:** Der reguläre Classic-Modus übernimmt ausgewählte Karten bisher **nur als Hintergrund**. Eigene Wandkollisionen und Effektfelder wirken derzeit **im Editor-Spieltest**, noch nicht in der normalen Classic-Runde.

**Als Nächstes geplant:** Große Multi-Tiles und Stempel, übersichtlichere Werkzeuge, Dächer mit transparentem Sichtbereich, flackernde Lichtquellen, Trigger und vollständig spielbare eigene Level.

🎨 **126 neue FrostAge-PNGs** liegen bereits im [Grafik-Eingangsordner](GamePICs/Incoming/Frost_Tiles/). Sie sind **noch nicht in den Grafik-Loader des Spiels eingebaut**.

## ⬇️ Unter Windows ausprobieren

Eine stabile, direkt herunterladbare Windows-Veröffentlichung gibt es **noch nicht**. Über [GitHub Actions](https://github.com/DemusOpalium/dark-snake-game/actions/workflows/python-app.yml) werden Windows-Testversionen gebaut; zum Herunterladen der Artefakte kann eine GitHub-Anmeldung nötig sein. Die Test-Builds sind nicht signiert.

Nach dem Download das Actions-Archiv und die darin enthaltene Spiel-ZIP vollständig entpacken, dann die EXE starten. Mehr dazu: [Windows-Build und Sicherheitshinweise](WINDOWS_BUILD.md).

**Aus dem Quellcode starten** (Python / pygame):

```bash
python -m pip install -r requirements.txt
python Dark_Snake/main.py
```

## ⌨️ Steuerung im Überblick

| Aktion | Standardtaste |
| --- | --- |
| Bewegung Spieler 1 / Spieler 2 | WASD / Pfeiltasten |
| Schießen | Leertaste (P1), + (P2) |
| Level-Editor | F2 |
| Entwickler-Panel | Tab |
| Zurück / Pausenmenüs | Esc |

Tasten und weitere Optionen lassen sich im Spiel anpassen. Weitere Details: [Steuerung](CONTROLS.md).

## 🤝 Mitmachen & Feedback

Du hast einen Spielfehler entdeckt, eine Level-Idee oder möchtest DARK SNAKE ausprobieren? Wir freuen uns über Rückmeldungen und Austausch.

**[💬 Discussions](https://github.com/DemusOpalium/dark-snake-game/discussions)** · **[🐛 Issues](https://github.com/DemusOpalium/dark-snake-game/issues)** · **[🛣️ Roadmap](ROADMAP.md)**

Mehr zum Projekt: [World Studio / Entwicklung](DEVELOPMENT_NOTES.md) · [Spielgalerie](GALLERY.md) · [Windows-Build](WINDOWS_BUILD.md).

**Lizenz:** [MIT](LICENSE). Entstanden mit Python, pygame und der Zusammenarbeit von Mensch und KI. 🐍
