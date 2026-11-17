# Molex 150200075 source-to-model applicability

This source-only audit binds the independently reviewed SD-15020-001 revision F
drawing and the retained electrical model code/inputs. It does not import NumPy,
run a solver, update the BOM or qualify the product. Run `python3 -B audit.py`
from this directory, optionally with `--output` naming a new file; existing
outputs are never overwritten. `python3 -B test_audit.py` runs small fixtures.

The parameter-consumption matrix distinguishes three important paths:
capacitance uses coplanar zero-thickness strips; partial inductance uses width
and thickness and solves a return-current distribution; conductor resistance
uses a separate S-FLEX 50mm resistance interval scaled only by length. Merely
changing thickness in the geometry does not replace that resistance evidence.
The coupled victim response is nonlinear; 49/53mm endpoint samples alone cannot
prove a full-domain maximum, especially across other changing parameters.

The exact source supports length 49..53mm and width 0.27..0.33mm. Copper 0.10mm
is nominal, with no tolerance supplied. The audit leaves product resistance,
electrical guarantees and qualification unset. It provides the symbolic
conductor-only relation `R = rho(T)*L/(w*t)` using SI units. The optional, clearly
conditional geometry interval is `L/(w*t)` in 1/mm with thickness assumed exactly
0.10mm: `[49000/33, 53000/27]`. This is not a guaranteed product resistance range;
it excludes contacts and does not supply resistivity or a temperature domain.

Still required for a product-specific numerical model: thickness bounds,
applicable rho(T), finite-thickness/dielectric model justification, end-region
coupling and assembled contact applicability, and a sound interval/extremum
method. The earlier 51mm result remains an unchanged-material length-only
counterfactual. No new ground-share result or numerical sweep is generated.
DRC, zone fill, formal adoption and manufacturing remain on hold.
