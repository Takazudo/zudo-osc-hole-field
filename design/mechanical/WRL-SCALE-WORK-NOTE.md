# WRL display-model scale repair (issue #56)

KiCad's VRML convention is 0.1 inch (2.54 mm) per coordinate unit. The
[KiCad source](https://gitlab.com/kicad/code/kicad/-/blob/9.0/pcbnew/exporters/exporter_vrml.cpp)
states the convention for external model files; the pinned 10.0.6 oracle
independently exported a one-footprint board in millimetres with a 2.54 root
scale. The regression in `scripts/libgen/fixtures/check_wrl_dimensions.py`
uses that native export, including the footprint's model scale, to compare all
three axis bounds with the source display envelopes.

The project model directory has 24 WRLs. Fourteen project-authored display
envelopes required repair: three from `gen_component_envelopes.py`, ten from
`gen_ic_package_envelopes.py`, and the Bourns PTV09A-4020F family model. The
former generators wrote millimetre values directly, giving 2.54 times the
intended bounds in KiCad. The PTV09 model used inch values, giving one tenth of
its 10 x 10 x 6.8 mm display body. All 14 now export at their stated x/y/z
bounds within 0.005 mm; their exact receipts and published model copies carry
the new hashes. No footprint model transform or fixed hardware position moved.

The other ten WRLs retain their existing provenance and bytes: imported or
copied family models for C0603, C0805, C1206, F1812, IDC, the two LEDs,
R0603, and SMA, plus the previously corrected project-authored SRBV160803
selector keepout. The retained SRBV regression already checks its 18.2 x 20.1
x 27 mm bounds in KiCad units. Their fidelity classes are unchanged.

These are display envelopes. Some dimensions are family bounds or estimates;
the PTV09 model omits shaft, mounting and seated detail. Issue #35 must use the
retained drawings and explicit allowances for board-stack analysis. Physical
seating, shaft and bushing fit, and hardware clearance remain **NOT RUN**
without a physical assembly. Every schematic and PCB remains an unvalidated
draft.
