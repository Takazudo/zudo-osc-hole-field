# Decision input: PWR-D3 (supply architecture) and PWR-D5 (degraded-mode policy)

**Draft recommendation for one combined owner decision. Nothing here is adopted.** It
changes no requirement, schematic, PCB, BOM or zudo-pd file. Every number is quoted
from the committed record in this directory ([README.md](README.md), `ledger.json`,
`decomposition.json`) or from
[`decisions/osc-supply-architecture.mdx`](../../../../doc/src/content/docs/decisions/osc-supply-architecture.mdx).
All values are CALCULATED or CONTRACT values, never measured. Prepared 2026-10-31.

## What OSC requires from any supply (unchanged contract)

| Item | +12 V | −12 V | +5 V | Source |
| --- | --- | --- | --- | --- |
| Continuous delivery (minimum) | 1700 mA | 1600 mA | 300 mA | supply-architecture table; README demand states |
| Transient delivery for at least 20 ms (minimum) | 2000 mA | 1900 mA | 400 mA | same |
| Maximum delivered current, limiter tolerance included | 2100 mA | 2000 mA | 500 mA | same |
| Source magnitude band, ripple included | 12.00–12.30 V | 12.00–12.20 V | 5.05–5.10 V | same |
| Magnitude at load | 11.53–12.48 V | 11.74–12.37 V | 4.81–5.20 V | same |
| Load ripple | < 1 mVp-p | < 1 mVp-p | < 1 mVp-p | supply-architecture L67 |
| Rail plus return loss | ≤ 0.20 V | ≤ 0.20 V | ≤ 0.20 V | same |
| Capacitance the source must start | 150 µF +20 % | 150 µF +20 % | 100 µF +20 % | same |

Startup and fault behaviour required on the OSC side or by the source:

- One common monotonic ramp, no faster than 10 ms; no upper bound is set (PWR-C1 is a
  candidate for a slower ramp and is unverified).
- No partial supply. Load-side three-rail monitoring, inhibited input enables while any
  rail is invalid, source reverse blocking and coordinated all-rail shutdown and
  discharge (#59; gap G4). AGND stays connected.
- Accept or refuse only: detect the negotiated contract before enabling any rail; on
  renegotiation, a lower contract, charger removal or brownout, shut all rails down
  together and treat it as a power cycle (PD-003 conditions, L2).
- The interface maximum must be enforced by a device; no current PD candidate does (R7).

Inlet: `OSC-EXT-PWR-8-R1`, at least 5 A per contact with the declared simultaneous
loads, ≥ 30 V, polarized, latched; connector NOT SELECTED.

## Why a decision is needed now

- The current 15 V / 3 A Board B fails the continuous requirement in two independent
  ways (PTC1/PTC3 holds and LDO table rows end at 1.5 A; LDO post-regulation alone
  needs ≥ 45.86 W against a 42–45 W input). U4 limits −12 V to 1.217 A.
- With any architecture, the 20 ms transient needs 48.82–49.82 W at the OSC inlet,
  above 45 W before any loss.
- The OSC planning demand is about 86 % fixed or reserve. A usage notice can remove
  at most about 149 / 149 / 21 mA, one 100 mA rounding step.

## PWR-D3 options (supply architecture)

| Option | What it is | Meets the contract on paper? | Main open items |
| --- | --- | --- | --- |
| D3-A **Revised PD path at 20 V** (Board P plus Board B change) | 20 V PDO, switcher-direct rails with terminal sense or a precision servo to reach the source bands | Continuous: yes at the PD-002 assumed efficiencies (2.60–2.79 A at 18.4–18.67 V). Transient: needs ≥ about 3.38 A at 20 V (about 68 W), 20 V / 5 A with a 5 A e-marked cable the most robust (L4) | TVS2200 vs STUSB4500 28 V abs max: 0.00 / −0.35 V margin (L7, blocking); interface-maximum limiter, reverse blocking, all-rail shutdown (R7); ripple and source bands NOT RUN (L6); efficiency unmeasured |
| D3-B **Keep 15 V / 3 A**, small in-product revision | Same input boundary | No. Continuous needs ≥ 91.4 % (45 W) / 97.9 % (42 W) end-to-end with any architecture; transient > 100 % | Inadmissible as a supply-side choice (R5); only demand closure could change it |
| D3-C **Separate dedicated supply** to `OSC-EXT-PWR-8-R1` | External regulated ±12 V / +5 V source sized to the table above | Only if its guaranteed ratings meet the table; nothing is selected | Source, cable and inlet selection; the same limiter, reverse-blocking, monitoring and ripple gates as D3-A |

**Recommended: D3-A with a 20 V / 5 A contract**, if a USB-C supply stays a product
requirement. It is the only option in the record that meets both delivery rows on
paper. Before adoption, the TVS/STUSB4500 clamp margin (L7) must close. The
interface-maximum limiter, reverse blocking and all-rail shutdown (R7, G3, G4) must be
designed, and the efficiency, ripple and source-band gates (L6, G6, G7) must be
measured. Viable 20 V / 3.5 or 4 A variants depend on efficiency evidence and
STUSB4500 NVM confirmation (L4). **Alternative: D3-C**, if USB-C is not required. It
moves the same gates to the selected source.

## PWR-D5 options (degraded mode)

| Option | What it is | Effect |
| --- | --- | --- |
| D5-1 **No degraded mode; accept or refuse** | Full OSC runs only on a contract that meets the table; otherwise no rail is enabled | Consistent with the OSC fault policy (no partial supply, all-rail shutdown) and PD-003 L2. Needs contract detection before enable (G12) |
| D5-2 Usage-limit re-basing | Re-derive the continuous requirement from the "explicit usage limit" candidate (1386 / 1287 / 203 mA → 1600 / 1500 / 300 mA) | One 100 mA step. Enforced only by the user and undetectable by the supply. Transient is unchanged unless re-derived. An OSC contract change |
| D5-3 Explicit degraded mode | Switchable power domains with their own all-rail sequencing, backfeed protection between sections, and panel indication | New circuits and hosting. Removes about 1.3 to 4.5 modules' worth of planning current, depending on the supply (README PD-003 table) |

**Recommended: D5-1.** OSC demand is mostly fixed quiescent and resistor current in one
EXT domain. A supply-side current limit therefore yields brownout, which the fault
policy forbids. D5-2 and D5-3 change the product or the contract and are not needed
under D3-A or D3-C.

## Combined question for the owner

Adopt **D3-A (20 V / 5 A PD revision) + D5-1 (accept or refuse)**? Alternatively, choose
D3-C + D5-1 if a separate supply is acceptable. Either choice keeps every OSC
requirement and leaves the listed gates open until they are measured. The answer
gates zudo-pd Board P/B renewal work and the OSC #59 protection circuit.
