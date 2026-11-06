# Stage19 X0X single native observation — execution PASS, parity FAIL

On 2026-10-16, fresh independent reviewer/execution owner Codex session `01a14620-af99-7435-90c6-ebcb3b6900e5` completed the approved single opportunity on x0x Ubuntu WSL. No implementation or preparation authorship was inherited or claimed. See [independence assessment](independent-prelaunch-review.md), [owner approval](run/owner-approval.json), [live review](run/live-review.json), and [13-file admission](run/admit.json). The approval is a transcription of the supplied owner's authenticated conversation evidence, not a fabricated signature.

## Immutable bindings and admission

- Source: `91403f4d78b72757187d8cfdbb4d2dc436a3cf72`.
- Verifier: `a57e02f6bfd770e55ebf448bc067e79fc6b08eb5`, pristine separate checkout.
- Request SHA256: `a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1`.
- Original run: `/home/takazudo/osc-stage18-native-001`.
- Container: `d476713a67d278f76f2714d739dd67d6963bdbbe51b1ebb857bf5dd24dade0b5`.
- Nonce: `9c288f95f704df39f8dd46ea704688b433dbe6c8bdc714f18979d5376488bd74`.
- Image: `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`, existing linux/amd64 image; no pull or install.

All 72 generated inputs, 155 verification files and five runtime files were independently revalidated, then rechecked by the host. Shared heavy guard SHA256 `074a463dd6b3a65b7e2168df95b200c0192c414862375bcfb95f979c34c67ee7` remained unchanged, using its shared one-slot default without overrides. Owner approval was issued 2026-10-16T19:10:51Z and expires 2026-10-17T19:10:51Z. Container started 19:18:22Z; live review issued at Unix `1792178372.4133594`, admission published at `1792178388.1210706`, and consumed at `1792178388.4120104`, before 300 seconds. Only one version/export opportunity was consumed; no retry occurred.

Fresh Docker inspection and actual cgroup/mount/network proofs established UID/GID 1000, two CPUs, 4 GiB RAM, zero swap, 128 PIDs, loopback only/network none, read-only root/control/inputs and no writable checked auxiliary paths. Output/config/cache/tmp share a 250 MiB tmpfs. The 600-second independent timeout and total 512 MiB output budget remained intact. [Capability](run/capability.json), [Docker inspection](run/docker-inspect.json), [exact argv](run/docker-argv.json).

## Execution and durable retention

Exactly these commands ran in order, both exiting zero:

```text
kicad-cli version
kicad-cli sch export netlist --format kicadxml -o /output/netlist.xml /inputs/stage18/generated/a01.kicad_sch
```

Version stdout was exactly `10.0.6` after stripping whitespace. Version/export elapsed times were 0.917/2.468 seconds. Supervisor completion was at 82.089 seconds; peak cgroup memory was 562393088 bytes with no OOM events. Shared guard reported `PASS exit=0 secs=229 min_mem_mb=10131`; this includes source preflight before container creation. [Commands](run/retained/commands.json), [resource evidence](run/retained/resource.json), [native assessment](run/assessment.json).

Forty files totaling 687620 bytes were durably retained and independently rechecked on disk for membership, size, SHA256, command order/count, version gate, consumption bindings and quiescence. The supervisor removed only the nonce-bound full container after verified retention. The subsequent Docker name inventory was empty. XML SHA256: `289f7771d87b81dafec5178dc42d1889a9671997c333dc42f51660f047ebc238`. [Retained XML](run/retained/netlist.xml), [retention receipt](run/retention.json), [final stopped inspection](run/docker-final.json). The exact copies, including bounded cache/config files, are retained under `run/`; manifest.json binds every published evidence file.

## Logical parity — FAIL, no omission waiver

After retention, the specified immutable Stage18 comparator ran once and exited 1: `unit slot roster mismatch C7101`. Its unchanged [result](run/xml-parity.json) is FAIL. Execution success does not establish parity acceptance.

A separate [exhaustive source-only diagnostic](run/full-parity-diagnostic.json) checked every reference and all pins/UUIDs against the unchanged comparator expectations. Both expected and observed rosters contain **118 references, 561 pins and 154 unit UUIDs**. No omission waiver was used. Findings:

1. **61 unit-slot mismatches**, with corresponding 61 unit-pin lookup failures: for example C7101 exports unit `A`, while `chr(64 + source_unit)` expects `@` for source unit zero. These are two checks reporting the same unit-label discrepancy, not 122 distinct missing units.
2. **9 property mismatches**: D7101, D7102, U7101, U7104, U7105, U7106, U7107, U7108 and U7109 include `ki_keywords` and `ki_fp_filters` not present in the expected property dictionaries.
3. **3 NC representation mismatches**: U7101 pins 1, 7 and 8 are singleton unconnected nets with `pintype="no_connect"`; the comparator requires an ending of `+no_connect`.

The diagnostic found no additional mismatch categories in the checks it performed, including complete endpoint roster, UUID coverage, values, field candidates, library pin rosters and connected pin/net mapping. It is diagnostic evidence, not a replacement acceptance result. The production comparator and immutable source were not changed. [Diagnostic implementation](diagnose_parity.py) records the exact checks.

## Checks, boundaries and next bounded source work

Independent Stage19 synthetic tests: 34/34 PASS. Complete request reconstruction and hash checks: PASS. Independent post-retention disk/hash/receipt/admission check: PASS. `pnpm circuit:check` was attempted but NOT RUN because pnpm is unavailable; `pnpm check` likewise cannot run without the existing command. Aggregate regeneration was NOT RUN because it invokes native work outside the exact approved opportunity. No dependencies were installed. Evidence publication uses `[skip ci]`; absent CI is not green.

Next bounded source work: use this immutable XML fixture and pinned KiCad 10.0.6 exporter source to establish (a) source unit-zero to XML unit-label semantics, (b) inherited library property emission, and (c) native `no_connect` pin-type versus explicit no-connect marker encoding. Add positive and adversarial regression cases preserving all 118/561/154 checks, and independently review any comparator correction. Do not suppress extra properties, alias units or weaken NC checks merely to make this fixture pass. No new native run is needed for this source investigation; any future native opportunity needs fresh authorization and admission.

Historical RUN002 remains FAIL. Current execution is PASS and current logical parity is FAIL. All CAD remains an unvalidated draft. No electrical/hardware acceptance, architecture adoption, ERC, DRC, routing or simulation claim. The 19 unresolved passive MPNs and unbound DIN/land footprints remain open. Canonical boards, locked placements, decision.json, KEEP_K1402_INCUMBENT and parked PRs remain unchanged. PR286 stays draft and unmerged.
