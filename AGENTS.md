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

## Asset lifecycle and agent context

- Start at [ASSET_GUIDE.md](ASSET_GUIDE.md) before using newly uploaded artwork, buttons, snake heads or bodies; it distinguishes source artwork from bundled runtime assets and from planned functionality.
- [GamePICs/README.md](GamePICs/README.md) explains staging, and [GamePICs/asset_inventory.json](GamePICs/asset_inventory.json) is a **dated snapshot** of 81 staged UI buttons plus 68 candidate head/body images (not a live game mapping).
- Do not import `GamePICs/` by runtime paths, move source PNGs, or turn unimplemented events/skins into working features merely because artwork exists.
- Check current code/tests and [ROADMAP.md](ROADMAP.md) for feature status; [PROJECT_STATE.md](PROJECT_STATE.md) and parts of [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) are historical snapshots. The guides do not supersede the implementation.
- Work on a dedicated branch and open a **draft PR**; do not auto-merge. Before removing apparently unused code, check UI action IDs, Pygame callbacks, dynamic imports and PyInstaller bundled resources. Keep the changes small and testable.
- Maintenance findings and ordering: [Issue #181](https://github.com/DemusOpalium/dark-snake-game/issues/181), [#183](https://github.com/DemusOpalium/dark-snake-game/issues/183), [#184](https://github.com/DemusOpalium/dark-snake-game/issues/184).
