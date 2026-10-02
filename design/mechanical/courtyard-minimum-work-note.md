# Source courtyard minimum preservation

The existing courtyard normalizer replaces every boundary with the pad/body
bounding box plus 0.25 mm. That can shrink a larger manufacturer-recommended
boundary, including the proposed KEMET 0603 Density B geometry. No capacitor
replacement or physical footprint is selected by this tooling change.

A footprint may declare a hidden `ProjectCourtyardMinimumBox` property containing
four whitespace-separated local millimetre coordinates: `xmin ymin xmax ymax`.
The generator unions that minimum with the unrounded normal envelope, then rounds
lower coordinates down and upper coordinates up to 0.01 mm. The minimum is a
floor, not an exact final size. A smaller source minimum cannot shrink the normal
envelope. Duplicate, malformed, non-finite unserializable precision, and zero/reversed-area declarations
are rejected. Explicit minima also require exact courtyard coordinates before reusing existing
bytes; tolerance cannot retain a slightly inward edge. Missing declarations retain
the previous nearest-rounding behavior.
Raw geometry callers of `envelope()` do not consume the source minimum.

Eight regression tests cover source dimensions, translated/asymmetric boxes,
smaller and non-grid minima, invalid declarations, raw geometry semantics and
byte-identical normalization of every existing floorless footprint. A fresh
pinned KiCad10.0.6 fixture verifies that the hidden property and outward courtyard
survive native load/save/reload. The fixture creates and removes disposable local
files; it is also run in CI.

The five existing monitor CAD receipts preserve the historical acquisition and
original derivation hashes: their represented assets remain byte-identical.
A first post-change run rejected updating only derivation hashes because the
receipt contract requires equality with acquisition inputs. No historical input
was rebound to new bytes; those proposed receipt edits were withdrawn. The fresh
current monitor native report binds the modified generator and unchanged assets;
its electrical values and qualification flags are unchanged.

Validation: baseline guarded aggregate regeneration passed (186 seconds); eight
focused tests and native roundtrip passed after review fixes. A post-change
aggregate plus documentation check passed (188 seconds) before those two targeted
rounding fixes; exact final aggregate replay runs in PR CI. Physical fit, seating and assembly qualification are NOT RUN.
