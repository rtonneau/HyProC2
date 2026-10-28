import copy


class ReactionConfig(dict):
    """Nuclear reaction and resonance parameters, serialised as plain JSON.

    Z1/A1 are the beam ion, Z2/A2 the profiled element; E_R (keV), Gamma (keV)
    and Sigma (mbarn) describe the resonance.
    """
    INT_KEYS = ("Z1", "A1", "Z2", "A2")
    FLOAT_KEYS = ("E_R", "Gamma", "Sigma")
    DEFAULTS = {"Z1": 1, "A1": 1, "Z2": 7, "A2": 15, "E_R": 6385.0, "Gamma": 1.8, "Sigma": 1.65}

    def __init__(self, data=None) -> None:
        super().__init__()
        values = dict(self.DEFAULTS)
        if data is not None:
            values.update({key: data[key] for key in self.DEFAULTS if key in data})
        for key in self.INT_KEYS:
            self[key] = int(float(values[key]))
        for key in self.FLOAT_KEYS:
            self[key] = float(values[key])


def reactions_from_sim(
    data: dict, defaults: tuple[ReactionConfig, ReactionConfig]
) -> tuple[ReactionConfig, ReactionConfig]:
    """Parse the standard and experiment reactions of a simulation file.

    A missing ``reactions`` block, or missing keys inside a side, are filled from
    ``defaults`` (standard, experiment). Malformed values raise ValueError.
    """
    saved = data.get("reactions")
    if saved is None:
        return ReactionConfig(defaults[0]), ReactionConfig(defaults[1])
    if not isinstance(saved, dict):
        raise ValueError("Saved reactions must be a JSON object.")
    parsed = []
    for side, side_defaults in zip(("standard", "experiment"), defaults):
        side_data = saved.get(side)
        if side_data is None:
            side_data = {}
        if not isinstance(side_data, dict):
            raise ValueError(f"Saved {side} reaction must be a JSON object.")
        try:
            parsed.append(ReactionConfig({**side_defaults, **side_data}))
        except (TypeError, ValueError, OverflowError) as e:
            raise ValueError(f"Invalid {side} reaction value: {e}") from e
    return parsed[0], parsed[1]


class Element(dict):
    def __init__(self, data=None, Z: int = 14, percent_at: float = 100.0)->None: # Default: Si, 100% at.
        super().__init__()
        if data is not None:
            self.update(data)
        else:
            self["Z"] = Z
            self["percent_at"] = percent_at

class Layer(dict):
    def __init__(self, data=None, AD: float = 1000.0)->None:
        super().__init__()
        if data is not None:
            self.update(data)
            self["elements"] = [Element(data=el) for el in data["elements"]]
        else:
            self["areal_density"] = AD
            self["stopping"] = 0.01 # Dummy value
            self["elements"] = [Element()] 

    def normalize(self)->bool:
        total = sum(el["percent_at"] for el in self["elements"])
        if total != 100.0:
            for el in self["elements"]:
                el["percent_at"] = el["percent_at"] / total * 100.0
            return True
        return False

    def add_element(self)->None:
        self["elements"].append(Element())
    
    def remove_element(self, index:int)->None:
        if len(self["elements"]) > 1:
            del self["elements"][index]

    def lock_and_normalize(self, index_to_keep:int)->None:
        elements = self["elements"]
        percentages = [el["percent_at"] for el in elements]
        total = sum(percentages)

        if abs(total - 100.0) < 1e-9:
            return   # Already sums to 100

        fixed_value = percentages[index_to_keep]
        remaining = 100.0 - fixed_value
        current_other_sum = total - fixed_value

        if current_other_sum == 0:
            elements[index_to_keep]["percent_at"] = 100.0
        else:
            for i, el in enumerate(elements):
                if i != index_to_keep:
                    el["percent_at"] = el["percent_at"] / current_other_sum * remaining

    def find_element(self, Z: int = 1) -> float | None:
        """
        Returns the atomic percentage of element Z if found, None otherwise.
        """
        for element in self.get("elements", []):
            if element.get("Z") == Z:
                return element.get("percent_at", 0)
        return None

class Target(dict):
    def __init__(self)->None:
        self["layers"] = [Layer()] 

    def normalize_all_layers(self) -> None:
        for i, layer in enumerate(self["layers"]):
            if layer.normalize():
                print(f"Normalised target layer {i + 1}")

    def add_layer(self)->None:
        self["layers"].append(Layer())  
    
    def remove_layer(self, index:int)->None:
        if len(self["layers"]) > 1:
            del self["layers"][index]
    
    def duplicate_layer(self, index:int)->None:
        original_layer = self["layers"][index]
        duplicated_layer = copy.deepcopy(original_layer)
        self["layers"].insert(index + 1, duplicated_layer)

    def move_layer_up(self, index:int)->None:
        if index > 0:
            self["layers"][index - 1], self["layers"][index] = self["layers"][index], self["layers"][index - 1]
    
    def move_layer_down(self, index:int)->None:
        if index < len(self["layers"]) - 1:
            self["layers"][index + 1], self["layers"][index] = self["layers"][index], self["layers"][index + 1]

