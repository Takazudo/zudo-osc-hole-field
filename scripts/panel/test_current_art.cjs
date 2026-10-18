const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const {svg, settings} = require('./export_art.cjs');
const grid = JSON.parse(fs.readFileSync(path.join(root, 'project/osc-hole-field/workbench/layout/grid.json')));
const lock = JSON.parse(fs.readFileSync(path.join(root, 'design/grid/placements.lock.json')));
assert.equal(settings.labelSwitch, 1.0);
assert.equal(settings.separatorGap, 2.5);
let historical = GridRenderer.render(grid, settings, {artOnly:true}).svg;
historical = historical.replace(/<text\b[^>]*>R21 ·[^<]*<\/text>/g, '').replace(/<text\b[^>]*>INTEGER CELLS \/[^<]*<\/text>/g, '');
// gen_panel.py excludes unstroked background fills from copper/mask/silk conversion.
const removeBackground = s => s.replace(/<circle\b[^>]*fill="#101211"[^>]*stroke="none"[^>]*\/>/g, '');
assert.equal(removeBackground(svg), removeBackground(historical));
for (const q of lock.placements.filter(q => q.kind === 'octave')) {
  const group = svg.match(new RegExp(`<g class="item [^>]*data-id="${q.uid.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}"[\\s\\S]*?<\\/g>`));
  assert.ok(group, q.uid);
  assert.ok(group[0].includes(`r="${q.hole_d_mm/2}" fill="#101211"`), q.uid);
}
assert.equal((historical.match(/r="3.5" fill="#101211"/g)||[]).length,0);
assert.equal((svg.match(/r="3.5" fill="#101211"/g)||[]).length,5);
console.log('PASS current art: shared export profile, 5 locked OCT cutouts; convertible artwork unchanged');
