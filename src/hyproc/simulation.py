"""Headless application workflow shared by the GUI and CLI.

Call ``run_simulation`` with a request captured from a session. It returns a
complete result without modifying the session. Call ``apply_result`` only after
success. No function in this module imports Tkinter or reads widgets.
"""

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

import numpy as np

from . import broadening, stopping, yield_calc
from .models import EnergyBounds, ReactionConfig, Session, Target
from .yield_calc import cH_make as depth_profile

__all__ = [
    "CalculationOptions",
    "CalculationRequest",
    "CalculationResult",
    "STOPPING_MODELS",
    "STRAGGLING_MODELS",
    "RunMode",
    "apply_result",
    "depth_profile",
    "generate_energies",
    "prepare_standard",
    "run_simulation",
    "select_energies",
    "use_simulated_curve_as_experiment",
    "validate_energy_bounds",
]

STOPPING_MODELS = ("SRIM", "SCS-25-Solid")
STRAGGLING_MODELS = ("Rud", "Rud corr", "Bohr")
RunMode = Literal["normal", "custom", "loaded_curve"]


@dataclass(frozen=True)
class CalculationOptions:
    """Validated numeric inputs. Beam width and offset are in keV."""

    standard_yield: float
    beam_width: float
    offset: float = 0.0
    stopping_model: str = "SRIM"
    straggling_model: str = "Rud corr"
    doppler: bool = True
    chi_bounds: EnergyBounds = (None, None)
    save_broadening: bool = False
    track_target: bool = False

    def __post_init__(self) -> None:
        if not all(np.isfinite(value) for value in (self.standard_yield, self.beam_width, self.offset)):
            raise ValueError("Standard yield, beam width and offset must be finite numbers.")
        if self.stopping_model not in STOPPING_MODELS or self.straggling_model not in STRAGGLING_MODELS:
            raise ValueError("Unsupported stopping or straggling model.")
        validate_energy_bounds(*self.chi_bounds)

    @classmethod
    def from_mapping(cls, values: dict) -> "CalculationOptions":
        """Convert version-1 entry strings and flags at the application boundary."""
        try:
            offset = float(values.get("offset", 0))
        except ValueError:
            offset = 0.0  # The desktop historically treats an empty offset as zero.
        return cls(
            standard_yield=float(values["standard_yield"]),
            beam_width=float(values["beam_width"]),
            offset=offset,
            stopping_model=values.get("stopping_model", "SRIM"),
            straggling_model=values.get("straggling_model", "Rud corr"),
            doppler=values.get("doppler", True),
            chi_bounds=tuple(
                float(values[key]) if str(values.get(key, "")).strip() else None
                for key in ("chi_energy_min", "chi_energy_max")
            ),
            save_broadening=values.get("save_broadening_data", False),
            track_target=values.get("track_target_changes", False),
        )


@dataclass(frozen=True)
class CalculationRequest:
    target: Target
    standard: Target
    standard_reaction: ReactionConfig
    experiment_reaction: ReactionConfig
    energies: tuple[float, ...]
    options: CalculationOptions
    experimental_energy: tuple[float, ...] = ()
    experimental_yield: tuple[float, ...] = ()
    output_directory: Path | None = None

    @classmethod
    def from_session(
        cls,
        session: Session,
        energies: Sequence[float],
        options: CalculationOptions,
        output_directory: str | Path | None = None,
    ) -> "CalculationRequest":
        """Snapshot inputs before handing work to another thread."""
        return cls(
            deepcopy(session.target),
            deepcopy(session.standard),
            ReactionConfig(session.standard_reaction),
            ReactionConfig(session.experiment_reaction),
            tuple(energies),
            options,
            tuple(session.experimental_energy),
            tuple(session.experimental_yield),
            Path(output_directory) if output_directory is not None else None,
        )


@dataclass(frozen=True)
class CalculationResult:
    target: Target
    standard: Target
    energies: list[float]
    yields: list[float]
    calibration_factor: float
    chi_squared: float
    chi_bounds: EnergyBounds
    layers_segmented: bool


def validate_energy_bounds(minimum: float | None, maximum: float | None) -> EnergyBounds:
    if any(value is not None and not np.isfinite(value) for value in (minimum, maximum)):
        raise ValueError("Energy bounds must be finite numbers.")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Minimum energy must be less than or equal to maximum energy.")
    return minimum, maximum


def generate_energies(minimum: float, maximum: float, step: float) -> list[float]:
    """Generate displayed energies, always including the upper endpoint."""
    validate_energy_bounds(minimum, maximum)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("Energy step size must be finite and positive.")
    interval_count = (maximum - minimum) / step
    if not np.isfinite(interval_count):
        raise ValueError("The energy range and step size produce too many calculation points.")
    full_steps = int(np.floor(interval_count))
    energies = [minimum + index * step for index in range(full_steps + 1)]
    if np.isclose(energies[-1], maximum, rtol=1e-12, atol=1e-12):
        energies[-1] = maximum
    else:
        energies.append(maximum)
    return energies


