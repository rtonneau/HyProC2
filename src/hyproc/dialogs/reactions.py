import math
import tkinter as tk
from tkinter import messagebox, ttk

import periodictable

from ..config import save_default_reactions
from ..models import ReactionConfig

# (ReactionConfig key, label shown in the dialog, integer or float)
FIELDS = (
    ("Z1", "Z1 (beam)", int),
    ("A1", "A1 (beam)", int),
    ("Z2", "Z2 (profiled)", int),
    ("A2", "A2 (profiled)", int),
    ("E_R", "E_R (keV)", float),
    ("Gamma", "Γ (keV)", float),
    ("Sigma", "σ (mbarn)", float),
)
FIELD_LABELS = {key: label for key, label, _ in FIELDS}
SIDES = (("standard", "Standard"), ("experiment", "Experiment"))


def _parse(values: dict[str, str], key: str, kind: type) -> int | float:
    text = str(values.get(key, "")).strip()
    label = FIELD_LABELS[key]
    try:
        number = kind(text)
    except ValueError:
        raise ValueError(f"{label}: '{text}' is not a valid {'integer' if kind is int else 'number'}.") from None
    if not math.isfinite(number):
        raise ValueError(f"{label}: '{text}' is not a finite number.")
    return number


def validate_reaction(values: dict[str, str]) -> ReactionConfig:
    """Builds a ReactionConfig from the raw entry texts, raising ValueError (naming the field) if invalid."""
    parsed = {key: _parse(values, key, kind) for key, _, kind in FIELDS}

    for key in ("Z1", "Z2"):
        if parsed[key] < 1:
            raise ValueError(f"{FIELD_LABELS[key]}: Z must be at least 1.")
    for zkey, akey in (("Z1", "A1"), ("Z2", "A2")):
        z, a = parsed[zkey], parsed[akey]
        try:
            periodictable.elements[z][a]
        except KeyError:
            raise ValueError(f"{FIELD_LABELS[akey]}: A={a} is not a known isotope for Z={z}.") from None
    for key in ("E_R", "Gamma", "Sigma"):
        if parsed[key] <= 0:
            raise ValueError(f"{FIELD_LABELS[key]}: must be greater than 0.")
    return ReactionConfig(parsed)


class ReactionsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.withdraw()
        self.transient(parent)
        self.title("Reactions")

        self.entries: dict[str, dict[str, ttk.Entry]] = {side: {} for side, _ in SIDES}
        self._build_ui()
        self._position(parent)

        self.grab_set()
        self.deiconify()

    def _build_ui(self):
        reactions = {
            "standard": self.parent.session.standard_reaction,
            "experiment": self.parent.session.experiment_reaction,
        }
        for column, (side, title) in enumerate(SIDES, start=1):
            ttk.Label(self, text=title, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=column, padx=10, pady=5)
            for row, (key, _, _) in enumerate(FIELDS, start=1):
                entry = ttk.Entry(self, width=14)
                entry.insert(0, str(reactions[side][key]))
                entry.grid(row=row, column=column, padx=10, pady=2)
                self.entries[side][key] = entry
        for row, (_, label, _) in enumerate(FIELDS, start=1):
            ttk.Label(self, text=label).grid(row=row, column=0, padx=10, pady=2, sticky="w")

        buttons = ttk.Frame(self)
        buttons.grid(row=len(FIELDS) + 1, column=0, columnspan=3, pady=10)
        ttk.Button(buttons, text="Copy experiment → standard", command=self.copy_experiment_to_standard).pack(
            side="left", padx=5
        )
        ttk.Button(buttons, text="Save as default", command=self.save_as_default).pack(side="left", padx=5)
        ttk.Button(buttons, text="OK", command=self.ok).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _position(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def copy_experiment_to_standard(self):
        for key, _, _ in FIELDS:
            entry = self.entries["standard"][key]
            entry.delete(0, tk.END)
            entry.insert(0, self.entries["experiment"][key].get())

    def _validate_both(self) -> tuple[ReactionConfig, ReactionConfig] | None:
        """Validates both columns, showing an error naming the side and field; None if invalid."""
        configs = []
        for side, title in SIDES:
            values = {key: entry.get() for key, entry in self.entries[side].items()}
            try:
                configs.append(validate_reaction(values))
            except ValueError as e:
                messagebox.showerror("Invalid reaction", f"{title} reaction - {e}", parent=self)
                return None
        return configs[0], configs[1]

    def save_as_default(self):
        configs = self._validate_both()
        if configs is None:
            return
        try:
            save_default_reactions(*configs)
        except OSError as e:
            messagebox.showerror("Save failed", f"Could not save the default reactions:\n{e}", parent=self)
            return
        messagebox.showinfo("Saved", "Default reactions saved.", parent=self)

    def ok(self):
        configs = self._validate_both()
        if configs is None:
            return
        self.parent.session.standard_reaction, self.parent.session.experiment_reaction = configs
        self.destroy()

    def show(self):
        self.wait_window()
