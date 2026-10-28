import os
import tempfile

# Settings (default reactions, SRIM path) come from the per-user config dir; point
# it at a throw-away directory before any hyproc import so tests never touch the
# real user settings.
os.environ["HYPROC_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hyproc-test-")
