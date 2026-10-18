# Current appearance editor verification

Panel baseline: `94daec5bbdbb007b40f2b5840534b4083ddece0f`. Remote before this work: `d8e21ba3d41ed3c87c45dedadb4f86dcbfe5ac89`. Connector research was retained separately at local checkpoint `381f63b6` on owner priority change, explicitly unadopted and not final-reviewed. This editor changes no hardware.

## Author checks

- `node project/osc-hole-field/workbench/current-editor/build.cjs --check`: PASS deterministic self-contained HTML. Build checks 438 locked features, 318×298 frame, fixed17/14 pitch and renderer/lock UID/kind/XY correspondence for ports/controls.
- `python3 scripts/panel/audit_current.py --check`: PASS all438 UID/reference/feature rows and historical electrical overrides.
- `node scripts/panel/render_current.cjs --check`: PASS unchanged audited SVG/HTML; SVG hash `36e8dc61022ae848ed3851ef764b40dca0570c02051343f85f906280cb90ef09`.
- `node scripts/panel/test_current_art.cjs`: PASS shared profile, five Ø7 OCT fills and native-convertible art preservation.
- `python3 -m unittest scripts.panel.test_current_audit`, repeated with `python3 -O`: five tests PASS each.
- Browser command (installed Chromium/Playwright, no installations):

```bash
HEAVY_GUARD_DIR=/workspace/shared/.agent-guard/heavy \
bash /workspace/codex-settings/.portable-profile-home/.codex/scripts/heavy-guard.sh \
--label current-panel-editor-browser -- \
python3 project/osc-hole-field/workbench/current-editor/test_browser.py
```

Five tests PASS, guard `verdict=PASS exit=0 secs=5 min_mem_mb=16522`. Covers1440×1000 desktop, all438 centres/dimensions/IDs, item-circle invariance under appearance changes, reset, malformed/geometry import rejection without mutation, actual UI settings download/upload roundtrip, deterministic SVG/embedded settings, detail/keyboard pan/zoom, PNG dimensions and byte equality to independently rasterized exported SVG in the same browser. Zero JS errors or external requests. Local blob URLs are used for downloads/rasterization. PNG consistency is browser/font-scoped, not cross-platform.

The test loads the entire bundled HTML into an isolated browser document without a web server. It verifies self-containment; actual `file:` navigation is not claimed on this host because its browser policy blocks that scheme. The standalone artifact uses no runtime fetch/import, so downloading and opening the HTML is the intended desktop delivery. Screenshots show the actual full/detail UI; they are observations, not deterministic golden acceptance images.

## First failures preserved

First browser run: geometry, save/load and exports passed; malformed `__proto__` test and “zero requests” assertion failed. The Playwright object transport dropped the prototype-named field before the application saw it. Changed the test to pass JSON text through `JSON.parse`, matching actual file import, retaining the rejection assertion. Added a plain-object validator too. The request assertion had counted local blob rasterization as external traffic; now excludes only `blob:` and continues rejecting all other requests. Second run still used the old object transport and retained that failure; the corrected JSON-text run passed. No geometry threshold or assertion weakened.

Reviewer suggested explicit null rejection and revision-binding LED parameters; both implemented before final verification. Geometry revision now hashes lock+panel parameters, not lock alone. No historical settings migration that can import geometry is provided.

Native KiCad regeneration/ERC/DRC, manufacturing exports, physical checks, energization, deployment and procurement NOT RUN. Current installed native version remains incompatible as recorded by the panel audit; no install or workaround. Full historical stage replay unnecessary because stage source bytes remain unchanged. This workbench-only bundle is not a site publication change; no site deployment or new site-build pass claimed.

Final repository checks and independent review appended after completion below.

## Final checks and independent review

`COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` and `pnpm check` PASS: manual68-line inventory (no schematic/placement binding), generated pages/preflight,31models/previews and TypeScript. Optimized browser command uses `python3 -O` through the same guard: five tests PASS, `verdict=PASS exit=0 secs=6 min_mem_mb=16469`.

Fresh-context reviewer `stage36_review`: **PASS_SOURCE_REVIEW_ONLY** after final substantive changes. Independently ran deterministic build and guarded five-test browser suite (`PASS exit0 secs6 min_mem_mb16527`), with temporary screenshot destinations. Both independent screenshots matched the supplied files byte-for-byte and were visually inspected. Receipt separately reviewed PASS, pre-append SHA256 `19bc8dff5e448fc5a75b83f9e4af3513ecbe0297dfdc75a8d4af0282262fe28b`. This final append records results only.

Reviewed source SHA256:

```text
README.md         942962d04e381928e28ffa55ce0986cb490cbf23b3fe12efd8501f4eb9cd89aa
build.cjs         e632a7b6b17a22ffae883aa1712173c0e2ca0a1aba94608eb1c39fd70eb5c7f1
editor.js         b9762e991ca1463362b2de802d4a209b0c2ecad19f0c3a91c6c6b1f1659099a0
index.html        a446a25e1fb98520be3b7201a6b447296466fb49c84e71772af711ab1d4c56ff
shell.html        cff1dd230607640a56c5d4f8ff148b90b8f938f1b318d080a28eddbceea0d8d6
style.css         ccf0b41e344612de4ecee44f52560287b781ac1ff1bb3673bf46df54470ffdb0
test_browser.py   4b6a36989b0dd9d79f07223111ae34ae132bc6083d7f55600639c2078531644b
editor-full.png   dd4043798e3aa5f25991f28a5803d518e8b0e612a77880b0cef8ae310d4f4e79
editor-detail.png 9f23233058e51ae1f6ed8299452f0a64d0fce2d87aa81e629312d6baa7ad2e13
```

Existing parent286 remains `b58068fbaeb65886958a67a4f4978613414e31c5`. Canonical boards/circuit/BOM/geometry, historical stages, coupon, both Stage36 viewers and the original historical workbench index remain unchanged. No CI pass claimed; commit skips native CI.
