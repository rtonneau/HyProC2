# Ticket 03: app-uses-standard-and-experiment-configs

**Status:** ✅ Done

## Local Test Result

`ruff check && pytest && grep -nE "6550|6385" src/hyproc/app.py` → All checks passed!; 20 passed; grep prints nothing (exit 1).

## Review Notes

Implemented by a subagent (Opus, low effort). Checked: std_reaction/exp_reaction replace self.reaction/self.Z2/load_Z2; k_factor in yield_calc simulates the standard at E_R(std)+STD_ENERGY_OFFSET (165 keV); load_std stopping at E_R(std); standard Z2 checks use std_reaction; target path uses exp_reaction; settings dialog no longer touches parent.Z2; new test_k_factor_uses_standard_reaction. Change after review: removed an unused `noqa` re-import of STD_ENERGY_OFFSET in app.py (the constant lives in yield_calc). Manual GUI check not done.

## Blockers / Challenges

The K test needs a 200000 TFU standard so the whole resonance (165 keV above E_R) fits inside it.

## Commits

- 53afd36 feat: use separate standard and experiment reaction configs (ticket 03)

## Time Spent

3m (ticket-start.js to ticket-complete.js)
