# Changelog

All notable changes to this project. Versions follow [semantic versioning](https://semver.org/).

## 0.2.0 (2026-10-28)

- The standard and the experiment now each have their own reaction config (beam ion, profiled element, E_R, Γ, σ).
- The standard is simulated at its own E_R + 165 keV, so the K factor follows the standard's resonance.
- New Settings → Reactions… dialog to edit both configs, copy the experiment's config to the standard, and save them as defaults.
- Simulation files now save both reaction configs; older files load with the default configs.
- Existing settings files are migrated automatically to separate standard and experiment defaults.
