import * as T from '__THREE__';
import {OrbitControls} from '__ORBIT__';
const D=window.REVIEW_DATA,el=document.getElementById('view');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0x101a24);el.append(renderer.domElement);
const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,1,3000);camera.up.set(0,0,1);scene.add(new T.HemisphereLight(0xffffff,0x324354,2.5));const light=new T.DirectionalLight(0xffffff,2.5);light.position.set(0,-400,700);scene.add(light);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;
const colors={panel:0x7d8d99,front:0x54bca0,middle:0x63b3ec,rear:0xc497ef,carriers:0xe5b862,connectors:0xf5d494,earlier:0x8595a5,routes:0xff7d6b,cover:0x6b8497};
const groups={};for(const k of Object.keys(colors)){groups[k]=new T.Group();scene.add(groups[k]);}
const toV=p=>new T.Vector3(p[0]-159,149-p[1],p[2]);
const objects=[];
function rect(name,bb,zz,layer,status,wire=false){const [x0,y0,x1,y1]=bb,[z0,z1]=zz;let geo=new T.BoxGeometry(x1-x0,y1-y0,Math.max(.05,z1-z0));let o;
 if(wire)o=new T.LineSegments(new T.EdgesGeometry(geo),new T.LineBasicMaterial({color:colors[layer],transparent:true,opacity:.65}));
 else o=new T.Mesh(geo,new T.MeshStandardMaterial({color:colors[layer],roughness:.65,transparent:true,opacity:layer==='connectors'?.65:.9}));
 o.position.copy(toV([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]));o.userData={name,status};groups[layer].add(o);objects.push(o);
 if(!wire){const edge=new T.LineSegments(new T.EdgesGeometry(geo),new T.LineBasicMaterial({color:0xd1e1ec,transparent:true,opacity:.25}));o.add(edge);}return o;}
// Panel is a zero-thickness reference, not a newly chosen manufacturing thickness.
rect('Fixed panel reference',[0,0,318,298],[0,0],'panel','Fixed 318 × 298 mm reference; marker size is illustrative',true);
const face=new T.Mesh(new T.PlaneGeometry(318,298),new T.MeshBasicMaterial({color:0x344350,transparent:true,opacity:.12,side:T.DoubleSide,depthWrite:false}));groups.panel.add(face);
for(const p of D.placements){const radius=p.kind==='led'?.55:1.25;const o=new T.Mesh(new T.CircleGeometry(radius,12),new T.MeshBasicMaterial({color:p.kind==='jack'?0xd8e4e8:p.kind==='led'?0xf5c25d:0x65c7b2,side:T.DoubleSide}));o.position.copy(toV([p.x_mm,p.y_mm,.1]));groups.panel.add(o);}
for(const b of D.boxes)rect(b.name,b.xy,b.z,b.layer,b.status,b.layer==='earlier');
for(const r of D.routes){const geo=new T.BufferGeometry().setFromPoints(r.points.map(toV));const line=new T.Line(geo,new T.LineBasicMaterial({color:colors.routes}));line.userData={name:r.name+' / '+r.design_length_mm+' mm design length',status:r.status};groups.routes.add(line);objects.push(line);}
rect('Existing study cover reference',[0,0,318,298],[105,105],'cover','z105 depth reference, not an enclosure solid',true);
// Explicit dimensions only: no invented shell origin or wall thickness.
const ray=new T.Raycaster();ray.params.Line.threshold=1;const mouse=new T.Vector2();el.addEventListener('pointermove',e=>{const a=el.getBoundingClientRect();mouse.set((e.clientX-a.left)/a.width*2-1,-(e.clientY-a.top)/a.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(objects,false).find(h=>h.object.visible&&h.object.parent.visible);document.getElementById('inspect').textContent=hit?hit.object.userData.name+' — '+hit.object.userData.status:'Drag to orbit · wheel to zoom · hover to inspect source status';});
function label(text,pos,color){const c=document.createElement('canvas');c.width=512;c.height=80;const ctx=c.getContext('2d');ctx.fillStyle='#'+color.toString(16);ctx.font='bold 26px sans-serif';ctx.fillText(text,12,46);const m=new T.SpriteMaterial({map:new T.CanvasTexture(c),depthTest:false,transparent:true});const s=new T.Sprite(m);s.position.copy(toV(pos));s.scale.set(105,16,1);scene.add(s);return s;}
const labels=[label('PANEL / FIXED XY',[70,310,0],0xa6baca),label('A01 FRONT',[190,185,35],colors.front),label('A01 MIDDLE',[300,130,50],colors.middle),label('A01 CORE',[275,285,75],colors.rear)];
let exploded=false;
function pose(){for(const [k,g] of Object.entries(groups)){g.position.z=exploded?({front:35,middle:85,rear:145}[k]||0):0;const box=document.querySelector('[data-layer="'+k+'"]');g.visible=box?box.checked:true;if(exploded&&['routes','connectors','carriers','cover','earlier'].includes(k))g.visible=false;}
 labels[1].position.z=35+(exploded?35:0);labels[2].position.z=50+(exploded?85:0);labels[3].position.z=75+(exploded?145:0);labels[0].visible=groups.panel.visible;labels[1].visible=groups.front.visible;labels[2].visible=groups.middle.visible;labels[3].visible=groups.rear.visible;
 document.getElementById('mode').textContent=exploded?'EXPLODED — display offsets only; connectors, routes, carriers and cover hidden':'INSTALLED REFERENCE — proposed geometry; no fit qualification';render();}
function view(name){const target=name==='a01'?toV([254,208,60]):new T.Vector3(0,0,exploded?100:45);controls.target.copy(target);const v=name==='front'?new T.Vector3(0,0,1):name==='side'?new T.Vector3(1,0,.06):new T.Vector3(1,-1.35,1.45);camera.up.set(0,name==='front'?1:0,name==='front'?0:1);camera.position.copy(target).add(v.normalize().multiplyScalar(name==='a01'?420:850));controls.update();render();}
function render(){renderer.render(scene,camera);window.REVIEW_FRAMES=(window.REVIEW_FRAMES||0)+1;}
function resize(){renderer.setSize(el.clientWidth,el.clientHeight);camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();render();}
new ResizeObserver(resize).observe(el);controls.addEventListener('change',render);document.querySelectorAll('[data-layer]').forEach(e=>e.onchange=pose);document.querySelectorAll('[data-camera]').forEach(e=>e.onclick=()=>view(e.dataset.camera));document.getElementById('explode').onchange=e=>{exploded=e.target.checked;pose();view('iso');};document.getElementById('save').onclick=()=>{render();const a=document.createElement('a');a.download='osc-structure-review.png';a.href=renderer.domElement.toDataURL('image/png');a.click();};
window.ReviewView={pose,view,groups,project:p=>toV(p).project(camera).toArray(),state:()=>({ready:true,exploded,boxes:D.boxes.length,markers:D.placements.length,routes:D.routes.length,visible:Object.entries(groups).filter(([k,g])=>g.visible).map(([k])=>k)})};pose();resize();view('iso');window.REVIEW_READY=true;
