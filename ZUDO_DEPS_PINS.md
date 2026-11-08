# ZUDO_DEPS_PINS

Provenance for artifacts vendored or generated from first-party (Takazudo/zudolab) upstreams.
Updated by `/dev-bump-zudo-deps` on every sync — keep `pinned:` accurate.

## create-zudo-doc

- repo: zudolab/zudo-doc
- what: doc-site host scaffold, copied with the `doc/` host-glue lines (chrome bindings import,
  islands seed import, `@takazudo/zudo-circuit-doc/styles.css` import) layered on top — see
  `circuit/WORKFLOW.md` and this project's own `zfb.config.ts`/`chrome-bindings.tsx` for what was
  added beyond the scaffold
- files: `doc/pages/docs/[[...slug]].tsx`, `doc/pages/index.tsx`, `doc/tsconfig.json`,
  `doc/src/styles/global.css` (the Wind CSS import chain; the `:root` override slot is empty
  by design), `doc/scripts/check-links.js`
- source: `packages/create-zudo-doc/templates/base/{pages/docs/[[...slug]].tsx,pages/index.tsx,tsconfig.json,src/styles/global.css,scripts/check-links.js}`
  (the pinned `create-zudo-doc@9.1.4` output, generated from published bytes and re-derived by the
  zudo-circuit-doc monorepo's upstream-scaffold parity check; `create-zudo-circuit-doc@0.2.1`
  vendors the same five files)
- track: releases
- pinned: 054c1dabb5810afa24485a5431bce094b14fae21 (create-zudo-doc@9.1.4 npm gitHead)
- updated: 2026-11-08
- sync: run `create-zudo-doc@9.1.4` into a scratch dir and diff its project output against the
  files listed above; `/dev-bump-zudo-deps` performs the upstream-scaffold parity check (#24) the
  same way. Never run an initializer over this repository.
- notes: `doc/scripts/check-links.js` is byte-identical to upstream — it resolves paths from
  `process.cwd()`, so this project's root `check:site` script invokes doc's own `check:links`
  script with pnpm's `--dir doc` flag (cwd becomes `doc/`) rather than pointing `node` at the
  script's path from the project root, to keep the vendored file unmodified.
  `doc/pages/docs/[[...slug]].tsx` carries one added line beyond the upstream docHistory-patched
  stub: `import "../lib/_circuit-doc-islands";` (ADR-016). `doc/src/styles/global.css` has one
  added `@import "@takazudo/zudo-circuit-doc/styles.css";` line after the upstream
  `@takazudo/zudo-doc/features.css` import (ADR-015). Re-apply both after any re-copy.
  The 9.1.4 stub takes `JSX` from `@takazudo/zfb/zudo-react/jsx-runtime` and
  `DocHistoryBoundary as DocHistory` from `@takazudo/zudo-doc/doc-history-area`; the 5.27.0
  preact pragmas, the react-to-preact `tsconfig` path aliases and the Tailwind directives are gone.
  `doc/zfb.config.ts` selects the Classic look explicitly (`themePack: "default"`,
  `themePacks: ["default"]`) because zudo-doc 9 defaults to Graphite.
  Two upstream findings from the 2026-11-08 migration are tracked where they live and worked
  around in `doc/zfb.config.ts`: zudo-wind scanning zudo-doc's asset-viewer bodies
  (Takazudo/zudo-front-builder#4647 → `assetViewerExclude: ["**/*.html"]`) and the
  `zudo-circuit-doc scan` adjacency false positive on long search bodies
  (Takazudo/zudo-circuit-doc#164 → the 5.27 `searchMaxBodyLength: 300` window is kept as this
  site's accepted behaviour).

## zfb family (registry-pinned, not vendored)

- repo: Takazudo/zudo-front-builder
- what: `@takazudo/zfb`, `@takazudo/zfb-runtime`, `@takazudo/zfb-md-wasm` — exact-pinned
  `dependencies` in `doc/package.json` (ADR-003), not a file copy; `/dev-bump-zudo-deps`'s
  registry-dep resolver already tracks these. This entry exists only so a `ZUDO_DEPS_PINS.md`
  sweep surfaces the fallback rule below instead of silently skipping the family.
- files: `doc/package.json`
- source: n/a (registry release, not a vendored file copy)
- track: releases
- pinned: 5.2.2
- updated: 2026-11-08
- sync: bump `doc/package.json` (registry dep edit), not a file sync
- notes: keep the three engine packages aligned, and the published platform binary
  (`@takazudo/zfb-linux-x64-gnu` on CI) must exist for the pinned version — never start a Rust
  build to stand in for a missing binary. zudo-doc and zudo-doc-history-server are exact-pinned
  at 9.1.4 (`create-zudo-doc@9.1.4` scaffold provenance above); the `@takazudo/zudo-circuit-doc`
  runtime `^0.3.0` requires peers `@takazudo/zudo-doc ^9.1.3` and `@takazudo/zfb ^5.2.2`, Node 24
  LTS (`>=24 <25`), pnpm 11.5.2 and TypeScript 5.9.
  Fallback rule (ADR-003, 5.x line) — there is no accepted fallback today: `@takazudo/zudo-circuit-doc`
  0.3.0's peer floor is `^5.2.2`, and 5.2.2 is the first release that satisfies it, so no older zfb
  release can stand in. If the build or island hydration ever fails on zfb 5.2.2, hold the family at
  5.2.2, file the failure with `/dev-upstream-report` (zfb or zudo-circuit-doc, whichever owns the
  cause), and report the site as blocked rather than pinning lower. Revisit this rule once a 5.2.x
  release newer than 5.2.2 exists: from then on the fallback is the previous 5.2.x that the peer
  floor accepts, pinned for all three packages here and in `doc/package.json`. Falling back below
  the peer floor (zfb 2.x / zudo-doc 5.x) means reverting the whole host migration, not a family pin.
