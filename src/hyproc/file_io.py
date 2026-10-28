"""Version-1 JSON persistence and experimental curve import, without Tkinter.

Decode and validate a complete document before replacing any application state.
Unknown target/layer/element fields survive round trips for existing user files.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .models import Layer, ReactionConfig, Session, Target, reactions_from_sim
from .simulation import STOPPING_MODELS, STRAGGLING_MODELS


def read_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: str | Path, data: dict) -> None:
    """Replace a JSON file only after encoding and writing have succeeded."""
    text = json.dumps(data, indent=4)
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def target_from_data(data: dict) -> Target:
    """Rebuild domain objects while retaining JSON-compatible extension fields."""
    if not isinstance(data, dict) or not isinstance(data.get("layers"), list) or not data["layers"]:
        raise ValueError("A target must contain a non-empty list of layers.")
    target = Target()
    target.update(data)
    layers = []
    for index, raw in enumerate(data["layers"], start=1):
        if not isinstance(raw, dict) or not isinstance(raw.get("elements"), list) or not raw["elements"]:
            raise ValueError(f"Layer {index} must contain a non-empty list of elements.")
        density = raw.get("areal_density")
        if (
            isinstance(density, bool)
            or not isinstance(density, (int, float))
            or not np.isfinite(density)
            or density <= 0
        ):
            raise ValueError(f"Layer {index} areal density must be a finite positive number in TFU.")
        for element in raw["elements"]:
            if not isinstance(element, dict):
                raise ValueError(f"Layer {index} elements must be JSON objects.")
            z, fraction = element.get("Z"), element.get("percent_at")
            if isinstance(z, bool) or not isinstance(z, int) or not 1 <= z <= 118:
                raise ValueError(f"Layer {index} has an invalid atomic number.")
            if (
                isinstance(fraction, bool)
                or not isinstance(fraction, (int, float))
                or not np.isfinite(fraction)
                or fraction < 0
            ):
                raise ValueError(f"Layer {index} has an invalid atomic percentage.")
        layer = Layer(data=raw)
        layer.setdefault("stopping", 0.01)
        layers.append(layer)
    target["layers"] = layers
    return target


def load_target(path: str | Path) -> Target:
    return target_from_data(read_json(path))


def save_target(path: str | Path, target: Target) -> None:
    write_json(path, target)


def load_simulation(path: str | Path, defaults: tuple[ReactionConfig, ReactionConfig]) -> tuple[Session, dict]:
    return simulation_from_data(read_json(path), defaults)


def simulation_from_data(data: dict, defaults: tuple[ReactionConfig, ReactionConfig]) -> tuple[Session, dict]:
    """Read the original format, including pre-reaction and point-count files."""
    if not isinstance(data, dict):
        raise ValueError("The simulation file must contain a JSON object.")
    if data.get("format") != "HyProC simulation" or data.get("version") != 1:
        raise ValueError("This file is not a supported HyProC simulation.")

    target_layers = data["target"]["layers"]
    standard_layers = data["standard"]["layers"]
    if not isinstance(target_layers, list) or not isinstance(standard_layers, list):
        raise ValueError("Target and standard layers must be lists.")
    if not target_layers or not standard_layers:
        raise ValueError("A simulation must contain a target and a standard.")
    target = target_from_data(data["target"])
    standard = target_from_data(data["standard"])
    std_reaction, exp_reaction = reactions_from_sim(data, defaults)

    experimental_curve = data["experimental_curve"]
    exp_energy = experimental_curve["energy"]
    ec_yield = experimental_curve["yield"]
    ec_y_error = experimental_curve["yield_error"]
    if not all(isinstance(values, list) for values in (exp_energy, ec_yield, ec_y_error)):
        raise ValueError("Experimental curve data must be stored as lists.")
    if bool(ec_yield) != bool(ec_y_error) or (ec_yield and not (len(exp_energy) == len(ec_yield) == len(ec_y_error))):
        raise ValueError("Experimental curve arrays must have equal lengths.")
    if not all(isinstance(value, (int, float)) for values in (exp_energy, ec_yield, ec_y_error) for value in values):
        raise ValueError("Experimental curve values must be numeric.")

    simulated_curve = data["simulated_curve"]
    sim_energy = simulated_curve["energy"]
    sim_curve = simulated_curve["yield"]
    if not isinstance(sim_energy, list) or not isinstance(sim_curve, list):
        raise ValueError("Simulated curve data must be stored as lists.")
    if len(sim_energy) != len(sim_curve):
        raise ValueError("Simulated curve arrays must have equal lengths.")
    if not all(isinstance(value, (int, float)) for values in (sim_energy, sim_curve) for value in values):
        raise ValueError("Simulated curve values must be numeric.")

    chi_values = data["chi_squared"]
    if not isinstance(chi_values, list):
        raise ValueError("Chi-squared history must be stored as a list.")
    if not all(isinstance(value, (int, float)) for value in chi_values):
        raise ValueError("Chi-squared values must be numeric.")
    chi_bounds_history = data.get("chi_squared_energy_bounds")
    if chi_bounds_history is None:
        chi_bounds_history = [None] * len(chi_values)
    if not isinstance(chi_bounds_history, list) or len(chi_bounds_history) != len(chi_values):
        raise ValueError("Chi-squared energy bounds history must match the chi-squared history length.")
    for bounds in chi_bounds_history:
        if bounds is None:
            continue
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ValueError("Each chi-squared energy bound entry must contain a minimum and maximum.")
        if any(
            value is not None
            and (isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value))
            for value in bounds
        ):
            raise ValueError("Chi-squared energy bounds must be finite numbers or null.")
        if bounds[0] is not None and bounds[1] is not None and bounds[0] > bounds[1]:
            raise ValueError("A saved chi-squared minimum energy is greater than its maximum.")
    chi_bounds_history = [None if bounds is None else (bounds[0], bounds[1]) for bounds in chi_bounds_history]
    options = data["options"]
    energy_range = data["energy_range"]
    if not isinstance(options, dict) or not isinstance(energy_range, dict):
        raise ValueError("Simulation options and energy range must be JSON objects.")
    if not all(key in energy_range for key in ("minimum", "maximum")):
        raise ValueError("Saved energy range is incomplete.")
    if energy_range["minimum"] is not None and not isinstance(energy_range["minimum"], (int, float)):
        raise ValueError("Minimum energy must be numeric or null.")
    if energy_range["maximum"] is not None and not isinstance(energy_range["maximum"], (int, float)):
        raise ValueError("Maximum energy must be numeric or null.")
    step_size = energy_range.get("step_size")
    if step_size is None and isinstance(energy_range.get("points"), int):
        point_count = energy_range["points"]
        minimum = energy_range["minimum"]
        maximum = energy_range["maximum"]
        if minimum is not None and maximum is not None and point_count > 1:
            step_size = (maximum - minimum) / (point_count - 1)
        else:
            step_size = 1.0
    if (
        isinstance(step_size, bool)
        or not isinstance(step_size, (int, float))
        or not np.isfinite(step_size)
        or step_size <= 0
    ):
        raise ValueError("Energy range step size must be a finite positive number.")
    if not all(isinstance(options[key], str) for key in ("standard_yield", "beam_width", "offset", "straggling_model")):
        raise ValueError("Saved calculation input values must be strings.")
    if not all(isinstance(options[key], bool) for key in ("doppler", "save_broadening_data", "track_target_changes")):
        raise ValueError("Saved calculation flags must be boolean values.")
    autoscale = options.get("autoscale", True)
    if not isinstance(autoscale, bool):
        raise ValueError("Saved autoscale setting must be a boolean value.")
    sim_markers = options.get("sim_markers", True)
    if not isinstance(sim_markers, bool):
        raise ValueError("Saved simulated curve markers setting must be a boolean value.")
    show_chi_energy_bounds = options.get("show_chi_energy_bounds", True)
    if not isinstance(show_chi_energy_bounds, bool):
        raise ValueError("Saved chi-squared energy bounds visibility setting must be a boolean value.")
    chi_energy_min = options.get("chi_energy_min", "")
    chi_energy_max = options.get("chi_energy_max", "")
    if not isinstance(chi_energy_min, str) or not isinstance(chi_energy_max, str):
        raise ValueError("Saved chi-squared energy bounds must be strings.")
    for value in (chi_energy_min, chi_energy_max):
        if value.strip():
            if not np.isfinite(float(value)):
                raise ValueError("Saved chi-squared energy bounds must be finite numbers.")
    if chi_energy_min.strip() and chi_energy_max.strip() and float(chi_energy_min) > float(chi_energy_max):
        raise ValueError("Saved chi-squared minimum energy is greater than its maximum.")
    if options["straggling_model"] not in STRAGGLING_MODELS:
        raise ValueError("The saved straggling model is not supported.")
    stopping_model = options.get("stopping_model")
    if stopping_model not in STOPPING_MODELS:
        stopping_model = "SRIM"
    chi_start = data.get("chi_squared_start", 0)
    if not isinstance(chi_start, int):
        raise ValueError("Chi-squared history position must be an integer.")

    options = dict(options)
    options.update(
        stopping_model=stopping_model,
        autoscale=autoscale,
        sim_markers=sim_markers,
        show_chi_energy_bounds=show_chi_energy_bounds,
        chi_energy_min=chi_energy_min,
        chi_energy_max=chi_energy_max,
    )
    session = Session(
        target=target,
        standard=standard,
        standard_reaction=std_reaction,
        experiment_reaction=exp_reaction,
        experimental_energy=exp_energy,
        experimental_yield=ec_yield,
        experimental_error=ec_y_error,
        simulated_energy=sim_energy,
        simulated_yield=sim_curve,
        chi_squared=chi_values,
        chi_bounds=chi_bounds_history,
        chi_start=chi_start,
        energy_min=energy_range["minimum"],
        energy_max=energy_range["maximum"],
        energy_step=step_size,
    )
    return session, options


def save_simulation(path: str | Path, session: Session, options: dict) -> None:
    """Keep version 1 and its original key names, including string-valued entries."""
    write_json(
        path,
        {
            "format": "HyProC simulation",
            "version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "target": session.target,
            "standard": session.standard,
            "reactions": {"standard": session.standard_reaction, "experiment": session.experiment_reaction},
            "experimental_curve": {
                "energy": session.experimental_energy,
                "yield": session.experimental_yield,
                "yield_error": session.experimental_error,
            },
            "simulated_curve": {"energy": session.simulated_energy, "yield": session.simulated_yield},
            "chi_squared": session.chi_squared,
            "chi_squared_energy_bounds": session.chi_bounds,
            "chi_squared_start": session.chi_start,
            "options": options,
            "energy_range": {
                "minimum": session.energy_min,
                "maximum": session.energy_max,
                "step_size": session.energy_step,
            },
        },
    )


def count_datapoints(frame: pd.DataFrame, header_row: int) -> int:
    """Count a table up to the first completely blank row."""
    count = 0
    for index in range(header_row + 1, len(frame)):
        if frame.iloc[index].isnull().all():
            break
        count += 1
    return count


def excel_tables(path: str | Path, columns: dict) -> dict[str, pd.DataFrame]:
    """Read candidate sheets once; the GUI decides among multiple matches."""
    required = [columns["energy"], columns["yield"]]
    with pd.ExcelFile(path) as workbook:
        frames = {sheet: pd.read_excel(workbook, sheet_name=sheet, header=None) for sheet in workbook.sheet_names}
    return {sheet: frame for sheet, frame in frames.items() if header_rows(frame, required)}


def header_rows(frame: pd.DataFrame, required: list[str]) -> list[int]:
    return frame[frame.apply(lambda row: all(name in row.values for name in required), axis=1)].index.tolist()


def read_excel_curve(
    path: str | Path, sheet: str, header_row: int, count: int, columns: dict
) -> tuple[list[float], list[float], list[float]]:
    """Let pandas disambiguate repeated column headers, as in legacy imports."""
    frame = pd.read_excel(path, sheet_name=sheet, skiprows=range(header_row), header=0, nrows=count)
    return curve_from_table(frame, columns)


def curve_from_table(frame: pd.DataFrame, columns: dict) -> tuple[list[float], list[float], list[float]]:
    """Return energy-sorted data, with zero uncertainty when that column is absent."""
    frame = frame.copy()
    energy, measured, uncertainty = (columns[key] for key in ("energy", "yield", "yield_err"))
    if energy not in frame or measured not in frame:
        raise ValueError("Curve table must contain energy and yield columns.")
    if uncertainty not in frame:
        frame[uncertainty] = 0.0
    frame = frame.dropna(subset=[energy, measured, uncertainty])
    frame = frame[pd.to_numeric(frame[energy], errors="coerce").notna()]
    frame = frame[[energy, measured, uncertainty]].astype(float).sort_values(energy, kind="stable")
    if frame.empty or not np.isfinite(frame.to_numpy()).all():
        raise ValueError("The curve must contain finite numeric data.")
    return tuple(frame[name].tolist() for name in (energy, measured, uncertainty))


def read_text_curve(path: str | Path, columns: dict) -> tuple[list[float], list[float], list[float]]:
    if Path(path).suffix.lower() == ".csv":
        frame = pd.read_csv(path, comment="#", engine="python")
    else:
        frame = pd.read_csv(path, comment="#", sep=r"[\t ]+", engine="python", header=None)
    if columns["energy"] not in frame or columns["yield"] not in frame:
        if len(frame.columns) < 2:
            raise ValueError("Curve file must contain at least two columns (energy and yield).")
        names = [columns["energy"], columns["yield"], columns["yield_err"]]
        frame = frame.rename(columns=dict(zip(frame.columns[:3], names)))
    return curve_from_table(frame, columns)


def save_curve(path: str | Path, energies: list[float], yields: list[float]) -> None:
    """Preserve the desktop export precision: keV to 3 decimals, yield to 1."""
    with open(path, "w", encoding="utf-8") as stream:
        for energy, value in zip(energies, yields):
            stream.write(f"{energy:.3f}\t{value:.1f}\n")
