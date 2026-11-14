import * as THREE from '__THREE__';
import {OrbitControls} from '__ORBIT__';

const $ = id => document.getElementById(id);
const D = JSON.parse($('data').textContent);
const TEX = JSON.parse($('tex').textContent);
const C = Object.fromEntries(D.part_columns.map((k, i) => [k, i]));
const FAM = D.families;
const famIndex = Object.fromEntries(FAM.map((f, i) => [f.key, i]));
const wx = x => x - 159, wy = y => 149 - y;
const fmt = n => n == null ? '—' : Number(n).toLocaleString('en-US');
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

// Layer tints: one distinct hue per copper plane (display only).
const LAYER_TINT = {'F.Cu': '#e8975a', 'In1.Cu': '#46b8a6', 'In2.Cu': '#7d8ff0', 'In3.Cu': '#d276c8', 'In4.Cu': '#93c95b', 'B.Cu': '#f0c75e'};
const BLOCK_PALETTE = ['#e07a5f', '#81b29a', '#f2cc8f', '#6d9dc5', '#c77dff', '#e9c46a', '#2a9d8f', '#f4a261', '#90be6d', '#f28482', '#84a59d', '#b5838d', '#48cae4', '#ffb703', '#a3b18a', '#cdb4db'];
// Explode offsets (mm along Z) per board key at slider = 1.
const EXPLODE = {PANEL: 70, EL: 38, JL: 0, JR: 0, P: -16, O1: -30, O3: -30, O5: -30, O2: -44, O4: -44, K: -80};

