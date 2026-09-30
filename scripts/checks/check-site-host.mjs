import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const requireFromDoc = createRequire(new URL("../../doc/package.json", import.meta.url));
const ts = requireFromDoc("typescript");

const configPath = join(repoRoot, "doc/zfb.config.ts");
const sourceText = await readFile(configPath, "utf8");
const source = ts.createSourceFile(configPath, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
if (source.parseDiagnostics.length > 0) {
  const diagnostic = source.parseDiagnostics[0];
  const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n");
  throw new Error(`Could not parse ${configPath}: ${message}`);
}

let siteUrl;
function visit(node) {
  if (
    ts.isCallExpression(node) &&
    ts.isIdentifier(node.expression) &&
    node.expression.text === "zudoDoc" &&
    node.arguments[0] &&
    ts.isObjectLiteralExpression(node.arguments[0])
  ) {
    for (const property of node.arguments[0].properties) {
      if (
        ts.isPropertyAssignment(property) &&
        (ts.isIdentifier(property.name) || ts.isStringLiteral(property.name)) &&
        property.name.text === "siteUrl" &&
        ts.isStringLiteralLike(property.initializer)
      ) {
        siteUrl = property.initializer.text;
      }
    }
  }
  ts.forEachChild(node, visit);
}
visit(source);

if (!siteUrl) {
  throw new Error(`Could not find a literal siteUrl in ${configPath}`);
}

const wranglerPath = join(repoRoot, "doc/wrangler.jsonc");
const wranglerText = await readFile(wranglerPath, "utf8");
const wranglerResult = ts.parseConfigFileTextToJson(wranglerPath, wranglerText);
if (wranglerResult.error) {
  const message = ts.flattenDiagnosticMessageText(wranglerResult.error.messageText, "\n");
  throw new Error(`Could not parse ${wranglerPath}: ${message}`);
}
const wrangler = wranglerResult.config;
const routePattern = wrangler.routes?.[0]?.pattern;
if (typeof routePattern !== "string" || routePattern.length === 0) {
  throw new Error(`Could not find routes[0].pattern in ${wranglerPath}`);
}

let siteHost;
try {
  siteHost = new URL(siteUrl).host;
} catch {
  throw new Error(`siteUrl is not a valid absolute URL: ${siteUrl}`);
}

if (siteHost !== routePattern) {
  throw new Error(`Site host mismatch: siteUrl host is "${siteHost}" but routes[0].pattern is "${routePattern}"`);
}

console.log(`site host: ${siteHost} matches Wrangler route`);
