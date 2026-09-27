import type { CircuitConfig } from "@takazudo/zudo-circuit-doc/config";
import { DEFAULT_PREVIEW_RENDERER } from "@takazudo/zudo-circuit-doc/config";

export default {
  configVersion: 1,
  project: {
    name: "zudo-osc-hole-field",
    title: "zudo-osc-hole-field",
  },
  docs: {
    root: "doc",
    generatedContent: "doc/src/content/docs/components",
    preflight: "circuit/generated/preflight.json",
    publicRoot: "doc/public",
    dist: "doc/dist",
    agentResources: true,
  },
  evidence: {
    contractVersion: 1,
    bundlesRoot: ".claude/skills",
    ownerPrefix: "component-",
    auditSkill: "component-spec-audit",
    integrationSkill: "circuit-spec-integration",
    inventory: ".claude/skills/component-spec-audit/references/inventory.json",
    integrationRules: ".claude/skills/circuit-spec-integration/references/rules.json",
    directRouting: ".claude/skills/component-spec-audit/references/direct-routing.json",
    vendorQualifiers: ".claude/skills/component-spec-audit/references/external-vendor-qualifiers.json",
    sourceCache: ".circuit-cache/sources",
  },
  inventoryProvider: { kind: "manual" },
  publication: {
    selection: "circuit/publication/selection.json",
    assets: "circuit/publication/assets.json",
  },
  cad: {
    enabled: true,
    libraryName: "zudo-osc-hole-field",
    symbolLibraries: ["symbols/zudo-osc-hole-field.kicad_sym"],
    footprintMasterRoot: "footprints/kicad/zudo-osc-hole-field.pretty",
    footprintLibraryRoot: "footprints/kicad/zudo-osc-hole-field.pretty",
    modelRoot: "footprints/kicad/zudo-osc-hole-field.3dshapes",
    modelLocatorPrefix: "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.3dshapes/",
    previewRenderer: {
      ...DEFAULT_PREVIEW_RENDERER,
      image: "kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec",
      version: "10.0.6",
      layers: ["F.Cu", "F.Silkscreen", "F.Fab", "F.CrtYd"],
    },
  },
  validation: {},
} satisfies CircuitConfig;
