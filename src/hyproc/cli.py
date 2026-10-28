"""Command-line adapter for the same workflow used by the desktop window."""

import argparse
import contextlib
import logging
import sys
from pathlib import Path

from . import config, file_io, simulation
from .models import Session


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Simulate a resonant-NRA excitation curve without opening the GUI.")
    source = result.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Saved HyProC version-1 simulation")
    source.add_argument("--target", type=Path, help="Target JSON (requires --standard and --energies)")
    result.add_argument("--standard", type=Path, help="Standard target JSON for a new simulation")
    result.add_argument("--output", type=Path, required=True, help="Output simulation JSON")
    result.add_argument("--curve", type=Path, help="Also export the simulated two-column text curve")
    result.add_argument(
        "--energies",
        type=float,
        nargs=3,
        metavar=("MIN", "MAX", "STEP"),
        help="Displayed energy range in keV; includes MAX",
    )
    result.add_argument("--stopping-model", choices=simulation.STOPPING_MODELS)
    result.add_argument("--straggling-model", choices=simulation.STRAGGLING_MODELS)
    result.add_argument("--standard-yield", type=float)
    result.add_argument("--beam-width", type=float, help="Beam standard deviation in keV")
    result.add_argument("--offset", type=float, help="Display energy offset in keV")
    result.add_argument("--diagnostics", type=Path, help="New directory for broadening data and the segmented target")
    result.add_argument("--verbose", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if arguments.verbose else logging.WARNING)
    try:
        defaults = config.default_reactions()
        if arguments.input:
            session, values = file_io.load_simulation(arguments.input, defaults)
        else:
            if arguments.standard is None or arguments.energies is None:
                raise ValueError("--target requires --standard and --energies.")
            session = Session(
                target=file_io.load_target(arguments.target),
                standard=file_io.load_target(arguments.standard),
                standard_reaction=defaults[0],
                experiment_reaction=defaults[1],
            )
            values = {
                "standard_yield": "",
                "beam_width": "",
                "offset": "0",
                "stopping_model": "SRIM",
                "straggling_model": "Rud corr",
                "doppler": True,
                "save_broadening_data": False,
                "track_target_changes": False,
            }
        for key in ("standard_yield", "beam_width", "offset", "stopping_model", "straggling_model"):
            value = getattr(arguments, key)
            if value is not None:
                values[key] = str(value)
        if not values["standard_yield"] or not values["beam_width"]:
            raise ValueError("Provide --standard-yield and --beam-width, or save them in the input simulation.")
        # Saving diagnostic files is explicit in a command-line run; never reuse
        # a GUI session's location or silently overwrite an earlier run folder.
        values["save_broadening_data"] = values["track_target_changes"] = arguments.diagnostics is not None
        options = simulation.CalculationOptions.from_mapping(values)
        if arguments.energies:
            session.energy_min, session.energy_max, session.energy_step = arguments.energies
            displayed = simulation.generate_energies(*arguments.energies)
            energies = simulation.select_energies(session, options.offset, "custom", displayed)
        else:
            energies = simulation.select_energies(session, options.offset)
            if energies is None:
                if session.energy_min is None or session.energy_max is None:
                    raise ValueError("No saved curve energies; provide --energies MIN MAX STEP.")
                displayed = simulation.generate_energies(session.energy_min, session.energy_max, session.energy_step)
                energies = simulation.select_energies(session, options.offset, "custom", displayed)
        request = simulation.CalculationRequest.from_session(session, energies, options, arguments.diagnostics)
        with contextlib.redirect_stdout(sys.stderr):
            result = simulation.run_simulation(request)
        simulation.apply_result(session, result)
        file_io.save_simulation(arguments.output, session, values)
        if arguments.curve:
            file_io.save_curve(arguments.curve, session.simulated_energy, session.simulated_yield)
    except Exception as error:
        # A CLI invocation is the outer error boundary, just like the GUI's job
        # completion handler. --verbose retains the traceback for diagnosis.
        if arguments.verbose:
            logging.getLogger(__name__).exception("Simulation failed")
        print(f"hyproc-simulate: {error}", file=sys.stderr)
        return 1
    print(f"Saved {len(result.energies)} points to {arguments.output}; K={result.calibration_factor:.8g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
