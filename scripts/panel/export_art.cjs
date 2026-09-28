/* Derive art-only SVG from the imported R21 renderer without modifying it. */
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const wb = path.join(root, 'project/osc-hole-field/workbench');
global.GRID_ICONS = JSON.parse(fs.readFileSync(path.join(wb, 'reference/icons.json')));
require(path.join(wb, 'src/render.js'));
const grid = JSON.parse(fs.readFileSync(path.join(wb, 'layout/grid.json')));
const settings = {
  px: 17, py: 14, labelModule: 1.6, labelKnob: 1.5,
  labelJack: 1.6, labelSwitch: 1.0, separatorGap: 2.5,
  headings: true, grid: false, bodies: false, plugs: false,
  plugDia: 12, relations: true, ledStyle: 'line', switchLabels: 'words',
  icons: {}, values: {}, signalValues: {}, stageLevels: {}, selected: null,
};
let svg = GridRenderer.render(grid, settings, {artOnly: true}).svg;
svg = svg.replace(/<text\b[^>]*>R21 ·[^<]*<\/text>/g, '');
svg = svg.replace(/<text\b[^>]*>INTEGER CELLS \/[^<]*<\/text>/g, '');
if (svg.includes('OSC PLAYGROUND') || svg.includes('17 \/ 14 mm GRID')) {
  throw new Error('forbidden review annotation survived art export');
}
const output = path.join(root, '.circuit-cache/panel/art.svg');
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, svg);
console.log(`Art-only SVG exported: ${output}`);
