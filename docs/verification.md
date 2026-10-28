# Refactor verification

Local checks performed on Windows with Python 3.13.11. The development `.venv`
was created from the available Conda interpreter. Personal settings were not
used: tests and smoke checks supplied temporary `HYPROC_CONFIG_DIR` directories.

## Baseline and final checks

| Check | Result |
|---|---|
| Original `ruff check` | Passed |
| Original `python -m pytest` | 69 passed |
| Final `ruff check` | Passed |
| Final source `python -m pytest -q` | 112 passed |
| Fresh installed-wheel `python -m pytest` | 112 passed |
| `python -m pip check` | Passed in development and wheel environments |
| `python -m build` | Wheel and source distribution built |
| `python -m twine check dist/*` | Both distributions passed |
| `git diff --check` | Passed |

Characterization was added before extracting the workflow. It covers numerical
curves, reaction separation, segmentation, energy selection and version-1 saved
files. Additional tests cover input snapshots, failed-run isolation, atomic
JSON/settings writes, curve imports, CLI errors and the GUI job boundary.

The installed-wheel suite ran from outside the repository root. The imported
package path was verified to be in the fresh environment's `site-packages`.
Its resources included default settings, SCS parameters and the manual. The
installed `hyproc-simulate` executable calculated the README synthetic example,
saved six points and diagnostics, then reloaded/recalculated an identical curve.
The source distribution contains test setup, examples, contributor instructions
and architecture documentation.

## Desktop and external adapter checks

A real Tk window was created and withdrawn for a scripted smoke check. It
constructed/saved the Settings dialog using isolated settings, accepted the
Reactions dialog, duplicated/removed a target layer, ran an actual three-point
SCS calculation through the worker/polling path, restored controls, copied the
simulated curve, saved/reloaded a session and refreshed plots without callback
errors. This supplements the display-free job success/failure tests.

SRIM adapter tests use a fake process to check input/output conversion and
child-process working-directory isolation. No real SRIM executable was run.

## Limits

- Native file dialogs, every interactive editing sequence, and the complete
  Broadplotter workflow have not received manual acceptance testing.
- Linux/macOS and actual Python 3.10 execution were not checked locally. The
  configured Windows/Linux CI matrix has not been run for these uncommitted
  changes. Python 3.10 syntax parsing alone is not runtime validation.
- Characterization preserves historical calculations; it does not establish
  physical correctness. The known segmentation arithmetic, comparison statistic,
  diagnostic interpretation and data provenance need the review described in
  [scientific-review.md](scientific-review.md).

These results support the refactor, not a claim of publication readiness.
