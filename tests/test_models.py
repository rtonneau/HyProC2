import json

import pytest

from hyproc.models import Element, Layer, ReactionConfig, Target, reactions_from_sim


def test_layer_normalize():
    layer = Layer()
    layer["elements"] = [Element(Z=14, percent_at=1.0), Element(Z=8, percent_at=3.0)]

    assert layer.normalize() is True
    assert [el["percent_at"] for el in layer["elements"]] == pytest.approx([25.0, 75.0])
    assert layer.normalize() is False


def test_layer_roundtrip_from_dict():
    data = {"areal_density": 500.0, "stopping": 0.1, "elements": [{"Z": 1, "percent_at": 10.0}]}
    layer = Layer(data=data)

    assert isinstance(layer["elements"][0], Element)
    assert layer.find_element(Z=1) == 10.0
    assert layer.find_element(Z=2) is None


def test_target_layer_operations():
    target = Target()
    target.add_layer()
    target["layers"][1]["areal_density"] = 42.0

    target.move_layer_up(1)
    assert target["layers"][0]["areal_density"] == 42.0

    target.remove_layer(0)
    target.remove_layer(0)  # the last layer is never removed
    assert len(target["layers"]) == 1


def test_reaction_config_defaults():
    reaction = ReactionConfig()

    assert reaction == {"Z1": 1, "A1": 1, "Z2": 7, "A2": 15, "E_R": 6385.0, "Gamma": 1.8, "Sigma": 1.65}


def test_reaction_config_casts_strings():
    reaction = ReactionConfig({"Z2": "7", "A2": "15", "E_R": "6385"})

    assert reaction["Z2"] == 7 and isinstance(reaction["Z2"], int)
    assert reaction["E_R"] == 6385.0 and isinstance(reaction["E_R"], float)
    assert json.loads(json.dumps(reaction)) == reaction


def _defaults():
    return ReactionConfig(), ReactionConfig({"Z1": 2, "A1": 4, "Z2": 13, "A2": 27, "E_R": 992.0})


def test_reactions_from_sim_roundtrip():
    std = ReactionConfig({"Z2": 6, "A2": 13, "E_R": 1748.0})
    exp = ReactionConfig({"Z1": 2, "A1": 4, "Z2": 8, "A2": 18, "Gamma": 0.5})
    saved = json.loads(json.dumps({"reactions": {"standard": std, "experiment": exp}}))

    loaded_std, loaded_exp = reactions_from_sim(saved, _defaults())

    assert loaded_std == std and loaded_exp == exp


def test_reactions_from_sim_old_file_and_partial_use_defaults():
    defaults = _defaults()

    assert reactions_from_sim({}, defaults) == defaults

    std, exp = reactions_from_sim({"reactions": {"experiment": {"E_R": "1000"}}}, defaults)
    assert std == defaults[0]
    assert exp == {**defaults[1], "E_R": 1000.0}


def test_reactions_from_sim_malformed_raises_value_error():
    with pytest.raises(ValueError):
        reactions_from_sim({"reactions": {"standard": {"Z1": "abc"}}}, _defaults())
    with pytest.raises(ValueError):
        reactions_from_sim({"reactions": []}, _defaults())
    with pytest.raises(ValueError):
        reactions_from_sim({"reactions": {"experiment": "x"}}, _defaults())