// ---------- renderer, camera, controls ----------
const stage = $('stage');
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
stage.append(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(34, 1, 2, 6000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = .09; controls.screenSpacePanning = true;
controls.minDistance = 15; controls.maxDistance = 2200; controls.zoomToCursor = true;
scene.add(new THREE.HemisphereLight(0xdfeaf2, 0x2a2420, 1.6));
const key = new THREE.DirectionalLight(0xfff3e2, 2.2); key.position.set(-250, 300, 420); scene.add(key);
const rim = new THREE.DirectionalLight(0x9cc4ff, 1.1); rim.position.set(300, -120, -400); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffffff, .5); fill.position.set(400, 100, 100); scene.add(fill);
const maxAniso = renderer.capabilities.getMaxAnisotropy();

let dirty = true;
const invalidate = () => { dirty = true; };
controls.addEventListener('change', invalidate);

// ---------- state ----------
const state = {mode: 'assembled', explode: 0, colorBy: 'family', focus: null, show: {panel: true, parts: true, copper: true, ghost: true}, peel: {}, layerOn: {}, selected: null, tour: null};
const boards = [];          // runtime board records
const byId = {};
const labels = [];          // {el, pos:Vector3, obj?:Object3D, kind}
const labelRoot = $('labels');
function addLabel(html, pos, cls, obj) {
  const el = document.createElement('div'); el.className = 'lbl ' + cls; el.innerHTML = html; labelRoot.append(el);
  const L = {el, pos: pos.clone(), obj, visible: true}; labels.push(L); return L;
}

// ---------- shared materials ----------
const famMats = FAM.map(() => new THREE.MeshStandardMaterial({color: 0xffffff, roughness: .55, metalness: .08}));
const boxF = new THREE.BoxGeometry(1, 1, 1).translate(0, 0, .5);
const boxB = new THREE.BoxGeometry(1, 1, 1).translate(0, 0, -.5);
const copperVS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;
const copperFS = `uniform sampler2D map; uniform vec3 color; uniform float opacity; uniform float glow; varying vec2 vUv;
void main(){ float a = texture2D(map, vUv).r; if (a < 0.02) discard;
  vec3 c = color * (1.0 + glow * 0.9); gl_FragColor = vec4(c, a * opacity);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function copperMaterial(tex, tint) {
  return new THREE.ShaderMaterial({uniforms: {map: {value: tex}, color: {value: new THREE.Color(tint)}, opacity: {value: .92}, glow: {value: 0}},
    vertexShader: copperVS, fragmentShader: copperFS, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, toneMapped: false});
}

// ---------- panel ----------
const panelGroup = new THREE.Group(); panelGroup.name = 'panel'; scene.add(panelGroup);
const P = D.panel;
const panelShape = new THREE.Shape();
{
  const w = P.width_mm / 2, h = P.height_mm / 2, r = P.corner_radius_mm || 0;
  panelShape.moveTo(-w + r, -h); panelShape.lineTo(w - r, -h); panelShape.quadraticCurveTo(w, -h, w, -h + r);
  panelShape.lineTo(w, h - r); panelShape.quadraticCurveTo(w, h, w - r, h); panelShape.lineTo(-w + r, h);
  panelShape.quadraticCurveTo(-w, h, -w, h - r); panelShape.lineTo(-w, -h + r); panelShape.quadraticCurveTo(-w, -h, -w + r, -h);
  for (const q of D.lock) {
    const d = q.kind === 'led' ? D.indicator_window_mm : q.hole_d_mm;
    const hole = new THREE.Path(); hole.absarc(wx(q.x_mm), wy(q.y_mm), d / 2, 0, Math.PI * 2, true); panelShape.holes.push(hole);
  }
}
const panelGeo = new THREE.ExtrudeGeometry(panelShape, {depth: P.thickness_mm, bevelEnabled: false, curveSegments: 10});
{ // artwork on the panel's own front triangles (no coincident second plane, avoids depth fighting)
  const pos = panelGeo.attributes.position, uv = panelGeo.attributes.uv;
  for (let i = 0; i < pos.count; i++) uv.setXY(i, (pos.getX(i) + 159) / 318, (pos.getY(i) + 149) / 298);
  panelGeo.clearGroups(); let start = 0, role = -1;
  for (let i = 0; i < pos.count; i += 3) {
    const r = [0, 1, 2].every(j => Math.abs(pos.getZ(i + j) - P.thickness_mm) < 1e-6) ? 0 : 1;
    if (r !== role) { if (i) panelGeo.addGroup(start, i - start, role); start = i; role = r; }
  }
  panelGeo.addGroup(start, pos.count - start, role);
}
const artMat = new THREE.MeshStandardMaterial({color: '#1a1d1b', roughness: .62, metalness: .05});
const panelEdgeMat = new THREE.MeshStandardMaterial({color: '#151816', roughness: .7});
const panelMesh = new THREE.Mesh(panelGeo, [artMat, panelEdgeMat]);
panelMesh.position.z = -P.thickness_mm; panelGroup.add(panelMesh);
const artReady = new Promise(resolve => {
  const svg = $('data') && D.artwork;
  const img = new Image();
  img.onload = () => {
    const cv = document.createElement('canvas'); cv.width = 318 * 8; cv.height = 298 * 8;
    cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = maxAniso;
    artMat.map = t; artMat.color.set('#ffffff'); artMat.needsUpdate = true; invalidate(); resolve(true);
  };
  img.onerror = () => resolve(false);
  img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
});

// ---------- meshes for pots and jacks (component-preview transforms) ----------
function meshGeometry(s, tf) {
  const g = new THREE.BufferGeometry(), a = new Float32Array(s.positions.length);
  for (let i = 0; i < s.positions.length; i += 3) { const p = tf(s.positions[i], s.positions[i + 1], s.positions[i + 2]); a[i] = p[0]; a[i + 1] = p[1]; a[i + 2] = p[2]; }
  g.setAttribute('position', new THREE.BufferAttribute(a, 3)); g.setIndex(s.indices); g.computeVertexNormals(); return g;
}
const potGeo = meshGeometry(D.meshes.pot.solids[0], (x, y, z) => [x - 6.9960603727775, y - 2.5, z - 9.89]);
{
  const pos = potGeo.attributes.position, idx = potGeo.index; let start = 0, last = -1;
  for (let i = 0; i < idx.count; i += 3) { const r = [0, 1, 2].every(j => pos.getZ(idx.getX(i + j)) >= -2.001) ? 1 : 0; if (r !== last) { if (i) potGeo.addGroup(start, i - start, last); start = i; last = r; } }
  potGeo.addGroup(start, idx.count - start, last);
}
const jackGeos = D.meshes.jack.solids.map(s => meshGeometry(s, (x, y, z) => [x - .8, -z, y - 12]));
const potMats = [new THREE.MeshStandardMaterial({color: '#7b5a35', roughness: .5}), new THREE.MeshStandardMaterial({color: '#aeb3aa', roughness: .45})];
const jackBody = new THREE.MeshStandardMaterial({color: '#1f2226', roughness: .45});
const jackMetal = new THREE.MeshStandardMaterial({color: '#c3cbcd', roughness: .3, metalness: .7});
const capMat = new THREE.MeshStandardMaterial({color: '#d9b970', roughness: .35, metalness: .5});
const leverMat = new THREE.MeshStandardMaterial({color: '#c9d0d2', roughness: .25, metalness: .8});
const plungerMat = new THREE.MeshStandardMaterial({color: '#3b434b', roughness: .5});
const hwMats = [...potMats, jackBody, jackMetal, capMat, leverMat, plungerMat];
const lockByUid = Object.fromEntries(D.lock.map(q => [q.uid, q]));

// ---------- copper textures ----------
async function loadTexture(name) {
  const img = new Image(); img.src = 'data:image/png;base64,' + TEX[name];
  await img.decode();
  const W = img.naturalWidth, H = img.naturalHeight;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const ctx = cv.getContext('2d', {willReadFrequently: true}); ctx.drawImage(img, 0, 0);
  const src = ctx.getImageData(0, 0, W, H).data, out = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) { const so = y * W * 4, dO = (H - 1 - y) * W; for (let x = 0; x < W; x++) out[dO + x] = src[so + x * 4]; }
  const t = new THREE.DataTexture(out, W, H, THREE.RedFormat, THREE.UnsignedByteType);
  t.unpackAlignment = 1; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter;
  t.anisotropy = maxAniso; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true;
  return t;
}

// ---------- boards ----------
const ghostRoot = new THREE.Group(); scene.add(ghostRoot);
function boardShape(b) {
  const s = new THREE.Shape(b.outline.map(([x, y]) => new THREE.Vector2(wx(x), wy(y))));
  for (const h of b.holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(wx(x), wy(y)))));
  for (const [x, y, d] of b.npth) if (d >= 1) { const p = new THREE.Path(); p.absarc(wx(x), wy(y), d / 2, 0, Math.PI * 2, true); s.holes.push(p); }
  return s;
}
function peelStep(R) { const [x0, y0, x1, y1] = R.b.bbox; return Math.max(6, Math.max(x1 - x0, y1 - y0) / 12); }
function layerZ(R, i, peel) {
  const n = R.b.layers.length, t = R.b.thickness_mm;
  return R.b.face_z_mm - t * i / (n - 1) - peel * i * peelStep(R);
}
const pickables = [];
for (const b of D.boards) {
  const R = {b, group: new THREE.Group(), fGroup: new THREE.Group(), bGroup: new THREE.Group(), planes: [], insts: [], hw: []};
  R.group.name = b.id; scene.add(R.group); R.group.add(R.fGroup, R.bGroup);
  boards.push(R); byId[b.id] = R; state.peel[b.id] = 0;
  const t = b.thickness_mm, z0 = b.face_z_mm;
  R.subMat = new THREE.MeshStandardMaterial({color: b.key === 'EL' ? '#1d4434' : '#173a2d', roughness: .78, metalness: .02, transparent: true, opacity: 1});
  R.sub = new THREE.Mesh(new THREE.ExtrudeGeometry(boardShape(b), {depth: t, bevelEnabled: false, curveSegments: 8}), R.subMat);
  R.sub.position.z = z0 - t; R.group.add(R.sub);
  // edge outline ghost (stays visible when a board is isolated away)
  const pts = b.outline.map(([x, y]) => new THREE.Vector3(wx(x), wy(y), z0));
  R.outline = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({color: '#6f8a96', transparent: true, opacity: .55}));
  ghostRoot.add(R.outline);
  // copper planes
  const [x0, y0, x1, y1] = b.bbox;
  b.layers.forEach((ln, i) => {
    state.layerOn[b.id + '|' + ln] = true;
    const geo = new THREE.PlaneGeometry(x1 - x0, y1 - y0);
    const m = new THREE.Mesh(geo, copperMaterial(null, LAYER_TINT[ln] || '#cccccc'));
    m.position.set(wx((x0 + x1) / 2), wy((y0 + y1) / 2), 0); m.renderOrder = 2 + i; m.visible = false;
    m.userData = {layer: ln, index: i, file: b.copper[i].file}; R.group.add(m); R.planes.push(m);
  });
  R.bGroup.position.z = 0;
  // component bodies, instanced per family and side
  const groups = {};
  b.parts.forEach((p, idx) => {
    const fam = FAM[p[C.family]].key;
    if (fam === 'mech') return;
    if ((fam === 'pot' || fam === 'jack') && p[C.panel_uid] && lockByUid[p[C.panel_uid]]) return; // real meshes below
    const k = p[C.side] + ':' + p[C.family]; (groups[k] ||= []).push(idx);
  });
  for (const [k, list] of Object.entries(groups)) {
    const [side, fi] = k.split(':').map(Number);
    const im = new THREE.InstancedMesh(side ? boxB : boxF, famMats[fi], list.length);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(), v = new THREE.Vector3();
    const h = FAM[fi].height_mm;
    list.forEach((idx, j) => {
      const p = b.parts[idx];
      e.set(0, 0, THREE.MathUtils.degToRad(p[C.rot])); q.setFromEuler(e);
      v.set(wx(p[C.cx]), wy(p[C.cy]), side ? z0 - t : z0); s.set(Math.max(p[C.w], .2), Math.max(p[C.h], .2), h);
      im.setMatrixAt(j, m4.compose(v, q, s));
    });
    im.userData = {board: b.id, idx: list}; im.instanceMatrix.needsUpdate = true;
    (side ? R.bGroup : R.fGroup).add(im); R.insts.push(im); pickables.push(im);
  }
  // panel hardware owned by this board: real pot/jack meshes, toggle levers, button plungers, selector shafts
  const potList = [], jackList = [], levers = [], plungers = [], shafts = [];
  b.parts.forEach((p, idx) => {
    const q = lockByUid[p[C.panel_uid]]; if (!q) return;
    const fam = FAM[p[C.family]].key;
    if (fam === 'pot') potList.push([q, idx]); else if (fam === 'jack') jackList.push([q, idx]);
    else if (fam === 'toggle') levers.push([q, idx]); else if (fam === 'button') plungers.push([q, idx]); else if (fam === 'selector') shafts.push([q, idx]);
  });
  const place = (list, geo, mat, extra) => {
    if (!list.length) return null;
    const im = new THREE.InstancedMesh(geo, mat, list.length), m4 = new THREE.Matrix4(), o = new THREE.Object3D();
    list.forEach(([q], j) => { o.position.set(wx(q.x_mm), wy(q.y_mm), 0); o.rotation.set(0, 0, -THREE.MathUtils.degToRad(q.rot_deg || 0)); if (extra) extra(o, q); o.updateMatrix(); im.setMatrixAt(j, o.matrix); });
    im.userData = {board: b.id, idx: list.map(l => l[1])}; R.fGroup.add(im); R.hw.push(im); pickables.push(im); return im;
  };
  place(potList, potGeo, potMats);
  jackGeos.forEach((g, i) => place(jackList, g, i === 0 ? jackBody : jackMetal));
  place(levers, new THREE.CylinderGeometry(1.2, 1.2, 12.5, 16).rotateX(Math.PI / 2).translate(0, 0, 3.4), leverMat, o => o.rotation.x = .22);
  place(levers, new THREE.CylinderGeometry(3, 3, 3, 24).rotateX(Math.PI / 2).translate(0, 0, -1.3), leverMat);
  place(plungers, new THREE.CylinderGeometry(2.3, 2.3, 7.8, 20).rotateX(Math.PI / 2).translate(0, 0, z0 + 3.5 + 3.9), plungerMat);
  place(shafts, new THREE.CylinderGeometry(3, 3, 10 - (z0 + 7.5), 20).rotateX(Math.PI / 2).translate(0, 0, (10 + z0 + 7.5) / 2), leverMat);
  place(shafts, new THREE.CylinderGeometry(4, 4, 9, 28).rotateX(Math.PI / 2).translate(0, 0, 5.5), capMat);
  // board label
  R.label = addLabel(`<b>${esc(b.key)}</b>${esc(b.label.startsWith(b.key) ? b.label.slice(b.key.length) : '')}<span>z ${b.face_z_mm}</span>`, new THREE.Vector3(wx(b.bbox[0]), wy(b.bbox[1]), z0), 'board', R.group);
  if (b.key.startsWith('O') && b.key !== 'O1') R.label.suppress = true;
}
// panel label + octave group label
addLabel('<b>PANEL</b><span>front z 0</span>', new THREE.Vector3(-159, 149, 0), 'board', panelGroup);
byId['osc-octave-1'].label.el.innerHTML = '<b>O1–O5</b><span>z −16 / −29</span>';

// ---------- enclosure ghost and depth ruler ----------
const ghost = new THREE.Group(); scene.add(ghost);
{
  const [ix0, iy0, ix1, iy1] = D.enclosure.internal_xy_mm, depth = D.enclosure.inside_depth_mm;
  const box = new THREE.BoxGeometry(ix1 - ix0, iy1 - iy0, depth);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(box), new THREE.LineDashedMaterial({color: '#5c7685', dashSize: 4, gapSize: 3, transparent: true, opacity: .55}));
  edges.computeLineDistances(); edges.position.set(wx((ix0 + ix1) / 2), wy((iy0 + iy1) / 2), -depth / 2); ghost.add(edges);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(ix1 - ix0, iy1 - iy0), new THREE.MeshBasicMaterial({color: '#2b3a44', transparent: true, opacity: .16, side: THREE.DoubleSide, depthWrite: false}));
  back.position.set(wx((ix0 + ix1) / 2), wy((iy0 + iy1) / 2), -depth); ghost.add(back);
  addLabel('ENCLOSURE PROPOSAL · INNER REAR −' + depth + ' MM · NO CASE SELECTED', new THREE.Vector3(wx(ix1), wy(iy0) + 3, -depth), 'ghost', ghost).el.style.transform = 'translate(-100%,-100%)';
  // ruler along the lower-left vertical edge
  const rx = wx(ix0) - 14, ry = wy(iy1);
  const rpts = [new THREE.Vector3(rx, ry, 0), new THREE.Vector3(rx, ry, -depth)];
  for (let z = 0; z >= -depth; z -= 5) { const L = z % 10 === 0 ? (z % 50 === 0 ? 6 : 3.5) : 2; rpts.push(new THREE.Vector3(rx, ry, z), new THREE.Vector3(rx - L, ry, z)); if (z % 50 === 0 || z === -depth) addLabel(z + ' mm', new THREE.Vector3(rx - 7, ry, z), 'tick' + (z % 50 === 0 ? ' major' : ''), ghost); }
  const ruler = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(rpts), new THREE.LineBasicMaterial({color: '#8197a3', transparent: true, opacity: .8, depthTest: false})); ruler.renderOrder = 20; ghost.add(ruler);
  // plane markers from ruler to the instrument edge
  const planes = [...new Set(D.boards.map(b => b.face_z_mm))];
  const mpts = []; for (const z of planes) mpts.push(new THREE.Vector3(rx, ry, z), new THREE.Vector3(wx(ix0), ry, z));
  ghost.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(mpts), new THREE.LineBasicMaterial({color: '#d9b970', transparent: true, opacity: .45})));
  // annotate the open span between the deepest front board's rear face and K
  const front = D.boards.filter(b => b.key !== 'K'), K = D.boards.find(b => b.key === 'K');
  const rear = Math.min(...front.map(b => b.face_z_mm - b.thickness_mm));
  const span = (rear - K.face_z_mm).toFixed(1);
  const bpts = [new THREE.Vector3(rx + 4, ry, rear), new THREE.Vector3(rx + 4, ry, K.face_z_mm), new THREE.Vector3(rx + 2, ry, rear), new THREE.Vector3(rx + 4, ry, rear), new THREE.Vector3(rx + 2, ry, K.face_z_mm), new THREE.Vector3(rx + 4, ry, K.face_z_mm)];
  const brace = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(bpts), new THREE.LineBasicMaterial({color: '#d9b970', depthTest: false, transparent: true})); brace.renderOrder = 20; ghost.add(brace);
  addLabel(`${span} mm with no board plane (O2/O4 rear ${rear} → K ${K.face_z_mm}). Harnesses and the EXT inlet reservation live here; neither is modelled.`, new THREE.Vector3(rx + 4, ry, (rear + K.face_z_mm) / 2), 'note', ghost);
  Object.assign(labels[labels.length - 1].el.style, {transform: 'translate(-50%, 14px)', textAlign: 'center', width: '250px'});
    D.spanMm = Number(span);
}

// ---------- colours ----------
function blockColor(name) { let h = 0; for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return BLOCK_PALETTE[h % BLOCK_PALETTE.length]; }
function applyColors() {
  const c = new THREE.Color();
  for (const R of boards) for (const im of R.insts) {
    im.userData.idx.forEach((idx, j) => {
      const p = R.b.parts[idx];
      if (state.colorBy === 'family') c.set(FAM[p[C.family]].color);
      else if (state.colorBy === 'side') c.set(p[C.side] ? '#5e9fd6' : '#e2b25c');
      else c.set(p[C.block] ? blockColor(p[C.block]) : '#555c63');
      im.setColorAt(j, c);
    });
    im.instanceColor.needsUpdate = true;
  }
  const lg = $('legend');
  if (state.colorBy === 'family') { const used = new Set(); for (const R of boards) for (const p of R.b.parts) used.add(p[C.family]); lg.innerHTML = [...used].filter(i => !['mech'].includes(FAM[i].key)).map(i => `<span><i style="background:${FAM[i].color}"></i>${esc(FAM[i].label)} · ${FAM[i].height_mm} mm</span>`).join(''); }
  else if (state.colorBy === 'side') lg.innerHTML = '<span><i style="background:#e2b25c"></i>F side (faces panel)</span><span><i style="background:#5e9fd6"></i>B side (faces rear)</span>';
  else { const bl = new Set(); for (const R of boards) for (const p of R.b.parts) if (p[C.block]) bl.add(p[C.block]); lg.innerHTML = `<span style="grid-column:1/-1">${bl.size} blocks from the footprints' Block property, hashed to ${BLOCK_PALETTE.length} hues (neighbours may share a hue)</span>`; }
  invalidate();
}

