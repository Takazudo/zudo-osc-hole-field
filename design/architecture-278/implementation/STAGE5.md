# Dual metrics, numerical budgets and a concrete header repair

Stage5 continues from014449e7161cd7c8666e662152722f0e26d67cd3. It completes the bounded source deliverables: separate interconnect metrics, captured-circuit numerical budgets, a characterization specification, official DIN evidence, explicit connector-exclusion repair and whole-package hosting options. This is not hardware acceptance or a broader partition implementation.

## Interconnect metrics without an accidental green result

[DUAL-METRICS.md](stage5/DUAL-METRICS.md) and its generator retain225crossings for each comparison, separating wire cut range, connector developed allocations, PCB trace allocations and total. All85 physical links account270conductors:160signal and110AGND. There are190 wired endpoint rows because some share a conductor;35 direct shared-to-rear rows have no wire and are marked NOT APPLICABLE. Every allocated cut remains60±3mm. A wire-length allocation pass does not qualify assembled capacitance, stability, error or the whole circuit.

The original harness-envelope and historical complete-path checks remain distinct. Historical stage3baseline/refined/stage4shared-repair failure counts remain38/50/38. The new header repair retains38 strict complete-path overlength rows and334.018298mm maximum. No allowance, source endpoint, return or limit is removed. Each row remains electrical UNKNOWN and combined NOT QUALIFIED. Shared direct capacitance uses nine separate network obligations and unique-segment accounting; the five1k/100nF octave receiver loads remain separate dynamics.

## Numerical source budgets and characterization

[stage5-electrical.md](stage5-electrical.md) provides the compact worst-case/unknown table. The generator maps all225identities to actual active terminals through captured resistors, switches/pots and AC-coupled branches. Source assertions across all five oscillators guard the explicit numerical models; passive traversal is bounded and state-dependent, not an assumed operating point.

Representative conditional calculations:

- A100k control pot has25k maximum nominal Thevenin resistance. The retained planning tolerance and1k series case reaches31.01k. Its deliberately loose loading bound is15.691mV; a source-conditioned15nA bias sensitivity is0.464mV. Those independent worst voltage/resistance assumptions need not occur at the same wiper position. OPA4196 bias remains unknown.
- The10k FM/PWM wiper case reaches4.01k planning source resistance. Loading sensitivity is2.035mV at its input; gain2 makes bias/load propagation material. Diagnostic RC response is not complete amplifier stability. Intentional TUNE/FINE/PW filtering must not be judged against an invented flat audio-band requirement.
- Protected1V input, OSC_GATE_REF, analog SYNC_BUFFER, conditioned SYNC_GATE and AC-coupled HARD/SOFT paths use different captured circuits. SYNC_BUFFER ideal threshold calculations are1.471965V rising/0.971509V falling against existing planning windows1.35–1.65V/0.85–1.15V. Reference, resistor, ground, VOL and actual driver errors remain to be included. A retained HC delay point at50pF does not qualify1nF pulse transport.
- Five selected octave receivers imply ideal25mA initial demand and2.5µC charge for a5V step; this is not proof that the shared buffer supplies either waveform. Actual source impedance/current limiting, switch bounce and simultaneous/staggered loads are unresolved.
- The704.5mA×0.5mΩ return example is352.25µV, exceeding the prior proposed200µV term. Neither the actual return resistance nor full-state current is known; cancellation/equal-sharing credit is not taken.

Retained manufacturer limits keep their original supply/common-mode/temperature conditions. They are not combined into a fictitious guaranteed whole-chain bound. A manufacturer's diagnostic1nF drive statement cannot establish assembled stability. The bounded characterization specification names models, parameter ranges, observable errors/transients and existing targets; new allocations/ranges are explicitly proposals. No simulator/native campaign runs. A validated exact OPA4196 model is a named dependency, not permission to substitute another amplifier.

## Official DIN evidence and repair

