// Browser smoke test for the instrument preview (Node + globally installed Playwright).
//   node project/osc-hole-field/instrument-preview/test_browser.mjs [--out DIR] [--publish]
// Loads index.html from disk, requires zero console errors / page errors and no request
// other than the file itself (blob: and data: URLs are in-memory, not network), drives every
// mode through window.__preview and saves screenshots. --publish also writes the four
// screenshots referenced by the docs into doc/public/assets/osc-hole-field/.
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import {execSync} from 'node:child_process';

const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); } catch {
  const root = execSync('npm root -g').toString().trim();
  playwright = require(path.join(root, 'playwright'));
}
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../../..');
const args = process.argv.slice(2);
const outDir = args.includes('--out') ? path.resolve(args[args.indexOf('--out') + 1]) : path.join(os.tmpdir(), 'osc-instrument-preview-shots');
const publish = args.includes('--publish');
fs.mkdirSync(outDir, {recursive: true});
const page_url = pathToFileURL(path.join(here, 'index.html')).href;

const failures = [];
const check = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) failures.push(msg); };

const browser = await playwright.chromium.launch();
const context = await browser.newContext({viewport: {width: 1440, height: 900}, deviceScaleFactor: 1});
const page = await context.newPage();
const consoleErrors = [], requests = [];
page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
page.on('request', r => requests.push(r.url()));
await page.goto(page_url);
await page.waitForFunction(() => window.__preview, null, {timeout: 120000});
await page.evaluate(() => window.__preview.ready);
await page.evaluate(() => window.__preview.idle());

const st0 = await page.evaluate(() => window.__preview.state());
check(st0.boards === 10, `10 boards loaded (${st0.boards})`);
const nLayers = await page.evaluate(() => JSON.parse(document.getElementById('data').textContent).boards.reduce((a, b) => a + b.layers.length, 0));
check(st0.textures === nLayers, `${nLayers} copper textures decoded (${st0.textures})`);
check(st0.instances > 6000, `instanced bodies and meshes (${st0.instances})`);
const shot = async (name, pub) => {
  await page.evaluate(() => window.__preview.idle());
  const file = path.join(outDir, name + '.png');
  await page.screenshot({path: file});
  if (publish && pub) fs.copyFileSync(file, path.join(repo, 'doc/public/assets/osc-hole-field', pub));
  console.log('  screenshot ' + file);
};
await shot('01-assembled', 'instrument-3d-assembled.png');
await page.evaluate(() => window.__preview.view('front', 10)); await shot('02-front');
await page.evaluate(() => window.__preview.view('side', 10)); await shot('03-depth-section');
await page.evaluate(() => window.__preview.view('rear', 10)); await shot('04-rear');
await page.evaluate(() => window.__preview.setMode('exploded'));
await page.evaluate(() => window.__preview.setExplode(0.8));
check((await page.evaluate(() => window.__preview.state())).mode === 'exploded', 'exploded mode');
await shot('05-exploded', 'instrument-3d-exploded.png');
await page.evaluate(() => window.__preview.setMode('xray'));
check((await page.evaluate(() => window.__preview.state())).mode === 'xray', 'x-ray mode');
await page.evaluate(() => window.__preview.view('hero', 10)); await shot('06-xray');
await page.evaluate(() => window.__preview.focusBoard('osc-core'));
let st = await page.evaluate(() => window.__preview.state());
check(st.mode === 'focus' && st.focus === 'osc-core' && /Core board/.test(st.info || ''), 'board focus card for K');
await shot('07-focus-core-card', 'instrument-3d-board-card.png');
await page.evaluate(() => window.__preview.setPeel('osc-core', 0.8));
await shot('08-core-layer-peel');
await page.evaluate(() => window.__preview.setPeel('osc-core', 0));
const hits = await page.evaluate(() => window.__preview.find('OPA4197'));
check(hits.length > 0, `search finds OPA4197 parts (${hits.length})`);
const k = hits.find(h => h.board === 'osc-core') || hits[0];
await page.evaluate(h => window.__preview.select(h.board, h.ref), k);
st = await page.evaluate(() => window.__preview.state());
check(st.selected && st.info && st.info.includes(k.ref), `select ${k.ref} shows its identity card`);
await shot('09-core-copper-closeup', 'instrument-3d-core-copper.png');
await page.evaluate(() => window.__preview.focusBoard('osc-jack-left'));
await shot('10-focus-jl');
await page.evaluate(() => window.__preview.focusBoard('osc-control'));
await shot('11-focus-p');
await page.evaluate(() => window.__preview.setMode('assembled'));
await page.evaluate(() => window.__preview.startTour(400));
await page.waitForFunction(() => window.__preview.state().tour === 2, null, {timeout: 60000});
await shot('12-tour');
await page.evaluate(() => window.__preview.stopTour());
check((await page.evaluate(() => window.__preview.state())).tour === null, 'tour runs and stops');
// click picking: a body on K in focus, then the opaque panel must block picks behind it
await page.evaluate(() => window.__preview.focusBoard('osc-core'));
await page.evaluate(() => window.__preview.idle());
const target = hits.find(h => h.board === 'osc-core') || hits[0];
const xy = await page.evaluate(h => window.__preview.screenOf(h.board, h.ref), target);
await page.mouse.click(xy.x, xy.y);
let picked = await page.evaluate(() => window.__preview.state().info);
check(picked && picked.includes(target.ref), `click on ${target.ref} opens its identity card (${picked})`);
await page.evaluate(() => window.__preview.setMode('assembled'));
await page.evaluate(() => window.__preview.view('front', 10));
await page.evaluate(() => window.__preview.idle());
const before = await page.evaluate(() => window.__preview.state().info);
const behind = await page.evaluate(h => window.__preview.screenOf(h.board, h.ref), target);
await page.mouse.click(behind.x, behind.y);
picked = await page.evaluate(() => window.__preview.state().info);
check(picked === before, `the opaque panel blocks picking ${target.ref} from the front`);
// narrow viewport
await page.setViewportSize({width: 1280, height: 720});
await page.evaluate(() => window.__preview.view('hero', 10)); await shot('13-laptop-1280');

const external = requests.filter(u => u !== page_url && !u.startsWith('blob:') && !u.startsWith('data:'));
check(external.length === 0, `no network requests besides the page (${external.length}: ${external.slice(0, 3).join(', ')})`);
check(consoleErrors.length === 0, `no console errors (${consoleErrors.length}: ${consoleErrors.slice(0, 3).join(' | ')})`);
await browser.close();
console.log(failures.length ? `FAIL ${failures.length} check(s)` : 'PASS browser smoke');
process.exit(failures.length ? 1 : 0);
