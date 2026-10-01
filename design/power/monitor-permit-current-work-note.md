# Monitor/permit current allocation

The isolated candidate now has a conditional DC allocation screen in
`monitor-permit-current-report.json`. It is still an unselected, unvalidated
draft. The screen does not qualify total supply current or change the original
20 mA per-rail allowance for all protection auxiliaries.

Five primary-source current rows are retained in the owner bundles: TPS37044
15 µA, TLV9022 35 µA per comparator (70 µA for both), REF3433 95 µA, SN74HC14
20 µA and SN74HC74 40 µA. Their sum is 240 µA, but the respective source
conditions differ from the complete candidate. In particular, the logic rows
use 6 V, rail-level inputs and unloaded outputs; the comparator row specifies
output low and input common mode at its negative supply; and the reference row specifies zero output load and 10 µF output
capacitance. Their application here remains an explicit assumption.

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
the bleed is not counted again as a separate +5 V feed.

With both the fault pullup and base drive counted simultaneously, the conditional
DC screen is 6.681 mA on +5 V, 2.108 mA on +12 V and 0.309 mA on −12 V. The
remaining allocated currents are 13.319, 17.892 and 19.691 mA respectively.
These are conditional allocation balances, not qualified physical margins.
The separate stable fault and permit-enabled states are also reported.

Still unbounded: HC slow-input/switching current; startup and capacitor charging;
reference slow-slew behavior; both retained RC clamp-return paths; negative-input
leakage; actual isolation/discharge circuits; and partial-power/ground-loss
behavior. Those loads must fit inside the existing allowance. No allowance is
removed from the master budget, and no rail/current limit is increased.


Verification: six focused accounting/topology regression tests, component and
documentation checks, fresh native monitor ERC/pin checks and guarded aggregate
regeneration pass. Independent primary-source/current-path review completed;
its missing-common-mode, independent-tolerance-validation and leakage-scope
findings were corrected. Installed/dynamic qualification remains NOT RUN.