// ---------- mode application ----------
function boardExplode(R) { return state.explode * (EXPLODE[R.b.key] ?? 0); }
function apply() {
  const xray = state.mode === 'xray';
  const focusId = state.mode === 'focus' ? state.focus : null;
  panelGroup.position.z = state.explode * EXPLODE.PANEL;
  panelGroup.visible = state.show.panel && !focusId;
  artMat.transparent = panelEdgeMat.transparent = xray; artMat.opacity = panelEdgeMat.opacity = xray ? .14 : 1; artMat.depthWrite = panelEdgeMat.depthWrite = !xray;
  for (const m of [...famMats, ...hwMats]) { m.transparent = xray; m.opacity = xray ? .28 : 1; m.depthWrite = !xray; m.needsUpdate = true; }
  for (const R of boards) {
    const iso = focusId && focusId !== R.b.id;
    R.group.visible = !iso;
    R.group.position.z = boardExplode(R);
    R.outline.position.z = boardExplode(R);
    R.outline.material.opacity = iso ? .28 : .35;
    const peel = state.peel[R.b.id] || 0, n = R.b.layers.length, t = R.b.thickness_mm;
    R.subMat.opacity = xray ? .1 : peel > 0 ? Math.max(.08, 1 - peel * 3) : 1;
    R.subMat.transparent = R.subMat.opacity < 1; R.subMat.depthWrite = R.subMat.opacity >= 1;
    R.bGroup.position.z = -peel * (n - 1) * peelStep(R);
    for (const m of R.planes) {
      const i = m.userData.index, outer = i === 0 || i === n - 1;
      m.position.z = layerZ(R, i, peel) + (i === 0 ? .04 : i === n - 1 ? -.04 : 0);
      const on = state.layerOn[R.b.id + '|' + m.userData.layer];
      m.visible = state.show.copper && on && (xray || peel > 0 || outer) && !!m.material.uniforms.map.value;
      m.material.uniforms.glow.value = xray ? .6 : 0;
      m.material.uniforms.opacity.value = xray ? .085 : peel > 0 ? .62 : .55;
      m.material.blending = xray ? THREE.AdditiveBlending : THREE.NormalBlending;
    }
    R.fGroup.visible = R.bGroup.visible = state.show.parts && peel < .05;
    R.label.visible = !iso;
    if (R.layerLabels) R.layerLabels.forEach((L, i) => { L.visible = peel > 0.05 && !iso; L.pos.z = layerZ(R, i, peel); });
  }
  ghost.visible = state.show.ghost && !focusId;
  ghostRoot.visible = true;
  document.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mode === state.mode)));
  $('explodeWrap').style.display = state.mode === 'exploded' ? 'block' : 'none';
  $('explode').value = state.explode;
  document.querySelectorAll('.boardrow').forEach(r => r.setAttribute('aria-pressed', String(r.dataset.id === focusId)));
  invalidate();
}

