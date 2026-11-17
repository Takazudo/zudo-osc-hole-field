# MC02 exact selected FFC interval audit

Source-only arithmetic for the five selected LX order codes on engineering
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`: C26618 (18 links), C29534 (28),
C32128 (3), C68390 (9), C81339 (3), total 61. Link-file hash and selected counts
are checked. No board, inventory, source generator or adopted hardware changes.

```sh
python3 -B scripts/checks/mc02_cable_contract/audit.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_cable_contract
pnpm circuit:check
```

`evidence.json` is the compact transcription of independent full-page reviews
made on 2026-11-17, with manufacturer document hashes and locators. Raw source
PDFs stay in the ignored coordinator cache. This offline audit validates frozen
reviewed metadata and performs Decimal endpoint arithmetic; it does not download
or re-inspect the PDFs. Source pin or exact/generic applicability changes require a new reviewed
transcription. The checked code/hash/scope contract prevents a generic sheet
from being relabelled as exact evidence at the same hash.

All numeric comparisons use closed declared intervals, not just nominal values.
An unbounded upper comparator represents a printed minimum. A missing cable
bound is UNSOURCED, not evidence of compliance. FH12 p2 insertion thickness and
adaptive-contact finish requirements are distinguished from p11 recommended
horizontal drawing dimensions. Support-length arithmetic remains conditional
on the drawing's end-support datum correspondence.

The exact C81339 and C68390 drawings declare insertion thickness 0.303 +/-0.05,
width +/-0.08, strip length 4 +/-1 and support length 8 +/-2 mm. C29534 declares
thickness 0.3 +/-0.03, width 4.5 +/-0.08, strip 3 +/-0.5 and support 5 +/-1 mm;
all three exact drawings give only nominal 0.225 mm supporting tape thickness,
so the explicit comparison to the recommended 0.188 mm minimum remains UNSOURCED.
C29534's STRUCTURE row specifies tin Sn 1 micrometre MIN against FH12's gold-plated
adaptive contact specification. C81339/C68390 finish is not established.

C26618's linked drawing is generic, with no exact customer code or selected
length: its family dimensions are deliberately not assigned to C26618.
C32128's publicly linked PDF is byte-identical to that generic drawing: source
bytes are available, but exact C32128 applicability is unestablished. Both remain
UNSOURCED for exact selected-code comparisons; neither inherits family dimensions
or another code's data.

The output preserves each declared interval and comparator, source hashes,
locators, requirement class, dimensional shortfall/excess, source scope and link
IDs. WITHIN_DECLARED_INTERVAL is only that numeric relation, not full mating
compatibility. An interval mismatch does not mean every physical unit fails.
No substitutions, tolerance waivers, nominal-only acceptance, contact-1 mapping,
mounted access, native KiCad, DRC, fill, manufacturing or formal adoption occur.

Implementation pre-check: circuit contract PASS, 84 manual inventory lines,
445 declared placements unverified; pin-asset check performed. No aggregate
regeneration is needed or admitted for this source-only independent checker.
