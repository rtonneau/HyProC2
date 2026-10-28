# Ticket 01: reaction-config-and-settings

**Model:** medium
**Model (Jev):** sonnet-5.5 (confidence 0.2)
**Effort:** high

**Acceptance Criteria:**
- [ ] `models.ReactionConfig(dict)` exists, with keys `Z1, A1, Z2, A2` (int) and `E_R, Gamma, Sigma` (float). It is built as `ReactionConfig(data=None)` (defaults: proton beam, ¹⁵N, 6385.0 / 1.8 / 1.65), casts the values from strings, and serialises as plain JSON.
- [ ] `default_settings.json` replaces the `reaction`/`resonance` blocks with `"reactions": {"standard": {...}, "experiment": {...}}`.
- [ ] `config.load_settings()` migrates an old-shape file (it has `reaction`/`resonance` and no `reactions`) by copying the old block into both `standard` and `experiment`, dropping the old keys and rewriting the file once.
- [ ] `config.default_reactions() -> tuple[ReactionConfig, ReactionConfig]` returns `(standard, experiment)`, and `config.save_default_reactions(standard, experiment) -> None` writes them back.
- [ ] Tests: migrating an old file (both sides equal the old values, the file on disk is rewritten, a second load is a no-op), a round trip through `save_default_reactions`, and `ReactionConfig` casting `"7"` to `7`.

**Files to Touch:**
- `src/hyproc/models.py`
- `src/hyproc/config.py`
- `src/hyproc/data/default_settings.json`
- `tests/test_config.py`
- `tests/test_models.py`

**Verification Step:**

Run:
```bash
.venv/Scripts/ruff check && .venv/Scripts/python -m pytest
```

Expected:
ruff reports `All checks passed!`, and pytest passes every test, including the new migration, round-trip and casting tests.

**Notes:**

Physics modules still read `settings["reaction"]` at import time until ticket 02, so keep them working in between. In this ticket, have them read `default_reactions()[1]` (the experiment config) instead of the old keys. To avoid an import cycle, `config.py` imports `ReactionConfig` from `models.py` (which has no imports from `config`). Tests use `HYPROC_CONFIG_DIR` (see `tests/conftest.py`), and the migration tests write an old-shape settings.json into a `tmp_path`, monkeypatching that env var.
