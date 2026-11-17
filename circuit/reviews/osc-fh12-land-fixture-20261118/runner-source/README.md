# Historical FH12 native fixture runner source

These three Python source artifacts preserve the exact source bytes used for successful
run `f0e743f662cb4cf1abbcaade7564987b` on x0x WSL on 2026-11-18.
`sha256.json` maps each original filename to its archived filename and SHA-256.
The `.py.txt` suffix prevents normal Python test discovery or direct tool entry
point discovery; the source bytes themselves are unchanged. They were copied from that run's retained
`runner-source` directory and checked byte-for-byte against its SHA-256 record.
No source edits, native execution or test reruns were performed for this archive.

This is historical review evidence, **not a portable production runner** and
not an automatic re-execution entry point. Do not invoke the archived scripts
as a repository check or import the archived test file for test discovery.

The original runner binds `ROOT` to
`/tmp/osc-mc02-height-audit-20261117` and the container helper to
`/tmp/osc-fh12-native-container-20261117.py`. The tests likewise import the
original temporary runner. The archived code deliberately retains these paths
and the exact source commit `467d6e4e6c6ed84a6121747b93271341db5dc707`.
Its external dependencies include the source tree and retained manufacturer
PDF, the canonical machine-wide heavy guard, systemd user services, Docker,
and the cached digest-pinned KiCad image. These dependencies are not bundled.
Any future execution requires a fresh review of the actual environment,
source closure, shared lock, effective limits and cleanup admission.

The successful run covered only the unadopted FH12 land fixture's 32
variant/face/rotation cases with KiCad CLI and pcbnew 10.0.6. It does not
establish project connector registration, a complete physical body envelope,
or hardware acceptance. DRC, zone fill, formal adoption and manufacturing
remain on hold. Raw manufacturer PDFs, generated boards and bulk logs remain
in the ignored local cache; this archive does not publish them.

The archived runner budgets host services and Docker workloads separately.
This does not prove that Docker and WSL use distinct underlying virtual
machines; no topology claim is inferred from a Docker daemon name.