def select_energies(
    session: Session, offset: float, mode: RunMode = "normal", custom_energies: list[float] | None = None
) -> list[float] | None:
    """Select the grid and subtract the display offset exactly once.

    Normal mode prefers a previous simulation, then imported energies. None
    means the caller must supply a range. Custom energies are displayed values.
    """
    if mode == "custom":
        source = custom_energies
    elif mode == "loaded_curve":
        if not session.experimental_energy:
            raise ValueError("No loaded curve energies are available.")
        source = session.experimental_energy
    elif mode == "normal":
        source = session.simulated_energy or session.experimental_energy
    else:
        raise ValueError(f"Unknown calculation mode: {mode}")
    return [energy - offset for energy in source] if source else None


def run_simulation(request: CalculationRequest) -> CalculationResult:
    """Calibrate, segment the target, broaden and integrate at each beam energy.

    The legacy physics routines mutate their targets. Private copies isolate
    those mutations, including on failure. The returned target must replace the
    caller's target because stopping can split layers. Exceptions propagate to
    the GUI/CLI boundary. Diagnostic files may remain after a failed run.
    """
    options = request.options
    if not request.energies or not all(np.isfinite(energy) for energy in request.energies):
        raise ValueError("A calculation needs a non-empty list of finite energies.")
    target, standard = deepcopy(request.target), deepcopy(request.standard)
    if len(standard["layers"]) != 1:
        raise ValueError("A standard must have exactly one layer. Select a single standard layer before calculating.")
    profiled_fraction = standard["layers"][0].find_element(request.standard_reaction["Z2"])
    if not profiled_fraction:
        raise ValueError(f"The standard contains no profiled element (Z={request.standard_reaction['Z2']}).")
    standard["layers"][0].normalize()
    factor = yield_calc.k_factor(
        standard,
        options.standard_yield,
        request.standard_reaction,
        options.beam_width,
        options.doppler,
        options.straggling_model,
        options.stopping_model,
    )
    target.normalize_all_layers()
    original_layer_count = len(target["layers"])
    target = stopping.assign_stopping(
        target, max(request.energies), request.experiment_reaction, options.stopping_model
    )

    output_directory = request.output_directory
    if options.save_broadening or options.track_target:
        if output_directory is None:
            raise ValueError("An output directory is required when saving run diagnostics.")
        output_directory.mkdir(parents=True, exist_ok=False)
        if options.track_target:
            # Local import avoids making file handling a requirement for callers
            # that only use energy-selection helpers.
            from .file_io import save_target

            save_target(output_directory / "_target.json", target)

    energies, yields = [], []
    for index, energy in enumerate(request.energies):
        point_directory = None
        if options.save_broadening:
            point_directory = output_directory / f"datapoint{index}"
            point_directory.mkdir()
            (point_directory / f"_E={energy:.1f}kev.dat").touch()
        _, depth, profile, _, _ = broadening.broadening(
            energy,
            target,
            options.beam_width,
            request.experiment_reaction,
            options.doppler,
            options.straggling_model,
            options.save_broadening,
            str(point_directory) if point_directory is not None else None,
        )
        yields.append(factor * yield_calc.compute_yield(target, request.experiment_reaction, depth, profile))
        energies.append(energy + options.offset)

    minimum, maximum = options.chi_bounds
    selected = [
        index
        for index, energy in enumerate(request.experimental_energy)
        if (minimum is None or energy >= minimum) and (maximum is None or energy <= maximum)
    ]
    chi_squared = -1.0
    if request.experimental_yield:
        chi_squared = yield_calc.chi_squared_test(
            [request.experimental_energy[index] for index in selected],
            [request.experimental_yield[index] for index in selected],
            energies,
            yields,
        )
    return CalculationResult(
        target,
        standard,
        energies,
        yields,
        factor,
        round(chi_squared, 2),
        options.chi_bounds,
        len(target["layers"]) != original_layer_count,
    )


def apply_result(session: Session, result: CalculationResult) -> None:
    """Publish a successful calculation as one session update."""
    session.target = result.target
    session.standard = result.standard
    session.simulated_energy = result.energies
    session.simulated_yield = result.yields
    session.chi_squared.append(result.chi_squared)
    session.chi_bounds.append(result.chi_bounds)


def use_simulated_curve_as_experiment(session: Session) -> None:
    """Copy a calculated curve for comparison, with zero measurement errors."""
    if not session.simulated_yield:
        raise ValueError("No simulation curve data to load as experimental curve.")
    session.experimental_energy = list(session.simulated_energy)
    session.experimental_yield = list(session.simulated_yield)
    session.experimental_error = [0.0] * len(session.simulated_energy)


def prepare_standard(target: Target, layer_index: int, reaction: ReactionConfig, stopping_model: str) -> Target:
    """Preserve the desktop's single-layer, 1500-TFU standard import convention."""
    standard = deepcopy(target)
    standard["layers"] = [standard["layers"][layer_index]]
    layer = standard["layers"][0]
    layer["areal_density"] = 1500.0
    if not layer.find_element(reaction["Z2"]):
        raise ValueError(f"The standard contains no profiled element (Z={reaction['Z2']}).")
    layer["stopping"] = stopping.calc_stopping_cross_section(layer, reaction["E_R"], reaction, stopping_model)
    return standard
