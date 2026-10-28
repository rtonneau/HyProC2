# HyProC

Python Tkinter app simulating resonant-NRA excitation curves for layered targets. This is a Python
project: the global Geant4/C++ conventions do not apply here; follow PEP 8 as already used in the
surrounding file.

## Commands

```bash
.venv/Scripts/python -m pip install -e ".[dev]"   # setup
.venv/Scripts/ruff check                          # lint (must pass)
.venv/Scripts/python -m pytest                    # tests (no GUI, no SRIM)
.venv/Scripts/hyproc                              # run the app
```

## Domain gotchas

- `reaction.Z1/A1` is the **beam ion**; `reaction.Z2/A2` is the **profiled element**. Defaults: proton
  beam, ¹⁵N profiled, `E_R` = 6385 keV.
- Units: areal density in TFU (1e15 at/cm²), energy in keV, stopping in keV/TFU, composition in at. %.
- `assign_stopping` returns a new target whose thick layers are split into sub-layers; the GUI then
  replaces `self.target` with it.

## Code gotchas

- `stopping`, `broadening`, `yield_calc` hold no reaction constants: every public function takes a `ReactionConfig`
  (`reaction`); `app.py` passes `self.reaction` (from `config.default_reactions()[1]`).
- Settings live in the per-user config dir (`config.settings_path()`), seeded from
  `src/hyproc/data/default_settings.json`. Tests isolate them via `HYPROC_CONFIG_DIR`
  (set in `tests/conftest.py` before any `hyproc` import).
- `app.py` imports the physics modules under legacy aliases (`mod2` = stopping, `mod3` = broadening,
  `mod4` = yield_calc).
- `app_layout.create_widgets(self)` attaches every widget as an attribute of the `GUI_App` instance.
- `Element` / `Layer` / `Target` subclass `dict` so they serialise straight to the save-file JSON;
  keep new fields JSON-compatible.
- The SRIM model is Windows-only: it writes `SR.IN`, `os.chdir`s into `<SRIM_path>/SR Module` and runs
  `SRModule.exe`. Use `"SCS-25-Solid"` in tests.
- Load packaged files with `config.data_path(name)`, never paths relative to `__file__`.

## Repo

Fork of `LouisDupont-2/HyProC` (`upstream` remote); `origin` is the fork.
