# DARK SNAKE – Machbarkeitsnotiz: bessere Grafik, Shader und Rendering
**Erfasst:** 20.11.2026 · **Status: IDEE / STUDIENAUFTRAG, NICHT IMPLEMENTIERT.**
**Priorität:** Nach Bossfähigkeiten (insbesondere Medusa Roll/Charge A). Keine neue Engine beschlossen.

## Ausgangspunkt
Demus hat eine zusätzliche externe, positiv formulierte Repo-Einschätzung
(Grok-Text) und den Wunsch nach moderner FrostAge-Grafik, Glow, Licht, Nebel
und optionalen Shadern eingebracht. **Die externe Einschätzung ist
kein unabhängiger Benchmark und kein Auftrag zum Umbau.** Der Wunsch ist,
die Werkzeuge für Mensch + Codex + Irian langfristig zu verbessern,
ohne Gameplay, Spielstände oder die Windows-EXE zu gefährden.
**Persönliche Angaben des Testers und Original-Zitate gehören nicht ins öffentliche Repo.**

## Ist-Zustand – im Repository nachgesehen
- `requirements.txt`: **pygame==2.6.1**; `Dark_Snake/config.py`:
  **FPS = 60**, 45×31 Spielraster bei aktuellem VIEW_SCALE.
- `Dark_Snake/modules/effect_manager.py`: **existiert bereits**:
  non-blocking Effektinstanzen, lokale JSON-`manifest.json`-Profile,
  PNG/WebP-Frames, transparente/layerbasierte Darstellung,
  `pygame.BLEND_ADD`, Ablaufsteuerung, Caches und prozedurale Fallbacks.
  **Noch kein allgemeines editierbares Partikelsystem und kein GPU-Shader-Backend.**
- `Dark_Snake/modules/graphics.py`: Bild-Loader, Fehlasset-Fallback,
  Sprite-/Skalierungscache.
- `Dark_Snake/modules/roof_render.py`: weiche Sichtfenstermasken
  für Roof/Foreground, in Pygame ohne GPU-Shader.
- `Dark_Snake/modules/game.py`: Pygame-Surface-Zeichnung mit
  `pygame.display.update()`, Boss- und AoE-VFX. `frame_metrics.py`
  erfasst Laufzeitphasen. `scripts/benchmark_game.py` ist vorhanden.
- Windows-Build: PyInstaller mit gebündelten Assets,
  `requirements-windows-build.txt` ist gepinnt/gehärtet. Eine neue
  Grafik-Bibliothek erfordert getrennte Dependency-/Lizenz-/EXE-Prüfung.
- World Studio hat Ground/Objects/Roof/Collision/Effects als getrennte
  Ebenen. Die *Grafik-Idee* berechtigt **nicht** zu neuen Editor-Funktionen.

## Variantenvergleich
| Kandidat | Machbarkeit für aktuelle Architektur | Nutzen | Entscheidung |
|---|---|---|---|
| **A. Reines Pygame:** vorhandenen `EffectManager` mit begrenzten, gepoolten Partikeln, Glow-Sprites, Trails, vorab berechneten Texturen erweitern | **Hoch** (keine neue Runtime-Abhängigkeit) | Sichtbarer Frost, Treffer-, Portal- und Boss-Punch | **Erster Kandidat**, nach Boss-Arbeit isoliert testen |
| **B. Offline-Grafikpipeline:** Pillow/NumPy als Build-/Autorentool, nicht zwingend in der EXE | **Hoch** (Tool-Ausgabe nur PNG/WebP) | Weichere Glow-/Frostframes, Spritesheets | Parallel zur Asset-Pflege prüfen |
| **C. pygame-ce:** in eigener virtueller Umgebung, **nicht** gleichzeitig mit pygame in gleicher Umgebung | **Unklar** bis Regression/Windows-Pakettest | Mögliche API- und Performanceverbesserungen | Optionale Einzelstudie, **keine Umstellung** |
| **D. ModernGL als optionaler Postprocessing-Renderer** | **Technisch möglich, Integrationsrisiko hoch** | Bloom, Shader, Distortion, dynamischere Farb-/Lichteffekte | **Erst separater Proof of Concept**; keine Änderung am Spiel-Fenster in dieser Phase |
| **E. Arcade/Godot als Spiel-Renderer** | **Migration mit hohem Risiko** | Andere Renderfähigkeiten | **Nicht** für den aktuellen Projektstand |
| **F. Numba/Cython, Pymunk/Box2D, externe Partikelbibliothek** | Nur für konkreten gemessenen Engpass/Physikbedarf | Situationsabhängig | **Nicht vorsorglich installieren** |

