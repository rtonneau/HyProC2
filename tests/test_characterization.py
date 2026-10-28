"""Numerical snapshots of the pre-refactor workflow, not model validation."""

import pytest

from hyproc import broadening, stopping, yield_calc
from hyproc.models import Element, ReactionConfig, Target


def reference_target(thickness=1000.0):
    target = Target()
    target["layers"][0]["areal_density"] = thickness
    target["layers"][0]["elements"] = [Element(Z=14, percent_at=90), Element(Z=7, percent_at=10)]
    return target


@pytest.mark.parametrize(
    "model,doppler,expected",
    [
        ("Rud", True, [7.41448637798068, 3.7819466812299907, 2.727429359796238]),
        ("Rud", False, [1.8645668481346547, 3.8315545447751354, 2.741604526340069]),
        ("Rud corr", True, [7.41448637798068, 6.013368423300998, 2.6920591079801204]),
        ("Rud corr", False, [1.8645668481346547, 6.222511972928381, 2.626629202567241]),
        ("Bohr", True, [7.41448637798068, 13.321439136433023, 0.2353774973971058]),
        ("Bohr", False, [1.8645668481346547, 11.672051276989713, 0.1918881083678745]),
    ],
)
def test_reference_curves(model, doppler, expected):
    reaction = ReactionConfig()
    target = stopping.assign_stopping(reference_target(), 6405.0, reaction, "SCS-25-Solid")
    assert target["layers"][0]["stopping"] == pytest.approx(0.0023149483342392494, rel=1e-10)
    # The original reference uses Rud corr + Doppler for calibration in all cases.
    factor = yield_calc.k_factor(reference_target(200000), 100, reaction, 1, True, "Rud corr", "SCS-25-Solid")
    assert factor == pytest.approx(0.005226744798860801, rel=1e-8)
    actual = []
    for energy in (6380.0, 6390.0, 6405.0):
        _, depth, profile, _, _ = broadening.broadening(energy, target, 1, reaction, doppler, model)
        actual.append(factor * yield_calc.compute_yield(target, reaction, depth, profile))
    assert actual == pytest.approx(expected, rel=1e-7)


def test_existing_layer_segmentation_arithmetic(monkeypatch):
    # Three halvings currently produce nine daughters of thickness AD/8.
    # Protect the baseline until a scientific review authorizes a correction.
    monkeypatch.setattr(stopping, "calc_stopping_cross_section", lambda layer, energy, reaction, model: energy)
    target = reference_target(0.04)
    result = stopping.assign_stopping(target, 100.0, ReactionConfig(), "SCS-25-Solid")
    assert len(result["layers"]) == 9
    assert sum(layer["areal_density"] for layer in result["layers"]) == pytest.approx(0.045)
