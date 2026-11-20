# Repository guidance

- Python source files are UTF-8 and German UI text must use real Unicode characters.
- Run `python -m compileall -q Dark_Snake tests` and the headless pytest suite.
- Resource locations belong in `Dark_Snake/modules/resources.py`; do not add cwd- or OS-specific paths.
- Keep the Windows PyInstaller workflow and its bundled `Dark_Snake/assets` directory working.

## Shared developer blackboard / Kaffeerunde

- **Read [DEVELOPMENT_BLACKBOARD.md](DEVELOPMENT_BLACKBOARD.md)** before planning larger changes. It contains the current team decision log, user-verified gameplay observations and an optional **coffee-round area for freely proposed ideas**.
- Agents are welcome to propose **useful observations beyond their immediate task** (bugs, possible performance improvements, game-design ideas or questions), but must label speculation versus verified behavior, give code references where possible, and keep suggestions brief and non-blocking.
- Do **not** invent messages, autonomous discussions, human approvals or agent work that did not occur. Agents communicate only when explicitly invoked and via actual GitHub comments/PRs; **no automatic background collaboration** is implied.
- **This repository and its PRs are public.** Do not add secrets, confidential transcripts, private personal details, credentials or security exploits to the board. Truly private notes belong in an access-controlled private repository.
- Offer new blackboard notes in small documentation PRs or existing issue/PR comments; respect the owner's review/merge authority. Ideas are **not** authorization to make gameplay changes. Existing code, tests and current PR/issue state take precedence over dated notes.

## Irians Auge / Developer Mode Plus (opt-in, local)

- Read [IRIANS_AUGE.md](IRIANS_AUGE.md) before touching the developer
  recorder, feedback dialogs, item effects, boss events or visualization.
  Source: `Dark_Snake/modules/dev_recorder.py` (bounded JSON and
  checkpoints), `dev_feedback_ui.py` (optional player opinions),
  `dev_vitals.py` (read-only HP/shared lives), `dev_session.py`
  (cross-round menu/session summaries and atomic save),
  `dev_analysis.py` (read-only timelines/heatmap), integration in
  `Dark_Snake/modules/game.py`, offline CLI
  `scripts/analyze_dev_report.py`.
- DEV+ is **OFF by default**; diagnostics belong only to local
  `Entwicklerberichte/IriansAuge/`, not the public website, repository,
  cloud or user profile progression. Never commit private user-generated
  reports, round IDs, ratings, free text or screenshots without explicit
  informed approval; redact them in public PR discussions.
- New item mechanics: check `modules.enums.ItemType`,
  `Game.handle_item_pickup` and before/after `item_applied` events.
  New boss moves: log meaningful warnings, hits and interruptions
  without creating a second collision system or disk IO per frame.
- This is three **stacked draft PRs** A #248 → B #249 → C #250.
  **No merged functionality may be claimed until each PR is
  actually merged and manually accepted.** Keep the opt-in,
  1P/2P, pause and error-isolation regressions green.

## Official Pages website / DE–EN public presentation

- `site/` is the **public GitHub Pages project website**, not game code
  and not a web-playable version. The original minimal HTML came from
  PR #241 to stop uploading the entire ~310 MB game to Pages.
- The site now presents real project screenshots, bosses, World Studio,
  FrostAge tiles and a **free Windows alpha release link**. Before any
  game update or release, inspect the date and the actual status of
  content shown on the site. Keep **released alpha**, **merged main**
  and **only planned** features distinct; do not market planned bosses
  or FrostAge enemies as playable.
- Follow [site/README.md](site/README.md) for language, accessibility,
  performance, asset-source and deployment contracts, and
  [site/asset-manifest.json](site/asset-manifest.json) for image provenance.
  Update **German and English together**. Respect alt texts, keyboard
  focus, 320px/mobile behavior, reduced motion, no tracking/CDNs and
  below-fold lazy images. Prefer smaller optimized versions to heavy PNGs.
- Never publish private GPT Project / chat / account content merely
  because it is available. Only explicitly project-public, appropriate
  assets and facts should be on the website.
- Website changes belong in a **draft PR** with
  `tests/test_site_presentation.py` and CI. The Pages workflow
  publishes only `site/` on a push to `main`. The GitHub
  **About → Website** field is a separate repo setting, not set by
  changing HTML. Manual browser/phone acceptance belongs to Demus.
- Keep this public website discoverable via `README.md` and
  `README.de.md`. Site updates should not be mixed into boss-gameplay
  changes without an explicit reason.

## Asset lifecycle and agent context

- Start at [ASSET_GUIDE.md](ASSET_GUIDE.md) before using newly uploaded artwork, buttons, snake heads or bodies; it distinguishes source artwork from bundled runtime assets and from planned functionality.
- [GamePICs/README.md](GamePICs/README.md) explains staging, and [GamePICs/asset_inventory.json](GamePICs/asset_inventory.json) is a **dated snapshot** of 81 staged UI buttons plus 68 candidate head/body images (not a live game mapping).
- Do not import `GamePICs/` by runtime paths, move source PNGs, or turn unimplemented events/skins into working features merely because artwork exists.
- Check current code/tests and [ROADMAP.md](ROADMAP.md) for feature status; [PROJECT_STATE.md](PROJECT_STATE.md) and parts of [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) are historical snapshots. The guides do not supersede the implementation.
- Work on a dedicated branch and open a **draft PR**; do not auto-merge. Before removing apparently unused code, check UI action IDs, Pygame callbacks, dynamic imports and PyInstaller bundled resources. Keep the changes small and testable.
- Maintenance findings and ordering: [Issue #181](https://github.com/DemusOpalium/dark-snake-game/issues/181), [#183](https://github.com/DemusOpalium/dark-snake-game/issues/183), [#184](https://github.com/DemusOpalium/dark-snake-game/issues/184).
