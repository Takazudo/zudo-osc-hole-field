# E5 source verification and room-study evidence

2026-11-17, Codex coordinator on x0x WSL. This is candidate evidence, not
hardware adoption, routing acceptance or a release of DRC/fill/manufacturing.

## Boolean and conditioned timing evidence

The E5 source contract covers12NAND gates,7inputs and128assignments, asserting
four outputs rather than relying on the earlier partially fixed-input test.
All128×4 outputs match. The45external contacts remain separately enumerated;
logical function does not establish physical delay, skew or routing budgets.

Four narrowly conditioned facts were added from retained TI sources at
109c8914d54c918f71a665f8af49e0b635f9133f:

- SN74HC00,SCLS181H,August2021, source SHA-256
  `aacc4e5e60c10be7412b635c327d42413c4f68a58bf381467fec1e54bff24af0`:
  propagation maximum23ns and output transition maximum19ns at4.5V,-40..85°C.
  No numeric load is asserted from its switching table;50pF application guidance
  is not promoted to that table's guaranteed test condition.
- SN74HC74,SCLS094F,June2021, source SHA-256
  `d1e57133ca40b595c670688718807c367b555b6fe57144c881d629de18230351`:
  D setup25ns worst required and D hold0ns minimum at4.5V,-40..85°C,
  with50pF measurement load. Measurement input transition<6ns is distinct from
  the500ns recommended input transition limit.

No minimum propagation/CLK-Q, actual5V/load/skew or cascade proof is inferred.
Exact DR package identities remain source-bound. Electrical coverage stays OPEN.
The metadata-bound contract e93f7ae17b7ca27833fa6e537dcc4d3f854ebd6a ran once as
9d3a253eba4a446aaff4303d172ff3cc:1.135s,exit0,cleanup VERIFIED, all128×4 unchanged.
Result SHA-256 `2c8763ada0aa2eec6252c86fb0e0e74a818286453fc1c8d1c86180bcce8243e5`.
Ignored coordinator archive index SHA-256
`f7f7de94bd5ef8b5096cb460c0ea510c8c4441e2a449b2195c7124aa53158e8b`.

Local `pnpm check`, `pnpm build`, `pnpm check:site` passed on exact109c8914 under
shared guard,1CPU/4GiB/swap0/256PIDs/480s service cap. Attempt
e05e20bc0d6c445d8c1e23f5ffad9865 took77.658s; cleanup VERIFIED.335pages built.
The existing workbench template-link scanner finding is covered by one existing
allowlist exception, not silently counted as zero raw findings. No deployment.
Archive index `be27f6bf87fa44811b62fc225d3ee29f41ce3be5b05349f68f5b2c70a84b10a1`.

## Blocker attribution and bounded next experiment

Implementation778f518ee9beba94069b1085e9c488e9af20254b inspected7,203diagnostic
points for U4524/U4526/U4527 against all681blockers. Attempt
f9f21bf97ad346268762cd7a7be3c00e took6.165s,exit0,cleanup VERIFIED. There are no
clear points. One U4527 point, index214 at(+1.591,-1.591), has accepted-body-only
blockers U4517 and R4577. Fixed-panel hits are1,587/1,605/1,506 respectively.
Result SHA-256 `a932d3693b9b64e1527599ac111889082dde113ad164cebe717c24b31785ca46`.
Archive index `7a95a9ed7f42dd8b1df2ca2434374860e2820d4496f3b706095fbcc7650b5cf6`.

The historical search already removed all replacement bodies before rebuilding
its accepted prefix. A three-unresolved-IC-only removal repeats that freedom.
U4517 at replacement row85 precedes U4527 row89; moving it offers a new degree
of freedom. R4577 row377 is a final-scene blocker, not the historical cause.
R4577 is a1kohm FALL_BASE_LIMIT analog boundary with blank MPN, not a selected
exact resistor or an incidental logic part. Full function/interface evidence is
retained, including all four U4517 gates, analog anchors and fixed decouplers.

The reviewed next pilot fixes U4527 at point214 and moves only U4517/R4577,
B face and existing orientations, at most2,401offsets each, both current-center
and original-center displacement<=25mm. At most100,000lexicographic pair checks;
cap is distinct from full-domain no-fit. All three models receive final mutual
and fixed-scene validation. All other geometry is frozen. Any witness is only
room feasibility, not timing/analog/decoupling/route acceptance.

Implementation a4a06f884bfe949dcad7764f0794bca33c56f532 passed independent review
and17fixtures. First actual attempt d048ec38abc24487826071192808251f stopped
before enumeration: frozen C4534 source assertion mismatch,3.17s,exit1,cleanup
VERIFIED. Independent source diagnosis confirms angle representation, not coordinate
roundoff: raw PCB/extractor retains C4534=-90°, while spec used equivalent270°.
Correct the strict expected value to-90 without loosening checks. Preserve this
failure; review the source-bound regression before one corrected attempt.
Actual exchange result: NOT OBTAINED at this checkpoint. Source-only envelope
work continues independently.