[MECHANICAL-REVIEW.md](stage5/MECHANICAL-REVIEW.md) records official HARTING unrestricted typesheets for selected09032966824 and09031966922 plus the official mating guide. Exact URLs, drawing identity and hashes are committed; raw PDFs and metadata remain ignored. Restricted CAD was not accessed. The drawings establish contact drill1±0.1mm with0.05mm diameter true-position, flange dimensions and body envelopes. The mating guide pairs the selected parts at18.3–20.0mm PCB distance, supporting the19.2±0.3mm proposed stack comparison.

The larger official drill screen exposes more exclusions than the earlier minimum-tail screen. Eight whole middle headers move: O3 SAW/PUL +1.2mmX; O3 selector pair +4.5mmX; O4 selector pair +0.4mmX to retain neighboring courtyard separation; O5 selector pair−2.4mmX. No front package/control or pin map changes. The final independent screen covers480contact holes,10flange-hole envelopes and all85headers, with zero screened drill-to-land, same-face header-courtyard or shared30-to-hole conflicts.

The rebudget recomputes all225paths and240returns;26 path rows and23 return records change. All270wire checks pass with12.224881mm minimum-cut straight-distance slack against the10mm allocation. Power source-package pad coordinates remain bound to the stage4normalized table; all85transport header pad sets are rebound in the new report. Two-grip/frame/withdrawal reservations remain unchanged.

Twelve opposite-face GH-courtyard/hole projections remain UNKNOWN. Annular-pad size, signed drawing/mating datum registration, complete body/tail solids, guides, load-bearing frame, cable bends, fastener/finger access and other-function occupancy are not qualified. Zero screened exclusions is not ERC/DRC or physical clearance. The checker derives hole/flange envelopes from bounded evidence and rejects unsupported rotation rather than silently assuming a new orientation.

## Hosting choices are source-only proposals

[HOSTING-OPTIONS.md](stage5/HOSTING-OPTIONS.md) accounts for5904packages/8226units/1067bypass associations in each complete option. It compares the historical whole instrument, a proposed front-redesign/replacement-host arrangement, and core-only full-front reuse. All2572non-OSC K packages and13POWER packages have explicit source groups, with new carrier geometry null. No broader placement, copper partition or native board change is implemented.

Mixed front ownership matters: JL contains285OSC+775other packages; P contains35OSC+250other. Full front reuse means retaining all2519frontpackages, not silently replacing only the OSC subset on unchanged physical boards. Core-only reuse requires its original front endpoints/interfaces and a new path analysis; redesigned-front path totals do not transfer. Physically retaining old K also retains770OSC+30shared packages and obstructs straight rear extraction. A deeper cover alone does not solve that service conflict.

A concrete owner-level proposal, if prioritizing front-copper reuse, is to develop the core-only/full-front option instead of mixed-front replacement. Consequences: retain2519frontpackages, but design interface adapters and re-evaluate complete paths;2572non-OSC+13POWER hosting/service remains unresolved. The alternative continues explicit JL/P replacement groups and their1,025non-OSC packages. Neither option is adopted, dimensioned to fit or presented as a cost saving. Owner preference should select a broader hosting option before its implementation; this stage supplies reviewable consequences, not a permission request for already completed source work.

## Named next work and boundary

Next work should address a concrete dependency: exact OPA4196 dynamic-model validation and proposed characterization targets; actual return/current/parasitic evidence; final annular-pad/datum/body clearance for the12projections; or a reviewed whole-package hosting option. Do not repeat the general provenance audit or add topology solely for the historical complete-length metric.

All canonical board/grid/decision/circuit/workflow artifacts, fixed front centres,33functions/fiveOSC and KEEP_K1402_INCUMBENT are preserved; parked260/277 remain unchanged. Native KiCad10.0.6/ERC/DRC/simulation/bench/physical qualification are NOT RUN. Stage1 and incomplete acceptance issues remain OPEN. No adoption, merge, purchase, fabrication or energization occurs. Independent reviews and final reproducible checks are recorded in WORK.md.
