# Ticket 02: physics-takes-reaction-config

**Model:** heavy
**Model (Jev):** opus-5.5 (confidence 0.42)
**Effort:** low

**Acceptance Criteria:**
- [ ] `stopping`, `broadening` and `yield_calc` no longer read settings at import time: no module-level `Z1/A1/Z2/A2/M1/M2/E_R/Gamma/sigma_R/energy_res`.
- [ ] Every public function that used those constants takes a `reaction: ReactionConfig` parameter. That covers `stopping.write_input`, `calc_stopping_cross_section`, `assign_stopping`, `broadening.broadening` (and its helpers), and `yield_calc.cH_make`, `compute_yield`. Masses are derived from the config (`periodictable.elements[Z][A].mass`).
- [ ] `app.py` builds `self.reaction = config.default_reactions()[1]` at startup and passes it to every `mod2`/`mod3`/`mod4` call. Behaviour with default settings is unchanged.
- [ ] Tests: the existing physics tests pass a `ReactionConfig()`. A new test shows that two configs differing only in `E_R` give broadening outputs shifted accordingly, and that `cH_make` with `Z2=1` vs `Z2=7` picks the matching element's percentage.
- [ ] `tests/conftest.py` comment about import-time settings is updated.

**Files to Touch:**
- `src/hyproc/stopping.py`
- `src/hyproc/broadening.py`
- `src/hyproc/yield_calc.py`
- `src/hyproc/app.py`
- `tests/test_physics.py`
- `tests/conftest.py`

**Verification Step:**

Run:
```bash
.venv/Scripts/ruff check && .venv/Scripts/python -m pytest && grep -nE "^(Z1|A1|Z2|A2|M1|M2|E_R|Gamma|sigma_R|energy_res|settings) *=" src/hyproc/stopping.py src/hyproc/broadening.py src/hyproc/yield_calc.py
```

Expected:
ruff and pytest pass, and the grep prints nothing and exits 1.

**Notes:**

Most of the work is in this ticket. Make the parameter keyword-friendly and place it consistently (after the existing positional args, before optional flags, e.g. `broadening(E_in, target, delta_B, reaction, Doppler=True, ...)`). The `__main__` demo blocks with hardcoded paths in `broadening.py`/`yield_calc.py` can simply construct `ReactionConfig()`. Leave them otherwise as they are. Update the CLAUDE.md gotcha about import-time constants.
