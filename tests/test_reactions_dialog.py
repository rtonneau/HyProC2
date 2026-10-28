import pytest

from hyproc.dialogs.reactions import validate_reaction
from hyproc.models import ReactionConfig

DEFAULTS = {key: str(value) for key, value in ReactionConfig().items()}


def values(**overrides):
    return {**DEFAULTS, **overrides}


def test_accepts_defaults():
    assert validate_reaction(DEFAULTS) == ReactionConfig()


def test_returns_typed_config():
    config = validate_reaction(values(E_R=" 6400 ", A2="14"))
    assert isinstance(config, ReactionConfig)
    assert config["E_R"] == 6400.0
    assert config["A2"] == 14


@pytest.mark.parametrize("key", ["Z1", "A1", "Z2", "A2", "E_R", "Gamma", "Sigma"])
@pytest.mark.parametrize("bad", ["abc", "", "nan", "inf"])
def test_rejects_non_numeric(key, bad):
    with pytest.raises(ValueError):
        validate_reaction(values(**{key: bad}))


@pytest.mark.parametrize("key", ["Z1", "A1", "Z2", "A2"])
def test_rejects_non_integer_z_a(key):
    with pytest.raises(ValueError):
        validate_reaction(values(**{key: "1.5"}))


@pytest.mark.parametrize("key", ["Z1", "Z2"])
@pytest.mark.parametrize("bad", ["0", "-1"])
def test_rejects_z_below_one(key, bad):
    with pytest.raises(ValueError, match="Z"):
        validate_reaction(values(**{key: bad}))


def test_rejects_unknown_isotope():
    with pytest.raises(ValueError, match="A2"):
        validate_reaction(values(A2="99"))
    with pytest.raises(ValueError, match="A1"):
        validate_reaction(values(A1="99"))


def test_rejects_unknown_element():
    with pytest.raises(ValueError):
        validate_reaction(values(Z2="500"))


@pytest.mark.parametrize("key", ["E_R", "Gamma", "Sigma"])
@pytest.mark.parametrize("bad", ["0", "-1.5"])
def test_rejects_non_positive_resonance_values(key, bad):
    with pytest.raises(ValueError):
        validate_reaction(values(**{key: bad}))
