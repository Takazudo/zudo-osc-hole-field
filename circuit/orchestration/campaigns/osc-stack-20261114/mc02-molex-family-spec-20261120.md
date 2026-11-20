# Claude Project resumption and Molex family-specification contract

2026-11-20 JST. Claude Code Cloud, Claude Project thread "Resume OSC instrument
order-readiness campaign" (project lead), branch `claude/project-thread-iw3gai`.

## Baseline confirmed unchanged

| Item | Observed |
| --- | --- |
| `main` | `690366aa69450b642f7daee2cb809eb5ded38d63` |
| Candidate `wsl/mc02-height-audit-20261117` | `6e517886e28a14de73891f117a1d32e73e0a559f`, 93 ahead / 0 behind main |
| `wsl/osc-mc03-c6-access-20261117` | ancestor of the candidate |
| This branch | starts at the candidate head; non-main pushes trigger no workflow |
| Toolchain (repo pins) | Node 24.22.3 (`>=24 <25`), pnpm 11.5.2; KiCad 10.0.6 via `scripts/kicad/run.sh` |
| Cloud KiCad oracle | NOT RUN here; the earlier Cloud image pull failed and is not repeated |
| `pnpm circuit:check` | PASS before and after this change (84 lines, 445 placements unverified) |

## Ownership replaces the Moya/Codex mapping

The owner's 2026-11-20 instruction makes the Claude Project lead (this thread) the
overall manager, queue owner, independent-review owner and final readiness assessor.
Native CAD phases go to Claude Code CLI on WSL on the owner's Windows machine as one
complete phase handoff; while WSL owns a phase, Project-side writes to its paths freeze.
GitHub issues, branches and exact commits are the communication boundary. No Moya or
Codex session is required. The single active writer is this thread until a WSL phase
is handed off.

## Sources retained in the private store

`Takazudo/circuit-dev-resources` branch `claude/project-thread-iw3gai` at
`d9440ccf7fa6b17e1258e35efd6507c57a47d6c8` now holds the cable sources that were only
in the WSL cache, so Cloud sessions can verify them:

| Store path | SHA-256 |
| --- | --- |
| `molex/150200075/15020-series-product-specification-ps-15020-001-rev-f.pdf` | `eb952ac2a7353fdb257be5c336288a7cfe9e9f6f2e83c2b64869248e6d046e4b` |
| `molex/150200075/150200075-sales-drawing-sd-15020-001-rev-f-owner-download.pdf` | `4c311098a1a05e163fc33c19d2c35f01a51ad18b0ff14edb32429e347bef2419` |
| `molex/150200075/150200075-sales-drawing-sd-15020-001-rev-f-web-2026-11-20.pdf` | `2826830f786eb0383f2575d2932f5607d33ff58bb9c773e8cd4c1aecbf71cda3` |
| `lx/ffc-0.5mm-same-side/lx-ffc-0.5mm-same-side-generic-drawing-a1-2023-04-12-lcsc-mirror.pdf` | `1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8` |

The two delivered PDFs were re-read from the owner's Dropbox folder and match the
retained hashes. The current molex.com drawing has the same size and text as the owner
download; only the pdftk stamp dates differ.

## Contract result

Implementation: `scripts/checks/mc02_molex_family_spec/` (see its README). Two independent
review rounds requested twelve corrections; all were applied (sheet scope, current
wording, 49 mm threshold, grid convergence, open boundary, eps range, input hashing).

| Item | Result |
| --- | --- |
| Scope | PS-15020-001 Rev F applies to 150200075; SD sheet 1 binds N8 / 51 ± 2 / type A. SD sheet 2 is odd-count only, so N8 width, span, conductor and layer data come from the PS. |
| Reinforcement length | Unresolved conflict, PS 6 ± 1 vs SD 6 ± 2, no stated precedence. Checks use 4–8 mm; FH12 4.5 mm support recommendation stays open. |
| Current | Molex 0.55 A rating (all loaded, ≤ 40 °C rise at 23 °C) vs 0.5 A listing; the lower is used. FH12 0.35 A governs. Allocation unchanged. |
| Ground share | **OPEN.** Source maximum 36.5 mΩ / 50 mm, no minimum. The legacy 65.3 mΩ minimum does not apply, so the retained PASS does not transfer. Requirement: ≥ 8.70 mΩ / 50 mm at the coldest applicable temperature (49 mm length, 0.35 A). Nominal copper at 20 °C gives 26.1 mΩ. |
| Capacitance / coupling | **OPEN, narrowed.** 62 pF/m has no fixture definition. A converged finite-thickness cross-section (grid ladder, open boundary, discretisation allowance) keeps all 26 evaluated links below 1.0 up to eps 4.7 when cable and harness share eps. With the harness at its retained 3.2, one link exceeds 1.0 above cable eps about 3.8. 62 pF/m implies eps about 3.3 (pair, others grounded) or about 4.4 (pair, others floating). The eps-scaling proxy is kept as a rejected method. |
| Remaining unknowns | minimum resistance or copper tolerance; capacitance fixture or a measured value; dielectric constant; end-region coupling; reinforcement precedence and thickness tolerance; FH12 positional/datum conformity; assembled contact resistance. |

Gate A check 1 (interface identity/applicability) therefore stays **incomplete**, now
narrowed to the items above. No BOM change, qualification, DRC, zone fill, adoption or
manufacturing step was taken.

## Prepared technical questions (not sent)

For a future Molex inquiry, when the owner authorises one:
1. Minimum conductor resistance, or copper thickness tolerance, for 150200075.
2. Fixture and conductor configuration for the 62 pF/m and 130 Ω figures, or the
   insulation's dielectric constant at 1 kHz to 10 MHz.
3. Which reinforcement-length tolerance governs 150200075: PS 6 ± 1 or SD 6 ± 2.
4. Reinforcement (stiffener) thickness tolerance.

## Next operation

Task C (cumulative placement and manual latch access) in the Project source lane,
consuming the frozen interface inputs above. Native work, when admitted, goes to WSL as
one phase brief.
