"""Test the desktop job boundary without creating a Tk window."""

from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

from hyproc.app import HyProCApp
from hyproc.models import Session, Target
from hyproc.simulation import CalculationResult


def window(future):
    return SimpleNamespace(
        pending_calculation=future,
        session=Session(),
        run_number=0,
        visible_count=9,
        after=Mock(),
        _set_busy=Mock(),
        target_editor=Mock(),
        standard_editor=Mock(),
        update_exc_plot=Mock(),
        update_chi_plot=Mock(),
        scroll_down=Mock(),
        autoscale_exc_bool=SimpleNamespace(get=lambda: True),
    )


def test_incomplete_job_only_schedules_poll():
    app = window(Future())
    app._poll_calculation = lambda: HyProCApp._poll_calculation(app)
    HyProCApp._poll_calculation(app)
    app.after.assert_called_once_with(50, app._poll_calculation)
    app._set_busy.assert_not_called()


def test_failed_job_preserves_session_and_unlocks_controls(monkeypatch):
    future = Future()
    future.set_exception(ValueError("invalid standard"))
    app = window(future)
    before = app.session.target
    error = Mock()
    monkeypatch.setattr("hyproc.app.messagebox.showerror", error)
    HyProCApp._poll_calculation(app)
    assert app.session.target is before
    assert app.pending_calculation is None
    assert app.run_number == 0
    app._set_busy.assert_called_with(False)
    error.assert_called_once()


def test_completed_job_replaces_target_and_updates_history():
    future = Future()
    result = CalculationResult(Target(), Target(), [6390], [10], 1, 2, (None, None), False)
    future.set_result(result)
    app = window(future)
    HyProCApp._poll_calculation(app)
    assert app.session.target is result.target
    assert app.session.simulated_yield == [10]
    assert app.session.chi_squared == [2]
    assert app.run_number == 1
    assert app.pending_calculation is None
    app.target_editor.refresh.assert_called_once()
