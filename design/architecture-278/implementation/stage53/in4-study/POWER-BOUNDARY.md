# Existing power-budget pointers; no power redesign

Parent is auditing zudo-pd capacity separately. Stage53 changes no supply assumption
and no power copper or protection definition. Preserving +12V topology is not a
current-capacity, voltage-drop or thermal qualification.

Current whole-instrument authority is `design/power/rail-ledger.json`,
`design/power/rail-budget.json`, `design/power/supply-architecture.json` and its
`-input.json`, summarized by
`doc/src/content/docs/architecture/osc-power.mdx`. The current conditional EXT
planning loads are 1534.819/1435.569/224.286 mA on +12/−12/+5V; minimum continuous
requirements 1700/1600/300 mA and 20 ms transient requirements 2000/1900/400 mA.
These are planning requirements, not measured supply capacity or guaranteed
whole-instrument maxima. Source, inlet and mate remain unselected; protection #59
and physical source #57 gates remain open. Raw/load boundary XB301 is requirement-only
and unimplemented (`design/reports/power-boundary.json`).

The historical pinned zudo-pd P+B target is 1200/800/500 mA, not a measured rating;
its 80% design ceilings 960/640/400 mA are superseded as the selected contract.
Do not treat the larger EXT requirement as a demonstrated zudo-pd capability.
The historical startup analysis also flags about 4.5 A for 2 ms against a 3 A source,
and the 15V-only programming/readback gate is unresolved. Parent should compare
any proposed supply increase against complete source, cable/contact, return-path,
startup, fault, thermal and voltage-drop evidence; this stage makes no choice.

For A01 harness-specific conditional terms, Stage34 `ledger.json` and
`design-input.json` correct Stage33's wrong X1 basis. They are not the complete
OSC current budget; wire/contact/fault-current and repeated-flex evidence remain
unresolved. Prior native connected-power-path checks establish membership only,
not ampacity. No supply redesign or energisation performed here.
