# Monitor/permit current allocation

The isolated candidate now has a conditional DC allocation screen in
`monitor-permit-current-report.json`. It is still an unselected, unvalidated
draft. The screen does not qualify total supply current or change the original
20 mA per-rail allowance for all protection auxiliaries.

Six package-current rows are retained: TPS37044 15 µA, both TLV9022
comparators 70 µA, REF3433 95 µA, two SN74LVC1G17 packages at 10 µA each and
one SN74LVC1G74 at 10 µA. Their sum is 210 µA. The SN74LVC1G17 row covers 1.65…5.5 V with **VI=5.5 V or GND** and
IO=0; it is not a general VI=VCC condition. The latch has its own retained
input conditions. These rows do not bound slow-input or switching current. The comparator row specifies output low and common mode at
its negative supply; the reference row specifies zero output load and 10 µF
output capacitance. Application remains conditional. U106 settles at approximately 4.545 V with
a 5 V supply because of R125. Both U104 and U106 actual HIGH inputs lack direct coverage by the
buffer ICC row. U106 additionally has a sustained divider voltage. Additional
steady input-stage current remains an open DC budget gate. The 500 µA ΔICC row at VCC−0.6 V is not extrapolated to this
voltage. The 210 µA sum is only a conditional table-row assumption.

The resistor screen uses the exact RT and RC families' separate tolerance/TCR
limits and a stated 25 °C reference / −40…125 °C analysis envelope. It assumes
zero input and output/off-state leakage, reference voltage at most 3.31 V and normal rail limits.
The coarse reference monitor does not establish that narrow reference bound.
A passive-network voltage bound deliberately overestimates the reference feed
through R102 rather than substituting a nominal current for a maximum.

The negative-fault veto can clamp REF_SENSE. Its feed bound now uses only
R109..R112, omitting the bypassed bottom resistor. That gives 4.545 mA
conditional reference output demand. This load is charged
**once to +5 V**, in addition to the reference's quiescent current. Base-drive
current already includes current subsequently flowing through the base bleed;
the base bleed is not counted again as a separate +5 V feed. The new timing
bleed R125 is separately counted through R120 in permit-enabled and conservative
states (nominally 45.45 µA); it is distinct from the transistor base bleed.

With both the fault pullup and base drive counted simultaneously, the conditional
DC screen is 6.699 mA on +5 V, 2.108 mA on +12 V and 0.309 mA on −12 V. The
remaining allocated currents are 13.301, 17.892 and 19.691 mA respectively.
These are conditional allocation balances, not qualified physical margins.
The separate stable fault and permit-enabled states are also reported.

Still unbounded: LVC slow-input/switching current; startup and capacitor charging;
reference slow-slew behavior; retained-charge return paths; negative-input
leakage; actual isolation/discharge circuits; and partial-power/ground-loss
behavior. Those loads must fit inside the existing allowance. No allowance is
removed from the master budget, and no rail/current limit is increased.


Verification: revised current accounting and topology tests pass. Source-table
applicability, dynamic and installed qualification remain open; final aggregate
and documentation verification are pending for this revision.
