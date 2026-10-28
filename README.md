# HyProC

HyProC is a desktop application for **depth profiling by resonant nuclear reaction analysis (NRA)**.
It simulates the excitation curve (gamma yield vs. beam energy) of a multi-layer target and compares it
with a measured curve, so that the depth profile of the probed element can be adjusted until the
simulation matches the experiment.

Author: Louis Dupont.

## Features

- Multi-layer target editor (areal density in TFU, composition in at. %), plus a reference standard
  used to normalise the yield.
- Stopping cross sections from either:
  - **SRIM** (external *SR Module*, Windows only), or
  - **SCS-25-Solid**: built-in electronic stopping parametrisation
    (J. Meersschaut et al., NIM B 553 (2024) 165406) plus Ziegler universal nuclear stopping.
- Energy broadening from the resonance cross section (Lorentzian), beam energy spread, Doppler
  broadening and energy straggling (several straggling models).
- Import of experimental excitation curves from Excel, CSV or text files.
- χ² comparison between simulated and experimental curves over a selectable energy window.
- Save/load of targets, standards and full simulations (JSON).
- `hyproc-broadplotter`: a small viewer for the broadening data saved during a run.

The reaction (incident ion `Z1`/`A1`, profiled element `Z2`/`A2`) and resonance parameters
(`E_R`, `Gamma`, `Sigma`) are read from the settings file.

## Installation

Requires Python 3.10 or newer (with Tkinter, included in the standard Windows/macOS installers).

```bash
git clone https://github.com/LouisDupont-2/HyProC.git
cd HyProC
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` elsewhere
pip install .
```

## Usage

```bash
hyproc                 # main application (or: python -m hyproc)
hyproc-broadplotter    # broadening data viewer
```

The user manual is available from the application menu (**Settings → Manual**) and in
`src/hyproc/data/HyProC_Manual.pdf`.

### Settings

On first launch, a settings file is created from the packaged defaults
(`src/hyproc/data/default_settings.json`) in the per-user configuration directory:

| OS      | Location                                             |
|---------|------------------------------------------------------|
| Windows | `%APPDATA%\HyProC\settings.json`                     |
| macOS   | `~/Library/Application Support/HyProC/settings.json` |
| Linux   | `~/.config/HyProC/settings.json`                     |

Set the `HYPROC_CONFIG_DIR` environment variable to use another directory.

The SRIM path, the data save path and the column headers used to import experimental curves can be
edited from the **Settings** dialog. The reaction and resonance parameters are edited directly in the
file; restart the application after changing them.

To use the SRIM stopping model, point the SRIM path to a SRIM installation containing the
`SR Module` folder.

## Development

```bash
pip install -e ".[dev]"
pre-commit install
ruff check
pytest
```

Project layout:

```
src/hyproc/
  app.py            main window and application logic
  app_layout.py     widget layout of the main window
  models.py         Element / Layer / Target data model
  stopping.py       stopping cross sections (SRIM, SCS-25-Solid) and layer segmentation
  broadening.py     energy broadening and energy-to-depth conversion
  yield_calc.py     yield integration, depth profile and χ² test
  config.py         user settings and packaged data files
  broadplotter.py   broadening data viewer
  dialogs/          energy range, import and settings dialogs
  data/             default settings, SCS-25-Solid parameters, user manual
tests/              unit tests (no GUI or SRIM required)
```

## License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
