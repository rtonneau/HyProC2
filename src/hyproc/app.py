"""Desktop adapter for the headless simulation workflow.

Session owns scientific data; this window owns widgets, selections and job
lifetime. All widget access stays on the main thread. Layout construction is in
app_layout; parsing and persistence are in file_io.
"""

import logging
import os
import subprocess
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Literal

import numpy as np
import periodictable
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import app_layout, file_io, simulation
from .config import data_path, default_reactions, load_settings, settings_path
from .dialogs.energy_range import EnergyRangeDialog
from .dialogs.import_selection import SheetSelectionDialog, TableSelectionDialog
from .dialogs.reactions import ReactionsDialog
from .dialogs.settings import SettingsDialog
from .models import Session


class HyProCApp(tk.Tk):
    """Tk adapter: collect inputs, manage editing, and present completed results."""

    def __init__(self):
        super().__init__()

        self.settings_path = settings_path()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        self.title("HyProC")
        self.geometry("850x900")

        self.style = ttk.Style(self)

        self.style.configure("Default.TButton", background="#f0f0f0", foreground="black")
        self.style.configure("Working.TButton", background="orange", foreground="black")

        # Load settings for constants
        standard_reaction, experiment_reaction = default_reactions()
        self.session = Session(standard_reaction=standard_reaction, experiment_reaction=experiment_reaction)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hyproc-calculation")
        self.pending_calculation = None
        self._disabled_controls = []
        self.profile_window = None

        self.run_number = 0

        self.session.chi_start = 0
        self.visible_count = 9

        app_layout.create_widgets(self)
        self.target_editor.refresh()
        self.standard_editor.refresh()
        self.rescale_excitation_curve()
        self.update_chi_plot()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _post_run_menu(self) -> None:
        x = self.run_menu_button.winfo_rootx()
        y = self.run_menu_button.winfo_rooty() + self.run_menu_button.winfo_height()
        self.run_menu.post(x, y)

    def update_chi_plot(self) -> None:
        self.ax1.clear()
        visible_values = self.session.chi_squared[self.session.chi_start : self.session.chi_start + self.visible_count]
        y_positions = range(len(visible_values))

        try:
            min_text = self.chi_energy_min_entry.get().strip()
            max_text = self.chi_energy_max_entry.get().strip()
            current_bounds = (
                float(min_text) if min_text else None,
                float(max_text) if max_text else None,
            )
            if any(value is not None and not np.isfinite(value) for value in current_bounds):
                current_bounds = None
            elif (
                current_bounds[0] is not None
                and current_bounds[1] is not None
                and current_bounds[0] > current_bounds[1]
            ):
                current_bounds = None
        except ValueError:
            current_bounds = None

        history_bounds = self.session.chi_bounds
        visible_bounds = history_bounds[self.session.chi_start : self.session.chi_start + self.visible_count]
        bar_colors = [
            "cornflowerblue" if used_bounds is not None and used_bounds == current_bounds else "gray"
            for used_bounds in visible_bounds
        ]
        if len(bar_colors) < len(visible_values):
            bar_colors.extend(["gray"] * (len(visible_values) - len(bar_colors)))

        bars = self.ax1.barh(y_positions, visible_values, color=bar_colors, height=0.8)

        self.ax1.invert_yaxis()
        self.ax1.set_yticks(y_positions)
        self.ax1.set_yticklabels([str(i + self.session.chi_start) for i in y_positions])
        self.ax1.set_ylim(self.visible_count - 0.5, -0.5)

        for i, (bar, val) in enumerate(zip(bars, visible_values)):
            self.ax1.text(val + 2, bar.get_y() + bar.get_height() / 2, f"{val}", va="center", ha="left", fontsize=7)

        if len(self.session.chi_squared) == 0:
            xmax = 10
        else:
            xmax = max(visible_values) + 10
        self.ax1.set_xlim(0, xmax)
        self.ax1.xaxis.set_visible(False)
        for spine in self.ax1.spines.values():
            spine.set_visible(False)

        self.canvas1.draw()

    def on_chi_energy_bounds_change(self, event=None) -> None:
        self.update_exc_plot()
        self.update_chi_plot()

    def scroll_up(self) -> None:
        if self.session.chi_start > 0:
            self.session.chi_start -= 1
            self.update_chi_plot()

    def scroll_down(self) -> None:
        if self.session.chi_start + self.visible_count < len(self.session.chi_squared):
            self.session.chi_start += 1
            self.update_chi_plot()

    def update_exc_plot(self, event=None, preserve_view: bool = True) -> None:
        has_existing_curve = bool(self.session.experimental_energy) or bool(self.session.simulated_energy)
        preserve_view = preserve_view and has_existing_curve
        if preserve_view:
            x_limits = self.ax0.get_xlim()
            y_limits = self.ax0.get_ylim()

        self.ax0.clear()

        has_experimental = bool(self.session.experimental_yield)
        has_simulated = bool(self.session.simulated_yield)

        if has_experimental:
            self.ax0.scatter(
                self.session.experimental_energy,
                self.session.experimental_yield,
                label="Exp",
                marker=".",
                color="tab:blue",
            )
            self.ax0.errorbar(
                self.session.experimental_energy,
                self.session.experimental_yield,
                self.session.experimental_error,
                fmt="none",
                color="tab:blue",
            )

        if has_simulated:
            marker = "." if self.sim_markers_bool.get() else None
            self.ax0.plot(
                self.session.simulated_energy,
                self.session.simulated_yield,
                label="Sim",
                linestyle="--",
                marker=marker,
                color="tab:orange",
            )

        legend = self.ax0.legend(loc="best") if has_experimental or has_simulated else None

        self.ax0.set_xlabel("Energy (keV)")
        self.ax0.set_ylabel("Yield (Count/µC)")
        self.ax0.set_ylim(bottom=0)
        self.ax0.grid(alpha=0.4)
        if preserve_view:
            self.ax0.set_xlim(x_limits)
            self.ax0.set_ylim(y_limits)

        show_bounds = self.show_chi_energy_bounds_bool.get()
        if legend is not None and show_bounds:
            self.canvas.draw()
            renderer = self.canvas.get_renderer()
            legend_bbox = legend.get_window_extent(renderer)
            legend_anchor = legend_bbox.transformed(self.ax0.transAxes.inverted())
            border_padding = legend.borderaxespad * legend.prop.get_size_in_points() * self.figure0.dpi / 72
            legend.set_bbox_to_anchor(
                (
                    legend_anchor.x0 - border_padding / self.ax0.bbox.width,
                    legend_anchor.y0 - border_padding / self.ax0.bbox.height,
                ),
                transform=self.ax0.transAxes,
            )
            legend.set_loc("lower left")

        if show_bounds:
            self.canvas.draw()
            x_limits = self.ax0.get_xlim()
            for entry in (self.chi_energy_min_entry, self.chi_energy_max_entry):
                try:
                    energy_bound = float(entry.get().strip())
                except ValueError:
                    continue
                if np.isfinite(energy_bound):
                    self.ax0.axvline(energy_bound, linestyle=":", color="gray")
            self.ax0.set_xlim(x_limits)

        self.canvas.draw()

    def rescale_excitation_curve(self) -> None:
        self.update_exc_plot(preserve_view=False)

    def update_autoscale_menu_label(self, *_args) -> None:
        state = "ON" if self.autoscale_exc_bool.get() else "OFF"
        self.autoscale_menu.entryconfigure(self.autoscale_menu_index, label=f"Autoscale: {state}")

    def update_sim_markers_menu_label(self, *_args) -> None:
        state = "ON" if self.sim_markers_bool.get() else "OFF"
        self.autoscale_menu.entryconfigure(self.sim_markers_menu_index, label=f"Sim markers: {state}")
        self.update_exc_plot()

    def update_chi_energy_bounds_menu_label(self, *_args) -> None:
        state = "ON" if self.show_chi_energy_bounds_bool.get() else "OFF"
        self.autoscale_menu.entryconfigure(
            self.chi_energy_bounds_menu_index, label=f"Chi-squared energy bounds: {state}"
        )
        self.update_exc_plot()

    def load_curve(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Excitation Curve", filetypes=[("Curve Files", "*.xlsx *.xls *.csv *.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            columns = load_settings()["import_curve"]["columns"]
            if Path(path).suffix.lower() in (".xlsx", ".xls"):
                sheets = file_io.excel_tables(path, columns)
                if not sheets:
                    raise ValueError("No sheet containing the expected headers was found.")
                sheet = next(iter(sheets)) if len(sheets) == 1 else SheetSelectionDialog(self, list(sheets)).show()
                if sheet is None:
                    return
                frame = sheets[sheet]
                rows = file_io.header_rows(frame, [columns["energy"], columns["yield"]])
                if len(rows) == 1:
                    row = rows[0]
                    count = file_io.count_datapoints(frame, row)
                else:
                    selection = TableSelectionDialog(self, frame, rows, file_io.count_datapoints).show()
                    if selection is None:
                        return
                    row, count = selection
                curve = file_io.read_excel_curve(path, sheet, row, count, columns)
            else:
                curve = file_io.read_text_curve(path, columns)
        except (OSError, ValueError, TypeError, KeyError, ImportError) as error:
            messagebox.showerror("Loading Error", f"Failed to load the curve.\n\n{error}", parent=self)
            return
        self.session.experimental_energy, self.session.experimental_yield, self.session.experimental_error = curve
        self.rescale_excitation_curve()

    def load_std(self) -> None:
        file_path = filedialog.askopenfilename(title="Load Standard", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        try:
            standard = file_io.load_target(file_path)
            layers = standard["layers"]

            index = self.ask_layer(layers) if len(layers) > 1 else 0
            if index is None:
                return
            self.session.standard = simulation.prepare_standard(
                standard, index, self.session.standard_reaction, self._get_stopping_model()
            )

            print("Standard loaded")
            self.standard_editor.refresh()
            self.target_notebook.select(self.standard_editor)  # Switch to the relevent tab

        except (OSError, KeyError, TypeError, ValueError) as e:
            messagebox.showerror(
                "Loading Error", f"Couldn't load the standard or calculate its stopping cross section.\n\n{e}"
            )

    def ask_layer(self, layers: list) -> int:
        """ "
        If multiple layers are found in the loaded standard, ask the user which one to keep.
        """
        popup = tk.Toplevel()
        popup.transient(self)
        popup.grab_set()
        popup.title("Select Layer")

        ttk.Label(
            popup,
            text="Multiple layers found. A standard should have a uniform composition and thus only one layer.\n\nSelect which layer to keep:",
            wraplength=300,
        ).pack(pady=5)

        def layer_label(i, layer):
            elements = sorted(layer.get("elements", []), key=lambda e: e.get("percent_at", 0), reverse=True)
            elements_str = ", ".join(
                f"{periodictable.elements[el['Z']].symbol}{int(el['percent_at'])}" for el in elements
            )
            return f"Layer {i + 1}: {layer['areal_density']} TFU ({elements_str})"

        options = [layer_label(i, layer) for i, layer in enumerate(layers)]
        selected = tk.StringVar(value=options[0])
        dropdown = ttk.Combobox(popup, textvariable=selected, values=options, state="readonly", width=50)
        dropdown.pack(pady=5)

        result = [None]

        def confirm():
            result[0] = options.index(selected.get())
            popup.destroy()

        ttk.Button(popup, text="Confirm", command=confirm).pack(pady=5)

        # Centering the popup on main window
        popup.withdraw()
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"400x150+{x}+{y}")
        popup.deiconify()

        popup.wait_window()
        return result[0]

    def load_target(self) -> None:
        path = filedialog.askopenfilename(title="Load Target", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            target = file_io.load_target(path)
        except (OSError, KeyError, TypeError, ValueError) as error:
            messagebox.showerror("Loading Error", f"Couldn't load the target.\n\n{error}", parent=self)
            return
        self.session.target = target
        self.target_editor.refresh(reset_selection=True)
        self.target_editor.refresh()
        self.target_notebook.select(self.target_editor)

    def save_simulation(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Save Simulation"
        )
        if not path:
            return
        try:
            file_io.save_simulation(path, self.session, self._read_options())
        except (OSError, TypeError, ValueError) as error:
            messagebox.showerror("Save Simulation", f"Couldn't save the simulation.\n\n{error}", parent=self)

    def load_simulation(self) -> None:
        path = filedialog.askopenfilename(title="Load Simulation", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            session, options = file_io.load_simulation(path, default_reactions())
        except (OSError, AttributeError, KeyError, TypeError, ValueError) as error:
            messagebox.showerror("Load Simulation", f"Couldn't load the simulation.\n\n{error}", parent=self)
            return
        self.session = session
        self.session.chi_start = max(0, min(session.chi_start, max(0, len(session.chi_squared) - self.visible_count)))
        self.target_editor.refresh(reset_selection=True)
        self.standard_editor.refresh(reset_selection=True)
        self._apply_options(options)
        self.target_editor.refresh()
        self.standard_editor.refresh()
        self.rescale_excitation_curve()
        self.update_chi_plot()
        self.target_notebook.select(self.target_editor)

    def _apply_options(self, options: dict) -> None:
        entries = {
            "standard_yield": self.standard_yield_entry,
            "beam_width": self.beam_width_entry,
            "offset": self.offset_entry,
            "chi_energy_min": self.chi_energy_min_entry,
            "chi_energy_max": self.chi_energy_max_entry,
        }
        for key, entry in entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, options[key])
        self.stopping_model_combobox.set(options["stopping_model"])
        self.straggling_model_combobox.set(options["straggling_model"])
        flags = {
            "doppler": self.doppler_var,
            "save_broadening_data": self.save_broadening_var,
            "track_target_changes": self.track_target_var,
            "autoscale": self.autoscale_exc_bool,
            "sim_markers": self.sim_markers_bool,
            "show_chi_energy_bounds": self.show_chi_energy_bounds_bool,
        }
        for key, variable in flags.items():
            variable.set(options[key])

    def generate_exp_from_sim(self) -> None:
        try:
            simulation.use_simulated_curve_as_experiment(self.session)
        except ValueError as error:
            messagebox.showerror("Generate curve", str(error), parent=self)
            return
        self.update_exc_plot()

    def on_remove_exp(self) -> None:
        self.session.experimental_yield = []
        self.session.experimental_error = []
        self.update_exc_plot()

    def on_remove_sim(self) -> None:
        self.session.simulated_yield = []
        self.session.simulated_energy = []
        self.update_exc_plot()

    def reset_chi_history(self) -> None:
        self.session.chi_squared = []
        self.session.chi_bounds = []
        self.session.chi_start = 0
        self.update_chi_plot()

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings_path)
        dialog.show()

    def open_reactions(self):
        dialog = ReactionsDialog(self)
        dialog.show()

    def open_manual(self):
        manual_path = str(data_path("HyProC_Manual.pdf"))
        if sys.platform == "win32":
            os.startfile(manual_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", manual_path])
        else:
            subprocess.run(["xdg-open", manual_path])

    def ask_energy_range(
        self, offset: float = 0.0
    ) -> tuple[float, float, float] | tuple[float, float, int, list[float]] | None:
        dialog = EnergyRangeDialog(
            self,
            offset=offset,
            e_min=self.session.energy_min,
            e_max=self.session.energy_max,
            step_size=self.session.energy_step,
            sim_energy=self.session.simulated_energy,
        )
        return dialog.show()

    def _get_stopping_model(self) -> str:
        return self.stopping_model_combobox.get()

    def _read_options(self) -> dict:
        """Retain entry text in saved files; numeric validation happens at run time."""
        return {
            "standard_yield": self.standard_yield_entry.get(),
            "beam_width": self.beam_width_entry.get(),
            "offset": self.offset_entry.get(),
            "stopping_model": self.stopping_model_combobox.get(),
            "straggling_model": self.straggling_model_combobox.get(),
            "doppler": self.doppler_var.get(),
            "save_broadening_data": self.save_broadening_var.get(),
            "track_target_changes": self.track_target_var.get(),
            "autoscale": self.autoscale_exc_bool.get(),
            "sim_markers": self.sim_markers_bool.get(),
            "show_chi_energy_bounds": self.show_chi_energy_bounds_bool.get(),
            "chi_energy_min": self.chi_energy_min_entry.get(),
            "chi_energy_max": self.chi_energy_max_entry.get(),
        }

    def start_calc(self, mode: simulation.RunMode = "normal") -> None:
        """Read widgets on the Tk thread; submit only a data snapshot to the worker."""
        if self.pending_calculation is not None:
            return
        try:
            options = simulation.CalculationOptions.from_mapping(self._read_options())
            energies = simulation.select_energies(self.session, options.offset, mode)
            if energies is None:
                selection = self.ask_energy_range(options.offset)
                if selection is None:
                    return
                if len(selection) == 4:
                    energies = list(selection[3])  # Dialog has already subtracted the offset.
                else:
                    self.session.energy_min, self.session.energy_max, self.session.energy_step = selection
                    displayed = simulation.generate_energies(*selection)
                    energies = simulation.select_energies(self.session, options.offset, "custom", displayed)
            settings = load_settings()
            output_directory = None
            if options.save_broadening or options.track_target:
                save_root = Path(settings["save_path"])
                if not save_root.is_dir():
                    raise ValueError("Save path not found. Please check your settings.")
                output_directory = save_root / "HyProC" / f"Session {self.timestamp}" / f"Run {self.run_number}"
                attempt = self.run_number
                while output_directory.exists():
                    attempt += 1
                    output_directory = output_directory.parent / f"Run {attempt}"
            request = simulation.CalculationRequest.from_session(self.session, energies, options, output_directory)
            self._set_busy(True)
            self.pending_calculation = self.executor.submit(simulation.run_simulation, request)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            self._set_busy(False)
            messagebox.showerror("Calculation failed", str(error), parent=self)
            return
        self.after(50, self._poll_calculation)

    def _set_busy(self, busy: bool) -> None:
        """Prevent edits from being overwritten by a completed input snapshot."""
        if busy:

            def disable(widget):
                if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton, tk.Listbox)):
                    self._disabled_controls.append((widget, str(widget.cget("state"))))
                    widget.configure(state="disabled")
                if isinstance(widget, tk.Menu):
                    for index in range((widget.index("end") or 0) + 1):
                        if widget.type(index) not in ("separator", "tearoff"):
                            self._disabled_controls.append((widget, index, widget.entrycget(index, "state")))
                            widget.entryconfigure(index, state="disabled")
                for child in widget.winfo_children():
                    disable(child)

            disable(self)
            self.run_button.configure(text="Working...")
        else:
            for control in self._disabled_controls:
                if len(control) == 2:
                    widget, state = control
                    widget.configure(state=state)
                else:
                    widget, index, state = control
                    widget.entryconfigure(index, state=state)
            self._disabled_controls.clear()
            self.run_button.configure(text="Run Calculation")

    def _poll_calculation(self) -> None:
        """The worker never calls Tk, even to schedule a callback or show errors."""
        if not self.pending_calculation.done():
            self.after(50, self._poll_calculation)
            return
        try:
            result = self.pending_calculation.result()
            self._set_busy(False)
            simulation.apply_result(self.session, result)
            self.run_number += 1
            self.target_editor.refresh()
            self.standard_editor.refresh()
            self.update_exc_plot(preserve_view=not self.autoscale_exc_bool.get())
            if len(self.session.chi_squared) > self.visible_count:
                self.scroll_down()
            self.update_chi_plot()
            if result.layers_segmented:
                messagebox.showinfo(
                    "Calculations",
                    "At least one layer has been segmented to more accurately describe stopping cross sections.",
                    parent=self,
                )
        except Exception as error:
            logging.getLogger(__name__).exception("Calculation failed")
            messagebox.showerror("Calculation failed", str(error), parent=self)
        finally:
            self.pending_calculation = None
            self._set_busy(False)

    def _close_depth_profile(self) -> None:
        self.profile_window.destroy()
        self.profile_window = None

    def plot_depth_profile(self) -> None:
        x, y = simulation.depth_profile(self.session.target, self.session.experiment_reaction)

        if self.profile_window is not None and self.profile_window.winfo_exists():
            self.profile_window.lift()

        else:
            self.profile_window = tk.Toplevel(self)
            self.profile_window.title(
                f"{periodictable.elements[self.session.experiment_reaction['Z2']].name.capitalize()} Profile"
            )
            fig = Figure(figsize=(8, 5))
            ax = fig.add_subplot()
            canvas_H = FigureCanvasTkAgg(fig, master=self.profile_window)
            canvas_H.draw()
            canvas_H.get_tk_widget().pack(fill="both", expand=True)

            toolbar = NavigationToolbar2Tk(canvas_H, self.profile_window)
            toolbar.update()
            toolbar.pack(fill="x")

            self.profile_window.fig = fig
            self.profile_window.ax = ax
            self.profile_window.canvas = canvas_H

            self.profile_window.update_idletasks()
            x_win = self.winfo_x() + (self.winfo_width() // 2) - (self.profile_window.winfo_width() // 2)
            y_win = self.winfo_y() + (self.winfo_height() // 2) - (self.profile_window.winfo_height() // 2)
            self.profile_window.geometry(f"800x600+{x_win}+{y_win}")

            self.profile_window.protocol("WM_DELETE_WINDOW", self._close_depth_profile)

        ax = self.profile_window.ax
        ax.clear()
        ax.step(x, y, where="pre", linewidth=2, color="tab:red")
        ax.set_xlabel("x (TFU)", fontsize=16)
        ax.set_ylabel(
            f"{periodictable.elements[self.session.experiment_reaction['Z2']].symbol} content (at. %)", fontsize=16
        )
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0.01)
        ax.set_ylim(top=max(y) + 9)
        ax.grid()
        ax.grid(which="minor")
        highlight_ranges = list(zip(x[:-1], x[1:]))

        # labels = ['Matrice C', 'Matrice Ti','','','']
        # legend_patches = [Patch(facecolor=colors[i], alpha=0.999, label=labels[i])

        # ax = plt.gca()
        colors = ["#cfcfcf" if i % 2 == 0 else "#f0f0f0" for i, _ in enumerate(highlight_ranges)]

        # Changing the background of the graph
        for i, (start, end) in enumerate(highlight_ranges):
            ax.axvspan(start, end, color=colors[i % len(colors)], alpha=0.85)
            pass

        # Add text labels above each step
        disp_y_shift = 1 * max(y) / 100 if not max(y) == 0 else 0.05
        for i in range(1, len(x) - 1):
            x_mid = (x[i - 1] + x[i]) / 2  # midpoint of the horizontal segment
            y_pos = y[i]
            ax.text(
                x_mid, y_pos + disp_y_shift, str(x[i] - x[max(i - 1, 0)]) + " TFU", ha="center", va="bottom", fontsize=9
            )
            ax.text(x_mid, y_pos + 5 * disp_y_shift, f"{y[i]:.2f} %", ha="center", va="bottom", fontsize=12)

        # Adjust the last point: center relative to previous x
        x_last = (x[-2] + x[-1]) / 2  # midpoint between last two x
        y_last = y[-1]
        ax.text(x_last, y_last + disp_y_shift, str(x[-1] - x[-2]) + " TFU", ha="center", va="bottom", fontsize=9)
        ax.text(x_last, y_last + 5 * disp_y_shift, f"{y_last:.2f} %", ha="center", va="bottom", fontsize=12)

        self.profile_window.canvas.draw_idle()

    def save_json(self, target_type: Literal["target", "std"] = "target", savepath: str | None = None) -> bool:
        """Return success so cancelling a save also cancels closing the window."""
        path = savepath or filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Save JSON File"
        )
        if not path:
            return False
        try:
            file_io.save_target(path, self.session.standard if target_type == "std" else self.session.target)
        except (OSError, TypeError, ValueError) as error:
            messagebox.showerror("Save target", str(error), parent=self)
            return False
        return True

    def save_sim_curve_txt(self) -> None:
        if not self.session.simulated_yield:
            messagebox.showwarning("Save simulated curve", "No simulated excitation curve to save", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("TXT file", "*.txt")], title="Save Simulated curve"
        )
        if not path:
            return
        try:
            file_io.save_curve(path, self.session.simulated_energy, self.session.simulated_yield)
        except OSError as error:
            messagebox.showerror("Save simulated curve", str(error), parent=self)

    def on_close(self) -> None:
        if self.pending_calculation is not None:
            messagebox.showinfo(
                "Calculation running", "Please wait for the calculation to finish before closing.", parent=self
            )
            return
        exitDialogResult = messagebox.askyesnocancel("Quit", "Save the target before closing?")
        if exitDialogResult is None:
            return
        if exitDialogResult and not self.save_json():
            return
        self.executor.shutdown(wait=False)
        self.destroy()


def main() -> None:
    app = HyProCApp()
    app.mainloop()


# Run app
if __name__ == "__main__":
    main()
