"""Create a vector PDF calculation sheet using only the Python standard library."""
def _pdf_text(text):
    text = str(text).replace("×", "x").replace("²", "2").replace("³", "3").replace("⁴", "4")
    return text.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Sheet:
    def __init__(self):
        self.pages = []
        self.commands = []
        self.y = 0
        self.new_page()

    def new_page(self):
        if self.commands:
            self.pages.append(self.commands)
        self.commands = []
        self.y = 752
        self.text("BEAM DESIGNER  |  CALCULATION SHEET", 15, bold=True)
        self.text("Strong-axis elastic beam analysis  |  US customary units", 9, color=(0.35, 0.4, 0.46))
        self.y -= 8

    def need(self, height):
        if self.y - height < 55:
            self.new_page()

    def text(self, text, size=10, bold=False, color=(0.1, 0.15, 0.2), indent=0):
        self.need(size + 6)
        r, g, b = color
        self.commands.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {r} {g} {b} rg 1 0 0 1 {48 + indent} {self.y} Tm ({_pdf_text(text)}) Tj ET")
        self.y -= size + 5

    def heading(self, title):
        self.need(36)
        self.y -= 6
        self.text(title.upper(), 11, bold=True, color=(0.12, 0.2, 0.3))
        self.commands.append(f"0.82 0.85 0.88 RG 48 {self.y + 2:.2f} m 564 {self.y + 2:.2f} l S")
        self.y -= 5

    def diagram(self, title, unit, xs, values, color):
        self.need(125)
        self.text(f"{title} ({unit})", 10, bold=True)
        left, right = 82, 548
        baseline = self.y - 43
        amplitude = 35
        peak = max((abs(v) for v in values), default=0.0)
        scale = peak or 1.0
        self.commands.append(f"0.8 0.83 0.86 RG 0.6 w {left} {baseline:.2f} m {right} {baseline:.2f} l S")
        self.commands.append(f"{color[0]} {color[1]} {color[2]} RG 1.2 w")
        span = xs[-1] or 1
        for i, (x, value) in enumerate(zip(xs, values)):
            xx = left + x / span * (right - left)
            yy = baseline + value / scale * amplitude
            self.commands.append(f"{xx:.3f} {yy:.3f} {'m' if i == 0 else 'l'}")
        self.commands.append("S")
        self.commands.append(f"BT /F1 8 Tf 0.35 0.4 0.46 rg 1 0 0 1 48 {baseline + amplitude:.2f} Tm (+{peak:.3g}) Tj ET")
        self.commands.append(f"BT /F1 8 Tf 0.35 0.4 0.46 rg 1 0 0 1 48 {baseline - amplitude:.2f} Tm (-{peak:.3g}) Tj ET")
        self.commands.append(f"BT /F1 8 Tf 0.35 0.4 0.46 rg 1 0 0 1 {left} {baseline - 48:.2f} Tm (0 ft) Tj ET")
        self.commands.append(f"BT /F1 8 Tf 0.35 0.4 0.46 rg 1 0 0 1 {right - 45} {baseline - 48:.2f} Tm ({span:g} ft) Tj ET")
        self.y = baseline - 62

    def write(self, stream):
        pages = self.pages + [self.commands]
        objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"]
        kids = []
        for index, commands in enumerate(pages, 1):
            page_id = len(objects) + 1
            content_id = page_id + 1
            kids.append(f"{page_id} 0 R")
            footer = f"BT /F1 8 Tf 0.4 0.4 0.4 rg 1 0 0 1 48 30 Tm (Beam Designer  |  Page {index} of {len(pages)}) Tj ET"
            content = ("\n".join(commands + [footer]) + "\n").encode("latin-1")
            objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii"))
            objects.append(f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"endstream")
        objects[1] = f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(kids)}] >>".encode("ascii")
        stream.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(stream.tell())
            stream.write(f"{i} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
        xref = stream.tell()
        stream.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            stream.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        stream.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))


def write_calculation_sheet(stream, result, material_name, section_name):
    r = result
    sec, mat = r["section"], r["material"]
    sheet = Sheet()
    sheet.heading("Inputs")
    sheet.text(f"Support: {r['support']}     Span: {r['length']:g} ft")
    sheet.text(f"Material: {material_name}     Section: {section_name}")
    sheet.text(f"E: {mat['E']:,.0f} psi     A: {sec['A']:g} in2     I: {sec['I']:g} in4     S: {sec['S']:g} in3")
    sheet.text(f"Allowable bending stress: {r['allowable']:,.0f} psi     Deflection limit: L/{r['deflection_denominator']:g}")
    sheet.text(f"Proportional limit: {mat['proportional']:,.0f} psi")
    sheet.text("Material and section properties are reference values; verify applicable standards.", 9)
    sheet.text(f"Material source: {mat['source']}", 9)
    sheet.text(f"Section source: {sec['source']}", 9)
    sheet.heading("Loads")
    if not r["loads"]:
        sheet.text("No loads")
    for i, load in enumerate(r["loads"], 1):
        if load.kind == "point":
            sheet.text(f"{i}. Point load: {load.magnitude:g} kip at {load.position:g} ft")
        else:
            sheet.text(f"{i}. Uniform load: {load.magnitude:g} kip/ft from {load.start:g} to {load.end:g} ft")
    sheet.heading("Results and checks")
    sheet.text(f"Reactions: {r['reactions']}")
    sheet.text(f"Maximum shear: {r['max_shear']:.3f} kip at {r['shear_x']:.3f} ft")
    sheet.text(f"Maximum moment: {r['max_moment']:.3f} kip-ft at {r['moment_x']:.3f} ft")
    sheet.text(f"Maximum deflection: {r['max_deflection']:.4f} in at {r['deflection_x']:.3f} ft")
    sheet.text(f"Bending: {r['stress']:,.1f} / {r['allowable']:,.1f} psi   {'PASS' if r['stress'] <= r['allowable'] else 'FAIL'}", bold=True)
    sheet.text(f"Deflection: {r['max_deflection']:.4f} / {r['limit']:.4f} in   {'PASS' if r['max_deflection'] <= r['limit'] else 'FAIL'}", bold=True)
    elastic = "WARNING: exceeds proportional limit" if r['stress'] > mat['proportional'] else "within proportional limit"
    sheet.text(f"Elastic range: {elastic}")
    sheet.text("Proportional limit is an elastic-range warning, not a strength check.", 9)
    sheet.text("Assumptions: static loading; strong-axis elastic bending; self-weight excluded.", 9)
    sheet.text("Bending stress = M/S; deflection from numerical integration of M/EI.", 9)
    sheet.heading("Diagrams")
    sheet.diagram("Shear V", "kip", r["xs"], r["shears"], (0.08, 0.55, 0.56))
    sheet.diagram("Moment M", "kip-ft", r["xs"], r["moments"], (0.78, 0.52, 0.15))
    sheet.diagram("Deflection", "in", r["xs"], r["deflections"], (0.42, 0.32, 0.62))
    sheet.write(stream)
