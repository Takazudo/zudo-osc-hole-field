# MC02 project-side FH12 endpoint mapping inventory

The retained 61 links define **122 virtual connector fields**, not 122 instantiated
numbered FH12 PCB footprints. `links_gate.py`'s `fh12_size` and `GeoMaker` generate
rectangle envelopes and cable tails. The source has logical conductor positions,
not an origin/rotation/pad-number assignment for physical connector footprints.
This extraction makes that boundary explicit while preparing all project-side
rows for a later primary-drawing correspondence review.

```sh
python3 -B scripts/checks/mc02_connector_mapping/mapping.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_connector_mapping
pnpm circuit:check
```

The checker freezes exact engineering `2c53715` source bytes and reuses the retained
geometry functions to reproduce every virtual field/tail rectangle, with no
placement search and no KiCad. It records each endpoint's exact connector string,
cable code, board, B face, specified bottom-contact type, panel-frame field
rectangle/center and direction from that field toward the slot. Front and K
endpoint directions are opposite. These are geometric field directions, **not**
KiCad footprint angles or contact-order handedness.

Each endpoint retains the complete logical conductor order and logical position1,
but explicitly leaves physical reference, footprint rotation, local/global pad1
coordinates and numbered-pad coordinates null (`NOT_ESTABLISHED`). The logical
position1 net must not be promoted to primary-source physical contact1 without a
reviewed correspondence and implemented placement/footprint transform.

The existing `flex-land-patterns.json` contains pad size/pitch formulas, but its
`st01h.contact_1_end` is UNSOURCED and the envelope model does not locate a numbered
pad relative to a footprint origin. That historical source state is recorded;
it does not contradict a later official drawing resolving which end is contact1.
The official drawing would still need an explicit project transform before it
establishes any of these physical pad coordinates.

The frozen ten board files are scanned for literal FH12 source names. No matches
are observed on these bytes. This is only a name-based observation, not a claim
that every arbitrary custom footprint's manufacturer identity was inferred.
Any newly named FH12 board object triggers a mapping-review error instead of
silently retaining the virtual-only classification.

Inputs carry SHA-256 pins and source locators. The output is stdout for local
ignored retention; no canonical source/output, footprint, board or inventory is
written. No primary-PDF access, source waiver, mounted access, pad binding,
actuator maximum, hardware adoption, native validation, DRC, fill or manufacturing
acceptance is claimed. In particular field geometry cannot prove contact-side
orientation after physical folds or human latch access.

Pre/post circuit checks PASS:84 manual inventory lines,445 declared placements
unverified; pin-asset check performed. Seven focused tests pass, including all61
retained geometry reproduction and rejection of a changed field rectangle.
