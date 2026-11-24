# Beam Designer

## Purpose
A Python desktop app built with Tkinter for designing and checking a simply
supported or cantilever beam. The app will calculate reactions, shear,
moment, deflection, bending stress, and whether the beam is strong and stiff
enough.

## Platform
- Implement as a desktop application in Python using Tkinter for its interface
- Present the beam workspace, inputs, and results in a desktop window
- Keep this specification focused on the application; web and mobile versions
  are out of scope

## Inputs
- Support type: simply supported or cantilever
- Beam length in feet
- Material type: steel or lumber
- Beam shape: steel W-shape or lumber size
- Beam designation or dimensions
- Deflection limit as L divided by a positive denominator (default 360)
- Point loads and uniform loads

## Beam properties
- Steel: W-shape selection and steel material preset
- Lumber: common dimensional-lumber sizes and wood material preset
- Include a local material database containing elastic modulus `E` and
  proportional-limit data for each supported material and grade/species
- Include a local beam-section database containing area `A`, moment of inertia
  `I`, section modulus `S`, and designation for each supported W-shape or
  lumber size
- Store database values with source, units, and a material or section identifier
- Display the selected beam section's cross-sectional area `A` both in the
  beam-property panel and beneath the beam model
- Show the selected material, grade/species, `E`, section designation, `I`,
  and `S` in the beam-property panel
- Clearly label database values as reference data and note that local values
  may require verification against the applicable standard
- Display the beam length, area, moment of inertia, and section modulus
- Strong-axis bending will be the initial behavior
- US customary units will be used throughout: ft, kip, psi, and inches
- Label every input and result with its unit

## Loads
- Provide point-load and uniform-load controls in the beam workspace
- Place load controls directly below the beam model
- For point loads, allow entry of the exact position along the beam in feet
- For uniform loads, allow entry of exact start and end positions in feet
- Provide an "Add load" action for numeric entry and a separate
  "Place on beam" action for click or drag placement
- Allow a user to drag or place a load on the beam after selecting its type
- Allow the magnitude, position, and endpoints to be edited numerically
- Support multiple point loads and multiple uniform load segments
- Show invalid or out-of-range loads with inline feedback
- Remove an individual load with an obvious delete control

## Calculations
- Reactions from static equilibrium
- Shear and moment diagrams
- Elastic deflection
- Bending stress `fb = M/S`
- Calculate flexural stress at the extreme fiber and compare it with the
  selected material's proportional limit
- Treat the proportional-limit check as an elastic-range warning, not as a
  strength pass/fail limit
- Maximum bending stress compared with the allowable bending stress
- Maximum deflection compared with the selected limit (default `L/360`)
- Report the location of maximum shear, moment, and deflection

## Outputs
- Beam drawing with supports and load arrows
- Draw a dashed, scaled deflected shape beneath the beam using the calculated
  deflection values and a physical vertical scale based on span length
- Shear, moment, and deflection diagrams
- Reactions and maximum calculated values
- Clear pass/fail cards for bending and deflection
- Show the maximum flexural stress and proportional limit for the selected
  material
- Highlight the beam in amber or red and display an inline warning when
  maximum bending stress exceeds the proportional limit
- Mark the corresponding high-stress location on the beam diagram or moment
  diagram
- Distinguish the proportional-limit warning from the allowable-stress pass/fail
  result
- A short calculation summary showing key assumptions and formulas
- Provide an Export results button that saves x (ft), shear V (kip), moment M
  (kip-ft), and deflection (in) at each calculation point to an Excel-compatible
  CSV file with column headers and units
- Require valid beam inputs and loads before exporting results

## Save and open
- Provide File > Save and File > Open for beam designs in a local file
- Save and restore support type, span, material and grade, section, allowable
  bending stress, deflection limit, and all loads
- Require a valid beam setup and valid loads before saving
- Recalculate after opening a design and report invalid or unreadable files
  without replacing the current design

## Layout
- Arrange left controls, center beam and diagrams, and right results in the
  desktop window
- Allow the window to resize while keeping panels and controls readable
- Keep the interface on a white background with pale neutral panels
- Use minimal borders, clear typography, and restrained shadows
- Use muted colors consistently: blue for loads, teal for shear, amber for
  moment, and purple or red for deflection
- Reserve green and red primarily for pass/fail status
- Add accessible labels and keyboard focus styles

## Look and feel
- Minimal engineering dashboard rather than an illustration-heavy interface
- Clean and professional
- Blank beam setup on initial load
- No sample beam or example loads are shown automatically
- Include a prominent "Load example" action that restores the 20-ft W12x26
  validation case
- Highlight the selected support, material, and load in a restrained way
- Use tooltips for terms such as moment of inertia, section modulus,
  elastic modulus, and the deflection limit

## Behavior and feedback
- Update calculations only after valid required inputs are complete
- Show neutral placeholders until enough data is available
- Include one action to reset all beam and load inputs
- Preserve entered values while changing unsupported presets, where possible
- Explain why a calculation cannot run using an inline status message
- Round displayed values only at presentation time; retain full precision
  internally

## Validation
The primary hand-check case is a 20-ft simply supported W12x26 beam with
a 1 kip/ft uniformly distributed load. The expected maximum moment is
50.0 kip-ft and deflection is 0.609 in.

Additional test cases should cover:
- A cantilever beam with a point load at the free end
- A cantilever beam with a uniform load
- A simply supported beam with a centered point load
- A simply supported beam with multiple point loads
- A stress case below the material proportional limit
- A stress case above the material proportional limit
- A section-property lookup case for both steel and lumber
- A database selection change that updates `E`, `I`, `S`, and proportional limit
- Valid and invalid beam lengths
- Loads at and outside beam endpoints
- Lumber and W-shape section-property lookups
- Material or beam preset changes after loads are entered
- Saving and opening a design with point and uniform loads and a custom limit
- Invalid or unreadable design files leave the current design intact
- Exported CSV headers and rows match the calculated beam values

Store hand calculations and test cases in `02_validation/README.md` and
related files under `02_validation/`. Store example screenshots or exported
results in `03_output/`.

## Out of scope
- Continuous beams
- Shear stress checks
- Buckling and lateral-torsional stability
- Connection design
- Beam self-weight
- Dynamic or moving loads
- Metric-unit mode
- Printing and PDF export
