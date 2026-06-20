# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Matcap Maker v3 — a layer-based Matcap texture generator. Desktop GUI app built with PySide6 + PyOpenGL (OpenGL 3.3 Core Profile, forced in `src/main.py`). Docs, commit messages, and UI are primarily Japanese.

## Commands

```powershell
# Project venv lives at .venv (use .venv\Scripts\python.exe if python isn't on PATH)
# Install dependencies (uv recommended, plain pip also works)
uv pip install -r requirements.txt

# Run the app (from repo root — imports are rooted at `src.`)
python -m src.main

# Build Windows app (PyInstaller onedir → dist/MatcapMaker/MatcapMaker.exe)
python build_exe.py

# Build the Windows installer (PyInstaller onedir + Inno Setup → dist/installer/MatcapMaker-Setup-<ver>.exe)
# Requires Inno Setup 6 (winget install JRSoftware.InnoSetup). Distribution version lives in src/version.py.
python build_installer.py

# Unit tests (unittest, no pytest config)
python -m unittest tests.test_io

# GL/UI verification scripts (open a real window briefly)
python tests\verify_refactor.py   # full pipeline checks on a live GL context
python tests\smoke_ui.py          # MainWindow + properties panel smoke test
```

Other files in `tests/` (`test_render.py`, `verify_*.py`, `repro_export.py`) are ad-hoc verification scripts, not a test suite. They open a real Qt/OpenGL window, render headlessly, and write a PNG — run individually with `python tests/test_render.py` on a machine with a display.

The app logs uncaught exceptions to `matcap_error.log` (in `%LOCALAPPDATA%\MatcapMaker\` when frozen — the install dir is read-only; in `src/` when run from source) — check it when the GUI crashes silently.

## Architecture

Data flow: **UI (`src/ui/`) → Engine (`src/core/engine.py`) → Compositor (`src/core/compositor.py`) → GLSL shaders (`src/shaders/`)**, with the layer stack (`src/core/layer_stack.py` + `src/layers/`) as the model. Detailed docs (Japanese) live in `DOCS/technical_manual/`.

### Rendering pipeline

The Compositor uses **ping-pong FBOs**: each enabled layer renders itself into a temporary FBO, then `blend.frag` composites it onto the accumulator (swapping ping/pong each step). All blend modes are implemented as math in `blend.frag` (programmable blending), not `glBlendFunc`; the accumulator stores **straight (un-premultiplied) alpha**. GL state (blend off, depth off, back-face culling) is set once by the Compositor — layer `render()` methods only set uniforms and draw. Layers whose class attribute `is_post_process = True` (e.g. AdjustmentLayer) are instead fed the accumulated texture on a full-screen quad. Layer opacity is applied centrally in the blend/post-process pass via `uOpacity`. Layers carry a dirty flag (`mark_dirty()`) to trigger re-render; UI param widgets must call it after changing a layer attribute. Anything needing a GL context (texture creation, geometry upload) must run during a render pass or inside `makeCurrent()` — UI callbacks defer such work to the next `render()` (see NoiseLayer.regenerate, ImageLayer lazy texture load).

### Layer system (the main extension point)

Each layer type = a Python class in `src/layers/` paired with a fragment shader in `src/shaders/`. To add a new layer:

1. Create the class (subclass `BaseLayer` / `LayerInterface`), load its shader via `ResourceManager().get_shader(...)`, set uniforms in `render()`.
2. Add the fragment shader in `src/shaders/`.
3. Register it in `src/layers/__init__.py` via `LayerRegistry.register(...)` — registration only happens when `src.layers` is imported (`main.py` does `import src.layers`).
4. Add UI strings to **both** `res/locales/en.json` and `res/locales/ja.json`; UI text goes through `tr()` from `src/core/i18n.py`.

No engine/compositor changes are needed for new layers.

### Serialization (project .json files)

`src/core/layer_serializer.py` serializes layers **reflectively**: every public attribute in `layer.__dict__` becomes a saved param, except underscore-prefixed attrs and a hardcoded exclusion list (GL handles, name/enabled/blend_mode/opacity which are top-level fields). Consequences:

- New persistent params: just add a public attribute with a default in `__init__` — the default is the backward-compat value when loading old files.
- Runtime-only state (texture IDs, caches) must be underscore-prefixed or added to the exclusion list, or it will leak into project files.
- Loading is lenient by design (spec in README.md): missing params use class defaults, unknown params are ignored, unknown layer types are skipped. Never make the loader strict.

### Resources and packaging

All file access to `res/`, `src/shaders/`, `LICENSE/` must go through `get_resource_path()` (`src/core/utils.py`), which handles PyInstaller's `_MEIPASS`. Those three directories are bundled by `build_exe.py` via `--add-data`; a new top-level resource directory must be added there too.

### Export padding

PNG export applies texture dilation (edge padding) to prevent UV seam bleeding — an iterative NumPy neighbor-fill in `src/core/export_padding.py` (`dilate` + `fill_background`), documented in `DOCS/technical_manual/05_export_padding.md`. Keep it vectorized; per-pixel Python loops are too slow at 2K/4K.
