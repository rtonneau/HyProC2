# Ticket 05: reactions-dialog

**Status:** ✅ Done

## Local Test Result

`.venv/Scripts/ruff check && .venv/Scripts/python -m pytest` → All checks passed!; 69 passed (parametrised validate_reaction cases).

## Review Notes

Implemented by a subagent (Sonnet, high effort); reviewed the diff and re-ran the verification here with no changes. Two-column dialog pre-filled from the app's configs; copy, save-as-default, OK, Cancel; pure validate_reaction (non-numeric, Z<1, unknown isotope, E_R/Γ/σ ≤ 0) with side-prefixed error messages; 'Reactions…' under the Settings menu; OK updates the app's configs so the next run uses them. The subagent checked the dialog headless; the manual hyproc → Run curve-shift check was not done.

## Blockers / Challenges

None.

## Commits

- 9d5232f feat: add Reactions dialog for standard and experiment configs (ticket 05)

## Time Spent

2m (ticket-start.js to ticket-complete.js)
