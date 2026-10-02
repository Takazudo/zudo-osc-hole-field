# AO model primitive and source identity guard

## Problem and preserved scope

The fixed ideal AO model guard checked passive roles, values and endpoints but not primitive identity. Replacing the captured 100 kΩ summer-feedback resistor with a capacitor symbol/prefix while retaining those fields was accepted. A second admitted mutation connected pot body pin 4 to the private sense node: the pot was already in the allowed-part set, so the extra-branch check did not reject that new connection.

These bypasses were reproduced with read-only in-memory mutations of main e09a5f0. No circuit specification, selected component, panel position, simulation deck, numerical criterion or physical qualification changes in this correction.

## Change

The guard now binds every checked passive's reference prefix, captured symbol template and unit. The ordinary wiper/fail resistors retain their RC0603 template; the precision resistors retain RT0603; the feedback capacitor retains C0603C101. This does not promote unmatched nominal values to exact sourced MPNs. Existing procurement/evidence conditions remain unchanged.

Amplifier and pot identity checks also require their captured prefix, full project-library symbol and supported unit. The PTV09A-4020F-B103 interface has five pins: 1/2/3 form the potentiometer, and body pins 4/5 are explicitly NC in this capture. The guard preserves that actual interface and rejects new body connections or missing/extra pins. It does not assume a three-pin symbol.

Coherent private wiper/sense renames and nonfunctional placement changes remain accepted. All existing value, polarity, duplicate, DNP, extra-internal-connection and fixed-boundary checks remain. Rejection happens before the oracle or report/deck writes.

The model remains ideal DC attenuverter/summer/restorer algebra. Finite wiper loading, contact/taper behavior, capacitor dynamics, amplifier rails, physical input/output chains and component qualification remain excluded. The ±15 V ideal endpoint remains a mathematical demand, not a realizable output claim.

## Verification

- Entry component contract PASS: 65 manual records; pin assets checked, schematic/placement binding outside that contract scope.
- Initial baseline was canceled while confirmed queued to give an older projection run priority: NOT RUN, exit 143. No source command had started.
- Retried guarded baseline PASS in 198 seconds, no tracked drift.
- Ten isolated candidate tests PASS, including primitive prefix/symbol/unit mutations, the reproduced capacitor substitution before oracle/write, pot body-to-sense/wiper/AGND connections, complete five-pin identity, and preserved private-node renames. An initial scratch-only three-pin assumption was rejected by the canonical fixture and corrected to the actual five-pin interface.
- Ten real-root tests PASS in 0.865 seconds; the strengthened guard returns exactly the retained nominal source projection. Final component contract PASS for 65 manual records. Integrated-head aggregate/model regeneration and unchanged seven-deck/report hashes are merge gates recorded on the exact PR head and in its local verification receipt.

## Remaining

This check prevents a fixed ideal model from silently accepting an unsupported captured subgraph. It does not establish complete component evidence, actual headroom, DC error, power-off behavior, protection, stability, harness fit or any physical qualification. No issue closure or fabrication action is included.
