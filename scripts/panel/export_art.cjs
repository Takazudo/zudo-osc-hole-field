/* Derive art-only SVG from the imported R21 renderer without modifying it. */
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const wb = path.join(root, 'project/osc-hole-field/workbench');
global.GRID_ICONS = JSON.parse(fs.readFileSync(path.join(wb, 'reference/icons.json')));
require(path.join(wb, 'src/render.js'));
const grid = JSON.parse(fs.readFileSync(path.join(wb, 'layout/grid.json')));
const settings = require('./art_profile.cjs');
const lock = JSON.parse(fs.readFileSync(path.join(root, 'design/grid/placements.lock.json')));
const apertureDiameters = Object.fromEntries(lock.placements.filter(q => q.kind !== 'led').map(q => [q.uid, q.hole_d_mm]));
let svg = GridRenderer.render(grid, settings, {artOnly: true, apertureDiameters}).svg;
svg = svg.replace(/<text\b[^>]*>R21 ·[^<]*<\/text>/g, '');
svg = svg.replace(/<text\b[^>]*>INTEGER CELLS \/[^<]*<\/text>/g, '');
if (svg.includes('OSC PLAYGROUND') || svg.includes('17 \/ 14 mm GRID')) {
  throw new Error('forbidden review annotation survived art export');
}
module.exports = {svg, settings};
if (require.main === module) {
const output = path.join(root, '.circuit-cache/panel/art.svg');
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, svg);
console.log(`Art-only SVG exported: ${output}`);
}
