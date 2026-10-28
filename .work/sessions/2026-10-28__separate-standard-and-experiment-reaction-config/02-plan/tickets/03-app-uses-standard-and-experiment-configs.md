# Ticket 03: app-uses-standard-and-experiment-configs

**Model:** heavy
**Model (Jev):** opus-5.5 (confidence 0.21)
**Effort:** low

**Acceptance Criteria:**
- [ ] `GUI_App` holds `self.std_reaction` and `self.exp_reaction` (from `config.default_reactions()`), replacing `self.reaction` and `self.Z2`/`load_Z2`.
- [ ] `std_calc` simulates the standard at `std_reaction["E_R"] + STD_ENERGY_OFFSET` (module constant `STD_ENERGY_OFFSET = 165.0` keV) with `std_reaction` for stopping, broadening and yield. `load_std` computes stopping at `std_reaction["E_R"]`. The literals 6550 and 6385 are gone from `app.py`.
- [ ] The "No <element> in the standard" checks use `std_reaction["Z2"]`. Target stopping, broadening, yield, `cH_make` and the profile window use `exp_reaction`.
- [ ] K is computed with `std_reaction` and applied to the experiment unchanged.
- [ ] `dialogs/settings.py` no longer pokes `parent.Z2`.
- [ ] Test: a pure-function test (no GUI) shows that a standard and a target using different configs give K computed from the standard's config. Extract the K computation into a testable function `yield_calc.k_factor(std_target, std_yield, reaction, beam_width, doppler, straggling_model, stopping_model) -> float` if needed.

**Files to Touch:**
- `src/hyproc/app.py`
- `src/hyproc/yield_calc.py`
- `src/hyproc/dialogs/settings.py`
- `tests/test_physics.py`

**Verification Step:**

Run:
```bash
.venv/Scripts/ruff check && .venv/Scripts/python -m pytest && grep -nE "6550|6385" src/hyproc/app.py
```

Expected:
ruff and pytest pass, and the grep prints nothing and exits 1.

**Notes:**

Use `"SCS-25-Solid"` in tests. If `k_factor` lives in `yield_calc`, it imports `stopping` and `broadening`; check that this creates no import cycle. Manual check: run `hyproc`, load a standard, then run a simulation with the default settings. The curve should match the one from before.
