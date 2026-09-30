# Wavefolder native ERC notes

Unvalidated draft — not bench tested. Source: design/spec/modules/wavefolder.py.
Run bash design/spec/modules/check_wavefolder.sh with pinned KiCad10.0.6.

W2/W1 have zero errors and six warnings each. The three retained white input-LED
symbols each expose two Unspecified pins, producing pin_to_pin warnings against
the passive driver network. Source-backed anode/cathode mapping is unchanged.
The checker verifies exact panel LED references and warning type. No suppression
or symbol pin-type alteration was made. The108 other warnings on this fork belong
to the previously captured pilot/filter/envelope/power families.

All22 locked panel UIDs occur once. W2 remains left of W1. Only rails/AGND are
global; AC_NODE and every fold junction remain local to each instance and its
core island. Lamps observe protected input buffers, never folding junctions.
Complete native pin/net parity passes, including unused OTA pins, decouplers,
remote controls and all explicit no-connect jack switch contacts.

Native checks do not establish analog operation, fold count, diode matching,
stability, fault protection, physical routing or current maxima. The feed-forward
signal graph excludes designed interstage regenerative feedback; real amplifier
loops and the PNP bias servo still need stability qualification.
