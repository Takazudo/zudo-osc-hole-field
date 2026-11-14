# Decision log: campaign osc-stack-20261114

Decisions taken inside the campaign, newest last. A row is a design or operating choice, never a validation result. Each row says how to reverse it. Owner decisions are copied here for reference; their authority is the owner's own message.

| ID | Date (UTC) | Decision | Decided by | Basis | Reverse by |
| --- | --- | --- | --- | --- | --- |
| DS-01 | 2026-11-14 | Board-to-board joints replace cable-only connections; cables stay only where board heights justify them | Owner | Project thread root message of 2026-11-14 | Owner message |
| DS-02 | 2026-11-14 | OSC2 and OSC4 lose their octave selectors; a SUB toggle (PUL normal, −1 octave, −2 octaves) takes each freed position | Owner | Decision card `cmsg_01Pv35emdXEU6gCRF3teSpo2BxKqjv97b5t2fmmH1R9aPY` | Owner message |
| DS-03 | 2026-11-14 | The stack work continues autonomously; difficult architectural decisions go to a Fable design agent at high effort, which decides | Owner | Project chat messages `cmsg_01Pv35emdXEU6gCRF3teSpo2W8nEGNoKNudGgdpt3nExqX` and `cmsg_01Pv35emdXEU6gCRF3teSpo2CKWZL4oD7iZ7K23pvXBhri` | Owner message |
| DS-04 | 2026-11-14 | Plan page #352 merged to `main` as a PROPOSAL; adoption of the stack stays at Gate A | Manager | DS-03; CI 7 of 7 on the merged head | Revert commit on `main` |
| DS-05 | 2026-11-14 | This campaign runs with one manager, in-session children in isolated worktrees, at most 3 at a time, and three batched review packets | Manager | ORCHESTRATION.md sections 1 to 4; VM capacity in [plan.md](plan.md) | Campaign revision |
| DS-06 | 2026-11-14 | K interface routing is held until Gate A: no "signal-escapes" stage and no transaction ending on a GH pad, an F.Cu trimmer or a power-land neighbourhood | Manager | The plan's routed-drafts section: these are the copper features the stack replaces | Campaign revision; lifted or confirmed at Gate A |
| DS-07 | 2026-11-14 | Wave 1 admits ST-01, ST-02 and ST-03 (parametric start); ST-05, ST-06 and ST-07 follow as slots free; ST-04 follows ST-01 and ST-03 | Manager | Critical path to Gate A is ST-01, ST-03, ST-04 | Campaign revision |

## Open decisions and their owner

| Plan question | Decided by | State |
| --- | --- | --- |
| Q1 adopt the direct stack (Gate A) | Design authority | Waits for ST-01, ST-03, ST-04 |
| Q3 connectors from outside the usual factory stock | Design authority for the design choice; any purchase stays with the owner | Waits for ST-01 |
| Q4 depth target, about 34 mm or about 31.5 mm | Design authority | Waits for ST-01 |
| Q5 EL fallback if the rigid joint fails | Design authority | Waits for ST-02, ST-03 |
| Q6 supply location and cable exit side | Design authority, as far as the stack needs it; the inlet itself stays under #57 | Waits for ST-03, ST-05 |
| Q7 build a connector coupon | **Owner only**: it is a fabrication order | Definition only (ST-03) |
| Q8 rear service with all trimmers on K's rear | Design authority | Waits for ST-03, ST-07 |