// ---------- camera animation ----------
let anim = null;
function flyTo(pos, target, ms = 1300) {
  anim = {p0: camera.position.clone(), t0: controls.target.clone(), p1: pos.clone(), t1: target.clone(), start: performance.now(), ms};
  invalidate();
  return new Promise(r => { anim.done = r; });
}
const VIEWS = {
  hero: () => [new THREE.Vector3(-560, 230, 500), new THREE.Vector3(0, -8, -52)],
  front: () => [new THREE.Vector3(0, 0, 640), new THREE.Vector3(0, 0, -40)],
  side: () => [new THREE.Vector3(900, 30, -58), new THREE.Vector3(0, -6, -58)],
  rear: () => [new THREE.Vector3(330, 210, -640), new THREE.Vector3(0, 0, -60)],
};
function view(name, ms) { const [p, t] = VIEWS[name](); return flyTo(p, t, ms); }
function boardCenter(R) { const [x0, y0, x1, y1] = R.b.bbox; return new THREE.Vector3(wx((x0 + x1) / 2), wy((y0 + y1) / 2), R.b.face_z_mm + R.group.position.z); }
function boardView(R, dir = new THREE.Vector3(-.22, -.5, 1)) {
  const [x0, y0, x1, y1] = R.b.bbox, size = Math.max(x1 - x0, (y1 - y0) * camera.aspect * .9, 30);
  const dist = size / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * (window.innerWidth < 900 ? 1.2 : 1.45);
  const c = boardCenter(R); return [c.clone().add(dir.normalize().multiplyScalar(dist)), c];
}

