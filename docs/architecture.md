# Architecture and extension guide

## Dependencies

```text
GUI (app, app_layout, target_editor, dialogs)    CLI
                  |                            |
                  +------ simulation ----------+
                         |          |
                      models     physics
                                   |
                                config

GUI/CLI -- file_io -- models
             |
       simulation model choices
```

`simulation.py` is the single calculation workflow. Physics modules do not know
about sessions, controls, CLI arguments or dialogs. `file_io` owns the on-disk
schema and curve decoding; it uses simulation's supported-model constants.
The workflow imports `file_io` locally only when writing run diagnostics.
`config` owns environment-dependent paths and settings migration.

Dictionary domain objects retain their JSON keys. `Session` is an in-memory
dataclass, serialized explicitly so internal names can improve without renaming
saved-file keys. Raw options remain strings in version-1 files, including blank
entries in sessions not yet run. `CalculationOptions` converts them at run time.

## Start-to-result path

1. `hyproc` / `python -m hyproc` call `app.main`; `hyproc-simulate` /
   `python -m hyproc.cli` call `cli.main`.
2. Load standard/experiment reactions with `config.default_reactions`.
   Saved reactions take precedence, with defaults filling older or partial files.
3. Choose energies with `select_energies` and/or `generate_energies`. Physical
   incident energies go into a request; subtract the display offset once.
4. `CalculationRequest.from_session` snapshots mutable input data. The workflow
   copies targets again because historical physics routines mutate their inputs.
   This protects both the session and a reusable request.
5. `run_simulation` normalizes the standard, calculates its calibration factor,
   normalizes/segments the target, broadens/integrates each energy, and calculates
   the existing comparison metric within the chosen bounds.
6. `apply_result` replaces the target and standard, publishes the curve, and
   appends comparison history. Returned energies already include the offset.

The GUI reads widgets on the Tk thread, disables editing, and submits the
request to a single-worker executor. A main-thread `after` poll retrieves the
result. Workers never call Tk, including `after` or message boxes. Failed runs
preserve previous scientific state; partial diagnostic files can remain.
Controls are restored in `finally`. Closing waits for work to finish;
calculation cancellation is not implemented.

`TargetEditor` owns selection indices and refreshes from a target provider, so
replacement targets do not leave stale references. The target and standard
share element handlers. `app_layout` builds visible sections in order; callbacks
on the window handle files and calculation actions. Plot preferences stay in the GUI.

## Python example

Run from the repository after installation:

```python
from hyproc import config, file_io, simulation
from hyproc.models import Session

standard_reaction, experiment_reaction = config.default_reactions()
session = Session(
    target=file_io.load_target("examples/target.json"),
    standard=file_io.load_target("examples/standard.json"),
    standard_reaction=standard_reaction,
    experiment_reaction=experiment_reaction,
)
options = simulation.CalculationOptions(
    standard_yield=100.0, beam_width=1.0, stopping_model="SCS-25-Solid",
)
displayed = simulation.generate_energies(6380.0, 6405.0, 5.0)
energies = simulation.select_energies(session, options.offset, "custom", displayed)
request = simulation.CalculationRequest.from_session(session, energies, options)
result = simulation.run_simulation(request)
simulation.apply_result(session, result)
file_io.save_curve("curve.txt", result.energies, result.yields)
```

These synthetic inputs demonstrate software use, not scientific validation.
`file_io.save_simulation(path, session, raw_options)` saves a desktop session;
`raw_options` follows the existing string/boolean keys.

## Compatibility

- Simulation JSON retains `format: "HyProC simulation"`, `version: 1`, and the
  original target, standard, reactions, curves, history, options and range keys.
- Missing reaction sides/keys use the corresponding per-user default. Old
  `energy_range.points` converts to a step. Missing display preferences and
  stopping model keep their historical defaults.
- Historical energy-only experimental curves remain usable calculation grids.
- Target, layer and element extension fields survive round trips. Malformed
  targets are rejected before replacing session state. Parsing does not normalize.
- Calculations require a single-layer standard, avoiding stale stopping values
  on extra layers. The GUI importer offers selection; CLI files must have one layer.
- JSON/settings saves use temporary siblings and replace only after successful
  writing. File failures propagate to the GUI/CLI error boundary.
- Diagnostics retain `Run N/_target.json` and
  `Run N/datapointN/{_E=...kev.dat, Beam.txt, ...}` for Broadplotter.
- Legacy physics names such as `cH_make` remain available to Python callers.
  `simulation.depth_profile` exposes that function through the application entry
  point. Renamed GUI internals are not a supported scripting interface.

## Extension points

Start workflow changes in `simulation.py`, testing requests/results. Obtain
scientific approval for equation changes and add independent references rather
than merely updating snapshots. New stopping models need a `STOPPING_MODELS`
entry, dispatch in `stopping` and reaction-specific tests; GUI and CLI share the list.

Keep version-1 reads when extending saved files, or introduce an explicit
format version with migration fixtures. GUI actions should pass domain data to
the workflow. Keep GUI imports out of models, configuration, storage and calculations.
