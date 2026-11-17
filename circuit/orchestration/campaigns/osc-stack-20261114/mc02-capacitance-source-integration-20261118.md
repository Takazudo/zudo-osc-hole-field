# Canonical capacitance evidence and local documentation verification

2026-11-18 JST, Codex coordinator on x0x WSL. This follows the completed isolated
[native land fixture](mc02-fh12-native-result-20261118.md). It does not repeat that
native run or promote component evidence into circuit/assembly acceptance.

## Evidence and source-bound contracts

Canonical commit `2f3f7c8999f3dccecfe41597f23739483272afad` adds three narrowly
conditioned input-capacitance facts for exact HC00/HC74/HC221 owners and refines
the existing HC14 fact without duplication. HC00/HC74 rows preserve2–6V and
-40..85°C conditions; HC14 preserves its explicit5V condition. HC221 preserves
the continued HC table context and dashed VCC/test-condition cells instead of
inventing a numerical test voltage. Source PDFs and identities are unchanged.
All electrical coverage OPEN states and blocker IDs remain unchanged. Published
facts increase791→794; generated pages pass consistency checks.

The42-contact E5 clock contract retains CLOCK_RC3,CLOCK19,READY20 contacts,
nominal47k/1nF with blank exact RC MPNs, and distinct driver/resistor/receiver
roles. The conditional catalog-maxima arithmetic is CLOCK170pF for17HC74 inputs,
READY190pF for15HC74+3HC00+1HC221 receivers. These are not actual total, receiver
or lower-bound project loads; driver/route/feedback/parasitic and application
conditions remain unestablished. Physical frequency, edge and timing bounds stay
null. The1nF CLOCK_RC capacitor is behind the47k resistor, not a direct CLOCK
lumped load. No aggregate capacitance was published as a guaranteed owner fact.

Contract rebind `b15e03b2ef993fd4611d38c4d492ea209de3efe6` preserves prior source
history and engineering2c53715.19clock and15logic fixtures pass independent
review. Canonical fact IDs/values/conditions/locators and OPEN coverage are
checked explicitly; drift or removed blockers fail closed.

Updated logic attempt7908f9b9e8494e748d1b971ba1d34524 completed1.27s,exit0,cleanup
VERIFIED under1CPU/512MiB/swap0/128PIDs/30s service/60s outer bound. All128×4
outputs,12gate graph,7boundary inputs,45external contacts and physical timing
nulls match the prior retained result; only provenance and conditioned owner
observations change. Result SHA-256
`d75fb491a23ba2ff5b065c079733895ceffac3f8b2413d94d5db5f623ac30b44`.
Actual clock receipt863989c4d05e4190983a82486879a912 SHA-256
`c129cfe0c512762070b087df59045451c2f467ad0cb98febb50f2383da68baf6`
binds the canonical facts without a native or truth-table rerun.

## Documentation verification at exact b15e03b2

Local commands were inspected for scope: check, build and check:site, with no
KiCad generation, deployment or credential operation. Execution was serialized
by the canonical shared heavy guard,1CPU/4GiB/swap0/256PIDs,480s service and600s
outer bound. The HEAD and nonignored source state remained frozen and clean.

1. First transaction fff5c9af32d8446d9e5dbce483f96e9a passed check/type/model/
   generation consistency, then reached470s guard limit during build.
   ENV_SUSPECT/exit124,cleanup VERIFIED; no source assertion failure established.
   Archive index `2ceb1c504a277085800de337707aa999b8d8eb21eaaa737c0be42c5dcb1518d0`.
2. The single policy-required ENV retry3e590380939d40b0a9bef395b59c8ba2 passed
   check and built335pages in55.47s. Host/assets/check-built also passed, then
   supervisor received signal15 during the remaining site chain. Signal origin
   is UNKNOWN. Original supervisor UNCERTAIN is retained; cleanup-details and
   separate live reconciliation verify inactive/empty owned workload and free
   shared slot. Do not rewrite this into an uninterrupted transaction PASS.
   Archive index `491e2d7ff018686a258158cc1ce7928e43666c9d19ac94f7eb3c7bed49f185ef`.
3. A separately reviewed check:site-only continuation
   a9171d37f02146eca7ef977d99bd4141 passed22.262s,exit0,cleanup VERIFIED. It binds
   exactly the same b15e03b2 source and all463existing dist files, before/after
   manifest SHA-256 `529067eac84a40d61881744c1f70c4bed951ff2b2a794e37e4179bcbe8a3c1f8`.
   No third build was run. Complete host/assets/check-built/public-artifact scan
   and strict link checks passed. The scanner examined38,688internal links and
   5,129IDs; one unchanged pre-existing allowlist exception for `${esc(x.url)}`
   remains, not zero raw scanner findings. Archive index
   `17a8d5e1b1379fe50b4bec45b5399831934d7b841eb161a8ba6cbfc1bae611be`.

Independent review confirms combined check/build/site completion against the
same frozen source/output, while preserving both earlier failure/interruption
records. No deferred-build issue is needed now. No CI was dispatched and none
of these results releases DRC/fill/adoption/manufacturing or main integration.

## Next input boundary

The provided18November artifact folder exists but was empty through the bounded
Dropbox and WSL delivery check. No PDF byte identity or duplicate claim is made
for that handoff yet. Continue with the [specific source requests](mc02-next-source-inputs-20261118.md)
on actual arrival; do not repeat completed verification or substitute generic
cable drawings for exact configurations. This is an external-delivery dependency,
not completion of the hardware project.