// ---------- UI: info cards ----------
const info = $('info');
function closeInfo() { info.classList.remove('show'); info.innerHTML = ''; frameOffset(); }
function meterHtml(st) {
  if (!st.trail || !st.trail.length) return '';
  const max = Math.max(...st.trail.map(t => t.open_edges));
  return `<div class="meter"><div class="bars">${st.trail.map((t, i) => `<div class="${i === st.trail.length - 1 ? 'cur' : ''}" style="height:${(t.open_edges / max * 100).toFixed(1)}%"><span>${fmt(t.open_edges)}</span></div>`).join('')}</div><div class="cap">${st.trail.map(t => `<span>${esc(t.recorded.slice(5))}</span>`).join('')}</div></div>
  <div style="color:var(--faint);font-size:10.5px">Open edges (unrouted connections) recorded at each checkpoint epoch of the current design. No total is recorded, so no percentage is shown.</div>`;
}
function showBoard(R) {
  const b = R.b, st = b.status, sides = [0, 0]; b.parts.forEach(p => sides[p[C.side]]++);
  const open = st.open_edges;
  const layersHtml = b.layers.map(ln => `<button data-layer="${esc(ln)}" aria-pressed="${state.layerOn[b.id + '|' + ln]}"><i style="background:${LAYER_TINT[ln]}"></i>${esc(ln)}</button>`).join('');
  info.innerHTML = `<button class="close" aria-label="Close">×</button>
  <h3><b>${esc(b.key)}</b>${esc(b.title)}</h3><div class="sub">${esc(b.label)} · ${esc(b.role)}</div>
  <dl>
   <dt>Status</dt><dd style="color:var(--warn)">Unvalidated draft${open ? ' · routing incomplete' : ''}</dd>
   ${st.adoption ? `<dt>Adoption</dt><dd>${esc(st.adoption)}</dd>` : ''}
   <dt>Open edges</dt><dd><b style="color:${open ? 'var(--warn)' : 'var(--ok)'}">${fmt(open)}</b>${st.rail_open_edges ? ` <span class="mono">(rails ${Object.entries(st.rail_open_edges).map(([k, v]) => k + ' ' + v).join(', ')}; AGND ${st.agnd_open_edges}; signal ${fmt(st.signal_open_edges)})</span>` : ''}<br><small style="color:var(--faint)">${esc(st.open_edges_source)}</small></dd>
   <dt>File</dt><dd class="mono">${esc(b.file)}</dd>
   <dt>SHA-256</dt><dd class="mono">${esc(b.sha256.slice(0, 16))}…</dd>
   <dt>Copper</dt><dd>${b.layers.length} layers, ${b.thickness_mm} mm</dd>
   <dt>F.Cu plane</dt><dd>z ${b.face_z_mm} mm (faces the panel); rear face ${+(b.face_z_mm - b.thickness_mm).toFixed(2)} mm</dd>
   <dt>Footprints</dt><dd>${fmt(b.counts.footprint)} (F ${fmt(sides[0])} · B ${fmt(sides[1])})</dd>
   <dt>Track segments</dt><dd>${fmt(b.counts.segment)}${b.counts.arc ? ' + ' + fmt(b.counts.arc) + ' arcs' : ''}</dd>
   <dt>Vias</dt><dd>${fmt(b.counts.via)}</dd>
   <dt>Zone fills</dt><dd>${fmt(b.counts.filled_polygon)} filled polygons in ${fmt(b.counts.zone)} zones</dd>
   ${st.remaining_issues && st.remaining_issues.length ? `<dt>Open issues</dt><dd>${st.remaining_issues.map(i => '#' + i).join(' ')}</dd>` : ''}
  </dl>
  ${meterHtml(st)}
  <div style="margin-top:12px"><div style="font:600 10px system-ui;letter-spacing:.14em;color:var(--faint);text-transform:uppercase">Layer peel</div>
   <input type="range" id="peel" min="0" max="1" step="0.01" value="${state.peel[b.id]}" aria-label="Separate copper layers">
   <div class="layers">${layersHtml}</div></div>
  <div class="note">Copper is rasterized from this file's tracks, vias, pads and zone fills (${b.ppm} px/mm). Silkscreen and mask are omitted. Not a native KiCad render.</div>`;
  info.classList.add('show'); frameOffset();
  info.querySelector('.close').onclick = () => { closeInfo(); };
  $('peel').oninput = e => setPeel(b.id, +e.target.value);
  info.querySelectorAll('[data-layer]').forEach(btn => btn.onclick = () => { const k = b.id + '|' + btn.dataset.layer; state.layerOn[k] = !state.layerOn[k]; btn.setAttribute('aria-pressed', String(state.layerOn[k])); apply(); });
}
function showPart(R, idx) {
  const b = R.b, p = b.parts[idx], fam = FAM[p[C.family]];
  const q = lockByUid[p[C.panel_uid]];
  info.innerHTML = `<button class="close" aria-label="Close">×</button>
  <h3><b>${esc(p[C.ref])}</b>${esc(p[C.value])}</h3><div class="sub">${esc(b.key)} · ${esc(b.title)} · ${p[C.side] ? 'B side (rear)' : 'F side (faces panel)'}</div>
  <dl>
   <dt>MPN</dt><dd>${esc(p[C.mpn] || '— not declared in the footprint')}</dd>
   <dt>Manufacturer</dt><dd>${esc(p[C.manufacturer] || '—')}</dd>
   <dt>Footprint</dt><dd class="mono">${esc(p[C.footprint] || '(board-only geometry)')}</dd>
   <dt>Block</dt><dd>${esc(p[C.block] || '—')}</dd>
   <dt>Position</dt><dd class="mono">panel x ${p[C.x]}, y ${p[C.y]} mm · ${p[C.rot]}°</dd>
   <dt>Extent</dt><dd>${p[C.w]} × ${p[C.h]} mm from ${esc(p[C.extent_source])}</dd>
   <dt>Display height</dt><dd>${fam.height_mm} mm (${esc(fam.label)}, illustrative)</dd>
   ${q ? `<dt>Panel feature</dt><dd>${esc(q.uid)} · locked centre (${q.x_mm}, ${q.y_mm})</dd>` : ''}
   ${p[C.dnp] ? '<dt>Fitting</dt><dd>DNP</dd>' : ''}
  </dl>
  <div class="note">${q && (fam.key === 'pot' || fam.key === 'jack') ? 'Shown with the retained third-party mesh at its locked centre; seating depth follows the component preview assumption and is not a fit claim.' : 'Body is a box over the footprint courtyard with an illustrative height.'}</div>
  <div class="row" style="margin-top:8px"><button class="btn" id="toBoard">Board card</button></div>`;
  info.classList.add('show'); frameOffset();
  info.querySelector('.close').onclick = () => { clearSelection(); closeInfo(); };
  $('toBoard').onclick = () => showBoard(R);
}

