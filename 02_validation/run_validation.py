"""Run the spec's beam calculation cases and print a results table."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from beam_designer import MATERIALS, SECTIONS, Load, analyze_beam  # noqa: E402


def solve(support: str, length: float, material: str, grade: str, section: str,
          loads: list[Load]):
    mat = MATERIALS[material][grade]
    sec = SECTIONS[material][section]
    return analyze_beam(length, sec, mat, mat["allowable"], support, loads)


def point_deflection_in(length_ft: float, loads: list[tuple[float, float]],
                        E: float, I: float) -> tuple[float, float]:
    """Independent closed-form superposition for simple-beam point loads."""
    length = length_ft * 12
    step_count = 100_000
    best_value, best_x = 0.0, 0.0
    for index in range(step_count + 1):
        x = length * index / step_count
        value = 0.0
        for position_ft, kip in loads:
            a = position_ft * 12
            b = length - a
            P = kip * 1_000
            if x <= a:
                value += P * b * x * (length**2 - b**2 - x**2) / (6 * length * E * I)
            else:
                value += P * a * (length - x) * (length**2 - a**2 - (length - x)**2) / (6 * length * E * I)
        if value > best_value:
            best_value, best_x = value, x / 12
    return best_value, best_x


def record(rows: list[tuple[str, str, str, bool]], name: str, expected: str,
           actual: str, passed: bool) -> None:
    rows.append((name, expected, actual, passed))


def check_close(name: str, expected: float, actual: float, tolerance: float = 1e-3) -> bool:
    return math.isclose(expected, actual, rel_tol=tolerance, abs_tol=tolerance)


def main() -> int:
    rows: list[tuple[str, str, str, bool]] = []
    all_passed = True
    steel = MATERIALS["Steel"]["A992 Steel"]
    a36 = MATERIALS["Steel"]["A36 Steel"]
    w12 = SECTIONS["Steel"]["W12×26"]

    cases = [
        ("Primary: 20-ft simple beam, 1 kip/ft", "Simply supported", 20, "Steel", "A992 Steel", "W12×26",
         [Load("uniform", 1, start=0, end=20)]),
        ("Cantilever: 1-kip tip load, 10 ft", "Cantilever", 10, "Steel", "A992 Steel", "W12×26",
         [Load("point", 1, position=10)]),
        ("Cantilever: 1-kip/ft full-span load, 10 ft", "Cantilever", 10, "Steel", "A992 Steel", "W12×26",
         [Load("uniform", 1, start=0, end=10)]),
        ("Simple beam: centered 1-kip load, 20 ft", "Simply supported", 20, "Steel", "A992 Steel", "W12×26",
         [Load("point", 1, position=10)]),
        ("Simple beam: 1 kip at 5 ft + 2 kip at 15 ft", "Simply supported", 20, "Steel", "A992 Steel", "W12×26",
         [Load("point", 1, position=5), Load("point", 2, position=15)]),
        ("Below proportional limit: A36, centered 10-kip load", "Simply supported", 20, "Steel", "A36 Steel", "W12×26",
         [Load("point", 10, position=10)]),
        ("Above proportional limit: A992, centered 30-kip load", "Simply supported", 20, "Steel", "A992 Steel", "W12×26",
         [Load("point", 30, position=10)]),
    ]

    analytic_expected: dict[str, dict[str, float]] = {
        "Primary: 20-ft simple beam, 1 kip/ft": {
            "max_moment": 1 * 20**2 / 8,
            "max_deflection": 5 * (1_000 / 12) * (20 * 12) ** 4 / (384 * steel["E"] * w12["I"]),
            "ra": 10, "rb": 10,
        },
        "Cantilever: 1-kip tip load, 10 ft": {
            "max_moment": 1 * 10,
            "max_deflection": 1_000 * (10 * 12) ** 3 / (3 * steel["E"] * w12["I"]),
            "ra": 1,
        },
        "Cantilever: 1-kip/ft full-span load, 10 ft": {
            "max_moment": 1 * 10**2 / 2,
            "max_deflection": (1_000 / 12) * (10 * 12) ** 4 / (8 * steel["E"] * w12["I"]),
            "ra": 10,
        },
        "Simple beam: centered 1-kip load, 20 ft": {
            "max_moment": 1 * 20 / 4,
            "max_deflection": 1_000 * (20 * 12) ** 3 / (48 * steel["E"] * w12["I"]),
            "ra": 0.5, "rb": 0.5,
        },
        "Simple beam: 1 kip at 5 ft + 2 kip at 15 ft": {
            "max_moment": 8.75, "ra": 1.25, "rb": 1.75,
        },
        "Below proportional limit: A36, centered 10-kip load": {
            "max_moment": 50, "stress": 50 * 12_000 / w12["S"],
        },
        "Above proportional limit: A992, centered 30-kip load": {
            "max_moment": 150, "stress": 150 * 12_000 / w12["S"],
        },
    }
    multi_defl, multi_x = point_deflection_in(20, [(5, 1), (15, 2)], steel["E"], w12["I"])
    analytic_expected["Simple beam: 1 kip at 5 ft + 2 kip at 15 ft"].update(
        max_deflection=multi_defl, deflection_x=multi_x)
    analytic_expected["Below proportional limit: A36, centered 10-kip load"]["max_deflection"] = (
        10_000 * (20 * 12) ** 3 / (48 * a36["E"] * w12["I"]))
    analytic_expected["Above proportional limit: A992, centered 30-kip load"]["max_deflection"] = (
        30_000 * (20 * 12) ** 3 / (48 * steel["E"] * w12["I"]))

    for name, support, length, material, grade, section, loads in cases:
        result = solve(support, length, material, grade, section, loads)
        expected = analytic_expected[name]
        if name == "Simple beam: 1 kip at 5 ft + 2 kip at 15 ft":
            exp_desc = (f"RA/RB {expected['ra']:.2f}/{expected['rb']:.2f} kip; "
                        f"M {expected['max_moment']:.2f} kip-ft; δ {expected['max_deflection']:.3f} in "
                        f"at {expected['deflection_x']:.2f} ft")
        elif name == "Below proportional limit: A36, centered 10-kip load":
            exp_desc = (f"M {expected['max_moment']:.2f} kip-ft; stress {expected['stress']:.0f} psi; "
                        f"under {a36['proportional']:,} psi proportional limit")
        elif name == "Above proportional limit: A992, centered 30-kip load":
            exp_desc = (f"M {expected['max_moment']:.2f} kip-ft; stress {expected['stress']:.0f} psi; "
                        f"over {steel['proportional']:,} psi proportional limit")
        else:
            exp_desc = (f"M {expected['max_moment']:.2f} kip-ft; δ {expected['max_deflection']:.3f} in; "
                        + (f"RA/RB {expected['ra']:.2f}/{expected['rb']:.2f} kip" if "rb" in expected
                           else f"fixed reaction {expected['ra']:.2f} kip"))
        if result is None:
            record(rows, name, exp_desc, "Rejected unexpectedly", False)
            all_passed = False
            continue
        checks = [check_close(key, value, result[key], tolerance=0.02 if key == "deflection_x" else 1e-3)
                  for key, value in expected.items()]
        if "stress" in expected:
            is_over = result["stress"] > result["material"]["proportional"]
            checks.append(is_over == ("Above proportional" in name))
            if "Below proportional" in name:
                checks.extend((result["stress"] <= result["allowable"], not is_over))
            else:
                checks.extend((result["stress"] > result["allowable"], is_over))
        actual_desc = (f"M {result['max_moment']:.2f} kip-ft; δ {result['max_deflection']:.3f} in"
                       + (f" at {result['deflection_x']:.2f} ft" if "deflection_x" in expected else "")
                       + f"; RA/RB {result['ra']:.2f}/{result['rb']:.2f} kip; stress {result['stress']:.0f} psi")
        if "Below proportional" in name:
            actual_desc += "; bending PASS; elastic range within limit"
        elif "Above proportional" in name:
            actual_desc += "; bending FAIL; elastic-range WARNING"
        passed = all(checks)
        all_passed &= passed
        record(rows, name, exp_desc, actual_desc, passed)

    # Both steel and lumber section lookups, including complete property sets.
    property_cases = [
        ("Steel W12×26 lookup", SECTIONS["Steel"]["W12×26"],
         {"id": "w12x26", "A": 7.65, "I": 204.0, "S": 33.4}),
        ("Lumber 2×10 lookup", SECTIONS["Lumber"]["2×10"],
         {"id": "2x10", "A": 13.875, "I": 98.93, "S": 21.39}),
    ]
    for name, actual, expected in property_cases:
        passed = all(actual[key] == value for key, value in expected.items()) and bool(actual.get("source"))
        all_passed &= passed
        record(rows, name, str(expected), str({k: actual[k] for k in expected}), passed)

    # Material and section selection changes must expose the newly selected
    # E, I, S and proportional limit while leaving the existing load intact.
    unchanged_loads = [Load("uniform", 1, start=0, end=20)]
    before = solve("Simply supported", 20, "Steel", "A992 Steel", "W12×26", unchanged_loads)
    after_section = solve("Simply supported", 20, "Steel", "A992 Steel", "W12×30", unchanged_loads)
    after_material = solve("Simply supported", 20, "Lumber", "Spruce-Pine-Fir No.2", "2×10", unchanged_loads)
    expected_props = ("W12×30 I 238 in⁴/S 38.6 in³; then SPF 2×10 E 1,400,000 psi, "
                      "I 98.93 in⁴, S 21.39 in³, proportional limit 5,500 psi; load retained")
    actual_props = (f"W12×30 I {after_section['section']['I']:g} in⁴/S {after_section['section']['S']:g} in³; "
                    f"then SPF 2×10 E {after_material['material']['E']:,} psi, "
                    f"I {after_material['section']['I']:g} in⁴, S {after_material['section']['S']:g} in³, "
                    f"proportional limit {after_material['material']['proportional']:,} psi; "
                    f"load retained ({len(unchanged_loads)})")
    passed = (before is not None and after_section is not None and after_material is not None
              and before["max_moment"] == after_section["max_moment"] == after_material["max_moment"] == 50
              and after_section["section"]["I"] == 238.0
              and after_section["section"]["S"] == 38.6
              and after_material["material"]["E"] == 1_400_000
              and after_material["section"]["I"] == 98.93
              and after_material["section"]["S"] == 21.39
              and after_material["material"]["proportional"] == 5_500
              and len(unchanged_loads) == 1)
    all_passed &= passed
    record(rows, "Preset changes after loads entered", expected_props, actual_props, passed)

    # Length validation and endpoint acceptance/rejection.
    valid = analyze_beam(20, w12, steel, steel["allowable"], "Simply supported", []) is not None
    invalid_lengths = [analyze_beam(x, w12, steel, steel["allowable"], "Simply supported", []) is None
                      for x in (0, -1)]
    passed = valid and all(invalid_lengths)
    all_passed &= passed
    record(rows, "Beam lengths: 20 ft valid; 0 and −1 ft invalid",
           "valid / rejected / rejected",
           f"{valid} / {invalid_lengths[0]} / {invalid_lengths[1]}", passed)

    endpoint_results = [analyze_beam(20, w12, steel, steel["allowable"], "Simply supported",
                                     [Load("point", 1, position=x)]) is not None for x in (0, 20)]
    outside_results = [analyze_beam(20, w12, steel, steel["allowable"], "Simply supported",
                                    [Load("point", 1, position=x)]) is None for x in (-0.1, 20.1)]
    passed = all(endpoint_results) and all(outside_results)
    all_passed &= passed
    record(rows, "Loads at endpoints 0/20 ft; outside at −0.1/20.1 ft",
           "accept / accept / reject / reject",
           " / ".join(str(x) for x in endpoint_results + outside_results), passed)

    uniform_boundaries = [
        analyze_beam(20, w12, steel, steel["allowable"], "Simply supported",
                     [Load("uniform", 1, start=0, end=20)]) is not None,
        analyze_beam(20, w12, steel, steel["allowable"], "Simply supported",
                     [Load("uniform", 1, start=-0.1, end=20)]) is None,
        analyze_beam(20, w12, steel, steel["allowable"], "Simply supported",
                     [Load("uniform", 1, start=0, end=20.1)]) is None,
    ]
    passed = all(uniform_boundaries)
    all_passed &= passed
    record(rows, "Uniform load spans 0–20 ft; endpoints outside span rejected",
           "accept / reject / reject", " / ".join(str(x) for x in uniform_boundaries), passed)

    print("| Validation case | Expected | Actual | Result |")
    print("|---|---|---|---|")
    for name, expected, actual, passed in rows:
        print(f"| {name} | {expected} | {actual} | {'PASS' if passed else 'FAIL'} |")
    print(f"\n{sum(row[3] for row in rows)}/{len(rows)} validation checks passed.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
