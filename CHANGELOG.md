# Changelog

All notable changes to this project. Versions follow [semantic versioning](https://semver.org/).

## Unreleased

- Share a headless calculation workflow between the desktop application and new `hyproc-simulate` CLI.
- Separate session data, file handling and GUI responsibilities; share target/standard editor behavior.
- Snapshot calculation inputs, keep Tk calls on the main thread, and restore controls on failed runs.
- Preserve version-1 simulations, older settings, numerical reference behavior and diagnostic filenames.
- Fix simulated-to-experimental curve copying, optional Excel uncertainties and `.xls` engine support.
- Keep SRIM's working directory local to the child process; serialize fixed-filename exchanges.
- Add contributor/API documentation, synthetic CLI examples and package verification.
- Record existing scientific concerns requiring review before publication, without changing the models.

## 0.2.0 (2026-10-28)

- The standard and the experiment now each have their own reaction config (beam ion, profiled element, E_R, Γ, σ).
- The standard is simulated at its own E_R + 165 keV, so the K factor follows the standard's resonance.
- New Settings → Reactions… dialog to edit both configs, copy the experiment's config to the standard, and save them as defaults.
- Simulation files now save both reaction configs; older files load with the default configs.
- Existing settings files are migrated automatically to separate standard and experiment defaults.