// ---------- selection ----------
const selBox = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), new THREE.LineBasicMaterial({color: '#7ff7ff', depthTest: false, transparent: true}));
selBox.renderOrder = 10; selBox.visible = false; scene.add(selBox);
const beacon = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), new THREE.MeshBasicMaterial({color: '#7ff7ff', transparent: true, opacity: .25, depthTest: false}));
beacon.renderOrder = 10; beacon.visible = false; scene.add(beacon);
function partWorld(R, idx) {
  const p = R.b.parts[idx], fam = FAM[p[C.family]], h = Math.max(fam.height_mm, .5), t = R.b.thickness_mm;
  const side = p[C.side], zf = R.b.face_z_mm + R.group.position.z, z = side ? zf - t + R.bGroup.position.z - h / 2 : zf + h / 2;
  const q = lockByUid[p[C.panel_uid]];
  if (q && (fam.key === 'pot' || fam.key === 'jack')) return {pos: new THREE.Vector3(wx(q.x_mm), wy(q.y_mm), zf + 4 + R.group.position.z * 0), size: new THREE.Vector3(fam.key === 'pot' ? 12.6 : 10.6, fam.key === 'pot' ? 11.4 : 10, 16), rot: 0, side};
  return {pos: new THREE.Vector3(wx(p[C.cx]), wy(p[C.cy]), z), size: new THREE.Vector3(Math.max(p[C.w], .4), Math.max(p[C.h], .4), h), rot: THREE.MathUtils.degToRad(p[C.rot]), side};
}
function clearSelection() { state.selected = null; selBox.visible = beacon.visible = false; invalidate(); }
function select(boardId, idx, fly = true) {
  const R = byId[boardId]; if (!R) return false;
  state.selected = {board: boardId, idx};
  if (fly && state.mode !== 'focus') { state.mode = 'focus'; state.focus = boardId; apply(); }
  else if (fly && state.focus !== boardId) { state.focus = boardId; apply(); }
  const w = partWorld(R, idx);
  selBox.position.copy(w.pos); selBox.scale.copy(w.size).addScalar(.6); selBox.rotation.set(0, 0, w.rot); selBox.visible = true;
  beacon.position.copy(w.pos); beacon.scale.setScalar(Math.max(w.size.x, w.size.y) * .9 + 1.5); beacon.visible = true;
  showPart(R, idx);
  if (fly) { const dir = new THREE.Vector3(-.25, -.35, w.side ? -1 : 1); return flyTo(w.pos.clone().add(dir.normalize().multiplyScalar(70)), w.pos, 1200); }
  invalidate(); return Promise.resolve();
}

// ---------- picking ----------
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(); let down = null;
renderer.domElement.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
  const r = renderer.domElement.getBoundingClientRect(); ndc.set(2 * (e.clientX - r.left) / r.width - 1, 1 - 2 * (e.clientY - r.top) / r.height);
  ray.setFromCamera(ndc, camera);
  const vis = pickables.filter(o => { let v = o; while (v) { if (!v.visible) return false; v = v.parent; } return true; });
  const xray = state.mode === 'xray';
  const shown = o => { let v = o; while (v) { if (!v.visible) return false; v = v.parent; } return true; };
  const barriers = xray ? [] : [panelMesh, ...boards.map(R => R.sub)].filter(o => shown(o) && (o === panelMesh || o.material.opacity >= 1));
  const hit = ray.intersectObjects([...vis, ...barriers], false)[0];
  if (hit && hit.instanceId != null && hit.object.isInstancedMesh) { const im = hit.object; select(im.userData.board, im.userData.idx[hit.instanceId], false); }
});

// ---------- search ----------
const index = [];
for (const R of boards) R.b.parts.forEach((p, i) => index.push({R, i, s: (p[C.ref] + ' ' + p[C.value] + ' ' + p[C.mpn] + ' ' + p[C.manufacturer] + ' ' + p[C.panel_uid]).toLowerCase()}));
function find(q) {
  q = q.trim().toLowerCase(); if (!q) return [];
  const exact = [], rest = [];
  for (const e of index) { const ref = e.R.b.parts[e.i][C.ref].toLowerCase(); if (ref === q) exact.push(e); else if (e.s.includes(q)) rest.push(e); }
  return exact.concat(rest);
}
$('find').addEventListener('input', e => {
  const res = find(e.target.value), box = $('results');
  box.innerHTML = res.slice(0, 40).map((r, k) => { const p = r.R.b.parts[r.i]; return `<button data-k="${k}" role="option">${esc(p[C.ref])} · ${esc(p[C.value])} <small>${esc(p[C.mpn])} · ${esc(r.R.b.key)} ${p[C.side] ? 'B' : 'F'}</small></button>`; }).join('') + (res.length > 40 ? `<small style="padding:4px">${res.length - 40} more matches</small>` : res.length ? '' : (e.target.value.trim() ? '<small style="padding:4px">No match</small>' : ''));
  box.querySelectorAll('button').forEach(b => b.onclick = () => { const r = res[+b.dataset.k]; select(r.R.b.id, r.i); });
});
$('find').addEventListener('keydown', e => { if (e.key === 'Enter') { const r = find(e.target.value)[0]; if (r) select(r.R.b.id, r.i); } });

// ---------- board list ----------
$('boardList').innerHTML = boards.map(R => {
  const st = R.b.status, open = st.open_edges;
  return `<button class="boardrow" data-id="${R.b.id}" aria-pressed="false"><span class="k">${esc(R.b.key)}</span><span class="t">${esc(R.b.title)}<small>${esc(R.b.label)} · z ${R.b.face_z_mm} · ${R.b.layers.length}L · ${fmt(R.b.counts.footprint)} fp</small></span><span class="o ${open ? 'open' : 'zero'}">${fmt(open)}</span></button>`;
}).join('');
document.querySelectorAll('.boardrow').forEach(r => r.onclick = () => focusBoard(r.dataset.id));