### Technischer Stolperstein bei Shadern (entscheidend)
Unser `Game.draw()` nutzt ein normales Pygame-Display und
`pygame.display.update()`. Laut Pygame-Dokumentation ist
`display.update()` **auf `OPENGL`-Displays nicht verwendbar**.
Man darf daher **nicht einfach `OPENGL` bei `set_mode` anhängen**:
UI, Blits, Resize, Overlay, Screenshots und Windows-Build müssten
gezielt angepasst oder auf eine separate Render-Ausgabe geroutet werden.
Das ModernGL-Beispiel nutzt eine Pygame-**Offscreen Surface** und
kopiert diese als Textur zur GPU; Kosten des Kopierens müssen
gemessen werden. Deshalb **kein Shader-Einbau mitten im Boss-PR**.

## Vorgeschlagene technische Untersuchung (nur nach bewusster Freigabe)
**0 – Baseline:** gleicher Seed/Boss, 1P/2P, gleiche Auflösung,
VSync/FPS, mit/ohne DEV+, feste Aufzeichnung über reale Windows-EXE.
Median/P95/P99 **Framezeit**, Draw-/Present-Zeit, Speicherverbrauch,
Partikelanzahl und seltene Ruckler messen. Keine FPS-Folgerung allein
aus einem Einzelwert. Profile nach Hardware/Build getrennt notieren.

**1 – Geringes Risiko:** eigenständiger Effektdemo-Prototyp mit 0 / 100 /
300 / 500 Partikeln, begrenzter Lebenszeit und sichtbarem Frost-Glow,
kompatibel mit der bestehenden `EffectManager`-JSON-Struktur;
vergleichbare Vorher-/Nachher-Messung. Keine Schadenslogik, keine
hitbox-abhängigen Shader, kein Tastatur-/Fensterumbau.

**2 – Optionaler GPU-Versuch:** eigenes Demo-/Branch-Modul statt
Produktionspfad: Pygame-Offscreen-Surface → GPU-Textur → einfacher
Bloom/Blur-Shader → Ausgabe. Pixelkopie, Skalierung, Text-/HUD-Schärfe,
GPU-Fallback, Treiber- und PyInstaller-Aufwand messen.
Rückweg zu **unverändertem Pygame-Renderer** muss eindeutig sein.

**3 – Benutzerseitige Bedienung erst bei Mehrwert:** VFX-Presets
`aus / niedrig / mittel / hoch`, reduzierte Blitze/
Bildschirmerschütterungen, separater Schalter für Photosensitivität.
Spätere Designer-Vorschau nur, wenn Effektdatenformat und
Bossmechanik-Schnittstelle tatsächlich stabil sind.

## Sicherheits-/Freigabebedingungen
- [ ] Keine Änderung an Bewegung, Tickrate, Boss-Kollisionen, Input,
      RNG, Schaden, HUD-Daten oder Karriere-/Level-Dateien.
- [ ] 1P/2P, Pausen, Resize, Minimieren/Alt-Tab, F9/F10 und
      DEV+-Overlay, Low-FPS-Szenarien, Windows-EXE vollständig prüfen.
- [ ] Fehlender Effekt/Shader → Spiel bleibt nutzbar; Shader als
      *optional* deaktivierbar, wenn Renderer das zulässt.
- [ ] GPU-Ressourcen und Texturen begrenzen; keine unkontrollierte
      Partikelerzeugung oder Datei-IO je Frame.
- [ ] Asset-Lizenzen und Bibliotheks-/PyInstaller-Hooks vor Release prüfen.
- [ ] CI **und** reale Sichtprüfung; keine Behauptung „besser“ ohne
      messbare Leistung, Lesbarkeit und Spielgefühl.
- [ ] Nur **separate Draft-PRs**, keinerlei automatische Übernahme
      dieses Konzeptes in `main`.

## Technische Primärquellen (abgerufen 20.11.2026)
- Pygame Display/OpenGL:
  https://www.pygame.org/docs/ref/display.html
- ModernGL Kontexte:
  https://moderngl.readthedocs.io/en/stable/reference/moderngl.html
- Offscreen-Pygame-auf-ModernGL-Demonstration:
  https://github.com/moderngl/moderngl-window/blob/master/examples/advanced/pygame2.py
- pygame-ce Projekt:
  https://github.com/pygame-community/pygame-ce

**Fazit:** Die derzeit sinnvollste Richtung ist **bestehende Pygame-
Effekte modular erweitern, VFX-Budgets messen und GPU-Postprocessing
nur als rückbaubare Studie testen**. Kein Engine-Wechsel.
