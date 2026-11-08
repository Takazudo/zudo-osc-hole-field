import { defineConfig } from "zfb/config";
import { zudoDoc } from "@takazudo/zudo-doc/config";

// The one config file for this project's doc site (@takazudo/zudo-doc). It
// must stay free of `node:*` imports and must not import `circuit.config.ts`
// (epic #1 Config contract, item 4): `zfb.config.ts` is evaluated through
// esbuild with `--platform=neutral`, a graph the circuit config never joins.
const site = zudoDoc({
  siteName: "zudo-osc-hole-field",
  siteUrl: "https://zudo-osc-hole-field.zudolab.dev",
  githubUrl: "https://github.com/Takazudo/zudo-osc-hole-field",
  // Required by the v1 asset URLs (FOOTPRINT_ASSET_BASE / MODEL_ASSET_BASE
  // in the package are root-absolute) — this already is the default, kept
  // explicit so it is never accidentally changed.
  base: "/",
  // ADR-020: templates set the locale explicitly.
  defaultLocale: "en",
  // Classic look (zudo-doc's `default` pack), selected explicitly: zudo-doc 9
  // defaults to Graphite, and this project keeps its appearance unchanged.
  themePack: "default",
  themePacks: ["default"],
  llmsTxt: true,
  // Preserve the zudo-doc 5.27 search index window (300 characters per page),
  // the accepted behaviour for this site: the search widget shows a short
  // match-centred snippet either way, and the authored pages open with their
  // summary. zudo-doc 9 defaults to 3000. (A longer window also exposed a
  // `zudo-circuit-doc scan` false positive on the records index — two adjacent
  // published table cells matching a withheld prompt — reported upstream as
  // https://github.com/Takazudo/zudo-circuit-doc/issues/164.)
  searchMaxBodyLength: 300,
  cjkFriendly: true,
  dynamicPageTransition: true,
  docHistory: true,
  // The generated component catalog is regenerated from evidence, not
  // hand-edited, so it carries no useful edit history of its own.
  docHistoryExclude: ["components", "components/**"],
  assetViewer: true,
  // HTML under public/assets is a self-contained application (the 3 MB
  // workbench), not a viewable document; its viewer page would only show the
  // raw source. Excluding it is also a workaround for
  // https://github.com/Takazudo/zudo-front-builder/issues/4647: zudo-doc 9
  // inlines every text asset body into a virtual module that zfb 5's
  // zudo-wind scanner reads for class candidates, and the workbench's JS
  // template literals (`label-${kind}`) fail `zfb build` there (ZW001). The
  // raw /assets/osc-hole-field/workbench.html URL the authored pages link is
  // unaffected; SVG/TXT assets keep their viewer pages.
  assetViewerExclude: ["**/*.html"],
  strictContentBridge: true,
  // ADR-016: ingest this project's `.claude/` tree (one level up from this
  // zfb project) so `/docs/claude/` and `/docs/claude-skills/<owner>/`
  // render the raw agent resources the generated pages link back to.
  claudeResources: { claudeDir: "../.claude", scanRoot: ".." },
  // These routes exist only for the default docsDir and never inside an
  // archived version directory; this project has no `versions` config, but
  // the prefixes stay explicit so a later version addition does not 404 them.
  defaultLocaleOnlyPrefixes: [
    "/docs/components/",
    "/docs/claude/",
    "/docs/claude-md/",
    "/docs/claude-skills/",
    "/docs/claude-agents/",
    "/docs/claude-commands/",
  ],
  chromeBindingsModule: "./src/chrome-bindings.tsx",
  headerNav: [
    { label: "Project", path: "/docs/project", categoryMatch: "project" },
    { label: "Architecture", path: "/docs/architecture", categoryMatch: "architecture" },
    { label: "Research", path: "/docs/research", categoryMatch: "research" },
    { label: "Decisions", path: "/docs/decisions", categoryMatch: "decisions" },
    { label: "Verification", path: "/docs/verification", categoryMatch: "verification" },
    {
      label: "Components",
      path: "/docs/components",
      categoryMatch: "components",
      children: [
        { label: "Catalog & Records", path: "/docs/components", categoryMatch: "components" },
        { label: "Raw agent resources", path: "/docs/claude", categoryMatch: "claude", versioned: false },
      ],
    },
  ],
  headerRightItems: [
    { type: "component", component: "theme-toggle" },
    { type: "component", component: "search" },
  ],
  footer: {
    links: [],
    copyright: "Built with zudo-circuit-doc on zudo-doc.",
  },
});

// zfb's source-level `linkValidation` (which zudoDoc() switches on) only sees
// anchor ids written as a literal `id` on an intrinsic element, never the id a
// component such as the generated pages' `<EvidenceAnchor>` renders — so it
// warned "broken link: #fact-…" / "#src-…" for every in-page evidence link
// (#52, #68). The built-HTML scan in `pnpm check:site` (`check:links
// --strict-anchors --strict-broken`) sees rendered ids and checks every page,
// and `resolveMarkdownLinks` still warns on unresolvable `.md` links, so the
// source-level check adds nothing but noise here.
delete site.markdown?.features?.linkValidation;

export default defineConfig(site);
