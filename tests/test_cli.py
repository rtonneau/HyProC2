import json
import os
import subprocess
import sys
from pathlib import Path

from hyproc import cli, file_io
from test_characterization import reference_target


def test_cli_runs_without_tkinter_and_saves_loadable_simulation(tmp_path):
    target, standard, output = (tmp_path / name for name in ("target.json", "standard.json", "result.json"))
    file_io.save_target(target, reference_target())
    file_io.save_target(standard, reference_target(200000))
    # An import guard fails even on machines with Tk installed if the CLI
    # accidentally acquires a desktop dependency.
    script = """
import sys
class NoTk:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'tkinter' or fullname.startswith('tkinter.'):
            raise RuntimeError('CLI must not import Tkinter')
sys.meta_path.insert(0, NoTk())
from hyproc.cli import main
raise SystemExit(main(sys.argv[1:]))
"""
    args = [
        "--target",
        str(target),
        "--standard",
        str(standard),
        "--output",
        str(output),
        "--energies",
        "6380",
        "6405",
        "10",
        "--standard-yield",
        "100",
        "--beam-width",
        "1",
        "--stopping-model",
        "SCS-25-Solid",
    ]
    completed = subprocess.run(
        [sys.executable, "-c", script, *args],
        capture_output=True,
        text=True,
        env={**os.environ, "HYPROC_CONFIG_DIR": str(tmp_path / "config")},
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    data = json.loads(output.read_text())
    assert data["simulated_curve"]["energy"] == [6380, 6390, 6400, 6405]
    assert len(data["simulated_curve"]["yield"]) == 4
    # Re-run the same saved file through the module entry point.
    completed = subprocess.run(
        [sys.executable, "-m", "hyproc.cli", "--input", str(output), "--output", str(tmp_path / "rerun.json")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads((tmp_path / "rerun.json").read_text())["simulated_curve"] == data["simulated_curve"]


def test_cli_invalid_input_has_nonzero_exit_and_no_output(tmp_path):
    output = tmp_path / "result.json"
    result = subprocess.run(
        [sys.executable, "-m", "hyproc.cli", "--input", str(Path("missing.json")), "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "hyproc-simulate:" in result.stderr
    assert not output.exists()


def test_cli_reports_external_process_failure(tmp_path, monkeypatch, capsys):
    target, standard, output = (tmp_path / name for name in ("target.json", "standard.json", "result.json"))
    file_io.save_target(target, reference_target())
    file_io.save_target(standard, reference_target(200000))

    def fail(request):
        raise subprocess.CalledProcessError(2, "SRModule.exe")

    monkeypatch.setattr(cli.simulation, "run_simulation", fail)
    code = cli.main(
        [
            "--target",
            str(target),
            "--standard",
            str(standard),
            "--output",
            str(output),
            "--energies",
            "6380",
            "6400",
            "10",
            "--standard-yield",
            "100",
            "--beam-width",
            "1",
        ]
    )
    assert code == 1
    error = capsys.readouterr().err
    assert "SRModule.exe" in error and "Traceback" not in error
    assert not output.exists()
