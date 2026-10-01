# ADG5401F protected output candidate — bounded issue-59 study

**ADG5401FBCPZ-RL7 provides a useful integrated main/feedback topology, but this candidate is not admissible protection.** Documented operation includes the actual ±12 V rails and the +8 V envelope outputs. The ±12 V dual-supply precision, bias and complete release limits remain unestablished. The datasheet expressly requires a ground reference for proper power-off operation, so the IC cannot independently close the local-ground-loss obligation. No installed part, source contract, current ceiling, geometry, old receipt or inventory was changed. Issue 59 stays open.

The [candidate input](integrated-output-candidate.json), [source records](integrated-output-candidate-sources.json), [calculator](../../scripts/checks/integrated_output_candidate.py) and [generated report](integrated-output-candidate-report.json) retain the exact topology, conditioned calculations and unresolved requirements. The original ±5 V / 10 kΩ / 5 nF precision scenario, 1 ms settling deadline, 1 mV load-dependent error, 2 mV calibrated error, 10% overshoot, external ±12 V faults, 33 modules and 438 centres remain unchanged.

## Evidence and exact identity

The official [ADG5401F Rev. 0 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adg5401f.pdf), printed page 32 / physical index 31, lists **ADG5401FBCPZ-RL7**, **CP-10-16**, a 10-lead LFCSP with 3 × 2 × 0.75 mm body, −40…125°C. [DigiKey's exact identity page](https://www.digikey.com/en/products/detail/analog-devices-inc/ADG5401FBCPZ-RL7/13617828) identifies **505-ADG5401FBCPZ-RL7CT-ND**. These observations do not establish stock, assembly suitability or a selected supplier route. ADG5401 without the **F** is a different device and is rejected by the checker.

The official datasheet and [UG-1755 Rev. A](https://www.analog.com/media/en/technical-documentation/user-guides/eval-adg5401febz-ug-1755.pdf) were readable through the web tool. Actual-byte requests to official lowercase/uppercase and evaluation URLs failed with HTTP/2 errors or bounded HTTP/1 timeouts. One manufacturer-authored Mouser mirror request also failed. Both PDF source records therefore remain **SOURCE UNAVAILABLE**, with zero-hash sentinels and exact observed locators. No PDF digest was invented, and the conditional table calculations are not promoted to primary-confirmed project limits.

Actual official [ADI evaluation wiki HTML](https://wiki.analog.com/resources/eval/adg5401fsdz) and its [Figure 20 schematic PNG](https://wiki.analog.com/_media/resources/eval/adg5401f_schematic.png) were downloaded, hash-bound and visually inspected. They are separate available sources for the demonstrated two-channel output/DAC arrangement and broad powered/unpowered S/SFB protection. They do not establish missing ±12 V performance. The wiki's board supply prose is not used as a chip rating. All downloaded bytes remain in ignored cache with their notices; only metadata and minimal extracts are committed.

## Concrete candidate connectivity

```text
Existing OPA4197IPWR channel:
  +IN = SIGNAL             -IN = FB               OUT = DRIVE
  DRIVE -- 10 MΩ || 10 nF -- FB

ADG5401FBCPZ-RL7:
  pin10 D   = DRIVE        pin1 S   = SW_DRIVE
  pin9 DFB  = FB           pin2 SFB = SENSE_LIMITED
  pin5 VDD  = VP           pin6 VSS = VN           pin4 GND = GND
  pin8 IN   = PERMIT       pin3 FF  = FAULT_N       pin7 POC = intentionally floating

SW_DRIVE -- 499 Ω -- 499 Ω -- JACK
SENSE_LIMITED -- 4.99 kΩ -- JACK
PERMIT -- 100 kΩ -- GND
FAULT_N -- 100 kΩ -- +5V
VP/VN each -- 100 kΩ -- GND
VP/VN each -- 100 nF -- GND
```

The exact 499 Ω, 4.99 kΩ, 10 MΩ, 10 nF and 100 kΩ identities/evidence are inherited unchanged from the prior precision candidate. The proposed bypass identity **GRM188R71H104KA93D** is already present in the project and appears in the observed evaluation-board BOM, but its manufacturer's effective capacitance, bias/temperature behavior and leakage evidence remain unavailable. This is a logical pin map, not a reviewed footprint or native schematic. The independent PERMIT generator, its power domain and physical ground-continuity sensing are still absent.

Keep both 499 Ω resistors **between S and the jack**. Moving them between the amplifier and D would remove the bound on current flowing from a cold external jack through a still-conducting main switch into the ADG5401F's internal D-to-rail clamps. Likewise, keep the sense limiter on the external side of SFB. Shorting S and SFB behind one common 998 Ω limiter would sense before that resistor and would not compensate its precision load drop.

During normal enable, the D–S and DFB–SFB channels close and the internal D–DFB path opens. During a powered disable or either source-channel fault, the documented internal D–DFB switch closes to retain local amplifier feedback (datasheet p30, physical index29). The persistent external 10 MΩ/10 nF path remains in every state. Internal feedback closure skew and operation through arbitrary rail collapse are not specified here; unpowered amplifier operation is not inferred.

Leaving POC floating disables the optional 30 kΩ source-to-GND pull, according to observed p31. IN absent is described as OFF; the added 100 kΩ pull-down supplies a local default-low bias under a valid reference. FF is an indication of source overvoltage relative to the local supply rails, not proof of independent return continuity or a complete all-rail supervisor.

## Actual ±12 V operation versus table conditions

Observed datasheet Table 1 and p29 describe ±5…±22 V dual operation and signal range VSS…VDD−2 V. The original minimum VP is 11.53 V, giving a +9.53 V positive signal limit and **1.53 V headroom above +8 V**. This removes the discrete BSS138N pull-up's particular +8 V gate-headroom problem. It does not establish on-resistance or accuracy.

The ±15 V table requires ±15 V ±10%; its resistance rows use ±13.5 V and leakage/current rows use ±16.5 V. The actual 11.53…12.48 / 11.74…12.37 V magnitudes are outside that table. The **+12 V single-supply** table requires VSS=GND and cannot certify this bipolar circuit. All numeric uses of those rows below are explicitly conditional sensitivities.

Using 12.5 Ω main resistance, 3.8 kΩ feedback resistance, the existing resistor bounds, 15 nA amplifier bias and a conservative two-terminal total of 80 nA feedback leakage gives:

- Effective drive resistance: **1033.704 Ω**; remote feedback resistance: **8905.539 Ω**.
- Ideal loaded-versus-unloaded change: at most **0.471 mV** over −5/0/+5 V and the stated bias signs.
- Uncalibrated static shift: up to **1.316 mV**. This is distinct from load error; no calibration/offset/finite-gain result is claimed.
- Normal S-to-SFB difference: approximately **0.511 V** at 5 V / 10 kΩ, below the manufacturer's observed less-than-1 V recommendation for optimal performance. Opposing faults can exceed that recommendation; it is not silently treated as a guaranteed operating envelope or an absolute maximum.

Added switch capacitance, feedback-channel resistance, switching skew, amplifier loop stability, overshoot and the original 1 ms settling requirement have not been verified. A scalar DC solution does not establish any of them. No transient model was run because an ideal or typical switch model would not supply the missing device limits.

## Faults, collapse and ground loss

The manufacturer-authored datasheet, **p28 / physical index27, “Power Off Protection,”** states: “A GND reference must always be present to ensure proper operation.” This is a decisive operating premise. It is stronger than merely finding no ground-loss table: the documented power-off behavior requires that reference. It does not prove that every ground-loss case causes damage; it prevents claiming that the IC independently meets that obligation.

Both external fault polarities are retained. The ±60 V source protection narrative applies to **S and SFB**, while D/DFB have rail clamps. The observed grounded-supply drain-leakage maximum is 55 nA at 125°C; floating-supply drain current is **2 µA typical**, and source power-off leakage is **11 µA typical**. All these rows maintain GND=0. Typical leakage cannot bound phantom powering. A two-drain/100 kΩ diagnostic gives about 11.25 mV, but excludes source-to-supply/GND leakage, other powered ports and local-GND loss; it is not a whole-cell or whole-board nonbackpower result.

External ±12 V may fall inside the actual local rails and therefore need not trigger the overvoltage detector. The external resistors remain necessary for contention. With the original resistor low bound and a 24.48 V opposing difference, main current is **25.103 mA** and sense current **5.021 mA**. The existing 25 mA source fault increment is a nominal planning allocation, not a tolerance-complete bound. A conditional main-switch I²R plus quiescent-power screen gives **12.36 mW**, about **2.10°C** on the datasheet's 170°C/W test-board model. These figures do not qualify transient clamp conduction, hot resistance, installed package temperature or amplifier stress.

The observed ±15 V table contains a **220 ns maximum digital off time** at 300 Ω / 35 pF / 10 V, and **1.2 µs maximum negative overvoltage response** at 1 kΩ / 5 pF. The response definition ends when D falls to **90% of the rail**, not at complete isolation. Neither figure is a bound for actual ±12 V collapse, the project's amplifier/load, or the full source/sense release trajectory. Charge injection and channel capacitances are typical values only. The 100 kΩ FF pull-up also differs from the 1 kΩ timing-test condition.

For comparison with the PhotoMOS bottleneck, the calculator assumes hypothetical **complete** release delays. It does not relabel the datasheet endpoints. Under cold +12 V forcing, the original resistor bounds give 12.305 mA per drive and 2.461 mA per precision sense. With an illustrative 0.3 V excursion and an optimistic, not proven reachable 120 µF:

- Sixteen drive/sense pairs permit **152.37 µs** equal complete release at zero detector delay.
- All **82 drives plus 16 senses** permit **34.34 µs**. A hypothetical 10 µs completion needs **34.95 µF**, leaving **24.34 µs** for detection; 50 µs would exceed the assumed reservoir budget.

The 30 reference paths and other backfeed paths remain unquantified. This is a concurrent-fault sensitivity, not a new simultaneous-output-short supply-capacity guarantee. Capacitors separated by the fault cannot be counted as reachable.

## Full population and conditional current ledger

One ADG5401F package supplies both main and feedback contacts for each of the 16 precision outputs. The 66 general outputs need one main-switch package each; the observed manufacturer recommendation ties S/SFB and D/DFB when separate feedback is unused. Their existing local amplifier feedback and external 998 Ω remain. All fault obligations still apply, including six 0…8 V ENV outputs.

Thirty additional one-package reference-receiver placements produce a **112-package budget sensitivity**. This is not an established reference circuit: both source/receiver partial-power states, orientation, precision and any additional endpoint protection remain open. No package count is claimed sufficient to close those obligations.

The budget retains every existing amplifier, all 110 installed input ICs and every previous auxiliary allowance. Each prospective package additionally carries its own two 100 kΩ rail bleeders, 100 kΩ IN pull-down, 100 kΩ FF pull-up and two 100 nF bypasses. The calculation charges the full possible FF pull-up demand, even though the flag is normally deasserted. There is no LED bias. Supply/input-current figures are conditional table values at their stated voltages, not actual ±12 V guarantees; bypass leakage and permit-driver power remain unbounded.

| Packages screened | Startup minimum | Prospective continuous +12/−12/+5 (mA) | Rounded transient (mA) | Positive limiter windows? |
| --- | --- | --- | --- | --- |
| 16 precision | 10 ms | 1700 / 1600 / 300 | 2000 / 1900 / 400 | 100 mA each, conditional |
| 82 outputs | 10 ms | 1800 / 1700 / 300 | 2100 / 2000 / 400 | No: zero analog windows |
| 112 including references | 10 ms | 1800 / 1700 / 300 | 2100 / 2000 / 400 | No: zero analog windows |
| 112 including references | 15 ms proposal | 1800 / 1700 / 300 | 2000 / 1900 / 400 | 100 mA each, conditional |

For 112 packages the screened normal demands are **1576.004 / 1463.187 / 236.767 mA**. The unrounded 10 ms transients are **2049.64 / 1947.66 / 362.4 mA**; they do not exceed the physical maxima, but existing rounding and strict-window requirements reject the zero-window result. The unselected 15 ms proposal gives **1974.76 / 1873.44 / 341.6 mA** before rounding. No startup source requirement changes here. The original 2100/2000/500 mA maxima, 4.6 A return and 40 mV protection-drop limit remain unchanged; prospective 1800/1700 mA delivery would tighten allowed protection-path resistance to 22.22/23.53 mΩ.

The added nominal bypass demand would be **11.2 µF per analog rail** for 112 packages. The existing ramp calculation already uses the entire unchanged 150 µF ceiling, so these parts would have to fit within that allocation; they are not permission to increase it, and their effective/locally reachable capacitance is not established.

## Reviewable next step

Retain the complete primary PDF evidence and establish a genuine ±12 V qualification basis. Then characterize this captured main/feedback/local-feedback cell, including enable, disable, fault, compensation and rail collapse, while preserving the external-side current limiters. Capture the independently observable return/rail/reference permit and the reference endpoint circuits before replication. The integrated topology resolves the discrete persistent sense-bias mechanism under intact ground; it does not resolve its own documented ground-reference dependency or supply-transition guarantees.

Portable tests cover exact identity/pin topology, external limiter placement, POC state, retained local feedback, source-availability sentinels, forbidden promotion of table/typical values, physical sensitivity domains, independent DC KCL, load/static-error separation, both fault polarities, complete output concurrency, the full population and unchanged current ceilings. Native CAD/ERC/PCB, dynamic model and bench qualification remain **NOT RUN**. This study selects no hardware.
