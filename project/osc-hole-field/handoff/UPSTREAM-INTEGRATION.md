# Official runtime integration

Reviewed source: https://github.com/Takazudo/zudo-circuit-doc/tree/5d0e2b630776489d394be341586b889dfe0d1cb8. Read `packages/create-zudo-circuit-doc/README.md` and the generated template's `circuit/WORKFLOW.md`. The repository README still labels development status; do not infer registry publication from a package.json version.

The wrapper invokes the published CLI at explicit version 0.1.0 when available. It uses `--no-git --no-install --agent both --yes` and an explicit empty destination. Node >=22.18.0 is checked before executing; dependency installation remains a separate local step. No existing project is adopted by force.

For an existing local checkout, build through the repo's documented `corepack pnpm install` and `pnpm build`. Packaging commands should follow `dev-docs/publishing.md` in that checked revision. Do not edit its fixture corpus. After obtaining the runtime tarball, run:

```sh
python3 bootstrap_project.py /absolute/new/project \
  --initializer-script /absolute/zudo-circuit-doc/packages/create-zudo-circuit-doc/bin/create-zudo-circuit-doc.js \
  --runtime-tarball /absolute/output/takazudo-zudo-circuit-doc-0.1.0.tgz
# Add --run to execute after reviewing the command.
```

The runtime file spec must be absolute because root and `doc/package.json` are at different depths. Keep the official version family together. This handoff does not vendor or patch the runtime. Official agent-entry files remain thin pointers to the generated workflow.

`install_resources.py` preflights every path and refuses non-identical collisions/symlinks. It appends links to the host's authored project entry/next-actions pages, and adds exact file paths to the existing public-asset allowlist. It does not mutate inventory, verdicts, generated pages, package manifests or upstream workflow. Generated output will be produced by `pnpm circuit:generate` after genuine evidence is added.

An empty generated component catalogue is valid at the narrative/candidate stage. It must not be populated by copying the earlier R20 handmade candidate MDX into `components/`. Candidates already have readable research pages and the workbench table. Promote selected parts via real source acquisition and native owner bundles.
