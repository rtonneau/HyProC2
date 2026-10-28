import json
from pathlib import Path

from hyproc import config
from hyproc.models import ReactionConfig


def test_settings_created_from_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    path = Path(config.settings_path())

    assert path == tmp_path / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    defaults = json.loads(config.data_path("default_settings.json").read_text(encoding="utf-8"))
    assert settings["reactions"] == defaults["reactions"]
    assert set(settings["reactions"]) == {"standard", "experiment"}
    assert "reaction" not in settings and "resonance" not in settings
    assert settings["save_path"]  # filled in on first run


def test_existing_settings_are_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(json.dumps({"SRIM_path": "X"}), encoding="utf-8")

    assert config.load_settings() == {"SRIM_path": "X"}


def test_packaged_data_files_exist():
    for name in ("default_settings.json", "SCS-2025-solid.json", "HyProC_Manual.pdf"):
        assert config.data_path(name).is_file()


OLD_SETTINGS = {
    "SRIM_path": "X",
    "reaction": {"Z1": "1", "A1": "2", "Z2": "7", "A2": "14"},
    "resonance": {"E_R": 1234.5, "Gamma": 2.5, "Sigma": 0.5},
}


def test_old_settings_are_migrated_once(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(OLD_SETTINGS), encoding="utf-8")
    old_values = {**OLD_SETTINGS["reaction"], **OLD_SETTINGS["resonance"]}

    settings = config.load_settings()

    assert settings["reactions"] == {"standard": old_values, "experiment": old_values}
    assert "reaction" not in settings and "resonance" not in settings
    assert settings["SRIM_path"] == "X"
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == settings

    # A second load is a no-op: the file is not rewritten.
    path.write_text(json.dumps(on_disk, indent=2), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    assert config.load_settings() == settings
    assert path.read_text(encoding="utf-8") == before

    standard, experiment = config.default_reactions()
    assert standard == experiment == ReactionConfig(old_values)
    assert experiment["A1"] == 2 and experiment["E_R"] == 1234.5


def test_default_reactions_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    standard = ReactionConfig({"Z1": 2, "A1": 4, "Z2": 13, "A2": 27, "E_R": 992.0, "Gamma": 0.1, "Sigma": 3.0})
    experiment = ReactionConfig({"E_R": 6385.0, "Sigma": 2.0})

    config.save_default_reactions(standard, experiment)
    loaded_standard, loaded_experiment = config.default_reactions()

    assert loaded_standard == standard
    assert loaded_experiment == experiment
    assert isinstance(loaded_standard, ReactionConfig)
    assert json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))["reactions"] == {
        "standard": dict(standard),
        "experiment": dict(experiment),
    }
