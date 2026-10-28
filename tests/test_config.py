import json
from pathlib import Path

from hyproc import config


def test_settings_created_from_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    path = Path(config.settings_path())

    assert path == tmp_path / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    defaults = json.loads(config.data_path("default_settings.json").read_text(encoding="utf-8"))
    assert settings["reaction"] == defaults["reaction"]
    assert settings["resonance"] == defaults["resonance"]
    assert settings["save_path"]  # filled in on first run


def test_existing_settings_are_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPROC_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(json.dumps({"SRIM_path": "X"}), encoding="utf-8")

    assert config.load_settings() == {"SRIM_path": "X"}


def test_packaged_data_files_exist():
    for name in ("default_settings.json", "SCS-2025-solid.json", "HyProC_Manual.pdf"):
        assert config.data_path(name).is_file()
