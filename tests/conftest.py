import os
import tempfile

# The physics modules read the user settings at import time; point them at a
# throw-away config directory so tests never touch the real user settings.
os.environ["HYPROC_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hyproc-test-")
