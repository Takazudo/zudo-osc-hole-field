# The 104 adjustments now have a procedure skeleton, but only 16 have a sourced target and no module has a test point

Task D step 1, 2026-11-20. Joins the ST-07 relocation plan (`design/stack/trimmers/relocation-plan.json`,
sha256 `56ce0dac…075dd`, pinned) with the io-partition pin map. For every adjustment and probe pad it records
the adjusted nets, the one-hop parts on them, a topological class, a module procedure group and order, a
proposed stimulus and observation, the sourced target, and the access state after the FFC projection.

```sh
python3 -B scripts/stack/studies/task_d1_calibration/inventory.py --output scripts/stack/studies/task_d1_calibration/result.json
```

`result.json` sha256 `c653cb3c406adbb72799da4ebbc02bc7b92871c7009232e161a368e9378bade1`.

## 32 trims sit at an amplifier input or feedback node, and 15 of those must move or are blocked

| Topological class (one-hop connectivity) | Count |
| --- | ---: |
| Reference divider, wiper isolated by a feed resistor | 38 |
| Rheostat at an amplifier input or feedback node | 32 |
| Exponential-pair reference node | 15 |
| Rheostat to ground through a fixed resistor (oscillator scale and RZ) | 10 |
| Oscillator core pin (HF) | 5 |
| Rail probe pad | 4 |

The 32 amplifier-node trims are the ones where added loop length matters most. Seventeen are already on
the rear, thirteen have unreviewed rear candidates (up to 25.74 mm, RV4502), and two (`RV8308`, `RV8408`,
TIA_CAL) are front-blocked with no candidate. The third blocked trim, `RV4508`, is a divider whose wiper is
isolated by a 470 kΩ feed resistor, so a longer wiper route is less exposed than on a feedback node.

## Only 16 adjustments have a sourced target

`design/standard/electrical-standard.json` (`calibration`) supplies the 5-cent pitch-tracking target over
0..5 V at 25 °C after 20 minutes of warm-up (oscillator HF, SCALE and RZ, 15 trims) and the 2 mV octave-step
error (octave reference gain, 1 trim). The other 88 targets are UNRESOLVED. The procedure text and order
in the file are proposals for the design reviewer, not sourced values.

## The standard calls for test points, but the only test pads are four rail probes

The standard says factory adjustment goes "through accessible test points". The K board has four D1.5 pads,
on +12 V, −12 V, +5 V and AGND. No module output or internal node has a test point, so every trim would have to be
observed at a panel jack or through new test points. That is a design decision for the reviewer.

## Scope

Source connectivity and the electrical standard only. Access is the unreviewed ST-07 courtyard screen.
No tool access, loop length, guard, measurement or acceptance claim.
