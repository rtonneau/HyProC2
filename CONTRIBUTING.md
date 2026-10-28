# Contributing

Read [README.md](README.md) for installation/units and
[docs/architecture.md](docs/architecture.md) for calculation/file contracts.
Use Python 3.10+ in a dedicated virtual or Conda environment.

```sh
python -m pip install -e ".[dev]"
python -m ruff check
python -m pytest
```

Use `python -m ruff format src tests` when changing Python files. CI checks
Windows/Linux with Python 3.10/3.13. Tests isolate settings through
`HYPROC_CONFIG_DIR` before package imports. Default tests use neither a display
nor real SRIM/personal settings.

Snapshots in `tests/test_characterization.py` were recorded before refactoring.
Changing them needs explanation and, for model changes, scientific approval
with independent validation. Preserve legacy file fixtures. CLI subprocess
tests block Tkinter imports to enforce the GUI dependency boundary.

## Packaging

```sh
python -m build
python -m twine check dist/*
```

Install the generated wheel in a fresh environment. Run `python -m pip check`,
`hyproc-simulate --help` and the README example. Confirm `config.data_path`
resolves defaults, SCS parameters and manual outside the repository. An editable
install alone is insufficient. CI builds wheel/sdist and tests the installed wheel.

## Desktop acceptance

Use a temporary `HYPROC_CONFIG_DIR` and a display with Tkinter:

1. Launch `hyproc`; edit/add/duplicate/reorder/remove layers and elements.
   Verify independent target/standard selections and scroll preservation.
2. Configure standard, beam width and SCS-25-Solid. Exercise normal/custom/loaded
   energy runs with an offset. Check controls restore after success and failure.
3. Import text/CSV/Excel (multiple sheets/tables, absent uncertainties), copy a
   simulated curve to experimental data, remove curves and rescale plots.
4. Save/load targets, standards and simulations, including older files. Cancel
   each dialog; try malformed JSON and unwritable destinations.
5. Edit reactions, save defaults, restart, and verify persistence. Check the
   profiled-element plot's title and units.
6. Save diagnostics and open the Run folder in `hyproc-broadplotter`.
7. With real Windows SRIM, calculate and verify unchanged application cwd.

Headless GUI-job tests cover success/failure transitions, not every native event.
Record actual interactive checks and OS versions. Publication requirements are
tracked in [docs/scientific-review.md](docs/scientific-review.md).
