<p align="center">
  <img src="docs/assets/hyproc-icon.svg" width="120" height="120" alt="HyProC: a resonance peak above layered targets">
</p>

<h1 align="center">HyProC</h1>

<p align="center">Depth profiling by resonant nuclear reaction analysis</p>

<p align="center">
  <a href="https://github.com/rtonneau/HyProC2/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/rtonneau/HyProC2/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="CI status"></a>
  <a href="#installation"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.10 or newer"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/version-0.2.0-14B8A6?style=flat-square" alt="Version 0.2.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-64748B?style=flat-square" alt="License: GPL-3.0-or-later"></a>
</p>

HyProC simulates excitation curves for **depth profiling by resonant nuclear reaction analysis (NRA)**.
Describe a layered target and a uniform reference standard, calculate gamma yield versus beam energy,
and compare with measured data. Use the Tkinter desktop application, command line, or Python API.

Original author: Louis Dupont. This is the [HyProC2 fork](https://github.com/rtonneau/HyProC2)
of [LouisDupont-2/HyProC](https://github.com/LouisDupont-2/HyProC).

## Installation

Requires Python 3.10 or newer. Tkinter is needed only for the desktop tools; the calculation module
and CLI work without it. On Linux, install your distribution's Tkinter package (often `python3-tk`)
for desktop use.

```powershell
git clone https://github.com/rtonneau/HyProC2.git
cd HyProC2
python -m venv .venv
.venv/Scripts/python -m pip install .
.venv/Scripts/hyproc
```

On macOS/Linux, use `.venv/bin/python` and `.venv/bin/hyproc` instead. Conda is also suitable:

```sh
conda create -n hyproc python=3.13 pip tk
conda activate hyproc
python -m pip install .
hyproc
```

## Desktop workflow

1. Load a target with **Target & Std → Load target**, or edit its layers and composition.
   Density is in TFU (10¹⁵ atoms/cm²); composition is in at. %.
2. Load/edit a standard containing the profiled element and enter its measured yield in Count/µC.
   Importing a standard in the GUI selects one layer and sets its thickness to 1500 TFU,
   preserving the original convention.
3. In **Settings → Reactions…**, configure the standard and experiment separately.
   `Z1/A1` means **beam ion**, `Z2/A2` means **profiled element**. Both defaults are proton beam,
   ¹⁵N profiled, resonance energy 6385 keV.
4. Enter the beam energy standard deviation in keV. Choose **SCS-25-Solid** for built-in stopping,
   or configure a Windows SRIM installation and choose **SRIM**. The initial GUI selection remains SRIM.
5. Optionally import an experimental curve, then **Run Calculation**. Normal runs reuse simulated
   energies first, then imported energies; otherwise a dialog asks for a range. The run menu also
   offers a custom range or loaded curve energies. The offset is subtracted for calculations and
   added back for display/export.
6. Save everything with **File → Save simulation**, or save just the target, standard, or simulated
   two-column curve. A successful calculation replaces the target with the stopping model's segmented layers.

Editing is disabled during calculation. A failed calculation reports its error and preserves the
previous target and curve. Wait for the run to finish before closing; active-run cancellation is not implemented.

Experimental imports support `.xlsx`, `.xls`, CSV and whitespace-separated text. Excel/CSV headers
are configured in Settings; text files use the first two columns as energy/yield and an optional
third as uncertainty. CSV files have a header row. Missing uncertainty columns become zero; rows
missing data are skipped and points are sorted by energy. Excel files with several matching sheets
or tables prompt for a selection.

`hyproc-broadplotter` opens saved broadening diagnostics. Enable **Save broadening data** and select
the resulting `Run N` folder in that viewer. **Track target changes** saves the segmented `_target.json`.

The bundled PDF is available through **Settings → Manual**. It is a legacy manual; this README
describes current reactions, saving and CLI behavior.

## Command line

After activation, use `hyproc-simulate`; without activation use `.venv/Scripts/python -m hyproc.cli`.
`--help` lists all options. Recalculate a desktop simulation using built-in stopping:

```sh
hyproc-simulate --input simulation.json --output result.json --stopping-model SCS-25-Solid
```

Start without the GUI using the included **synthetic examples**:

```sh
hyproc-simulate --target examples/target.json --standard examples/standard.json --standard-yield 100 --beam-width 1 --energies 6380 6405 5 --stopping-model SCS-25-Solid --output result.json --curve curve.txt
```

The examples exercise software behavior; they are not experimental validation or recommended physical
parameters. A CLI standard must have exactly one layer, and its saved thickness is retained. A new
calculation uses per-user default reactions. An input simulation retains its saved reactions.

`--energies MIN MAX STEP` specifies **displayed** energies in keV, including the upper endpoint.
Without it, saved simulated/imported energies are reused, then the saved range. Numeric overrides
include `--offset`, `--beam-width`, `--standard-yield` and `--straggling-model`. Add
`--diagnostics new-directory` to save the segmented target and broadening arrays. The directory must
not exist, preventing overwrite of an earlier run. GUI diagnostic flags are not implicitly enabled in CLI runs.

Success returns exit code 0; failure returns a nonzero code and a diagnostic on stderr. `--verbose`
adds diagnostics and tracebacks. Output simulation JSON can be opened by the desktop app.

## Settings and scientific conventions

Settings are created on first use from packaged defaults:

| OS | Location |
|---|---|
| Windows | `%APPDATA%/HyProC/settings.json` |
| macOS | `~/Library/Application Support/HyProC/settings.json` |
| Linux | `$XDG_CONFIG_HOME/HyProC/settings.json`, or `~/.config/HyProC/settings.json` |

Set `HYPROC_CONFIG_DIR` to isolate another configuration. Settings controls the SRIM installation,
diagnostic save directory and import headers. The Reactions dialog edits session reactions;
**Save as default** also persists them for future sessions. Older single-reaction settings migrate automatically.

SRIM is external, Windows-only software and is not bundled. Set its root directory so that
`SR Module/SRModule.exe` exists underneath it. Each invocation writes `SR.IN` and reads `Output`
in that directory. HyProC serializes calls in one process and gives the child its own working
directory. Separate HyProC processes must use separate SRIM installations to avoid filename collisions.

Built-in stopping uses SCS-25-Solid electronic stopping plus Ziegler universal nuclear stopping.
The parameter data records the reference J. Meersschaut et al., NIM B 553 (2024) 165406 and a
December 2025 submission. Stopping is in keV/TFU; beam and resonance energies/widths are in keV;
resonance cross section is in mbarn. The standard is calibrated at its own resonance energy + 165 keV.

The GUI's historical “chi-squared” is **mean squared yield residual**, without uncertainty weighting;
it is not reduced chi-squared. The implementation and label are retained for compatibility.
Read [scientific review notes](docs/scientific-review.md) before using results for publication:
characterization tests protect existing behavior but do not establish scientific validity.

## Development and architecture

```sh
python -m pip install -e ".[dev]"
python -m ruff check
python -m pytest
pre-commit install
```

Tests need neither a display nor real SRIM. See [CONTRIBUTING.md](CONTRIBUTING.md) for package and desktop checks.

`hyproc.simulation` is the shared application entry point. It accepts a `CalculationRequest` snapshot
and returns a `CalculationResult`; `apply_result` updates an explicit `Session`. The GUI and CLI
supply inputs and present errors/results. Neither models nor calculations import Tkinter.

| Module | Responsibility |
|---|---|
| `simulation.py` | Energy selection, calibration/calculation workflow, result application |
| `models.py` | JSON-compatible target/reaction objects and session state |
| `stopping.py`, `broadening.py`, `yield_calc.py` | Existing physics calculations |
| `file_io.py` | Version-1 JSON, target files, curve import/export |
| `config.py` | Per-user settings, migration, packaged resources |
| `cli.py` | Command-line input and output |
| `app.py`, `app_layout.py` | Desktop events, job lifetime, plotting and layout |
| `target_editor.py`, `dialogs/` | Target/composition editing and modal input |

See [architecture and Python API](docs/architecture.md) for dependencies, threading, compatibility
and an executable example.

## License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE). The repository license does not
establish redistribution permission for external software or third-party parameter data; provenance
review is listed in the publication notes.
