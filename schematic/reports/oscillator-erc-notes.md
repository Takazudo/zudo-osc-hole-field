# Oscillator/native schematic checks

Run `bash design/spec/modules/check_oscillator.sh` to regenerate and export with the pinned KiCad 10.0.6 oracle. The compact retained result is `oscillator-checks.json`; complete temporary ERC/netlist outputs remain local under `.circuit-cache/oscillator-check/`.

The O1–O5 and OCTAVE_REF sheets have **zero errors and zero warnings**. The initial integrated master retains twelve `pin_to_pin` warnings from the H1/H2 pilot LED symbols; they are outside the oscillator sheets and justified in the pilot report. They are not suppressed globally by the oscillator check.

The local `VEE_POWER_FLAG` asserts that the precision amplifier actively drives `VEE5` through its 100 ohm resistor. KiCad otherwise does not classify an amplifier output as a power source for AS3340 pin 3. It does not assert an externally available -5 V rail or prove startup behavior. Buffered -5 V regulation/load/sequencing remains a bench gate.

Exported pin-to-net parity covers every master component. Additional assertions prove all 80 oscillator panel UIDs bind once and the five timing nets remain separate (`/O1/TIMING_CAP` through `/O5/TIMING_CAP`). Only intended shared references and supply rails are global.

Source/hardware boundary: ALFA AS3340D SOIC-16 pin identities are confirmed from retained manufacturer bytes, but no V/oct accuracy, core startup, sync, output amplitude, protection or physical-board result is established by ERC.
