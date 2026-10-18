/* Bundle the existing audited renderer and owner icon library; no network runtime. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const dir=__dirname,root=path.resolve(dir,'../../../..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const paths={grid:'project/osc-hole-field/workbench/layout/grid.json',lock:'design/grid/placements.lock.json',params:'design/panel/panel-params.json',icons:'project/osc-hole-field/workbench/reference/icons.json',renderer:'project/osc-hole-field/workbench/src/render.js',profile:'scripts/panel/art_profile.cjs'};
const hashes=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,crypto.createHash('sha256').update(read(p)).digest('hex')]));
const data={grid:JSON.parse(read(paths.grid)),lock:JSON.parse(read(paths.lock)),params:JSON.parse(read(paths.params)),icons:JSON.parse(read(paths.icons)),profile:require(path.join(root,paths.profile)),geometrySHA256:crypto.createHash("sha256").update(hashes.lock+":"+hashes.params).digest("hex"),hashes};
global.GRID_ICONS=data.icons;require(path.join(root,paths.renderer));
if(data.profile.px!==17||data.profile.py!==14||data.lock.frame.panel_width_mm!==318||data.lock.frame.panel_height_mm!==298||data.lock.placements.length!==438)throw Error('Unexpected audited geometry');
const locked=new Map(data.lock.placements.map(q=>[q.uid,q]));
for(const q of [...data.grid.ports,...data.grid.controls]){const p=GridRenderer.pos(q,data.profile),l=locked.get(q.uid);if(!l||p.x!==l.x_mm||p.y!==l.y_mm||q.kind!==l.kind)throw Error('Renderer/lock geometry drift: '+q.uid);}
const json=JSON.stringify(data).replace(/</g,'\\u003c');
let html=fs.readFileSync(path.join(dir,'shell.html'),'utf8').replace('/*STYLE*/',fs.readFileSync(path.join(dir,'style.css'),'utf8')).replace('<!--DATA-->',`<script id="source-data" type="application/json">${json}</script>`).replace('/*RENDERER*/',read(paths.renderer)).replace('/*HARDWARE*/',fs.readFileSync(path.join(dir,'hardware.js'),'utf8')).replace('/*EDITOR*/',fs.readFileSync(path.join(dir,'editor.js'),'utf8'));
if(process.argv.includes('--check')){if(fs.readFileSync(path.join(dir,'index.html'),'utf8')!==html)throw Error('Offline editor is stale');console.log('PASS deterministic offline editor');}
else{fs.writeFileSync(path.join(dir,'index.html'),html);console.log('Built current editor: '+Buffer.byteLength(html)+' bytes');}
