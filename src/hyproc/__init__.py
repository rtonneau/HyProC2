"""HyProC: depth profiling by resonant nuclear reaction analysis."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hyproc")
except PackageNotFoundError:
    __version__ = "0.0.0"
