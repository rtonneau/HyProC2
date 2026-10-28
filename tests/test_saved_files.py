"""Compatibility checks captured against the original desktop file handlers."""

import json

import pytest

from hyproc import file_io
from hyproc.models import ReactionConfig, Session, Target


@pytest.fixture
def saved_file(tmp_path):
    path = tmp_path / "simulation.json"
    session = Session(
        experimental_energy=[6390.0],
        experimental_yield=[10.0],
        experimental_error=[1.0],
        simulated_energy=[6390.0],
        simulated_yield=[9.0],
        chi_squared=[1.0],
        chi_bounds=[(None, 6400.0)],
        energy_min=6380.0,
        energy_max=6400.0,
    )
    options = {
        "standard_yield": "100",
        "beam_width": "1",
        "offset": "0",
        "chi_energy_min": "",
        "chi_energy_max": "6400",
        "doppler": True,
        "save_broadening_data": False,
        "track_target_changes": False,
        "autoscale": True,
        "sim_markers": True,
        "show_chi_energy_bounds": True,
        "stopping_model": "SCS-25-Solid",
        "straggling_model": "Rud corr",
    }
    file_io.save_simulation(path, session, options)
    return path


def load(path):
    return file_io.load_simulation(path, (ReactionConfig(), ReactionConfig()))


def test_version_one_roundtrip(saved_file):
    session, options = load(saved_file)
    assert session.target == Target()
    assert session.simulated_yield == [9.0]
    assert session.chi_bounds == [(None, 6400.0)]
    assert session.energy_step == 2.5
    assert options["standard_yield"] == "100"
    assert json.loads(saved_file.read_text())["version"] == 1


def test_older_optional_fields_and_point_count(saved_file):
    data = json.loads(saved_file.read_text())
    del data["reactions"]
    del data["chi_squared_energy_bounds"]
    data["energy_range"] = {"minimum": 6380, "maximum": 6400, "points": 5}
    for key in (
        "stopping_model",
        "autoscale",
        "sim_markers",
        "show_chi_energy_bounds",
        "chi_energy_min",
        "chi_energy_max",
    ):
        data["options"].pop(key)
    saved_file.write_text(json.dumps(data))
    session, options = load(saved_file)
    assert session.energy_step == 5
    assert session.chi_bounds == [None]
    assert session.standard_reaction == ReactionConfig()
    assert options["stopping_model"] == "SRIM"


def test_bad_file_rejected_before_returning_state(saved_file):
    data = json.loads(saved_file.read_text())
    data["simulated_curve"]["yield"] = []
    saved_file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="equal lengths"):
        load(saved_file)


def test_target_extensions_and_domain_types_roundtrip(tmp_path):
    target = Target()
    target["notes"] = "sample 15N"
    target["layers"][0]["annotation"] = {"source": "measurement"}
    path = tmp_path / "target.json"
    file_io.save_target(path, target)
    restored = file_io.load_target(path)
    assert restored == target
    assert restored["layers"][0].find_element(14) == 100


def test_failed_encoding_preserves_existing_file(tmp_path):
    path = tmp_path / "target.json"
    path.write_text("original")
    with pytest.raises(TypeError):
        file_io.write_json(path, {"invalid": object()})
    assert path.read_text() == "original"


@pytest.mark.parametrize("bad", [{}, {"layers": []}, {"layers": [{}]}])
def test_malformed_targets_have_actionable_errors(bad):
    with pytest.raises(ValueError):
        file_io.target_from_data(bad)
