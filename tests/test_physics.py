import math

import numpy as np
import pytest

from hyproc import broadening, stopping, yield_calc
from hyproc.models import Element, Layer, ReactionConfig, Target

REACTION = ReactionConfig()


def make_target(z2_percent: float = 10.0, z2: int = REACTION["Z2"]) -> Target:
    """Single 1000 TFU Si layer containing the profiled element Z2."""
    target = Target()
    layer = Layer(AD=1000.0)
    layer["elements"] = [
        Element(Z=14, percent_at=100.0 - z2_percent),
        Element(Z=z2, percent_at=z2_percent),
    ]
    target["layers"] = [layer]
    return target


def test_scs_stopping_sio2():
    layer = Layer()
    layer["elements"] = [Element(Z=14, percent_at=33.333), Element(Z=8, percent_at=66.667)]

    electronic, nuclear = stopping._calc_scs_stopping_components(layer, 5000.0, REACTION)

    assert math.isfinite(electronic) and electronic > 0
    assert 0 < nuclear < electronic
    assert stopping.calc_stopping_cross_section(layer, 5000.0, REACTION, "SCS-25-Solid") == pytest.approx(
        electronic + nuclear
    )


def test_scs_stopping_zero_energy():
    assert stopping._calc_scs_stopping_components(Layer(), 0.0, REACTION) == (0.0, 0.0)


def test_unknown_stopping_model():
    with pytest.raises(ValueError):
        stopping.calc_stopping_cross_section(Layer(), 1000.0, REACTION, "unknown")


def test_assign_stopping_sets_positive_stopping():
    target = stopping.assign_stopping(make_target(), REACTION["E_R"] + 20.0, REACTION, "SCS-25-Solid")

    assert target["layers"]
    assert all(layer["stopping"] > 0 for layer in target["layers"])


def test_profile_steps():
    x, y = yield_calc.cH_make(make_target(z2_percent=10.0), REACTION)

    assert list(x) == [0.0, 1000.0]
    assert y == [0.0, 10.0]


def test_broadening_and_yield():
    energy = REACTION["E_R"] + 5.0
    target = stopping.assign_stopping(make_target(), energy, REACTION, "SCS-25-Solid")

    center, x, y, _, _ = broadening.broadening(energy, target, delta_B=1.0, reaction=REACTION)

    assert x.shape == y.shape and x.size > 0
    assert np.all(np.isfinite(y))
    assert center > 0
    assert yield_calc.compute_yield(target, REACTION, x, y) > 0


def test_chi_squared():
    x = [1.0, 2.0, 3.0]
    assert yield_calc.chi_squared_test(x, [1.0, 2.0, 3.0], x, [1.0, 2.0, 3.0]) == 0.0
    assert yield_calc.chi_squared_test(x, [1.0, 2.0, 3.0], x, [2.0, 3.0, 4.0]) == pytest.approx(1.0)
    assert yield_calc.chi_squared_test(x, [1.0, 2.0], x, [1.0, 2.0, 3.0]) == -1.0


def test_resonance_energy_shifts_broadening():
    shifted = ReactionConfig({"E_R": REACTION["E_R"] + 50.0})
    energy = REACTION["E_R"] + 5.0
    target = stopping.assign_stopping(make_target(), energy, REACTION, "SCS-25-Solid")

    c0, x0, _, _, _ = broadening.broadening(energy, target, delta_B=1.0, reaction=REACTION)
    c1, x1, _, _, _ = broadening.broadening(energy, target, delta_B=1.0, reaction=shifted)

    # A higher resonance energy leaves less energy to lose: the resonance sits closer to the surface.
    assert c1 < c0
    assert x0.shape != x1.shape or not np.allclose(x0, x1)


def test_profile_follows_reaction_z2():
    target = Target()
    layer = Layer(AD=1000.0)
    layer["elements"] = [Element(Z=14, percent_at=80.0), Element(Z=1, percent_at=15.0), Element(Z=7, percent_at=5.0)]
    target["layers"] = [layer]

    _, y_h = yield_calc.cH_make(target, ReactionConfig({"Z2": 1, "A2": 1}))
    _, y_n = yield_calc.cH_make(target, ReactionConfig({"Z2": 7, "A2": 15}))

    assert y_h == [0.0, 15.0]
    assert y_n == [0.0, 5.0]


def thick_target() -> Target:
    target = make_target()
    target["layers"][0]["areal_density"] = 200000.0
    return target


def test_k_factor_uses_standard_reaction():
    std_reaction = ReactionConfig({"E_R": 6385.0})
    exp_reaction = ReactionConfig({"E_R": 6000.0})
    assert std_reaction["Z2"] == exp_reaction["Z2"]
    k_std = yield_calc.k_factor(thick_target(), 100.0, std_reaction, 1.0, True, "Rud corr", "SCS-25-Solid")
    k_exp = yield_calc.k_factor(thick_target(), 100.0, exp_reaction, 1.0, True, "Rud corr", "SCS-25-Solid")

    # Reference computed by hand from the standard's config
    energy = std_reaction["E_R"] + yield_calc.STD_ENERGY_OFFSET
    ref = thick_target()
    ref["layers"][0]["stopping"] = stopping.calc_stopping_cross_section(
        ref["layers"][0], energy, std_reaction, "SCS-25-Solid"
    )
    _, x, y, _, _ = broadening.broadening(energy, ref, 1.0, std_reaction, True, "Rud corr")
    assert k_std == pytest.approx(100.0 / yield_calc.compute_yield(ref, std_reaction, x, y))
    assert k_std != pytest.approx(k_exp)
