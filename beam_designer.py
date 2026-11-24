"""Tkinter desktop beam designer. Reference properties are for educational use."""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk


COLORS = {
    "navy": "#1d2d44", "text": "#172033", "muted": "#657184",
    "line": "#dfe4ea", "panel": "#f7f8fa", "blue": "#3978b8",
    "teal": "#148f91", "amber": "#d29536", "red": "#bd3f48",
    "green": "#32855d", "purple": "#7560a6", "white": "#ffffff",
}

MATERIALS = {
    "Steel": {
        "A36 Steel": {"id": "a36", "E": 29_000_000, "allowable": 22_000, "proportional": 36_000,
                      "units": {"E": "psi", "allowable": "psi", "proportional": "psi"},
                      "source": "Typical structural-steel reference"},
        "A992 Steel": {"id": "a992", "E": 29_000_000, "allowable": 33_000, "proportional": 50_000,
                       "units": {"E": "psi", "allowable": "psi", "proportional": "psi"},
                       "source": "Typical structural-steel reference"},
    },
    "Lumber": {
        "Douglas Fir-Larch No.2": {"id": "df2", "E": 1_600_000, "allowable": 900, "proportional": 6_000,
                                   "units": {"E": "psi", "allowable": "psi", "proportional": "psi"},
                                   "source": "Common dimensional-lumber reference"},
        "Spruce-Pine-Fir No.2": {"id": "spf2", "E": 1_400_000, "allowable": 875, "proportional": 5_500,
                                 "units": {"E": "psi", "allowable": "psi", "proportional": "psi"},
                                 "source": "Common dimensional-lumber reference"},
    },
}

