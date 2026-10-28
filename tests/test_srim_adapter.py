from pathlib import Path

import pytest

from hyproc import stopping
from hyproc.models import Layer, ReactionConfig


@pytest.fixture
def srim_module(tmp_path, monkeypatch):
    directory = tmp_path / "SR Module"
    directory.mkdir()
    (directory / "SRModule.exe").touch()
    monkeypatch.setattr(stopping, "load_settings", lambda: {"SRIM_path": str(tmp_path)})
    return directory


def test_srim_input_does_not_change_process_directory(srim_module):
    before = Path.cwd()
    try:
        stopping.write_input(Layer(), 6400, ReactionConfig())
        assert Path.cwd() == before
        text = (srim_module / "SR.IN").read_text()
        assert "---Ion(Z), Ion Mass(u)" in text
        assert text.endswith("6400")
    finally:
        # Restore cwd even against the pre-refactor implementation.
        import os

        os.chdir(before)


def test_srim_process_uses_explicit_directory_and_converts_ev_to_kev(srim_module, monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        (srim_module / "Output").write_text("Stopping Units =  eV/(1E15 atoms/cm2)\nheader\n6400 2.0 0.5\n")

    monkeypatch.setattr(stopping.subprocess, "run", run)
    before = Path.cwd()
    try:
        assert stopping.calc_stopping_cross_section(Layer(), 6400, ReactionConfig(), "SRIM") == pytest.approx(0.0025)
        assert Path(calls[0][1]["cwd"]) == srim_module
        assert calls[0][1]["check"] is True
        assert Path.cwd() == before
    finally:
        import os

        os.chdir(before)
