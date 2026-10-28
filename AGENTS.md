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
  replaces `session.target` with it. The legacy routine also mutates its input;
  `simulation.run_simulation` isolates those mutations with copies.

## Code gotchas

- `simulation.py` is the shared headless workflow for GUI and CLI. Use
  `CalculationRequest.from_session`, `run_simulation`, then `apply_result`.
- Physics functions use explicit `ReactionConfig` values. Calibration uses
  `session.standard_reaction`; target calculations use `session.experiment_reaction`.
  Defaults come from `config.default_reactions()` in (standard, experiment) order.
- Settings live in the per-user config dir (`config.settings_path()`), seeded from
  `src/hyproc/data/default_settings.json`. Tests isolate them via `HYPROC_CONFIG_DIR`
  (set in `tests/conftest.py` before any `hyproc` import).
- `Session` holds scientific state. `HyProCApp` owns job lifetime and plotting;
  `app_layout` constructs the main sections; `TargetEditor` owns layer/element widgets and selections.
  Workers receive snapshots and never access Tk, even to call `after`; the Tk thread polls results.
- `file_io.py` owns version-1 simulation JSON, target JSON and curve imports/exports.
  Preserve key names, optional-field defaults, old point-count ranges and extension fields.
  Parse completely before replacing session state.
- `Element` / `Layer` / `Target` subclass `dict` so they serialise straight to the save-file JSON;
  keep new fields JSON-compatible.
- SRIM is Windows-only: it writes `SR.IN` and runs `SRModule.exe` with child-process
  `cwd=<SRIM_path>/SR Module`. Keep the application's cwd unchanged. Calls share a process-local
  lock because SRIM uses fixed filenames. Use `"SCS-25-Solid"` or fake processes in tests.
- Load packaged files with `config.data_path(name)`, never paths relative to `__file__`.
- Before changing physics, read `docs/scientific-review.md`: known segmentation and diagnostic
  concerns are deliberately characterized, not corrected. Ask for scientific approval to change them.
- For architecture/API changes read `docs/architecture.md`; for packaging and desktop checks read
  `CONTRIBUTING.md`. Run lint and tests; use `python -m build` and `python -m twine check dist/*`
  for package changes. CLI entry points are `hyproc-simulate` and `python -m hyproc.cli`.

## Repo

Fork of `LouisDupont-2/HyProC` (`upstream` remote); `origin` is the fork.