SECTIONS = {
    "Steel": {
        "W12×26": {"id": "w12x26", "A": 7.65, "I": 204.0, "S": 33.4,
                   "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "AISC tabulated properties"},
        "W12×30": {"id": "w12x30", "A": 8.79, "I": 238.0, "S": 38.6,
                   "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "AISC tabulated properties"},
        "W10×22": {"id": "w10x22", "A": 6.49, "I": 118.0, "S": 23.2,
                   "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "AISC tabulated properties"},
    },
    "Lumber": {
        "2×8": {"id": "2x8", "A": 10.875, "I": 47.63, "S": 12.0,
                "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "Nominal 2×8, actual 1.5×7.25 in"},
        "2×10": {"id": "2x10", "A": 13.875, "I": 98.93, "S": 21.39,
                 "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "Nominal 2×10, actual 1.5×9.25 in"},
        "2×12": {"id": "2x12", "A": 16.875, "I": 178.0, "S": 31.64,
                 "units": {"A": "in²", "I": "in⁴", "S": "in³"}, "source": "Nominal 2×12, actual 1.5×11.25 in"},
    },
}


@dataclass
class Load:
    kind: str
    magnitude: float
    position: float = 0.0
    start: float = 0.0
    end: float = 0.0


def analyze_beam(length: float, section: dict, material: dict, allowable: float,
                 support: str, loads: list[Load]) -> dict | None:
    """Analyze a beam using the same calculation path as the desktop UI."""
    if (not math.isfinite(length) or length <= 0 or not math.isfinite(allowable)
            or allowable <= 0 or support not in ("Simply supported", "Cantilever")):
        return None
    if not all(math.isfinite(load.magnitude) and load.magnitude != 0 for load in loads):
        return None
    valid_loads: list[Load] = []
    for load in loads:
        if load.kind == "point" and math.isfinite(load.position) and 0 <= load.position <= length:
            valid_loads.append(load)
        elif (load.kind == "uniform" and math.isfinite(load.start) and math.isfinite(load.end)
              and 0 <= load.start < load.end <= length):
            valid_loads.append(load)
    if len(valid_loads) != len(loads):
        return None

    total_load = 0.0
    load_moment = 0.0
    for load in valid_loads:
        if load.kind == "point":
            total_load += load.magnitude
            load_moment += load.magnitude * load.position
        else:
            resultant = load.magnitude * (load.end - load.start)
            total_load += resultant
            load_moment += resultant * (load.start + load.end) / 2
    if support == "Simply supported":
        rb = load_moment / length
        ra = total_load - rb
        reactions = f"A {ra:.2f} kip   ·   B {rb:.2f} kip"
    else:
        ra, rb = total_load, 0.0
        reactions = f"Fixed reaction {ra:.2f} kip   ·   Moment {load_moment:.2f} kip-ft"

    # Include all load breakpoints so point and partial uniform loads are
    # represented at their exact positions in the diagrams and integration.
    count = 500
    xs = sorted({length * i / count for i in range(count + 1)} |
                {q for load in valid_loads for q in
                 ((load.position,) if load.kind == "point" else (load.start, load.end))})
    shears: list[float] = []
    moments: list[float] = []
    for x in xs:
        if support == "Simply supported":
            shear = ra
            moment = ra * x
            for load in valid_loads:
                if load.kind == "point":
                    if x > load.position:
                        shear -= load.magnitude
                        moment -= load.magnitude * (x - load.position)
                elif x > load.start:
                    loaded_length = max(0.0, min(x, load.end) - load.start)
                    shear -= load.magnitude * loaded_length
                    moment -= load.magnitude * loaded_length * (x - (load.start + min(x, load.end)) / 2)
        else:
            shear = 0.0
            moment = 0.0
            for load in valid_loads:
                if load.kind == "point" and x < load.position:
                    shear += load.magnitude
                    moment -= load.magnitude * (load.position - x)
                elif load.kind == "uniform":
                    start = max(x, load.start)
                    if load.end > start:
                        loaded_length = load.end - start
                        shear += load.magnitude * loaded_length
                        moment -= load.magnitude * loaded_length * ((load.end + start) / 2 - x)
        shears.append(shear)
        moments.append(moment)

    # Integrate EI*v'' = M in inch units. The simply supported beam gets
    # a linear correction so both end deflections are zero.
    curvature = [moment * 12_000 / (material["E"] * section["I"]) for moment in moments]
    slopes = [0.0]
    deflections = [0.0]
    for i in range(1, len(xs)):
        dx_in = (xs[i] - xs[i - 1]) * 12
        slopes.append(slopes[-1] + (curvature[i - 1] + curvature[i]) * 0.5 * dx_in)
        deflections.append(deflections[-1] + (slopes[i - 1] + slopes[i]) * 0.5 * dx_in)
    if support == "Simply supported" and length:
        end_drift = deflections[-1]
        deflections = [v - end_drift * x / length for x, v in zip(xs, deflections)]

    def maximum(values: list[float]) -> tuple[float, float]:
        i = max(range(len(values)), key=lambda j: abs(values[j]))
        return abs(values[i]), xs[i]

    max_shear, shear_x = maximum(shears)
    max_moment, moment_x = maximum(moments)
    max_deflection, deflection_x = maximum(deflections)
    stress = max_moment * 12_000 / section["S"]
    limit = length * 12 / 360
    return {
        "length": length, "section": section, "material": material,
        "allowable": allowable, "support": support, "loads": valid_loads,
        "xs": xs, "shears": shears, "moments": moments, "deflections": deflections,
        "ra": ra, "rb": rb, "reactions": reactions, "max_shear": max_shear,
        "shear_x": shear_x, "max_moment": max_moment, "moment_x": moment_x,
        "max_deflection": max_deflection, "deflection_x": deflection_x,
        "stress": stress, "limit": limit,
    }


def tooltip(widget: tk.Widget, text: str) -> None:
    """Attach a small help bubble to a control."""
    tip = tk.Toplevel(widget)
    tip.withdraw()
    tip.overrideredirect(True)
    label = tk.Label(tip, text=text, background="#fff8df", foreground=COLORS["text"],
                     relief="solid", borderwidth=1, padx=7, pady=4, wraplength=260)
    label.pack()

    def show(_event: tk.Event) -> None:
        x, y = widget.winfo_pointerxy()
        tip.geometry(f"+{x + 12}+{y + 16}")
        tip.deiconify()

    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", lambda _event: tip.withdraw(), add="+")


class BeamDesigner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Beam Designer")
        self.geometry("1460x900")
        self.minsize(1050, 700)
        self.configure(background=COLORS["white"])
        self.loads: list[Load] = []
        self.tool = tk.StringVar(value="Point load")
        self.placement = False
        self.drag_start: float | None = None
        self.result: dict | None = None
        self._setup_style()
        self._build_shell()
        self._build_controls()
        self._build_workspace()
        self._build_results()
        self._populate_options()
        self._render_loads()
        self._calculate()

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["white"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["white"], foreground=COLORS["text"], font=("Segoe UI", 9))
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground=COLORS["navy"])
        style.configure("Section.TLabel", font=("Segoe UI", 9, "bold"), foreground=COLORS["muted"])
        style.configure("TButton", padding=(8, 5), font=("Segoe UI", 9))
        style.configure("Primary.TButton", background=COLORS["navy"], foreground="white")
        style.map("Primary.TButton", background=[("active", "#2c4262")])
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=4)

    def _build_shell(self) -> None:
        header = ttk.Frame(self, padding=(16, 10))
        header.pack(fill="x")
        ttk.Label(header, text="BD", background=COLORS["navy"], foreground="white",
                  padding=(9, 6), font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 10))
        ttk.Label(header, text="Beam Designer", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Reset", command=self.reset).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Load example", style="Primary.TButton", command=self.load_example).pack(side="right")
        ttk.Separator(self).pack(fill="x")

        self.panes = ttk.Panedwindow(self, orient="horizontal")
        self.panes.pack(fill="both", expand=True, padx=8, pady=8)
        self.left = ttk.Frame(self.panes, padding=12, width=260)
        self.center = ttk.Frame(self.panes, padding=10)
        self.right = ttk.Frame(self.panes, padding=12, width=280)
        self.panes.add(self.left, weight=0)
        self.panes.add(self.center, weight=1)
        self.panes.add(self.right, weight=0)

    def _section(self, parent: ttk.Frame, title: str, pad=(0, 12)) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=pad)
        frame.pack(fill="x", anchor="n")
        ttk.Label(frame, text=title.upper(), style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        return frame

    def _field(self, parent: ttk.Frame, label: str, variable: tk.StringVar | None = None,
               values: tuple[str, ...] | None = None, width: int = 20) -> ttk.Widget:
        box = ttk.Frame(parent)
        box.pack(fill="x", pady=3)
        ttk.Label(box, text=label).pack(anchor="w", pady=(0, 3))
        if values is not None:
            widget = ttk.Combobox(box, textvariable=variable, values=values, state="readonly", width=width)
        else:
            widget = ttk.Entry(box, textvariable=variable, width=width)
        widget.pack(fill="x")
        return widget

    def _build_controls(self) -> None:
        setup = self._section(self.left, "Beam setup")
        self.support_var = tk.StringVar(value="Simply supported")
        self.length_var = tk.StringVar()
        self.material_var = tk.StringVar(value="Steel")
        self.grade_var = tk.StringVar()
        self.section_var = tk.StringVar()
        self.allowable_var = tk.StringVar()
        self.support_combo = self._field(setup, "Support type", self.support_var,
                                         ("Simply supported", "Cantilever"))
        self.support_combo.bind("<<ComboboxSelected>>", self._on_setup)
        self.length_entry = self._field(setup, "Span length (ft)", self.length_var)
        self.length_entry.bind("<KeyRelease>", self._on_setup)
        self._field(setup, "Material", self.material_var, ("Steel", "Lumber")).bind("<<ComboboxSelected>>", self._on_material)
        self.grade_combo = self._field(setup, "Grade / species", self.grade_var, ())
        self.grade_combo.bind("<<ComboboxSelected>>", self._on_material)
        self.section_combo = self._field(setup, "Beam section", self.section_var, ())
        self.section_combo.bind("<<ComboboxSelected>>", self._on_setup)
        self.setup_error = ttk.Label(setup, text="", foreground=COLORS["red"], wraplength=230)
        self.setup_error.pack(anchor="w", pady=(4, 0))

        capacity = self._section(self.left, "Allowable stress")
        stress_entry = self._field(capacity, "Allowable bending stress (psi)", self.allowable_var)
        stress_entry.bind("<KeyRelease>", lambda _event: self._calculate())
        self.properties = ttk.Frame(capacity)
        self.properties.pack(fill="x", pady=(8, 0))
        self.source_note = ttk.Label(capacity, text="Reference database only. Verify values against applicable standards.",
                                     style="Muted.TLabel", wraplength=230)
        self.source_note.pack(anchor="w", pady=(8, 0))

        load_section = self._section(self.left, "Loads", pad=(0, 0))
        self.load_list = ttk.Frame(load_section)
        self.load_list.pack(fill="both", expand=True)
        self.load_message = ttk.Label(load_section, text="", foreground=COLORS["red"], wraplength=230)
        self.load_message.pack(anchor="w", pady=(5, 0))

    def _build_workspace(self) -> None:
        model = ttk.Frame(self.center, relief="solid", borderwidth=1, padding=10)
        model.pack(fill="both", expand=True)
        head = ttk.Frame(model)
        head.pack(fill="x")
        ttk.Label(head, text="BEAM MODEL", style="Section.TLabel").pack(side="left")
        self.model_status = ttk.Label(head, text="Enter beam properties", style="Muted.TLabel")
        self.model_status.pack(side="right")
        self.warning = tk.Label(model, text="", bg="#fff8e8", fg="#7f5a21", anchor="w", justify="left", padx=8, pady=6)
        self.warning.pack(fill="x", pady=(8, 0))
        self.canvas = tk.Canvas(model, background="white", highlightthickness=0, height=300)
        self.canvas.pack(fill="both", expand=True, pady=6)
        self.canvas.bind("<Configure>", lambda _e: self._draw_beam())
        self.canvas.bind("<ButtonPress-1>", self._place_press)
        self.canvas.bind("<ButtonRelease-1>", self._place_release)
        self.canvas.bind("<Motion>", self._place_motion)

        controls = ttk.Frame(model, padding=(0, 5))
        controls.pack(fill="x")
        types = ttk.Frame(controls)
        types.pack(side="left", padx=(0, 10))
        ttk.Radiobutton(types, text="Point load", variable=self.tool, value="Point load",
                        command=self._update_load_fields).pack(anchor="w")
        ttk.Radiobutton(types, text="Uniform load", variable=self.tool, value="Uniform load",
                        command=self._update_load_fields).pack(anchor="w")
        fields = ttk.Frame(controls)
        fields.pack(side="left", fill="x", expand=True)
        self.position_var = tk.StringVar(value="10")
        self.start_var = tk.StringVar(value="0")
        self.end_var = tk.StringVar(value="20")
        self.magnitude_var = tk.StringVar(value="1")
        self.position_field = self._compact_field(fields, "Position (ft)", self.position_var)
        self.start_field = self._compact_field(fields, "Start (ft)", self.start_var)
        self.end_field = self._compact_field(fields, "End (ft)", self.end_var)
        self.magnitude_field = self._compact_field(fields, "Magnitude (kip)", self.magnitude_var)
        actions = ttk.Frame(controls)
        actions.pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Add load", style="Primary.TButton", command=self._add_load).pack(fill="x", pady=2)
        ttk.Button(actions, text="Place on beam", command=self._begin_placement).pack(fill="x", pady=2)
        for var in (self.position_var, self.start_var, self.end_var, self.magnitude_var):
            var.trace_add("write", lambda *_args: self._update_load_fields())
        self._update_load_fields()

        diagrams = ttk.Frame(self.center)
        diagrams.pack(fill="x", pady=(10, 0))
        self.diagram_canvases: dict[str, tk.Canvas] = {}
        for key, color, title in (("shear", COLORS["teal"], "SHEAR"),
                                  ("moment", COLORS["amber"], "MOMENT"),
                                  ("deflection", COLORS["purple"], "DEFLECTION")):
            card = ttk.Frame(diagrams, relief="solid", borderwidth=1, padding=5)
            card.pack(side="left", fill="both", expand=True, padx=(0, 6))
            row = ttk.Frame(card)
            row.pack(fill="x")
            ttk.Label(row, text=title, style="Section.TLabel").pack(side="left")
            self.diagram_max = getattr(self, "diagram_max", {})
            maximum = ttk.Label(row, text="", style="Muted.TLabel")
            maximum.pack(side="right")
            self.diagram_max[key] = maximum
            if key == "deflection":
                tooltip(maximum, "The serviceability limit is span length divided by 360 (L/360).")
            plot = tk.Canvas(card, height=105, background="white", highlightthickness=0)
            plot.pack(fill="x", expand=True)
            plot.bind("<Configure>", lambda _e, k=key: self._draw_diagram(k))
            self.diagram_canvases[key] = plot

    def _compact_field(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> ttk.Frame:
        box = ttk.Frame(parent, padding=(3, 0))
        box.pack(side="left", fill="x", expand=True)
        ttk.Label(box, text=label).pack(anchor="w")
        entry = ttk.Entry(box, textvariable=variable, width=9)
        entry.pack(fill="x", pady=(3, 0))
        return box

    def _build_results(self) -> None:
        key = self._section(self.right, "Key results")
        self.key_results = ttk.Frame(key)
        self.key_results.pack(fill="x")
        checks = self._section(self.right, "Capacity checks", pad=(0, 0))
        self.checks = ttk.Frame(checks)
        self.checks.pack(fill="x")
        self._render_placeholders()

    def _populate_options(self) -> None:
        material = self.material_var.get()
        self.grade_combo.configure(values=tuple(MATERIALS[material]))
        if self.grade_var.get() not in MATERIALS[material]:
            self.grade_var.set(next(iter(MATERIALS[material])))
        self.section_combo.configure(values=tuple(SECTIONS[material]))
        if self.section_var.get() not in SECTIONS[material]:
            self.section_var.set("")
        self.allowable_var.set(str(MATERIALS[material][self.grade_var.get()]["allowable"]))
        self._render_properties()
        self._calculate()

    def _on_material(self, _event: tk.Event | None = None) -> None:
        self._populate_options()

    def _on_setup(self, _event: tk.Event | None = None) -> None:
        if _event is not None and _event.widget is self.length_entry:
            length = self._number(self.length_var.get())
            if length is not None and length > 0:
                self.position_var.set(f"{length / 2:g}")
                self.start_var.set("0")
                self.end_var.set(f"{length:g}")
        self._render_properties()
        self._calculate()

    def _render_properties(self) -> None:
        for child in self.properties.winfo_children():
            child.destroy()
        material = MATERIALS[self.material_var.get()].get(self.grade_var.get())
        section = SECTIONS[self.material_var.get()].get(self.section_var.get())
        rows: list[tuple[str, str]] = []
        if material:
            rows.extend((("Material", self.grade_var.get()),
                         ("Elastic modulus E", f"{material['E'] / 1_000_000:.2f} million psi"),
                         ("Proportional limit", f"{material['proportional']:,} psi")))
        if section:
            rows.extend((("Section", self.section_var.get()), ("Area A", f"{section['A']:g} in²"),
                         ("Moment I", f"{section['I']:g} in⁴"), ("Section S", f"{section['S']:g} in³")))
        for name, value in rows:
            row = ttk.Frame(self.properties)
            row.pack(fill="x", pady=1)
            label = ttk.Label(row, text=name, style="Muted.TLabel")
            label.pack(side="left")
            if name == "Elastic modulus E":
                tooltip(label, "Elastic modulus E describes the material's stiffness in the elastic range.")
            elif name == "Moment I":
                tooltip(label, "Area moment of inertia I measures the section's resistance to bending.")
            elif name == "Section S":
                tooltip(label, "Section modulus S relates bending moment to extreme-fiber stress: fb = M/S.")
            ttk.Label(row, text=value, font=("Segoe UI", 9, "bold")).pack(side="right")
        if section:
            ttk.Label(self.properties, text=f"Source: {section['source']}", style="Muted.TLabel",
                      wraplength=230).pack(anchor="w", pady=(5, 0))
        if material:
            ttk.Label(self.properties, text=f"Material source: {material['source']}", style="Muted.TLabel",
                      wraplength=230).pack(anchor="w", pady=(3, 0))

    @staticmethod
    def _number(raw: str) -> float | None:
        try:
            value = float(raw)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    def _valid_setup(self) -> tuple[float, dict, dict, float] | None:
        length = self._number(self.length_var.get())
        material = MATERIALS[self.material_var.get()].get(self.grade_var.get())
        section = SECTIONS[self.material_var.get()].get(self.section_var.get())
        allowable = self._number(self.allowable_var.get())
        if length is None or length <= 0:
            self.setup_error.configure(text="Enter a span length greater than zero.")
        elif section is None:
            self.setup_error.configure(text="Select a beam section.")
        elif material is None:
            self.setup_error.configure(text="Select a material grade.")
        elif allowable is None or allowable <= 0:
            self.setup_error.configure(text="Enter an allowable bending stress greater than zero.")
        else:
            self.setup_error.configure(text="")
            return length, section, material, allowable
        return None

    def _update_load_fields(self) -> None:
        uniform = self.tool.get() == "Uniform load"
        self.position_field.pack_forget()
        self.start_field.pack_forget()
        self.end_field.pack_forget()
        if uniform:
            self.start_field.pack(side="left", fill="x", expand=True)
            self.end_field.pack(side="left", fill="x", expand=True)
            self.magnitude_field.winfo_children()[0].configure(text="Intensity (kip/ft)")
        else:
            self.position_field.pack(side="left", fill="x", expand=True)
            self.magnitude_field.winfo_children()[0].configure(text="Magnitude (kip)")

    def _add_load(self) -> None:
        setup = self._valid_setup()
        if setup is None:
            self.load_message.configure(text="Complete the beam setup before adding loads.")
            return
        length = setup[0]
        magnitude = self._number(self.magnitude_var.get())
        if magnitude is None or magnitude == 0:
            self.load_message.configure(text="Enter a nonzero load magnitude.")
            return
        if self.tool.get() == "Point load":
            position = self._number(self.position_var.get())
            if position is None or not 0 <= position <= length:
                self.load_message.configure(text=f"Point-load position must be between 0 and {length:g} ft.")
                return
            self.loads.append(Load("point", magnitude, position=position))
        else:
            start, end = self._number(self.start_var.get()), self._number(self.end_var.get())
            if start is None or end is None or not 0 <= start < end <= length:
                self.load_message.configure(text=f"Distributed-load limits must be within 0–{length:g} ft and differ.")
                return
            self.loads.append(Load("uniform", magnitude, start=start, end=end))
        self.load_message.configure(text="")
        self._render_loads()
        self._calculate()

    def _render_loads(self) -> None:
        for child in self.load_list.winfo_children():
            child.destroy()
        if not self.loads:
            ttk.Label(self.load_list, text="No loads added.", style="Muted.TLabel").pack(anchor="w")
            self._draw_beam()
            return
        for index, load in enumerate(self.loads):
            card = ttk.Frame(self.load_list, padding=6, relief="solid", borderwidth=1)
            card.pack(fill="x", pady=3)
            header = ttk.Frame(card)
            header.pack(fill="x")
            ttk.Label(header, text="Point load" if load.kind == "point" else "Uniform load",
                      font=("Segoe UI", 9, "bold")).pack(side="left")
            ttk.Button(header, text="Delete", command=lambda i=index: self._delete_load(i)).pack(side="right")
            fields = ttk.Frame(card)
            fields.pack(fill="x", pady=(5, 0))
            if load.kind == "point":
                self._load_entry(fields, "Position (ft)", load.position, index, "position")
                self._load_entry(fields, "Magnitude (kip)", load.magnitude, index, "magnitude")
            else:
                self._load_entry(fields, "Start (ft)", load.start, index, "start")
                self._load_entry(fields, "End (ft)", load.end, index, "end")
                self._load_entry(fields, "Intensity (kip/ft)", load.magnitude, index, "magnitude")

    def _load_entry(self, parent: ttk.Frame, label: str, value: float, index: int, field: str) -> None:
        cell = ttk.Frame(parent)
        cell.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Label(cell, text=label, style="Muted.TLabel", font=("Segoe UI", 8)).pack(anchor="w")
        var = tk.StringVar(value=f"{value:g}")
        entry = ttk.Entry(cell, textvariable=var, width=8)
        entry.pack(fill="x", pady=(2, 0))
        entry.bind("<KeyRelease>", lambda _e, v=var, i=index, f=field: self._edit_load(i, f, v.get()))
        entry.bind("<FocusOut>", lambda _e, v=var, i=index, f=field: self._edit_load(i, f, v.get()))

    def _edit_load(self, index: int, field: str, raw: str) -> None:
        if index >= len(self.loads):
            return
        value = self._number(raw)
        load = self.loads[index]
        if value is None or (field == "magnitude" and value == 0):
            self.load_message.configure(text="Load values must be valid numbers; magnitude cannot be zero.")
            return
        setattr(load, field, value)
        setup = self._valid_setup()
        length = setup[0] if setup else None
        valid = (length is not None and
                 ((load.kind == "point" and 0 <= load.position <= length) or
                  (load.kind == "uniform" and 0 <= load.start < load.end <= length)))
        self.load_message.configure(text="" if valid else "Load position or endpoints are outside the beam.")
        self._calculate()

    def _delete_load(self, index: int) -> None:
        del self.loads[index]
        self._render_loads()
        self._calculate()

    def _begin_placement(self) -> None:
        if self._valid_setup() is None:
            self.load_message.configure(text="Complete the beam setup before placing loads.")
            return
        self.placement = True
        self.load_message.configure(text="Click beam for a point load; drag for a uniform load.")
        self.canvas.configure(cursor="crosshair")

    def _canvas_position(self, event: tk.Event) -> float:
        valid = self._valid_setup()
        length = valid[0] if valid else 1.0
        left, right = 44, 32
        fraction = (event.x - left) / max(1, self.canvas.winfo_width() - left - right)
        return max(0.0, min(length, fraction * length))

    def _place_press(self, event: tk.Event) -> None:
        if not self.placement:
            return
        position = self._canvas_position(event)
        if self.tool.get() == "Point load":
            magnitude = self._number(self.magnitude_var.get())
            if magnitude is None or magnitude == 0:
                self.load_message.configure(text="Enter a nonzero load magnitude before placing it.")
            else:
                self.loads.append(Load("point", magnitude, position=position))
                self.placement = False
                self.canvas.configure(cursor="")
                self.load_message.configure(text="")
                self._render_loads()
                self._calculate()
        else:
            self.drag_start = position

    def _place_motion(self, event: tk.Event) -> None:
        if self.placement and self.drag_start is not None:
            self._draw_beam(preview=self._canvas_position(event))

    def _place_release(self, event: tk.Event) -> None:
        if not self.placement or self.drag_start is None:
            return
        end = self._canvas_position(event)
        start = self.drag_start
        self.drag_start = None
        magnitude = self._number(self.magnitude_var.get())
        if magnitude is None or magnitude == 0 or abs(end - start) < 0.01:
            self.load_message.configure(text="Drag across a nonzero span and enter a nonzero intensity.")
        else:
            self.loads.append(Load("uniform", magnitude, start=min(start, end), end=max(start, end)))
            self.placement = False
            self.canvas.configure(cursor="")
            self.load_message.configure(text="")
            self._render_loads()
            self._calculate()

    def _analyze(self) -> dict | None:
        setup = self._valid_setup()
        if setup is None:
            return None
        length, section, material, allowable = setup
        return analyze_beam(length, section, material, allowable,
                            self.support_var.get(), self.loads)

    def _calculate(self) -> None:
        result = self._analyze()
        self.result = result
        if result is None:
            self.model_status.configure(text="Enter beam properties and valid loads")
            self.warning.configure(text="")
            self._render_placeholders()
            self._draw_beam()
            for key in self.diagram_canvases:
                self._draw_diagram(key)
            return
        self.model_status.configure(text=f"{self.support_var.get()}  ·  {self.section_var.get()}  ·  {result['length']:.2f} ft")
        over = result["stress"] > result["material"]["proportional"]
        if over:
            self.warning.configure(text=(f"Proportional-limit warning: maximum flexural stress is "
                                         f"{result['stress']:,.0f} psi, above {result['material']['proportional']:,} psi "
                                         f"at {result['moment_x']:.2f} ft. This is an elastic-range warning.") )
        else:
            self.warning.configure(text="")
        self._render_results(result)
        self._draw_beam()
        for key in self.diagram_canvases:
            self._draw_diagram(key)

    def _render_placeholders(self) -> None:
        for frame in (self.key_results, self.checks):
            for child in frame.winfo_children():
                child.destroy()
            ttk.Label(frame, text="Enter beam properties and loads to calculate results.",
                      style="Muted.TLabel", wraplength=250).pack(anchor="w", pady=4)
        for key in self.diagram_max:
            self.diagram_max[key].configure(text="")

    def _result_card(self, parent: ttk.Frame, title: str, value: str, detail: str = "",
                     status: str | None = None) -> None:
        color = COLORS["line"]
        if status == "PASS":
            color = COLORS["green"]
        elif status == "FAIL":
            color = COLORS["red"]
        elif status == "WARNING":
            color = COLORS["amber"]
        card = tk.Frame(parent, background="white", highlightbackground=color, highlightthickness=1,
                        padx=9, pady=7)
        card.pack(fill="x", pady=4)
        head = tk.Frame(card, background="white")
        head.pack(fill="x")
        tk.Label(head, text=title, background="white", foreground=COLORS["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        if status:
            tk.Label(head, text=status, background="white", foreground=color,
                     font=("Segoe UI", 8, "bold")).pack(side="right")
        tk.Label(card, text=value, background="white", foreground=COLORS["text"],
                 font=("Segoe UI", 13, "bold"), anchor="w", justify="left", wraplength=250).pack(fill="x", pady=(4, 0))
        if detail:
            tk.Label(card, text=detail, background="white", foreground=COLORS["muted"],
                     font=("Segoe UI", 8), anchor="w", justify="left", wraplength=250).pack(fill="x", pady=(2, 0))

    def _render_results(self, r: dict) -> None:
        for frame in (self.key_results, self.checks):
            for child in frame.winfo_children():
                child.destroy()
        self._result_card(self.key_results, "Reactions", r["reactions"])
        self._result_card(self.key_results, "Maximum shear", f"{r['max_shear']:.2f} kip",
                          f"At {r['shear_x']:.2f} ft")
        self._result_card(self.key_results, "Maximum moment", f"{r['max_moment']:.2f} kip-ft",
                          f"At {r['moment_x']:.2f} ft")
        self._result_card(self.key_results, "Maximum deflection", f"{r['max_deflection']:.3f} in",
                          f"At {r['deflection_x']:.2f} ft")
        self._result_card(self.key_results, "Flexural stress", f"{r['stress']:,.0f} psi",
                          f"Proportional limit: {r['material']['proportional']:,} psi")
        bending = "PASS" if r["stress"] <= r["allowable"] else "FAIL"
        deflection = "PASS" if r["max_deflection"] <= r["limit"] else "FAIL"
        elastic = "WARNING" if r["stress"] > r["material"]["proportional"] else "WITHIN LIMIT"
        self._result_card(self.checks, "Bending stress", f"{r['stress']:,.0f} / {r['allowable']:,.0f} psi",
                          "Maximum stress compared with allowable stress.", bending)
        self._result_card(self.checks, "Deflection", f"{r['max_deflection']:.3f} / {r['limit']:.3f} in",
                          f"Limit is L/360 ({r['limit']:.3f} in).", deflection)
        self._result_card(self.checks, "Elastic range", f"{r['stress']:,.0f} psi",
                          f"Proportional limit: {r['material']['proportional']:,} psi. Informational warning only.",
                          "WARNING" if elastic == "WARNING" else "PASS")
        assumptions = ttk.Label(self.checks,
                                text="Assumptions: strong-axis elastic bending; static loads; beam self-weight excluded. "
                                     "Stress = M/S; deflection limit = L/360.",
                                style="Muted.TLabel", wraplength=250, justify="left")
        assumptions.pack(anchor="w", pady=(6, 0))
        self.diagram_max["shear"].configure(text=f"|V|max {r['max_shear']:.2f} kip")
        self.diagram_max["moment"].configure(text=f"|M|max {r['max_moment']:.2f} kip-ft")
        self.diagram_max["deflection"].configure(text=f"|δ|max {r['max_deflection']:.3f} in")

    def _draw_beam(self, preview: float | None = None) -> None:
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 200), max(c.winfo_height(), 200)
        left, right, y = 48, w - 32, h * 0.48
        length = self._number(self.length_var.get())
        valid = self.result is not None
        support = self.support_var.get()
        stress_over = valid and self.result["stress"] > self.result["material"]["proportional"]
        beam_color = COLORS["amber"] if stress_over else COLORS["navy"]
        c.create_line(left, y, right, y, fill=beam_color if valid else "#9aa5b3", width=4)
        if support == "Simply supported":
            for x in (left, right):
                c.create_polygon(x, y + 2, x - 12, y + 22, x + 12, y + 22,
                                 outline="#78869a", fill="white", width=2)
                c.create_line(x - 16, y + 25, x + 16, y + 25, fill="#78869a", width=2)
        else:
            c.create_line(left - 8, y - 25, left - 8, y + 25, fill="#78869a", width=6)
            for yy in range(int(y - 20), int(y + 20), 9):
                c.create_line(left - 16, yy, left - 3, yy + 7, fill="#78869a")
        if not valid:
            c.create_text((left + right) / 2, y - 28, text="Add beam properties to begin", fill=COLORS["muted"],
                          font=("Segoe UI", 10))
        else:
            r = self.result
            px = lambda x: left + (x / r["length"]) * (right - left)
            c.create_text(left, y + 45, text="0 ft", anchor="w", fill=COLORS["muted"])
            c.create_text(right, y + 45, text=f"{r['length']:.1f} ft", anchor="e", fill=COLORS["muted"])
            c.create_text((left + right) / 2, y + 45,
                          text=f"{self.section_var.get()} · A = {r['section']['A']:g} in²",
                          fill=COLORS["text"], font=("Segoe UI", 9, "bold"))
            for load in self.loads:
                if load.kind == "point":
                    x = px(load.position)
                    c.create_line(x, y - 53, x, y - 6, fill=COLORS["blue"], width=2, arrow="last")
                    c.create_text(x, y - 62, text=f"{load.magnitude:g} kip", fill=COLORS["blue"])
                    c.create_text(x, y + 17, text=f"{load.position:g} ft", fill=COLORS["muted"])
                else:
                    x1, x2 = px(load.start), px(load.end)
                    c.create_line(x1, y - 43, x2, y - 43, fill=COLORS["blue"], width=2)
                    for x in range(int(x1 + 8), int(x2), 20):
                        c.create_line(x, y - 42, x, y - 6, fill=COLORS["blue"], arrow="last")
                    c.create_text((x1 + x2) / 2, y - 54, text=f"{load.magnitude:g} kip/ft", fill=COLORS["blue"])
            max_defl = max((abs(v) for v in r["deflections"]), default=0.0)
            scale = min(45 / max_defl, (right - left) / (r["length"] * 12)) if max_defl > 1e-12 else 1
            pts = []
            for x, d in zip(r["xs"], r["deflections"]):
                pts.extend((px(x), y - d * scale))
            if len(pts) >= 4:
                c.create_line(*pts, fill=COLORS["purple"], width=2, dash=(5, 4), smooth=True)
            c.create_text(right, y - 22, text=f"Deflected shape · max {r['max_deflection']:.3f} in",
                          anchor="e", fill=COLORS["purple"])
            if stress_over:
                sx = px(r["moment_x"])
                c.create_line(sx, y - 30, sx, y - 5, fill=COLORS["red"], width=2)
                c.create_text(sx, y - 34, text="max stress", fill=COLORS["red"])
        if preview is not None and length and length > 0:
            px = lambda x: left + (x / length) * (right - left)
            if self.tool.get() == "Point load":
                c.create_line(px(preview), y - 50, px(preview), y - 5, fill=COLORS["blue"], dash=(3, 2), arrow="last")
            elif self.drag_start is not None:
                c.create_rectangle(px(min(preview, self.drag_start)), y - 43, px(max(preview, self.drag_start)), y - 5,
                                   outline=COLORS["blue"], dash=(3, 2))

    def _draw_diagram(self, key: str) -> None:
        c = self.diagram_canvases[key]
        c.delete("all")
        w, h = max(c.winfo_width(), 100), max(c.winfo_height(), 60)
        color = {"shear": COLORS["teal"], "moment": COLORS["amber"], "deflection": COLORS["purple"]}[key]
        c.create_line(24, h / 2, w - 8, h / 2, fill=COLORS["line"])
        if self.result is None:
            c.create_text(w / 2, h / 2 - 12, text="Waiting for beam data", fill=COLORS["muted"])
            return
        vals = {"shear": self.result["shears"], "moment": self.result["moments"],
                "deflection": self.result["deflections"]}[key]
        maximum = max((abs(v) for v in vals), default=0.0) or 1.0
        baseline, amplitude = h / 2, h * 0.39
        points = []
        for i, value in enumerate(vals):
            x = 24 + (i / max(1, len(vals) - 1)) * (w - 32)
            y = baseline - value / maximum * amplitude
            points.extend((x, y))
        if len(points) >= 4:
            c.create_line(*points, fill=color, width=2, smooth=True)

    def load_example(self) -> None:
        self.support_var.set("Simply supported")
        self.length_var.set("20")
        self.material_var.set("Steel")
        self.grade_var.set("A992 Steel")
        self.section_var.set("W12×26")
        self.allowable_var.set("33000")
        self.tool.set("Uniform load")
        self._update_load_fields()
        self.loads = [Load("uniform", 1.0, start=0.0, end=20.0)]
        self.load_message.configure(text="Validation example loaded: 20 ft, W12×26, 1 kip/ft.")
        self._render_properties()
        self._render_loads()
        self._calculate()

    def reset(self) -> None:
        self.support_var.set("Simply supported")
        self.length_var.set("")
        self.material_var.set("Steel")
        self.grade_var.set("A36 Steel")
        self.section_var.set("")
        self.allowable_var.set("22000")
        self.tool.set("Point load")
        self.position_var.set("10")
        self.start_var.set("0")
        self.end_var.set("20")
        self.magnitude_var.set("1")
        self._update_load_fields()
        self.loads.clear()
        self.load_message.configure(text="")
        self._render_properties()
        self._render_loads()
        self._calculate()


if __name__ == "__main__":
    BeamDesigner().mainloop()
