# Isolated FH12 native land fixture result

2026-11-17 UTC / 2026-11-18 JST. Coordinator: Codex on x0x WSL. The admitted
[isolated fixture contract](mc02-fh12-native-plan-20261117.md) and DS-141 remain
limited to incomplete, unadopted land patterns. No canonical board was mounted
or changed. This is not aggregate, DRC, fill or hardware acceptance.

## Actual successful result

Implementation `467d6e4e6c6ed84a6121747b93271341db5dc707`.
Attempt `f0e743f662cb4cf1abbcaade7564987b` completed32distinct cases:
8/14/26/40contacts × F/B ×0/90/180/270degrees. Native load, pre-save semantic
checks, save and reload checks all passed;32disposable fixture boards retained.
CLI and pcbnew both reported10.0.6 in the exact pinned image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.
No image pull, host pcbnew or ngspice substitution.

- Status `NATIVE_LAND_FIXTURE_ONLY`; guardian PASS,command exit0.
- Guardian16.598seconds; complete guardian service22.902seconds.
- Cleanup VERIFIED,errors[]; guardian/controller/worker inactive with empty
  cgroups, exact owned container absent.
- Result SHA-256
  `de95f45875bd862f4f8a608dca700fd879051d41cd5f826c83870898b95093df`.
- Full ignored run archive index SHA-256
  `f9ea1381b48dac65d5411f55e571386438d0e8fdc92685fd59f66ae349adec92`.
- Runner SHA-256
  `a989a21e2f38c79678401cbd0cc64cbd47b963863eba9c36068546c2043a8d4d`;
  container helper
  `f3a9cdf5c927d643e310b24edffd7117bbb1dcb373d0960f2d8e22e1eb23e8c5`.
  Exact runner/helper/tests are retained with the run.

Independent review confirmed staged and output hashes, committed source identity,
case coverage, actual caps/configuration, non-OOM exit and cleanup.13fixture
unit tests and34runner lifecycle tests passed before this corrected attempt.
Native log retains372duplicate image-handler debug messages; there are no
Error/Warning/Traceback lines. The earlier read-only user-data warning is absent
with supported XDG_DATA_HOME inside the existing bounded /tmp; HOME and root
read-only protection were unchanged.

## What was checked and what remains unknown

The native checker uses its own literal EDC A/F/G table, independently of the
generator's pad calculation. It checks contact numbers, integer positions/sizes,
rectangle orientation, exact copper layer sets, unconnected nets, incomplete
metadata and absence of invented graphics/models before and after serialization.
Both unnumbered mounting lands survive. Source nominal copper0.3mm width is not
replaced by the separate0.25mm stencil width.

All artifacts remain `INCOMPLETE_NOT_FOR_LAYOUT; NO_ADOPTION`. Physical project
registration is null and endpoint bindings are empty. Body/courtyard/3D,
installed height/access, mask/paste design, cable compatibility, timing/routing,
DRC, zone fill and formal hardware adoption were NOT validated. No fabrication,
ordering, global library registration or main/CI acceptance occurred. The older
successful aggregate remains bound tofb0ed106 and was not rerun.

## Runtime evidence and retained failures

Effective workload limits were inspected independently in each group:
guardian0.02CPU/128MiB/16PIDs, controller0.03CPU/64MiB/8PIDs,
worker0.20CPU/320MiB/40PIDs, Docker0.75CPU/2GiB/128PIDs; swap0 throughout.
The combined ceiling is1CPU/2.5GiB/192PIDs. Actual host runtime/termination
properties and container230s+10s deadline were checked, with600s outer bound.
Initial/terminal systemd control-plane clients are disclosed separately;
underlying VM topology or daemon baseline is not claimed to be capped.
Only a small read-only staged source closure was bound, with32MiB /tmp and64MiB
output tmpfs. Bounded exec-export verifies count, sizes, paths/types, hashes,
end marker and EOF before evidence is accepted.

Actual identity/controller-loss preflight
`facca1c8df9c451fac703cb551f1f8ab` completed
`EXPECTED_CONTROLLER_FAILURE_CLEANUP_VERIFIED`,17.300s guardian/23.012s service.
The exact controller terminated by signal9. Canonical shared-lock device2096,
inode802706 remained held by the same guard before loss, after loss and after
cleanup; independent nonblocking acquisition became possible only after guardian
exit. All three units and the owned container were independently checked absent.
Archive index `83366cbde8e0eb5a9f968dc6b8f275c9030d2c38030a0122817b1618217e32e9`.
This preflight is lifecycle evidence, not a native semantic pass.

Two earlier identity probes e06553d4/60c2e064 were incomplete because Docker cp
cannot retrieve tmpfs as required; the first did not retain its internal output
and the second retained an empty archive view. Neither proves a KiCad failure.
The documented supported exec-export correction was independently tested before
a new probe. Their full receipts/source archives remain, with index hashes
`577b290e1508073319a85dffbc16b51e34e64c1edd5d8028582a36acdb3ddc79` and
`af7c2886df960d1cc2fcede395c38ce0d2f9d1832ff0e055ebb3e4e5b3d64aa1`.

The first actual fixture00165c1f failed at the unsupported GetDescription API,
not at a geometric comparison. Its complete failure evidence and verified
cleanup remain under archive index
`61ad975aee4e8d28bf1861106c5280cdd45b35abea26df80c75b9d8209587a04`.
Official10.0.6 source supported the strict GetLibDescription correction; expected
metadata and dimensions were not relaxed. No unchanged failure was retried.

## Next dependencies

Continue from the [specific source input list](mc02-next-source-inputs-20261118.md)
and the active queue audit. Exact selected cable configuration data and physical
registration/assembly evidence remain separate obligations. Do not turn this
serialization result into placement adoption or rerun it without changed inputs.
