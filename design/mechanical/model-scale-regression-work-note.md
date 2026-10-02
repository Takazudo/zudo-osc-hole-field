# Native display-scale regression completion

Issue 56's existing repair divides generated WRL coordinates by KiCad's 2.54 mm
coordinate unit and corrects the PTV09 display body. Later placement checks cover
axes, offsets and board-side transforms. This continuation adds explicit native
rejection evidence for the two original scale errors, preserving the repaired
assets and their historical acquisition/derivation receipts.

The pinned KiCad exporter reads disposable copies of an IC body with coordinates
multiplied by 2.54 and a PTV09 body multiplied by 0.1. A separate loaded footprint
has only its model Z scale doubled. Before requiring rejection against unchanged
baseline dimensions, the checker independently verifies that the native export
actually reproduced the intended erroneous dimensions. The report retains both
baseline and observed XYZ dimensions and the mutation parameters.

The historical IC mutation exports approximately 4.445 x 7.747 x 3.683 mm instead
of 1.75 x 3.05 x 1.45 mm. The pot mutation exports 1 x 1 x 0.68 mm instead of
10 x 10 x 6.8 mm. The footprint Z mutation exports approximately 1.75 x 3.05 x
2.90 mm. All three are rejected with GeometryMismatch. Temporary WRLs are removed
in a finally block; all snapshotted source assets remain byte-identical.

Positive coverage now includes every model from the generic component-envelope
generator, adding both compact LED bodies to the existing native unit checks.
The fresh pinned run passes 21 positive cases and 11 negative controls; the
existing 11 transform/geometry unit tests and component contract also pass.
Baseline guarded aggregate regeneration passed in 201 seconds. Final aggregate
and CI results are recorded in the PR.

This verifies display-model units and the existing placement scope. It does not
establish exact seating, actuator/shaft/bushing geometry, solderability, thermal
behavior or installed fit. Original family/derived classifications remain intact;
DIP height and other stated unknowns are not promoted to qualified dimensions.

Final guarded aggregate regeneration and documentation check pass (190 seconds).
Independent review confirms the three native rejection controls preserve source
assets and close the scale-regression acceptance gap. The two additional LED
unit cases also pass in the final 21-case run. Physical qualification remains
NOT RUN; publication and exact final CI are tracked in the PR.
