import math

import numpy as np
import pytest

from hyproc import broadening, stopping, yield_calc
from hyproc.models import Element, Layer, Target


def make_target(z2_percent: float = 10.0) -> Target:
    """Single 1000 TFU Si layer containing the profiled element Z2."""
    target = Target()
    layer = Layer(AD=1000.0)
    layer["elements"] = [
        Element(Z=14, percent_at=100.0 - z2_percent),
        Element(Z=yield_calc.Z2, percent_at=z2_percent),
    ]
    target["layers"] = [layer]
    return target


def test_scs_stopping_sio2():
    layer = Layer()
    layer["elements"] = [Element(Z=14, percent_at=33.333), Element(Z=8, percent_at=66.667)]

    electronic, nuclear = stopping._calc_scs_stopping_components(layer, 5000.0)

    assert math.isfinite(electronic) and electronic > 0
    assert 0 < nuclear < electronic
    assert stopping.calc_stopping_cross_section(layer, 5000.0, "SCS-25-Solid") == pytest.approx(electronic + nuclear)


def test_scs_stopping_zero_energy():
    assert stopping._calc_scs_stopping_components(Layer(), 0.0) == (0.0, 0.0)


def test_unknown_stopping_model():
    with pytest.raises(ValueError):
        stopping.calc_stopping_cross_section(Layer(), 1000.0, "unknown")


def test_assign_stopping_sets_positive_stopping():
    target = stopping.assign_stopping(make_target(), broadening.E_R + 20.0, "SCS-25-Solid")

    assert target["layers"]
    assert all(layer["stopping"] > 0 for layer in target["layers"])


def test_profile_steps():
    x, y = yield_calc.cH_make(make_target(z2_percent=10.0))

    assert list(x) == [0.0, 1000.0]
    assert y == [0.0, 10.0]


def test_broadening_and_yield():
    energy = broadening.E_R + 5.0
    target = stopping.assign_stopping(make_target(), energy, "SCS-25-Solid")

    center, x, y, _, _ = broadening.broadening(energy, target, delta_B=1.0)

    assert x.shape == y.shape and x.size > 0
    assert np.all(np.isfinite(y))
    assert center > 0
    assert yield_calc.compute_yield(target, x, y) > 0


def test_chi_squared():
    x = [1.0, 2.0, 3.0]
    assert yield_calc.chi_squared_test(x, [1.0, 2.0, 3.0], x, [1.0, 2.0, 3.0]) == 0.0
    assert yield_calc.chi_squared_test(x, [1.0, 2.0, 3.0], x, [2.0, 3.0, 4.0]) == pytest.approx(1.0)
    assert yield_calc.chi_squared_test(x, [1.0, 2.0], x, [1.0, 2.0, 3.0]) == -1.0
