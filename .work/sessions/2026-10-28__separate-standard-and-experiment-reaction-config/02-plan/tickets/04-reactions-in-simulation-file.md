# Ticket 04: reactions-in-simulation-file

**Model:** medium
**Model (Jev):** sonnet-5.5 (confidence 0.41)
**Effort:** high

**Acceptance Criteria:**
- [ ] The simulation save file gains `"reactions": {"standard": {...}, "experiment": {...}}`.
- [ ] Loading a file restores both into `std_reaction`/`exp_reaction`. A file without `reactions` (older format) silently falls back to `config.default_reactions()`. A partially specified config gets the missing keys filled from the defaults.
- [ ] Parsing lives in a pure function `models.reactions_from_sim(data: dict, defaults: tuple[ReactionConfig, ReactionConfig]) -> tuple[ReactionConfig, ReactionConfig]`.
- [ ] Tests: a new-format round trip, an old file without `reactions` getting the defaults, and malformed values (`"Z1": "abc"`) raising `ValueError`, which the existing load error dialog surfaces.

**Files to Touch:**
- `src/hyproc/models.py`
- `src/hyproc/app.py`
- `tests/test_models.py`

**Verification Step:**

Run:
```bash
.venv/Scripts/ruff check && .venv/Scripts/python -m pytest
```

Expected:
ruff and pytest pass, including the three new `reactions_from_sim` tests.

**Notes:**

Save happens around `app.py:785-805` and load around `app.py:840-1005`. Follow the existing validation style there, raising `ValueError` inside the try block.
