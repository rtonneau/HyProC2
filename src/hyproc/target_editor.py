"""Target and standard editors sharing the same composition-editing behavior."""

import math
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

import periodictable

from .models import Layer, Target


class TargetEditor(ttk.Frame):
    """Own widget selections while editing the current session's target.

    The provider is evaluated on each edit because loading or calculating may
    replace the target. Standard mode exposes only the first layer's composition,
    matching the original single-layer reference editor.
    """

    def __init__(self, parent, target: Callable[[], Target], *, standard: bool = False):
        super().__init__(parent)
        self._target = target
        self.standard = standard
        self.layer_index = 0
        self.element_index = 0
        self._refreshing = False
        if not standard:
            self._build_layers()
        self._build_composition()

    @property
    def layer(self) -> Layer:
        return self._target()["layers"][self.layer_index]

    def _build_layers(self) -> None:
        left = ttk.Frame(self)
        left.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        frame = ttk.LabelFrame(left, text="Layers", height=150)
        frame.pack(fill="x", padx=10)
        self.layers = tk.Listbox(frame, exportselection=False, height=8)
        self.layers.pack(fill="both", expand=True, padx=5, pady=5)
        self.layers.bind("<<ListboxSelect>>", self._select_layer)

        details = ttk.LabelFrame(left, text="Layer Details")
        details.pack(fill="x", padx=10, pady=5)
        ttk.Label(details, text="Areal density (TFU):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.density = ttk.Entry(details)
        self.density.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(details, text="").grid(row=1, column=0, padx=5, pady=5)
        self.density.bind("<FocusOut>", self._update_density)
        self.density.bind("<Return>", self._update_density)

        buttons = ttk.Frame(left)
        buttons.pack(padx=10, pady=5, anchor="center")
        for label, action, row, column in (
            ("Add Layer", "add", 0, 0),
            ("Remove Layer", "remove", 1, 0),
            ("Move Up", "up", 0, 1),
            ("Move Down", "down", 1, 1),
        ):
            ttk.Button(buttons, text=label, width=18, command=lambda action=action: self._edit_layers(action)).grid(
                row=row, column=column, padx=5
            )
        ttk.Button(buttons, text="Duplicate Layer", width=39, command=lambda: self._edit_layers("duplicate")).grid(
            row=2, column=0, columnspan=2, padx=5, pady=(5, 0)
        )

    def _build_composition(self) -> None:
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=(0, 10) if not self.standard else 10, pady=10)
        frame = ttk.LabelFrame(right, text="Elements", height=150)
        frame.pack(fill="x", padx=10)
        self.elements = tk.Listbox(frame, exportselection=False, height=8)
        self.elements.pack(fill="both", expand=True, padx=5, pady=5)
        self.elements.bind("<<ListboxSelect>>", self._select_element)

        details = ttk.LabelFrame(right, text="Elements Details")
        details.pack(fill="x", padx=10, pady=5)
        self.entries = {}
        for row, (key, label) in enumerate((("Z", "Z:"), ("percent_at", "% at:"))):
            ttk.Label(details, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(details)
            entry.grid(row=row, column=1, padx=5, pady=5)
            for event in ("<FocusOut>", "<Return>"):
                entry.bind(event, lambda event, key=key: self._update_element(key))
            self.entries[key] = entry
        buttons = ttk.Frame(right)
        buttons.pack(anchor="center", padx=10, pady=5)
        for row, (label, action) in enumerate(
            (("Add Element", "add"), ("Remove Element", "remove"), ("Isolate & Normalize", "normalize"))
        ):
            ttk.Button(buttons, text=label, width=30, command=lambda action=action: self._edit_elements(action)).grid(
                row=row, padx=5, pady=(5, 0) if row == 2 else 0
            )

    @staticmethod
    def _set_entry(entry, value) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    @staticmethod
    def _fill_list(widget, labels, selected) -> None:
        top = widget.nearest(0) if widget.size() else 0
        widget.delete(0, tk.END)
        for label in labels:
            widget.insert(tk.END, label)
        widget.select_set(selected)
        widget.yview(min(top, widget.size() - 1))

    def refresh(self, *, reset_selection: bool = False) -> None:
        """Reflect replacement/splitting while retaining valid selection and scroll."""
        self._refreshing = True
        try:
            if reset_selection:
                self.layer_index = self.element_index = 0
            layers = self._target()["layers"]
            self.layer_index = min(self.layer_index, len(layers) - 1)
            self.element_index = min(self.element_index, len(self.layer["elements"]) - 1)
            if not self.standard:
                labels = []
                for index, layer in enumerate(layers, start=1):
                    elements = sorted(layer["elements"], key=lambda element: element["percent_at"], reverse=True)
                    composition = ", ".join(
                        f"{periodictable.elements[e['Z']].symbol}{round(e['percent_at'])}" for e in elements
                    )
                    labels.append(f"Layer {index}: {layer['areal_density']} TFU ({composition})")
                self._fill_list(self.layers, labels, self.layer_index)
                self._set_entry(self.density, self.layer["areal_density"])
            labels = [
                f"{periodictable.elements[e['Z']].symbol} (Z={e['Z']}), {e['percent_at']:.2f} % at."
                for e in self.layer["elements"]
            ]
            self._fill_list(self.elements, labels, self.element_index)
            self._show_element()
        finally:
            self._refreshing = False

    def _show_element(self) -> None:
        element = self.layer["elements"][self.element_index]
        for key, entry in self.entries.items():
            self._set_entry(entry, element[key])

    def _select_layer(self, event=None) -> None:
        selected = self.layers.curselection()
        if self._refreshing or not selected or selected[0] == self.layer_index:
            return
        self.layer_index = selected[0]
        self.refresh()

    def _select_element(self, event=None) -> None:
        selected = self.elements.curselection()
        if self._refreshing or not selected:
            return
        self.element_index = selected[0]
        self._show_element()

    def _edit_layers(self, action: str) -> None:
        target = self._target()
        if action == "add":
            target.add_layer()
            self.layer_index = len(target["layers"]) - 1
            self.element_index = 0
        elif action == "remove":
            target.remove_layer(self.layer_index)
            self.layer_index = max(0, self.layer_index - 1)
            self.element_index = 0
        elif action == "duplicate":
            target.duplicate_layer(self.layer_index)
            self.layer_index += 1
        elif action == "up":
            target.move_layer_up(self.layer_index)
            self.layer_index = max(0, self.layer_index - 1)
        elif action == "down":
            target.move_layer_down(self.layer_index)
            self.layer_index = min(len(target["layers"]) - 1, self.layer_index + 1)
        self.refresh()
        if action == "add":
            self.layers.see(self.layer_index)

    def _edit_elements(self, action: str) -> None:
        if action == "add":
            self.layer.add_element()
            self.element_index = len(self.layer["elements"]) - 1
        elif action == "remove":
            self.layer.remove_element(self.element_index)
            self.element_index = max(0, self.element_index - 1)
        elif action == "normalize":
            self.layer.lock_and_normalize(self.element_index)
        self.refresh()
        if action == "add":
            self.elements.see(self.element_index)

    def _update_density(self, event=None) -> None:
        if self._refreshing or self.density.cget("state") == "disabled":
            return
        try:
            value = float(self.density.get())
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Areal density must be a finite positive number in TFU.")
            self.layer["areal_density"] = value
        except ValueError as error:
            messagebox.showerror("Invalid areal density", str(error), parent=self)
        self.refresh()

    def _update_element(self, key: str) -> None:
        if self._refreshing or self.entries[key].cget("state") == "disabled":
            return
        try:
            text = self.entries[key].get()
            value = int(text) if key == "Z" else float(text)
            if key == "Z" and not 1 <= value <= 118:
                raise ValueError("Atomic number must be an integer from 1 to 118.")
            if key == "percent_at" and (not math.isfinite(value) or not 0 <= value <= 100):
                raise ValueError("Atomic percentage must be between 0 and 100.")
            self.layer["elements"][self.element_index][key] = value
        except ValueError as error:
            messagebox.showerror("Invalid composition", str(error), parent=self)
        self.refresh()
