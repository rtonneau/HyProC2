"""User settings and packaged data files.

The user's settings live in a per-user config directory and are created from
the packaged ``default_settings.json`` on first use.
"""
import json
import os
import sys
from importlib import resources
from pathlib import Path

APP_NAME = "HyProC"


def data_path(name: str) -> Path:
    """Returns the path of a data file shipped with the package."""
    return Path(str(resources.files("hyproc") / "data" / name))


def user_config_dir() -> Path:
    """Returns the per-user configuration directory (overridable with HYPROC_CONFIG_DIR)."""
    override = os.environ.get("HYPROC_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def settings_path() -> str:
    """Returns the path of the user's settings file, creating it from the defaults if needed."""
    path = user_config_dir() / "settings.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path("default_settings.json"), "r", encoding="utf-8") as f:
            settings = json.load(f)
        if not settings.get("save_path"):
            settings["save_path"] = str(Path.home())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    return str(path)


def load_settings() -> dict:
    """Loads the user's settings."""
    with open(settings_path(), "r", encoding="utf-8") as f:
        return json.load(f)
