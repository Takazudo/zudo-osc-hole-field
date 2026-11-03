/* Source-only current profile, with locked apertures overlaid; not native artwork. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const {svg: art, settings} = require('./export_art.cjs');
const lock = JSON.parse(fs.readFileSync(path.join(root, 'design/grid/placements.lock.json')));
const params = JSON.parse(fs.readFileSync(path.join(root, 'design/panel/panel-params.json')));
const out = path.join(root, 'design/panel/current-audit');
const features = lock.placements.map(q => {
  const diameter = q.kind === 'led' ? params.indicator_window.diameter_mm : q.hole_d_mm;
  return `<circle data-uid="${q.uid}" data-kind="${q.kind}" cx="${q.x_mm}" cy="${q.y_mm}" r="${diameter/2}" fill="${q.kind === 'led' ? '#52564b' : '#080a09'}"/>`;
}).join('');
const svg = art.replace('aria-label="R21 user-grid panel"', 'aria-label="Current panel source preview, not a machining drawing"')
  .replace('</svg>', `<g id="locked-features">${features}</g></svg>`);
const caption = 'Current panel source preview — not machining data or a native KiCad render. Locked 318 × 298 mm frame, 438 centres; apertures are proposals. Grey discs denote undrilled windows, not lit LEDs. Source profile: switch text 1.0 mm; separator clearance 2.5 mm. Browser fonts/strokes differ from native art; three long native jack labels have an additional 0.4 mm offset. No circuit simulation or physical fit claim.';
const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Current panel source audit</title><body style="margin:24px;background:#e8e9e4;color:#161914;font-family:Arial,sans-serif"><h1>Current panel source preview</h1><p style="max-width:80ch">${caption}</p><p><a href="README.md">Audit and open decisions</a> · <a href="current-panel.svg">SVG</a></p><div style="max-width:1200px">${svg.replace('class="panel"', 'class="panel" style="width:100%;height:auto"')}</div></body></html>\n`;
const files = {'current-panel.svg': svg+'\n', 'current-panel.html': html};
const check = process.argv.includes('--check');
for (const [name, data] of Object.entries(files)) {
  const file = path.join(out, name);
  if (check) {
    if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== data) throw Error(`Stale current preview: ${name}`);
  } else fs.writeFileSync(file, data);
}
console.log(`PASS source preview: ${lock.placements.length} locked features, sha256 ${crypto.createHash('sha256').update(files['current-panel.svg']).digest('hex')}`);
