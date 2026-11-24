"""Exercise the File menu handlers with a real Tk window and temporary files."""
import json
import csv
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from beam_designer import BeamDesigner, Load


def main():
    app = BeamDesigner()
    app.withdraw()
    try:
        app.load_example()
        app.allowable_var.set("29000")
        app.deflection_var.set("240")
        app.loads.append(Load("point", 3, position=7))
        app._render_loads()
        app._calculate()
        before = app.result
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "design.json"
            csv_path = Path(directory) / "results.csv"
            with patch("beam_designer.filedialog.asksaveasfilename", return_value=str(csv_path)):
                app.export_results()
            with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
            assert rows[0] == ["x (ft)", "V (kip)", "M (kip-ft)", "deflection (in)"]
            expected_rows = list(zip(before["xs"], before["shears"], before["moments"], before["deflections"]))
            assert len(rows) == len(expected_rows) + 1
            assert [tuple(map(float, row)) for row in rows[1:]] == expected_rows
            pdf_path = Path(directory) / "calculation.pdf"
            with patch("beam_designer.filedialog.asksaveasfilename", return_value=str(pdf_path)):
                app.export_calculation_sheet()
            pdf = pdf_path.read_bytes()
            assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
            for expected in (b"INPUTS", b"A992 Steel", b"W12x26", b"Uniform load", b"Point load",
                             b"RESULTS AND CHECKS", b"PASS", b"DIAGRAMS", b"Shear V", b"Moment M", b"Deflection"):
                assert expected in pdf, expected
            startxref = int(pdf.rsplit(b"startxref\n", 1)[1].splitlines()[0])
            assert pdf[startxref:startxref + 4] == b"xref"
            app.deflection_var.set("0")
            with patch("beam_designer.filedialog.asksaveasfilename") as dialog, \
                    patch("beam_designer.messagebox.showerror") as error:
                app.export_results()
            assert error.called and not dialog.called
            with patch("beam_designer.filedialog.asksaveasfilename") as dialog, \
                    patch("beam_designer.messagebox.showerror") as error:
                app.export_calculation_sheet()
            assert error.called and not dialog.called
            app.deflection_var.set("240")
            with patch("beam_designer.filedialog.asksaveasfilename", return_value=str(path)):
                app.save_design()
            saved = json.loads(path.read_text(encoding="utf-8"))
            assert saved["deflection_denominator"] == 240
            assert len(saved["loads"]) == 2
            app.reset()
            with patch("beam_designer.filedialog.askopenfilename", return_value=str(path)):
                app.open_design()
            assert app.support_var.get() == "Simply supported"
            assert app.length_var.get() == "20.0"
            assert app.material_var.get() == "Steel" and app.grade_var.get() == "A992 Steel"
            assert app.section_var.get() == "W12×26" and float(app.allowable_var.get()) == 29000
            assert float(app.deflection_var.get()) == 240 and len(app.loads) == 2
            assert app.result["max_moment"] == before["max_moment"]
            assert app.result["max_deflection"] == before["max_deflection"]
            assert app.result["limit"] == 1.0
            path.write_text('{"version":1,"loads":[]}', encoding="utf-8")
            with patch("beam_designer.filedialog.askopenfilename", return_value=str(path)), \
                    patch("beam_designer.messagebox.showerror") as error:
                app.open_design()
            assert error.called and len(app.loads) == 2 and app.result["limit"] == 1.0
            path.write_text("not json", encoding="utf-8")
            with patch("beam_designer.filedialog.askopenfilename", return_value=str(path)), \
                    patch("beam_designer.messagebox.showerror") as error:
                app.open_design()
            assert error.called and app.result["max_moment"] == before["max_moment"]
            app.support_var.set("Cantilever")
            app.material_var.set("Lumber")
            app.grade_var.set("Spruce-Pine-Fir No.2")
            app.section_var.set("2×10")
            app.allowable_var.set("875")
            app.loads = [Load("point", 2, position=20)]
            app._render_loads()
            app._calculate()
            with patch("beam_designer.filedialog.asksaveasfilename", return_value=str(path)):
                app.save_design()
            app.reset()
            with patch("beam_designer.filedialog.askopenfilename", return_value=str(path)):
                app.open_design()
            assert app.support_var.get() == "Cantilever" and app.material_var.get() == "Lumber"
            assert app.grade_var.get() == "Spruce-Pine-Fir No.2" and app.section_var.get() == "2×10"
            assert app.loads == [Load("point", 2, position=20)]
            assert app.result["max_moment"] == 40
        print("PDF and CSV export, invalid input, save/open round trip, and invalid-file preservation: PASS")
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
