# Issue #25 work note

## Requested result

Capture the two B1/B2 precision 1-to-3 multiples and X1/X2 maintained manual A/B selectors from the locked panel UIDs; generate shared family sheets, document design decisions and open bench gates, and provide per-instance rail estimates.

## Files and changes

- Added `mult.py` and `manual_ab.py`; added both families to `instrument.py` at indices 31–34 without changing existing reservations.
- Added per-family current worksheets/builders, topology and panel-binding tests, authored architecture pages and ERC warning notes.
- Regeneration initially exposed the fixed-ref collision between B1's locked input LED `D109` and H1's existing internal magnitude-bridge diode `D109`. With parent authorization, internal sample-hold diodes now use the `DH` reference prefix; all pin nets and locked LED references are preserved. Added a regression comparing sample-hold internal references with the complete panel lockfile.
- Generated `mult.kicad_sch` and `manual_ab.kicad_sch` through the spec generator. No panel positions changed.

## Evidence and limits

- MULT uses the high-impedance precision input cell and three OSC-ES-1 precision output cells, one OPA4197 quad per instance. The 1 mV open-to-10 kΩ output-load behavior and its 1.2 cent conversion are stated as targets/calculations, not results.
- A/B inputs are isolated and buffered before separate 2.2 kΩ switch-contact resistors. A 10 MΩ resistor biases the common node. The 2MS1 pin/contact and lever-A mapping remains provisional because a manufacturer-primary contact drawing is unavailable in retained evidence; verify with a continuity coupon.
- Switching clicks are accepted. No click-free behavior or 1 V/octave tolerance is claimed.
- No usable retained OPA4197 model or switch transition model is available; module simulation is NOT RUN.
- Rail estimates use the preliminary standard load table and remain planning allowances. Guaranteed maximum rail currents, fault/clamp currents and overlap transients are not established.

## Verification

- Fresh-branch `bash scripts/checks/regen-all.sh`: pass; no baseline diff was present before edits.
- `bash scripts/checks/regen-all.sh --check`: pass after implementation.
- `pnpm circuit:check`: pass; `SCOPE: inventory provider=manual; schematic/placement binding not performed (42 lines, 0 declared placements unverified); pin-asset check performed`.
- `pnpm check`: pass; generated component pages/preflight/models/previews are current and site type-check passes.
- `python3 -m unittest discover -s design/spec/modules -p 'test_*.py'`: 32 tests pass; report builder `--check` commands pass; `python3 -m unittest discover -s scripts/schgen -p 'test_*.py'`: 7 tests pass.
- `bash scripts/schgen/smoke.sh` with pinned KiCad 10.0.6: zero ERC errors, 64 remaining pin-to-pin warnings all documented for LED bridge pin types, exported netlist parity passes, and the deliberate H1/H2 held-node mutation is rejected.

Visual schematic inspection was not run. This work did not run browser, full-site build or hardware tests.
