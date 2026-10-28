"""User settings and packaged data files.

The user's settings live in a per-user config directory and are created from
the packaged ``default_settings.json`` on first use.
"""
import json
import os
import sys
from importlib import resources
from pathlib import Path

from .models import ReactionConfig

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
        _write_settings(str(path), settings)
    return str(path)


def _write_settings(path: str, settings: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def _migrate_reactions(settings: dict) -> bool:
    """Replaces the old ``reaction``/``resonance`` blocks by ``reactions``; returns True if changed."""
    if "reactions" in settings or not ("reaction" in settings or "resonance" in settings):
        return False
    old = {**settings.pop("reaction", {}), **settings.pop("resonance", {})}
    settings["reactions"] = {"standard": dict(old), "experiment": dict(old)}
    return True


def load_settings() -> dict:
    """Loads the user's settings, migrating an old-shape file (rewritten once)."""
    path = settings_path()
    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    if _migrate_reactions(settings):
        _write_settings(path, settings)
    return settings


def default_reactions() -> tuple[ReactionConfig, ReactionConfig]:
    """Returns the default (standard, experiment) reaction configs."""
    reactions = load_settings().get("reactions", {})
    return ReactionConfig(reactions.get("standard")), ReactionConfig(reactions.get("experiment"))


def save_default_reactions(standard: ReactionConfig, experiment: ReactionConfig) -> None:
    """Writes the default (standard, experiment) reaction configs to the user's settings."""
    settings = load_settings()
    settings["reactions"] = {"standard": dict(standard), "experiment": dict(experiment)}
    _write_settings(settings_path(), settings)
