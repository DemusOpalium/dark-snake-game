<p align="center">
  <img src="GamePICs/Dunkle%20Frostschlange%20im%20Eisk%C3%B6nigreich.png" alt="DARK SNAKE — FrostAge: a dark snake in a frozen kingdom (concept artwork)" width="820">
</p>

<h1 align="center">🐍 DARK SNAKE</h1>
<p align="center"><strong>Arcade Snake with roguelite ambitions, boss battles, elemental chaos and a growing world editor.</strong></p>
<p align="center"><strong>English</strong> · <a href="README.de.md">Deutsch 🇩🇪</a> · <a href="https://github.com/DemusOpalium/dark-snake-game/discussions">Join the discussion</a> · <a href="ROADMAP.md">Roadmap</a></p>

> 🚧 **Playable, actively developed alpha.** This is a hobby game made by DemusOpalium, developed and playtested personally with help from Irian and AI-assisted coding. The picture above is **FrostAge concept artwork**, not gameplay footage.

## 🎮 A quick look

| FrostAge main menu | Boss fight |
| :---: | :---: |
| <img src="GamePICs/DarkSnake%20Titel%20Screen.png" alt="Current DARK SNAKE title screen captured on 14 November 2026" width="420"> | <img src="GamePICs/boss%20fight%20game.png" alt="Actual DARK SNAKE boss-fight screenshot" width="420"> |

**The point?** Guide your snake, collect points and items, survive enemies and incoming attacks, and stay alive when bosses appear. You begin with **three lives**. The action mixes classic Snake with timed events, health, projectiles, portals, a **D20 dice-event system**, unusual bonuses and increasingly unpredictable situations. The core is arcade; the broader roguelite adventure is still in development.

Play alone or locally with a second player. Choose your snake's appearance and play your own background music. Some encounters are frantic; others are just a chance to relax, chase a score and try another run.

## 🛠️ World Studio — build your own maps

<p align="center"><img src="GamePICs/World%20Studio%20DarkSnake.png" alt="Actual World Studio 3.0 editor on 14 November 2026, with illustrated toolbar and FrostAge level" width="820"></p>
<p align="center"><em>World Studio captured on 14 November 2026: enlarged editor layout, illustrated controls and FrostAge roof demo. Screenshots show development builds, not necessarily the 13 November pre-release.</em></p>

Press **F2** to open the editor. Already available: **495 classic tiles**, **175 FrostAge PNG assets**, large **multi-tile objects**, named JSON level drafts, themed world organization, Undo/Redo and isolated **1P/2P playtests** for WALL/BARRIER collision and Damage/Slow fields. World Studio now includes a **resizable window**, a searchable tile library, zoomable map, separate border sides and corners with preview, and **58 illustrated editor PNGs** registered in the runtime catalogue (with **62 action IDs** including shared artwork). The FrostAge artwork also powers the main menu.

**Playable in the isolated level test:** a separate **Roof/Foreground layer** with soft, player-specific see-through roof windows; the supplied roof-arch demo lets both snakes pass underneath. Roof artwork and its visibility settings can also be chosen for a later Classic background, but authored collision and effects currently have different rules between the isolated editor test and regular Classic mode.

**In current `main` (after PRs #174, #179 and #180):** Layer Explorer with visibility, locks and solo view; DE/EN switching for the **World Studio editor**; drag painting/erasing with Undo/Redo; and **Learn → My First Level**, a guided five-step FrostAge practice map. These editor additions are **newer than the 13 November pre-release**. A game-wide translation is not claimed.

**Still planned:** persistent full-map landscape backgrounds beneath tiles, lighting and fog, configurable FrostAge enemy/projectile/item behavior, interactive triggers and a complete multi-level roguelite adventure. [The roadmap](ROADMAP.md) and [asset guide](ASSET_GUIDE.md) distinguish functioning features from concept artwork.

## ⬇️ Try the Windows alpha

The **[FrostAge Alpha pre-release (13 November 2026)](https://github.com/DemusOpalium/dark-snake-game/releases/tag/frostage-alpha-2026-11-13)** is available directly on GitHub Releases. Download `DARK-Snake-v1.0.0-Windows-x64.zip`, extract it completely and launch `DARK-Snake.exe`. The accompanying `.sha256` file lets you verify the download. **The EXE is unsigned**, and Windows or browsers may display warnings. A stable, signed release is **not yet available**. More recent test builds (including features absent from this tagged alpha) appear in [GitHub Actions](https://github.com/DemusOpalium/dark-snake-game/actions/workflows/python-app.yml). See the [Windows guide](WINDOWS_BUILD.md).

Run from Python source instead:

```bash
python -m pip install -r requirements.txt
python Dark_Snake/main.py
```

## ⌨️ Controls & game modes

| Action | Default |
| --- | --- |
| Player 1 / Player 2 movement | WASD / arrow keys |
| Fire | Space (P1), Enter / + (P2) |
| World Studio | F2 |
| Developer panel | Tab |
| Pause / navigation | P / Esc |

Bindings can be customized in-game; see [full controls](CONTROLS.md). The main menu supports mouse, keyboard and mapped controller inputs. **Continue** resumes an interrupted round while the game remains open. Some menu entries (Workshop, Boss Rush, Inventory, Statistics, Credits) are currently shown as **unavailable** rather than claiming features that do not exist yet.

## 🤝 A game that grows through playing

DARK SNAKE is a long-term personal project, developed step by step rather than rushed into a release. I play it, find what feels fun or frustrating, adjust it, and play again. Bugs, ideas, suggestions and contributions from other players are welcome — no need to be an expert.

**[💬 Discussions](https://github.com/DemusOpalium/dark-snake-game/discussions)** · **[🐛 Issues](https://github.com/DemusOpalium/dark-snake-game/issues)** · **[🛣️ Roadmap](ROADMAP.md)** · **[☕ Developer Blackboard](DEVELOPMENT_BLACKBOARD.md)** · **[📷 Gallery](GALLERY.md)**

**License:** [MIT](LICENSE). Made with Python, pygame, and human–AI collaboration. 🐍
