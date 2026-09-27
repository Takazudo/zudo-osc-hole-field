import { lstat, readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const maxBytes = 25 * 1024 * 1024;
const assetRoots = ["doc/public", "doc/dist"];
const oversized = [];
let scannedFiles = 0;

async function scanDirectory(directory) {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return;
    throw error;
  }

  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await scanDirectory(path);
    } else if (entry.isFile()) {
      const details = await lstat(path);
      scannedFiles += 1;
      if (details.size > maxBytes) {
        oversized.push({ path: relative(repoRoot, path), size: details.size });
      }
    }
  }
}

for (const root of assetRoots) {
  await scanDirectory(join(repoRoot, root));
}

if (oversized.length > 0) {
  console.error("site asset size check failed: files may not exceed 25 MiB");
  for (const asset of oversized) {
    console.error(`- ${asset.path}: ${(asset.size / (1024 * 1024)).toFixed(2)} MiB`);
  }
  process.exitCode = 1;
} else {
  console.log(`site asset size check passed: ${scannedFiles} files are at most 25 MiB`);
}
