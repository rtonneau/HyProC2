"""Build the desktop layout in visible sections; callbacks live in app.py.

Widgets belong to the window and are created exactly once. Scientific data
belongs to its Session, never to a widget. Construction order below matters:
menus create plot variables, shell creates parents, plots are built last.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from .simulation import STOPPING_MODELS, STRAGGLING_MODELS
from .target_editor import TargetEditor

if TYPE_CHECKING:
    from .app import HyProCApp


def create_widgets(app: "HyProCApp") -> None:
    _create_menu(app)
    _create_shell(app)
    _create_run_controls(app)
    _create_standard_controls(app)
    _create_options(app)
    _create_history(app)
    _create_target_editor(app)
    _create_excitation_plot(app)


def _create_menu(app: "HyProCApp") -> None:
    # Menu bar
    menubar = tk.Menu(app)
    app.config(menu=menubar)
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Load simulation", command=app.load_simulation)
    file_menu.add_command(label="Save simulation", command=app.save_simulation)

    target_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Target & Std", menu=target_menu)
    target_menu.add_command(label="Load target", command=app.load_target)
    target_menu.add_command(label="Save target", command=app.save_json)
    target_menu.add_separator()
    target_menu.add_command(label="Load standard", command=app.load_std)
    target_menu.add_command(label="Save standard", command=lambda: app.save_json(target_type="std"))

    plot_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Plot", menu=plot_menu)
    plot_menu.add_command(label="Rescale excitation curve", command=app.rescale_excitation_curve)
    app.autoscale_exc_bool = tk.BooleanVar(value=True)
    app.autoscale_menu = plot_menu
    plot_menu.add_checkbutton(label="Autoscale: ON", variable=app.autoscale_exc_bool)
    app.autoscale_menu_index = plot_menu.index("end")
    app.autoscale_exc_bool.trace_add("write", app.update_autoscale_menu_label)
    app.sim_markers_bool = tk.BooleanVar(value=True)
    plot_menu.add_checkbutton(label="Sim curve markers: ON", variable=app.sim_markers_bool)
    app.sim_markers_menu_index = plot_menu.index("end")
    app.sim_markers_bool.trace_add("write", app.update_sim_markers_menu_label)
    app.show_chi_energy_bounds_bool = tk.BooleanVar(value=True)
    plot_menu.add_checkbutton(label="Chi-squared energy bounds: ON", variable=app.show_chi_energy_bounds_bool)
    app.chi_energy_bounds_menu_index = plot_menu.index("end")
    app.show_chi_energy_bounds_bool.trace_add("write", app.update_chi_energy_bounds_menu_label)
    plot_menu.add_separator()
    plot_menu.add_command(label="Save simulated curve data", command=app.save_sim_curve_txt)
    plot_menu.add_command(label="Load sim curve as exp curve", command=app.generate_exp_from_sim)
    plot_menu.add_separator()
    plot_menu.add_command(label="Remove experimental curve", command=app.on_remove_exp)
    plot_menu.add_command(label="Remove simulated curve", command=app.on_remove_sim)
    plot_menu.add_separator()
    plot_menu.add_command(label="Reset Chi-squared history", command=app.reset_chi_history)

    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    settings_menu.add_command(label="Settings", command=app.open_settings)
    settings_menu.add_command(label="Reactions…", command=app.open_reactions)
    settings_menu.add_command(label="Manual", command=app.open_manual)


def _create_shell(app: "HyProCApp") -> None:
    # Main Frame
    app.main_frame = ttk.Frame(app)
    app.main_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("Center.TButton", font=("Segoe UI", 9), justify="center")
    style.configure("Center.TMenubutton", font=("Segoe UI", 9), justify="center")


def _create_run_controls(app: "HyProCApp") -> None:
    # Left Frame
    app.left_frame = ttk.Frame(app.main_frame, width=150)
    app.left_frame.pack(side="left", fill="y", expand=False, padx=5, pady=5)

    app.import_button = ttk.Button(app.left_frame, text="Import excitation curve", width=20, command=app.load_curve)
    app.import_button.pack(fill="x", padx=10, pady=(10, 0))

    app.run_frame = ttk.Frame(app.left_frame)
    app.run_frame.pack(fill="x", padx=10, pady=(0, 0))

    app.run_button = ttk.Button(
        app.run_frame, text="Run Calculation", command=lambda: app.start_calc(mode="normal"), style="Center.TButton"
    )
    app.run_button.pack(side="left", fill="x", expand=True, ipady=10)

    app.run_menu = tk.Menu(app, tearoff=0)
    app.run_menu.add_command(label="Run Calculation", command=lambda: app.start_calc(mode="normal"))
    app.run_menu.add_command(
        label="Run Calculation (custom energy range)", command=lambda: app.start_calc(mode="custom")
    )
    app.run_menu.add_command(
        label="Run Calculation (Loaded curve energy)", command=lambda: app.start_calc(mode="loaded_curve")
    )

    app.run_menu_button = ttk.Button(
        app.run_frame, text="▼", width=3, command=app._post_run_menu, style="Center.TButton"
    )
    app.run_menu_button.pack(side="left", ipady=10)

    app.extract_button = ttk.Button(app.left_frame, text="Extract profile", command=app.plot_depth_profile)
    app.extract_button.pack(fill="x", padx=10, pady=(0, 10), ipady=5)


def _create_standard_controls(app: "HyProCApp") -> None:
    # Standard frame
    app.std_frame = ttk.LabelFrame(app.left_frame, text="Standard")
    app.std_frame.pack(fill="x", expand=False, padx=10, pady=5)
    app.std_frame.grid_columnconfigure(1, weight=1)

    ttk.Label(app.std_frame, text="Yield (Count/µC):").grid(row=0, column=0, padx=(10, 0), pady=5, ipadx=10, sticky="e")
    app.standard_yield_entry = ttk.Entry(app.std_frame, width=10)
    app.standard_yield_entry.grid(row=0, column=1, padx=10, pady=(5, 0), sticky="we")

    app.load_std_button = ttk.Button(app.std_frame, text="Load", command=app.load_std)
    app.load_std_button.grid(row=1, column=0, padx=(10, 0), pady=5, sticky="we")
    app.save_std_button = ttk.Button(
        app.std_frame, text="Save", width=10, command=lambda: app.save_json(target_type="std")
    )
    app.save_std_button.grid(row=1, column=1, padx=10, pady=5, sticky="we")


def _create_options(app: "HyProCApp") -> None:
    # Options checkbox
    app.options_frame = ttk.LabelFrame(app.left_frame, text="Options")
    app.options_frame.pack(fill="x", expand=False, padx=10, pady=5)

    app.options_frame1 = ttk.Frame(app.options_frame)
    app.options_frame1.pack(fill="x", expand=False, padx=10, pady=(0, 5))
    app.options_frame1.grid_columnconfigure(1, weight=1)

    ttk.Label(app.options_frame1, text="Stopping model:").grid(row=0, column=0, padx=(0, 5), pady=(5, 0), sticky="w")
    app.stopping_model_combobox = ttk.Combobox(
        app.options_frame1,
        values=STOPPING_MODELS,
        state="readonly",
        width=10,
    )
    app.stopping_model_combobox.grid(row=0, column=1, padx=5, pady=(5, 0), sticky="we")
    app.stopping_model_combobox.set("SRIM")

    ttk.Label(app.options_frame1, text="Straggling model:").grid(row=1, column=0, padx=(0, 5), pady=(5, 0), sticky="w")
    app.straggling_model_combobox = ttk.Combobox(
        app.options_frame1, values=STRAGGLING_MODELS, state="readonly", width=10
    )
    app.straggling_model_combobox.grid(row=1, column=1, padx=5, pady=(5, 0), sticky="we")
    app.straggling_model_combobox.set("Rud corr")

    ttk.Label(app.options_frame1, text="Beam width SD (keV):").grid(
        row=2, column=0, padx=(0, 5), pady=(5, 0), sticky="e"
    )
    app.beam_width_entry = ttk.Entry(app.options_frame1, width=8)
    app.beam_width_entry.grid(row=2, column=1, padx=5, pady=(0, 0), sticky="e")

    ttk.Label(app.options_frame1, text="Offset (keV):").grid(row=3, column=0, padx=(0, 5), pady=5, sticky="e")
    app.offset_entry = ttk.Entry(app.options_frame1, width=8)
    app.offset_entry.grid(row=3, column=1, padx=5, pady=(0, 0), sticky="e")
    app.offset_entry.insert(0, "0.0")

    app.options_frame2 = ttk.Frame(app.options_frame)
    app.options_frame2.pack(fill="x", expand=False, padx=5, pady=0)

    app.doppler_var = tk.BooleanVar(value=True)
    app.options_doppler_entry = ttk.Checkbutton(app.options_frame2, text="Doppler", variable=app.doppler_var)
    app.options_doppler_entry.pack(padx=5, pady=(0, 0), anchor="w")

    app.save_broadening_var = tk.BooleanVar(value=False)
    app.broadSave_entry = ttk.Checkbutton(
        app.options_frame2, text="Save broadening data", variable=app.save_broadening_var
    )
    app.broadSave_entry.pack(padx=5, pady=0, anchor="w")

    app.track_target_var = tk.BooleanVar(value=False)
    app.TrackTargetChange_entry = ttk.Checkbutton(
        app.options_frame2, text="Track target changes", variable=app.track_target_var
    )
    app.TrackTargetChange_entry.pack(padx=5, pady=(0, 5), anchor="w")


def _create_history(app: "HyProCApp") -> None:
    # Chi-squared graph
    app.chi_frameLabel = ttk.LabelFrame(app.left_frame, text="Chi-squared history")
    app.chi_frameLabel.pack(fill="x", expand=False, padx=10, pady=5)

    app.chi_frame = ttk.Frame(app.chi_frameLabel)
    app.chi_frame.pack(side="left", fill="both", expand=True, padx=10, pady=(5, 10))

    app.chi_energy_range_frame = ttk.Frame(app.chi_frame)
    app.chi_energy_range_frame.pack(fill="x", padx=5, pady=(0, 6))
    ttk.Label(app.chi_energy_range_frame, text="Range (keV):").grid(row=0, column=0, columnspan=4, sticky="w")
    ttk.Label(app.chi_energy_range_frame, text="E Min").grid(row=1, column=0, padx=(10, 3), pady=(3, 0))
    app.chi_energy_min_entry = ttk.Entry(app.chi_energy_range_frame, width=7)
    app.chi_energy_min_entry.grid(row=1, column=1, padx=(0, 10), pady=(3, 0))
    app.chi_energy_min_entry.bind("<KeyRelease>", app.on_chi_energy_bounds_change)
    app.chi_energy_min_entry.bind("<FocusOut>", app.on_chi_energy_bounds_change)
    app.chi_energy_min_entry.bind("<Return>", app.on_chi_energy_bounds_change)
    ttk.Label(app.chi_energy_range_frame, text="E Max").grid(row=1, column=2, padx=(5, 3), pady=(3, 0))
    app.chi_energy_max_entry = ttk.Entry(app.chi_energy_range_frame, width=7)
    app.chi_energy_max_entry.grid(row=1, column=3, pady=(3, 0))
    app.chi_energy_max_entry.bind("<KeyRelease>", app.on_chi_energy_bounds_change)
    app.chi_energy_max_entry.bind("<FocusOut>", app.on_chi_energy_bounds_change)
    app.chi_energy_max_entry.bind("<Return>", app.on_chi_energy_bounds_change)

    app.figure1 = Figure(figsize=(2, 1.5), dpi=100, constrained_layout=True)
    app.ax1 = app.figure1.add_subplot()
    app.canvas1 = FigureCanvasTkAgg(app.figure1, master=app.chi_frame)
    app.canvas1.get_tk_widget().pack(expand=True, fill="both", pady=(5, 0))

    app.chi_bounds_legend_frame = ttk.Frame(app.chi_frame)
    app.chi_bounds_legend_frame.pack(fill="x", pady=(2, 0))
    tk.Label(app.chi_bounds_legend_frame, text="■ Current bounds", fg="cornflowerblue").pack(side="left")
    tk.Label(app.chi_bounds_legend_frame, text="■ Different bounds", fg="gray").pack(side="left", padx=(8, 0))

    app.chi_scroll_frame = ttk.Frame(app.chi_frame)
    app.chi_scroll_frame.pack(fill="x", pady=(10, 0))
    app.chi_scroll_frame.grid_columnconfigure((0, 1), weight=1, uniform="chi_scroll_buttons")
    ttk.Button(app.chi_scroll_frame, text="↑ Scroll Up ↑", command=app.scroll_up).grid(
        row=0, column=0, sticky="ew", padx=(5, 2)
    )
    ttk.Button(app.chi_scroll_frame, text="↓ Scroll Down ↓", command=app.scroll_down).grid(
        row=0, column=1, sticky="ew", padx=(2, 5)
    )


def _create_target_editor(app: "HyProCApp") -> None:
    app.target_notebook = ttk.Notebook(app.main_frame)
    app.target_notebook.pack(fill="both", expand=False, padx=10, pady=10)
    app.target_editor = TargetEditor(app.target_notebook, lambda: app.session.target)
    app.standard_editor = TargetEditor(app.target_notebook, lambda: app.session.standard, standard=True)
    app.target_notebook.add(app.target_editor, text="Target")
    app.target_notebook.add(app.standard_editor, text="Standard")


def _create_excitation_plot(app: "HyProCApp") -> None:
    # Canvas for excitation curves
    app.exc_curve_frameLabel = ttk.LabelFrame(app.main_frame, text="Excitation curves")
    app.exc_curve_frameLabel.pack(fill="both", expand=False, padx=10, pady=(5, 5))
    app.exc_curve_frame = ttk.Frame(app.exc_curve_frameLabel)
    app.exc_curve_frame.pack(side="left", fill="both", expand=True, padx=10, pady=(10, 0))

    app.figure0 = Figure(figsize=(10, 5), constrained_layout=True)
    app.ax0 = app.figure0.add_subplot()
    app.canvas = FigureCanvasTkAgg(app.figure0, master=app.exc_curve_frame)
    app.toolbar = NavigationToolbar2Tk(app.canvas, app.exc_curve_frame)
    app.toolbar.update()
    app.toolbar.pack(side="bottom", fill="x")
    app.canvas.get_tk_widget().pack(expand=True, fill="both")
