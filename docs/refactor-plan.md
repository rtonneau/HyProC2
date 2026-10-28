# Maintainability refactor

The requested design is a Tkinter-independent calculation module, shared by the
desktop application and a command-line interface. Existing equations, default
reactions, units and version-1 JSON files remain the compatibility baseline.

1. Characterize numerical results, energy selection and version-1 serialization
   before extracting the existing workflow. Baseline: Ruff clean, 69 tests pass
   on Windows / Python 3.13.11 in a fresh local `.venv`.
2. Put explicit session data in `models.py`, calculation requests/results and
   orchestration in `simulation.py`, and JSON/curve parsing in `file_io.py`.
   Keep physics independent of Tkinter; retain existing mathematical interfaces.
3. Make the window collect inputs on the Tk thread, run a snapshot in a worker,
   and apply completed results on the Tk thread. Group layout by visible section.
4. Add `hyproc-simulate` / `python -m hyproc.cli`, using the same calculation and
   version-1 file handling as the GUI. Exercise it through a subprocess.
5. Review settings, SRIM process isolation, packaging, install instructions,
   contributor documentation and AGENTS.md. Retain CLAUDE.md's AGENTS.md include.
6. Run lint, tests, wheel/sdist builds, installed-wheel checks and a GUI smoke
   check where available. Record scientific questions and unverified platforms.

Review focus: failed loads must not partially replace a session; failed runs
must restore controls and preserve results; workers must not call Tk; reaction
defaults must remain separate; diagnostics must keep their Broadplotter layout.
No commits, pushes, publishing or PR creation are part of this work.

## Implementation status

- Shared workflow, CLI, explicit Session, storage and target editor implemented.
- Numerical/serialization characterization passed before extraction.
- Independent review findings fixed: single-layer standard requirement, CLI
  subprocess failures, and Excel duplicate-header compatibility.
- Windows/Tk smoke passed for startup, actual threaded SCS calculation, control
  restoration, target editing and plot refresh.
- Source checks and all 112 installed-wheel tests pass. Package, CLI and desktop
  checks and their limits are recorded in `docs/verification.md`.