function setMode(m) {
  if (!['assembled', 'exploded', 'xray', 'focus'].includes(m)) throw new Error('unknown mode ' + m);
  if (m === 'focus' && !state.focus) state.focus = 'osc-core';
  if (m === 'exploded' && state.explode < .05) state.explode = .65;
  if (m === 'assembled') state.explode = 0;
  const wasFocus = state.mode === 'focus';
  state.mode = m; apply();
  if (m === 'focus') { showBoard(byId[state.focus]); const [p, t] = boardView(byId[state.focus]); return flyTo(p, t); }
  if (wasFocus) { closeInfo(); clearSelection(); return view('hero'); }
  if (m === 'exploded') return view('hero');
  return Promise.resolve();
}
function focusBoard(id) {
  const R = byId[id]; if (!R) throw new Error('unknown board ' + id);
  state.focus = id; state.mode = 'focus'; clearSelection(); apply(); showBoard(R);
  const [p, t] = boardView(R); return flyTo(p, t);
}
function setPeel(id, v) {
  const R = byId[id]; state.peel[id] = v;
  if (!R.layerLabels) R.layerLabels = R.b.layers.map((ln, i) => addLabel(ln, new THREE.Vector3(wx(R.b.bbox[0]), wy(R.b.bbox[3]), layerZ(R, i, 0)), 'layer', R.group));
  R.layerLabels.forEach((L, i) => { L.el.style.color = LAYER_TINT[R.b.layers[i]]; });
  const was = R.peeled; R.peeled = v > 0; if ($('peel') && state.focus === id) $('peel').value = v;
  apply();
  if (v > 0 && !was && state.mode === 'focus') { const [p, t] = boardView(R, new THREE.Vector3(-1, -.42, .42)); t.z -= (R.b.layers.length - 1) * peelStep(R) * v / 2; return flyTo(p, t, 1100); }
  return Promise.resolve();
}
document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => setMode(b.dataset.mode));
document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => { stopTour(); view(b.dataset.view); });
document.querySelectorAll('[data-color]').forEach(b => b.onclick = () => { state.colorBy = b.dataset.color; document.querySelectorAll('[data-color]').forEach(x => x.setAttribute('aria-pressed', String(x === b))); applyColors(); });
$('explode').oninput = e => { state.explode = +e.target.value; apply(); };
for (const [id, k] of [['showPanel', 'panel'], ['showParts', 'parts'], ['showCopper', 'copper'], ['showGhost', 'ghost']]) $(id).onchange = e => { state.show[k] = e.target.checked; apply(); };
$('railToggle').onclick = () => $('rail').classList.toggle('open');

// ---------- status banner and sources ----------
const extractedRaw = D.extracted_utc;
$('bannerText').textContent = D.status;
$('bannerMeta').textContent = `base ${D.base_commit} · data ${extractedRaw}`;
$('subtitle').textContent = `${D.boards.length} native board drafts behind one panel · ${fmt(D.totals.footprints)} footprints · ${fmt(D.totals.segments)} track segments · true depth scale`;
{
  const rows = Object.entries(D.inputs).map(([p, v]) => `<tr><td>${esc(p)}</td><td>${v.sha256.slice(0, 12)}</td><td>${(v.bytes / 1e6).toFixed(2)} MB</td></tr>`).join('');
  const ex = Object.entries(D.excluded).map(([p, why]) => `<tr><td>${esc(p)}</td><td colspan="2" style="color:var(--dim)">${esc(why)}</td></tr>`).join('');
  $('sources').innerHTML = `<button class="close btn" style="float:right" id="srcClose">Close</button><h4 style="margin-top:0">Inputs (SHA-256 prefix)</h4><table>${rows}</table>
  <h4>Excluded board files</h4><table>${ex}</table>
  <h4>Method</h4><p style="color:var(--dim);margin:0">Boards are parsed from native .kicad_pcb text in pure Python. KiCad coordinates map to the panel frame by the per-board offset recorded in each footprint's FootprintOriginMm property (${D.boards.map(b => b.key + ' ' + b.kicad_to_panel_offset_mm.join(',')).slice(0, 1)} for every board); world X = x − 159, Y = 149 − y. F.Cu faces the panel and the viewer, so no board is mirrored. KiCad render: NOT RUN (the pinned oracle needs Docker, unavailable in the build container). Base commit ${esc(D.base_commit)}; data extracted ${esc(extractedRaw)}.</p>
  <h4>Licences and model attribution</h4><pre>${esc($('licenses').textContent)}</pre>`;
  $('sourcesBtn').onclick = () => $('sources').classList.toggle('show');
  $('srcClose').onclick = () => $('sources').classList.remove('show');
}

// ---------- guided tour ----------
const K = D.boards.find(b => b.key === 'K');
const TOUR = [
  {cap: 'Panel face', text: `The 318 × 298 mm panel with its 438 fixed feature centres from the placement lock. Artwork is the retained current-panel SVG; pot and jack bodies are third-party meshes.`,
    go: () => { state.mode = 'assembled'; state.explode = 0; state.focus = null; apply(); return flyTo(new THREE.Vector3(-40, -70, 470), new THREE.Vector3(0, 0, -10), 1800); }},
  {cap: 'Stage optical board · EL', text: `EL sits at −4.2 mm, just 2.2 mm behind the panel's rear face: a 0.4 mm two-layer board carrying the twelve stage indicators and their drivers.`,
    go: () => { state.mode = 'exploded'; state.explode = .55; apply(); return flyTo(new THREE.Vector3(330, -10, 150), new THREE.Vector3(105, 30, 0), 1800); }},
  {cap: 'Jack halves and control board · JL, JR, P', text: `JL and JR at −10 mm (six layers) carry all 180 jacks and their circuits; P at −11.8 mm (four layers) carries every pot, toggle and button.`,
    go: () => { state.explode = .55; apply(); return flyTo(new THREE.Vector3(-260, -230, 230), new THREE.Vector3(-10, 10, -14), 1800); }},
  {cap: 'Octave adapters · O1–O5', text: `Five small two-layer adapters hold the rotary octave selectors, alternating between −16 mm and −29 mm so neighbouring selectors clear each other.`,
    go: () => { state.explode = .2; apply(); return flyTo(new THREE.Vector3(-210, -10, 40), new THREE.Vector3(-110, -36, -24), 1800); }},
  {cap: 'Across the gap', text: `Then about ${Math.round(D.spanMm)} mm with no board plane. Harnesses and the external inlet reservation occupy this space; neither is modelled here.`,
    go: () => { state.explode = 0; state.mode = 'assembled'; apply(); return flyTo(new THREE.Vector3(560, 60, -40), new THREE.Vector3(0, 0, -58), 2000); }},
  {cap: 'Core board · K', text: `K at −100 mm: ${fmt(K.counts.footprint)} footprints and ${fmt(K.counts.segment)} track segments over ${K.layers.length} copper layers. ${fmt(K.status.open_edges)} open edges remain, so its routing is visibly incomplete.`,
    go: () => { state.mode = 'xray'; state.focus = null; apply(); return flyTo(new THREE.Vector3(60, -250, -400), new THREE.Vector3(0, 0, -100), 2200); }},
];
let tourTimer = null;
function stopTour() { if (!state.tour) return; clearTimeout(tourTimer); state.tour = null; $('caption').classList.remove('show'); $('tourBtn').textContent = '▶ Tour'; }
async function tourStep(i) {
  if (!state.tour) return;
  if (i >= TOUR.length) { stopTour(); return; }
  state.tour.step = i; const s = TOUR[i];
  $('capStep').textContent = `${i + 1} / ${TOUR.length} · ${s.cap}`; $('capText').textContent = s.text; $('caption').classList.add('show');
  closeInfo();
  await s.go(); if (!state.tour || state.tour.step !== i) return;
  tourTimer = setTimeout(() => tourStep(i + 1), state.tour.dwell);
}
function startTour(dwell = 5200) { stopTour(); state.tour = {step: 0, dwell}; $('tourBtn').textContent = '■ Stop'; tourStep(0); }
$('tourBtn').onclick = () => state.tour ? stopTour() : startTour();
$('tourSkip').onclick = stopTour;
$('tourNext').onclick = () => { if (state.tour) { clearTimeout(tourTimer); tourStep(state.tour.step + 1); } };
addEventListener('keydown', e => { if (e.key === 'Escape') { stopTour(); $('sources').classList.remove('show'); } });
controls.addEventListener('start', () => { if (state.tour) stopTour(); anim = null; });

