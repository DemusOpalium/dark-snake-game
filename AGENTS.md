# Repository guidance

- Python source files are UTF-8 and German UI text must use real Unicode characters.
- Run `python -m compileall -q Dark_Snake tests` and the headless pytest suite.
- Resource locations belong in `Dark_Snake/modules/resources.py`; do not add cwd- or OS-specific paths.
- Keep the Windows PyInstaller workflow and its bundled `Dark_Snake/assets` directory working.
