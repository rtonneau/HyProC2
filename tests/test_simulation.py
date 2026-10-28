from copy import deepcopy

import pytest

from hyproc import simulation
from hyproc.models import Session
from test_characterization import reference_target


def request(**overrides):
    session = Session(target=reference_target(), standard=reference_target(200000))
    options = simulation.CalculationOptions(100, 1, stopping_model="SCS-25-Solid", **overrides)
    return session, simulation.CalculationRequest.from_session(session, [6380, 6390, 6405], options)


def test_headless_workflow_matches_original_and_preserves_inputs():
    session, inputs = request(offset=5)
    before = deepcopy(session)
    result = simulation.run_simulation(inputs)
    assert session == before
    assert inputs.target == before.target
    assert result.energies == [6385, 6395, 6410]
    assert result.yields == pytest.approx([7.41448637798068, 6.013368423300998, 2.6920591079801204], rel=1e-7)
    simulation.apply_result(session, result)
    assert session.target is result.target
    assert session.simulated_yield == result.yields
    assert session.chi_bounds == [(None, None)]


def test_failed_run_does_not_mutate_session_or_request(monkeypatch):
    session, inputs = request()
    before = deepcopy(inputs)

    def fail(target, *args):
        target["layers"].clear()
        raise ValueError("failed stopping")

    monkeypatch.setattr(simulation.stopping, "assign_stopping", fail)
    with pytest.raises(ValueError, match="failed stopping"):
        simulation.run_simulation(inputs)
    assert inputs == before
    assert session.target == before.target


def test_snapshot_is_independent_of_later_edits():
    session, inputs = request()
    session.target["layers"][0]["areal_density"] = 99
    assert inputs.target["layers"][0]["areal_density"] == 1000


def test_multilayer_standard_rejected_before_using_cached_stopping():
    session, inputs = request()
    inputs.standard.add_layer()
    with pytest.raises(ValueError, match="exactly one layer"):
        simulation.run_simulation(inputs)


def test_workflow_keeps_standard_reaction_and_replaces_segmented_target():
    session, _ = request()
    session.target["layers"][0]["areal_density"] = 50000
    session.experiment_reaction["E_R"] = 6380.0
    options = simulation.CalculationOptions(100, 1, stopping_model="SCS-25-Solid")
    inputs = simulation.CalculationRequest.from_session(session, [6390], options)
    result = simulation.run_simulation(inputs)
    assert result.calibration_factor == pytest.approx(0.005226744798860801, rel=1e-8)
    assert result.layers_segmented
    assert len(session.target["layers"]) == 1
    simulation.apply_result(session, result)
    assert len(session.target["layers"]) > 1
    assert sum(layer["areal_density"] for layer in session.target["layers"]) == pytest.approx(50000)


def test_energy_precedence_and_offset():
    session = Session()
    assert simulation.select_energies(session, 2) is None
    session.experimental_energy = [10, 20]
    assert simulation.select_energies(session, 2) == [8, 18]
    session.simulated_energy = [11, 21]
    assert simulation.select_energies(session, 2) == [9, 19]
    assert simulation.select_energies(session, 2, "loaded_curve") == [8, 18]
    assert simulation.select_energies(session, 2, "custom", [12, 22]) == [10, 20]
    assert simulation.select_energies(session, 2, "custom") is None


@pytest.mark.parametrize(
    "minimum,maximum,step,expected",
    [
        (1, 2, 0.4, [1, 1.4, 1.8, 2]),
        (1, 2, 0.5, [1, 1.5, 2]),
        (1, 2, 5, [1, 2]),
    ],
)
def test_energy_range_includes_endpoint(minimum, maximum, step, expected):
    assert simulation.generate_energies(minimum, maximum, step) == pytest.approx(expected)


@pytest.mark.parametrize("values", [(2, 1, 1), (1, 2, 0), (1, float("inf"), 1)])
def test_invalid_energy_range(values):
    with pytest.raises(ValueError):
        simulation.generate_energies(*values)


def test_diagnostics_keep_broadplotter_layout(tmp_path):
    session, _ = request()
    options = simulation.CalculationOptions(
        100, 1, stopping_model="SCS-25-Solid", save_broadening=True, track_target=True
    )
    directory = tmp_path / "Run 0"
    inputs = simulation.CalculationRequest.from_session(session, [6390], options, directory)
    simulation.run_simulation(inputs)
    assert (directory / "_target.json").is_file()
    assert (directory / "datapoint0" / "_E=6390.0kev.dat").is_file()
    assert (directory / "datapoint0" / "Total_Broadening_TFU.txt").is_file()


def test_copy_simulation_to_experiment_is_json_compatible_and_independent():
    session = Session(simulated_energy=[1, 2], simulated_yield=[3, 4])
    simulation.use_simulated_curve_as_experiment(session)
    assert session.experimental_energy == [1, 2]
    assert session.experimental_yield == [3, 4]
    assert session.experimental_error == [0, 0]
    session.simulated_yield[0] = 5
    assert session.experimental_yield[0] == 3
