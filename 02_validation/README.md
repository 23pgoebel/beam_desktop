# Beam calculation validation

Run the checks from the project root with:

```powershell
python 02_validation/run_validation.py
python 02_validation/save_open_validation.py
```

The runner calls `analyze_beam`, the same calculation function used by the
Tkinter app. Exact beam formulas are used for the primary uniform-load case,
cantilever cases, and centered point-load cases. The asymmetric multiple-load
deflection is independently calculated by point-load superposition and a dense
span scan; the app's sampled maximum location is allowed a 0.02-ft tolerance.
Where the spec names a case but gives no load values, this file records the
representative validation inputs used below. Load magnitudes are downward and
the reference section/material values are the app's local database values.

## Results

Run on 2026-11-24. All 13 validation checks passed.

The save/open check also passed: it round-tripped steel and lumber designs,
point and uniform loads, allowable stress, and a custom L/240 limit. It
confirmed that malformed and incomplete files leave the current design intact.
The CSV export check confirms its headers, units, and every data row against the
calculated results, and checks that invalid inputs prevent export.
The calculation-sheet check confirms PDF structure, inputs, load entries,
diagram labels, and checks, and verifies invalid inputs prevent PDF export.

| Validation case | Expected | Actual | Result |
|---|---|---|---|
| Primary: 20-ft simple beam, 1 kip/ft | M 50.00 kip-ft; δ 0.609 in; reactions 10.00/10.00 kip | M 50.00 kip-ft; δ 0.609 in; reactions 10.00/10.00 kip; stress 17,964 psi | PASS |
| Cantilever: 1-kip tip load, 10 ft | M 10.00 kip-ft; δ 0.097 in; fixed reaction 1.00 kip | M 10.00 kip-ft; δ 0.097 in; reaction 1.00 kip; stress 3,593 psi | PASS |
| Cantilever: 1 kip/ft full-span load, 10 ft | M 50.00 kip-ft; δ 0.365 in; fixed reaction 10.00 kip | M 50.00 kip-ft; δ 0.365 in; reaction 10.00 kip; stress 17,964 psi | PASS |
| Simple beam: centered 1-kip load, 20 ft | M 5.00 kip-ft; δ 0.049 in; reactions 0.50/0.50 kip | M 5.00 kip-ft; δ 0.049 in; reactions 0.50/0.50 kip; stress 1,796 psi | PASS |
| Simple beam: 1 kip at 5 ft + 2 kip at 15 ft | reactions 1.25/1.75 kip; M 8.75 kip-ft; δ 0.101 in at 10.41 ft | reactions 1.25/1.75 kip; M 8.75 kip-ft; δ 0.101 in at 10.40 ft; stress 3,144 psi | PASS |
| Below proportional limit: A36, centered 10-kip load | M 50.00 kip-ft; stress 17,964 psi < 36,000 psi limit | M 50.00 kip-ft; stress 17,964 psi; bending PASS; elastic range within limit | PASS |
| Above proportional limit: A992, centered 30-kip load | M 150.00 kip-ft; stress 53,892 psi > 50,000 psi limit | M 150.00 kip-ft; stress 53,892 psi; bending FAIL; elastic-range WARNING | PASS |
| Steel W12×26 section lookup | A 7.65 in²; I 204 in⁴; S 33.4 in³ | A 7.65 in²; I 204 in⁴; S 33.4 in³ | PASS |
| Lumber 2×10 section lookup | A 13.875 in²; I 98.93 in⁴; S 21.39 in³ | A 13.875 in²; I 98.93 in⁴; S 21.39 in³ | PASS |
| Preset changes after loads entered | W12×30 I 238 in⁴/S 38.6 in³; SPF 2×10 E 1,400,000 psi, I 98.93 in⁴, S 21.39 in³, limit 5,500 psi; load retained | Same selected values; full-span load retained and moment remained 50 kip-ft | PASS |
| Beam lengths: 20 ft, 0 ft, −1 ft | valid / rejected / rejected | valid / rejected / rejected | PASS |
| Point loads at 0/20 ft and outside at −0.1/20.1 ft | accept / accept / reject / reject | accept / accept / reject / reject | PASS |
| Uniform load from 0–20 ft and endpoints outside span | accept / reject / reject | accept / reject / reject | PASS |

## Interpretation

Deflection values are compared before display rounding. The multiple-point-load
case has a 0.01-ft difference in the location of the maximum: the independent
reference scan gives 10.41 ft and the app's 500-interval sample reports 10.40
ft. The deflection magnitude rounds to the same 0.101 in. This is within the
runner's documented sampling tolerance.

The below-limit stress case also passes its 22,000-psi A36 allowable-stress
check. The above-limit A992 case exceeds both the allowable stress and the
proportional limit; the latter is reported as an elastic-range warning.
