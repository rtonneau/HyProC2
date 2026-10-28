import os
import tempfile

# Settings (default reactions, SRIM path) come from the per-user config dir; point
# it at a throw-away directory before any hyproc import so tests never touch the
# real user settings.
_settings_directory = tempfile.TemporaryDirectory(prefix="hyproc-test-")
os.environ["HYPROC_CONFIG_DIR"] = _settings_directory.name
