# DARK SNAKE – öffentliche Projektseite / public project website

**Zweck (20.11.2026):** Aus der technischen GitHub-Pages-Reparatur #241 wurde bewusst eine öffentliche, **zweisprachige DE/EN Präsentations- und Downloadseite**. Sie ist **kein Webspiel, keine Pygame-Bibliothek und kein Ersatz für README, Issues, Wiki oder Windows-EXE**. Das öffentliche Repo ist der Quellort, `site/` die separate statische Darstellung.

**Live-Ziel:** https://demusopalium.github.io/dark-snake-game/  
**Deployment:** `.github/workflows/static.yml` veröffentlicht bei Push auf `main` ausschließlich `site/`, nicht das vollständige Spiel. Der Link muss auf der Repository-Startseite (README) und – vom Kontoinhaber in **About → Website** – sichtbar eingetragen werden. CI-Grün beweist den erfolgreichen Deploymentlauf, nicht einen echten Browser-/Mobil-/Sichttest.

## Architektur
- `index.html`: Inhalte mit exakten Aussagen zu spielbarer **13.11.2026-Alpha** vs. **neuerem main** vs. **erst geplanten Features**. Nur lokale CSS- und JS-Dateien.
- `styles.css`: responsives Dark-Fantasy-Layout ohne externe Fonts/Bibliotheken; focus-visible; reduced-motion.
- `main.js`: DE/EN Umschalter per Browser-Sprache/Button, barrierefreie ARIA-States, kein Tracking, keine Cookies, kein API-/Game-Backend.
- `media/`: echte Bilder aus `GamePICs` und `Dark_Snake/assets` als unveränderte Git-Blob-Kopien; Herkunft und Größen in `asset-manifest.json`. Spiel-/Rohdateien NICHT umbenennen oder verändern.
- Nur Bosskampf-Screenshot (78 KB) und sehr kleine Bossgrafiken initial. Größere Screenshots/Tiles erhalten `loading="lazy"`. Einzelne PNGs sind **nicht optimiert** und können bei langem Scrollen mehrere MB übertragen: vor zukünftigem Ausbau kleinformatige WebP/AVIF-Derivate erzeugen und tatsächliche Bytes messen.
- Alle Downloadbuttons gehen auf den **bestätigten veröffentlichten GitHub-Release-Tag**; neuere Action-Builds getrennt gekennzeichnet. Keine erfundenen Direktdownload-URLs, Versionen oder ungetesteten Downloadzusicherungen.
- Die Seite hostet **keine** Download-ZIP, keine persönlichen Daten und keine automatische KI-Funktion. Keine externen CDNs oder Drittanbieter-Skripte.

## Website-Pflege bei zukünftigen Features (Agents)
1. Zuerst `ROADMAP.md`, `GALLERY.md`, `README.de.md`, `ASSET_GUIDE.md` und aktuelle PR-/Release-Stände prüfen.
2. Auf der Website zwischen `release`, `main (development)` und `planned` unterscheiden. Merge einer Funktion bedeutet **nicht**, dass sie im neuesten freigegebenen Release ist.
3. Neue Medien nur aus bestätigten Projektquellen und mit Darstellung-/Nutzungsfreigabe aufnehmen. PNG-Größe, Alpha, Herkunft, alternative DE/EN-Beschreibung, Ladezeit und Mobilansicht prüfen. Keine nichtöffentlichen Projektbilder automatisch veröffentlichen.
4. DE und EN **gemeinsam** bearbeiten, beide Sprachen, 320px/768px/Desktop, Tastatur, Schriftgrößen, kontrastreiche Buttons, Bildunterschriften und Reduced Motion testen. Keine zufällige neue Layoutbibliothek.
5. Webseitenänderungen als **kleinen Draft-PR**; statische Tests aus `tests/test_site_presentation.py`, Windows-CI und CodeQL. GitHub Pages selbst deployt erst nach Demus' Merge in `main`; dann öffentliches Seitenbild und tatsächliche Links prüfen.
6. Zwecks Sichtbarkeit Link in Repo-README pflegen. Das About-Feld **Website** ist eine GitHub-Repository-Einstellung und erfordert ggf. eine manuelle UI-Änderung des Besitzers. Screenshot-/Grafikreview ist **nicht** durch headless Tests ersetzt.
7. Keine automatische Verbreitung oder Werbung, keine personenbezogenen Details/privaten Chat-Inhalte. Demus entscheidet über Gestaltung, Releases und Merge.

## Live-Links
- Site: https://demusopalium.github.io/dark-snake-game/
- Repository: https://github.com/DemusOpalium/dark-snake-game
- Downloads: https://github.com/DemusOpalium/dark-snake-game/releases
- Neuere Test-Builds: https://github.com/DemusOpalium/dark-snake-game/actions/workflows/python-app.yml

## Historie
- PR #241: GitHub-Pages-Fix. Statt ca. 310 MB gesamter Spielordner nur noch `site/` deployen; zunächst bewusst minimalistischer Platzhalter.
- 20.11.2026: Vollständige, DE/EN, responsive Indie-Spielpräsentation mit echten Bildern, Bossen, World-Studio-Tiles, transparentem Download-/Statusbereich und Agents-Pflegevertrag.
