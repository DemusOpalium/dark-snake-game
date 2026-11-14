# Repository guidance

- Python source files are UTF-8 and German UI text must use real Unicode characters.
- Run `python -m compileall -q Dark_Snake tests` and the headless pytest suite.
- Resource locations belong in `Dark_Snake/modules/resources.py`; do not add cwd- or OS-specific paths.
- Keep the Windows PyInstaller workflow and its bundled `Dark_Snake/assets` directory working.

## Asset lifecycle and agent context

- Start at [ASSET_GUIDE.md](ASSET_GUIDE.md) before using newly uploaded artwork, buttons, snake heads or bodies; it distinguishes source artwork from bundled runtime assets and from planned functionality.
- [GamePICs/README.md](GamePICs/README.md) explains staging, and [GamePICs/asset_inventory.json](GamePICs/asset_inventory.json) is a **dated snapshot** of 81 staged UI buttons plus 68 candidate head/body images (not a live game mapping).
- Do not import `GamePICs/` by runtime paths, move source PNGs, or turn unimplemented events/skins into working features merely because artwork exists.
- Check current code/tests and [ROADMAP.md](ROADMAP.md) for feature status; older [PROJECT_STATE.md](PROJECT_STATE.md) and [DEV_STRUCTURE.md](DEV_STRUCTURE.md) may describe earlier alphas.
