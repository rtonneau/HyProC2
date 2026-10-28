# Session: separate standard and experiment reaction config

**Date:** 2026-10-28T15:19:50.207Z
**Status:** Grill phase complete

## Problem Statement

The standard and the experiment must be able to use different reaction configs (beam ion Z1/A1, profiled element Z2/A2, resonance E_R/Γ/σ). Today one global reaction config serves both, so a standard measured with one reaction cannot calibrate an experiment measured with another.

## Context & Constraints

- **Current behavior:** `stopping`, `broadening` and `yield_calc` read `reaction`/`resonance` from settings.json at import time into module constants; changes need an app restart. `std_calc` simulates the standard at a hardcoded 6550 keV and `load_std` computes its stopping at a hardcoded 6385 keV. The K factor (measured std yield / simulated std yield) is applied to the experiment simulation.
- **Pain point:** no way to give the standard and the experiment different reactions; reaction changes need a restart; the standard's energies are hardcoded to the ¹⁵N 6385 keV resonance.
- **Dependencies:** keep the save-file format JSON-compatible (Element/Layer/Target subclass dict); old simulation files and existing users' settings.json must still load; tests isolate settings via `HYPROC_CONFIG_DIR` and use `"SCS-25-Solid"`.
- **Tech stack:** Python, Tkinter, numpy/scipy, periodictable; pytest, ruff.

## Success Metrics

- A simulation with different standard and experiment reaction configs computes K with the standard's config and the excitation curve with the experiment's config.
- Changing either reaction config in the GUI takes effect on the next run without restarting the app.
- Both configs are saved in and restored from the simulation file; old files without them load with the settings.json defaults.
- An existing settings.json with the single `reaction`/`resonance` block is migrated once into separate standard and experiment defaults.
- The standard is simulated at E_R(std) + 165 keV, and its stopping at load is computed at E_R(std); no hardcoded 6550/6385 remains.
- `ruff check` and `pytest` pass, with new tests for physics with two configs, settings migration and old-file loading.

## Architecture & Approach

- Introduce a `ReactionConfig` (Z1, A1, Z2, A2, E_R, Gamma, Sigma), JSON-compatible, and pass it explicitly to the stopping, broadening and yield functions; remove the import-time module constants.
- `std_calc`/`load_std` use the standard's config (energy E_R(std) + 165 keV; stopping at E_R(std)); the profiled-element presence check uses the standard's Z2. Target simulation, profile and chi-square use the experiment's config.
- K is computed with the standard's config and applied to the experiment as is.
- New "Reactions…" dialog (menu entry) with Standard and Experiment columns, a "Copy experiment → standard" button and a "Save as default" button that writes both to settings.json.
- Simulation save file gains both reaction configs; on load, missing configs fall back silently to the settings.json defaults.
- settings.json defaults become separate standard and experiment blocks; `load_settings` auto-migrates the old single block into both and rewrites the file once. `default_settings.json` updated accordingly.

## Assumptions & Trade-offs

- The detection efficiency is assumed equal for both reactions: no efficiency-ratio correction on K (user's choice).
- The 165 keV offset above E_R(std) is kept fixed, assuming the standard is thick enough to contain the whole resonance.
- Not doing: editing reaction configs in the Settings dialog; per-layer or per-run reactions beyond the two configs.

## Open Questions

None.

## Notes

- Glossary terms added: Reaction config, Standard, Experiment, K factor.
- Leftover hardcoded test paths in `broadening.py`/`yield_calc.py` `__main__` blocks are out of scope.