// ---------- render loop ----------
const tmp = new THREE.Vector3(), occ = new THREE.Raycaster();
function hiddenByPanel(world) {
  if (!panelGroup.visible || state.mode === 'xray') return false;
  const d = world.distanceTo(camera.position);
  occ.set(camera.position, tmp.copy(world).sub(camera.position).normalize()); occ.far = d - 1;
  return occ.intersectObject(panelMesh, false).length > 0;
}
function updateLabels() {
  const w = renderer.domElement.clientWidth, h = renderer.domElement.clientHeight;
  for (const L of labels) {
    let vis = L.visible && !L.suppress; let o = L.obj; while (vis && o) { if (!o.visible) vis = false; o = o.parent; }
    if (vis && L.el.classList.contains('board') && L.obj !== panelGroup) { const wp = L.pos.clone(); if (L.obj) wp.z += L.obj.position.z; if (hiddenByPanel(wp)) vis = false; }
    if (vis) { tmp.copy(L.pos); if (L.obj && L.obj !== ghost) tmp.z += L.obj.position.z; tmp.project(camera); vis = tmp.z < 1 && Math.abs(tmp.x) < 1.2 && Math.abs(tmp.y) < 1.2; }
    L.el.style.display = vis ? '' : 'none';
    if (vis) { L.el.style.left = ((tmp.x + 1) / 2 * w).toFixed(1) + 'px'; L.el.style.top = ((1 - tmp.y) / 2 * h).toFixed(1) + 'px'; }
  }
}
let frames = 0;
function loop(now) {
  requestAnimationFrame(loop);
  if (anim) {
    const k = Math.min(1, (now - anim.start) / anim.ms), e = ease(k);
    camera.position.lerpVectors(anim.p0, anim.p1, e); controls.target.lerpVectors(anim.t0, anim.t1, e);
    if (k >= 1) { const d = anim.done; anim = null; d && d(); }
    dirty = true;
  }
  if (beacon.visible) { beacon.material.opacity = .18 + .14 * Math.sin(now / 260); dirty = true; }
  if (controls.update()) dirty = true;
  if (!dirty) return;
  dirty = false; renderer.render(scene, camera); updateLabels(); frames++;
}
function frameOffset() {
  const w = stage.clientWidth, h = stage.clientHeight;
  if (w < 900) { camera.clearViewOffset(); return; }
  const left = $('rail').getBoundingClientRect().right + 8, right = info.classList.contains('show') ? w - info.getBoundingClientRect().left + 8 : 0;
  const shift = Math.round((left - right) / 2);
  camera.setViewOffset(w, h, -shift, 0, w, h); invalidate();
}
function resize() { const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); frameOffset(); invalidate(); }
new ResizeObserver(resize).observe(stage);
new ResizeObserver(() => document.documentElement.style.setProperty('--bannerH', ($('banner').offsetHeight + 8) + 'px')).observe($('banner'));
resize();

// ---------- boot ----------
const [p0, t0] = VIEWS.hero(); camera.position.copy(p0); controls.target.copy(t0); controls.update();
applyColors(); apply(); requestAnimationFrame(loop);
const ready = (async () => {
  const jobs = boards.flatMap(R => R.planes.map(m => [R, m]));
  let done = 0;
  for (const [R, m] of jobs) {
    $('loadMsg').textContent = `${R.b.key} ${m.userData.layer}`;
    const name = m.userData.file.replace(/^data\//, '');
    m.material.uniforms.map.value = await loadTexture(name);
    $('loadBar').style.width = (++done / jobs.length * 100).toFixed(0) + '%';
    await new Promise(r => setTimeout(r, 0));
  }
  await artReady;
  apply();
  $('loading').classList.add('done');
  await new Promise(r => setTimeout(r, 550)); $('loading').style.display = 'none';
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
})();

window.__preview = Object.freeze({
  ready, setMode, focusBoard, select: (board, ref) => { const R = byId[board]; const i = R ? R.b.parts.findIndex(p => p[C.ref] === ref) : -1; if (i < 0) throw new Error('no part ' + ref); return select(board, i); },
  find: q => find(q).slice(0, 50).map(r => ({board: r.R.b.id, ref: r.R.b.parts[r.i][C.ref]})),
  setExplode: v => { state.explode = v; apply(); }, setPeel, view, startTour, stopTour, setColorBy: c => document.querySelector(`[data-color="${c}"]`).click(),
  idle: () => new Promise(r => { const chk = () => (anim ? setTimeout(chk, 50) : requestAnimationFrame(() => requestAnimationFrame(r))); chk(); }),
  state: () => ({mode: state.mode, focus: state.focus, explode: state.explode, frames, boards: boards.length, instances: boards.reduce((a, R) => a + R.insts.reduce((s, m) => s + m.count, 0) + R.hw.reduce((s, m) => s + m.count, 0), 0), textures: boards.reduce((a, R) => a + R.planes.filter(m => m.material.uniforms.map.value).length, 0), triangles: renderer.info.render.triangles, tour: state.tour ? state.tour.step : null, selected: state.selected, info: info.classList.contains('show') ? info.querySelector('h3')?.textContent : null}),
  screenOf: (board, ref) => { const R = byId[board]; const i = R.b.parts.findIndex(p => p[C.ref] === ref); const w = partWorld(R, i).pos.project(camera); const r = renderer.domElement.getBoundingClientRect(); return {x: r.left + (w.x + 1) / 2 * r.width, y: r.top + (1 - w.y) / 2 * r.height}; },
  partWorld: (board, ref) => { const R = byId[board]; const i = R.b.parts.findIndex(p => p[C.ref] === ref); const w = partWorld(R, i); return {x: w.pos.x, y: w.pos.y, z: w.pos.z}; },
});
