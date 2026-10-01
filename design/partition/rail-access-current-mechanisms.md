# Rail access current mechanisms

Status: source topology and remaining constitutive conditions only. No new
terminal-current maximum, operating class or source variant is selected here.
The unchanged 1 mOhm common rail, 20 mV hot distribution and 0.20 V total
limits still require every shared and individual access cost.

## U1416 and its physical bypass pair

U1416 is the O4 OPA4196IDR package. Its exact source units are three input
buffers and the sine-output buffer. C1450 bypasses U1416 pin 4 (+12 V), and
C1451 bypasses pin 11 (-12 V). Their packing keys are not the decoupled package
identity; `physical_packages[].decouples_ref` supplies that exact mapping.

| Output | Source net | Explicit resistive branch | Other direct component contact |
| --- | --- | --- | --- |
| U1416:1 | /O4/FM_BUFFER | R1421, 100k, to /O4/C1eb779_SUM | U1412:3 input and own feedback U1416:2 |
| U1416:7 | /O4/PWM_BUFFER | R1427, 100k, to /O4/C42d8cd_SUM | U1412:10 input and own feedback U1416:6 |
| U1416:8 | /O4/SYNC_BUFFER | R1456, 100k, to /O4/C99bd37_GATE_SENSE | Own feedback U1416:9 |
| U1416:14 | /O4/C70dbdb_DRIVE | RB1402, 499 ohm RC1210FR-07499RL, to /O4/C70dbdb_ISO_MID | Own feedback U1416:13 |

These are series/load-network branches, not four 100k ground shunts. Source
crossings retain the complete endpoints across J/K. A supported voltage
difference and operating resistance minimum can bound each *resistive*
contribution. Input leakage/bias and all parasitic displacement are additional
terms. Blank component identities do not inherit another resistor's guarantee.

The retained OPA4196 fact gives a 250 uA per-amplifier full-temperature
quiescent maximum with **IO = 0 A**. It does not bound the loaded or dynamic
package current. The resistor network explains why the full 2.1 A rail envelope
at one IC pin is a loose diagnostic, but does not authorize substituting a
quiescent or guessed package cap. A smaller package bound requires its actual
normal output/input waveforms, internal loaded current and qualified conditions.

## Shared feed and local loop accounting

Take currents positive into each component at the rail pad. The actual +12 V
shared island cut carries

```
I_shared = I(U1416:4) + I(C1450:1).
```

Writing the two currents as `a + q` and `-q` is an exact change of variables:
the shared cut carries `a`, and the two individual access paths carry their
respective full currents. It supplies no upper bound on `a` or `q`. The PCB
response to `q` uses the difference of the two actual contact profiles; shared
and individual conductor costs remain in the same operator. Nearby placement
or the packing key does not establish cancellation.

The capacitor's rail and AGND terminal currents must both appear with opposite
signs for its two-terminal constitutive model. Normal `C*dV/dt`, leakage and
parasitic/environment terms need explicit bounds before any smaller dynamic
access-current claim. The IC has two rails and multiple signal contacts; its
ground response is not replaced by an invented AGND supply pin. Aggregate
source-current, external patch, startup/fault and thermal qualification scopes
remain under #57/#59/#65.

The source-owned parallel-feed repair reduces the actual shared access
resistance without assuming a smaller current. It changes the native conductor,
so the historical 5.124917301 mOhm U1416:4 diagnostic is not rebound to it.
