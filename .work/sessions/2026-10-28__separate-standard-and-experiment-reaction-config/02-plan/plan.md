# Implementation Plan

**Session:** separate standard and experiment reaction config
**Date:** 2026-10-28T15:30:45.131Z
**Estimated effort:** 1-2 days

## Strategy

Bottom-up. First the data model and settings (ReactionConfig, defaults, migration). Then the physics modules take the config explicitly, with app behaviour unchanged. Then the app separates the standard config from the experiment config. Then persistence in the simulation file, and finally the GUI dialog. After every ticket the app still runs and the tests pass.

## Tickets Overview

- **Ticket 1:** ReactionConfig model, separate standard/experiment defaults in settings.json, and auto-migration of the old block.
- **Ticket 2:** stopping/broadening/yield_calc take an explicit ReactionConfig, and the import-time constants are removed.
- **Ticket 3:** the app holds std_reaction and exp_reaction; the standard is simulated at E_R(std)+165 keV, and K comes from the standard's config.
- **Ticket 4:** both configs are saved and restored in the simulation file, with old files falling back to the defaults.
- **Ticket 5:** a Reactions… dialog with copy, save-as-default and validation.

## Sequencing Rationale

Each ticket uses the interface the previous one produced: 02 needs ReactionConfig and default_reactions from 01, 03 needs the parametrised physics from 02, and 04 and 05 need the app's std_reaction/exp_reaction from 03. The GUI comes last because it is the only part without automated tests.

## Risks & Mitigation

- **Risk:** the physics refactor silently changes results → **Mitigation:** ticket 02 keeps the existing physics tests green with the default config, and the app passes the same config it used before.
- **Risk:** migration corrupts an existing user's settings.json → **Mitigation:** it rewrites only when `reactions` is missing, keeps the other keys, and is tested on an old-shape file.
- **Risk:** import cycle between config and models, or between yield_calc and stopping/broadening → **Mitigation:** models imports nothing from config, and import order is checked in tickets 01 and 03.

## Assumptions

- The detection efficiency is the same for both reactions, so K is applied as is.
- A fixed 165 keV above E_R(std) covers the whole resonance in a thick standard.
- Tests run without a GUI and without SRIM ("SCS-25-Solid").
