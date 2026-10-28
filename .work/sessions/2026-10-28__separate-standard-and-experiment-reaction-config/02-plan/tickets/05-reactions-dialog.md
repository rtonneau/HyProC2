# Ticket 05: reactions-dialog

**Model:** medium
**Model (Jev):** sonnet-5.5 (confidence 0.24)
**Effort:** high

**Acceptance Criteria:**
- [ ] New `dialogs/reactions.py`: a `ReactionsDialog(tk.Toplevel)` with two columns, Standard and Experiment. Each has entries for Z1, A1, Z2, A2, E_R (keV), Γ (keV) and σ (mbarn), pre-filled from the app's `std_reaction`/`exp_reaction`.
- [ ] Buttons: "Copy experiment → standard", "Save as default" (validates, then `config.save_default_reactions`), "OK" (validates, then sets the app's two configs) and "Cancel".
- [ ] Validation is a pure function `validate_reaction(values: dict[str, str]) -> ReactionConfig`. It rejects non-numeric values, Z < 1, an isotope unknown to `periodictable` (`elements[Z][A]` missing), and E_R/Γ/σ ≤ 0. Errors are shown with `messagebox.showerror` naming the field and the side.
- [ ] A "Reactions…" entry is added to the menu (`app_layout.py`), and the change applies on the next run without a restart.
- [ ] Tests: `validate_reaction` accepts the defaults and rejects each invalid case (no GUI).

**Files to Touch:**
- `src/hyproc/dialogs/reactions.py`
- `src/hyproc/app.py`
- `src/hyproc/app_layout.py`
- `tests/test_reactions_dialog.py`

**Verification Step:**

Run:
```bash
.venv/Scripts/ruff check && .venv/Scripts/python -m pytest
```

Expected:
ruff and pytest pass, including the `validate_reaction` tests. Manual check: `hyproc` → Reactions… → set the experiment E_R to 6400 → OK → Run. The curve shifts and no restart is needed.

**Notes:**

Mirror `dialogs/settings.py` for the layout, positioning and `grab_set`. Keep `validate_reaction` importable without creating a Tk root.
