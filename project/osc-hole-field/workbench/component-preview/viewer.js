import * as THREE from '__THREE__';
import {OrbitControls} from '__ORBIT__';
const data=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);
const scene=new THREE.Scene();scene.background=new THREE.Color('#172229');
const view=$('view'),renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));view.append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(40,1,.1,3000);camera.up.set(0,1,0);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;
scene.add(new THREE.HemisphereLight(0xe5f4ff,0x53616a,2.5));
for(const [x,y,z] of [[150,220,400],[-200,-100,-300]]){const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(x,y,z);scene.add(light);}
const mat=(c,metal=0)=>new THREE.MeshStandardMaterial({color:c,metalness:metal,roughness:.5});
const bodyMat=mat('#88673e'),shaftMat=mat('#657463'),metalMat=mat('#bbc7c9',.55),blackMat=mat('#273039'),capMat=mat('#d5a64d'),approxMat=mat('#6498ad');
const panelGroup=new THREE.Group(),componentGroup=new THREE.Group();scene.add(panelGroup,componentGroup);
const shape=new THREE.Shape();shape.moveTo(-159,-149);shape.lineTo(159,-149);shape.lineTo(159,149);shape.lineTo(-159,149);shape.closePath();
for(const q of data.lock.placements){const hole=new THREE.Path();hole.absarc(q.x_mm-159,149-q.y_mm,(q.kind==='led'?data.params.indicator_window.diameter_mm:q.hole_d_mm)/2,0,Math.PI*2,true);shape.holes.push(hole);}
// Put artwork on the panel's own front triangles. A separate plane 0.02 mm
// above this face competed for depth at orbit distances on 24-bit buffers.
const panelGeometry=new THREE.ExtrudeGeometry(shape,{depth:2,bevelEnabled:false,curveSegments:12});
const panelPositions=panelGeometry.attributes.position,panelUV=panelGeometry.attributes.uv;
panelGeometry.clearGroups();let panelStart=0,panelRole=-1;
for(let i=0;i<panelPositions.count;i++)panelUV.setXY(i,(panelPositions.getX(i)+159)/318,(panelPositions.getY(i)+149)/298);
for(let i=0;i<panelPositions.count;i+=3){
 const role=[0,1,2].every(j=>panelPositions.getZ(i+j)===2)?0:1;
 if(role!==panelRole){if(i)panelGeometry.addGroup(panelStart,i-panelStart,panelRole);panelStart=i;panelRole=role;}
}
panelGeometry.addGroup(panelStart,panelPositions.count-panelStart,panelRole);
const artworkMaterial=new THREE.MeshBasicMaterial({color:'#273332'});
const panel=new THREE.Mesh(panelGeometry,[artworkMaterial,mat('#273332',.15)]);panel.position.z=-2;panelGroup.add(panel);
const artImage=new Image();artImage.onload=()=>{
 const canvas=document.createElement('canvas');canvas.width=1272;canvas.height=1192;
 canvas.getContext('2d').drawImage(artImage,0,0,1272,1192);
 const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;
 artworkMaterial.map=tex;artworkMaterial.color.set('#ffffff');artworkMaterial.needsUpdate=true;draw();
};artImage.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(data.artwork)));
function meshGeometry(s,transform){const g=new THREE.BufferGeometry(),a=[];for(let i=0;i<s.positions.length;i+=3)a.push(...transform(...s.positions.slice(i,i+3)));g.setAttribute('position',new THREE.Float32BufferAttribute(a,3));g.setIndex(s.indices);g.computeVertexNormals();return g;}
const potGeo=meshGeometry(data.meshes.pot.solids[0],(x,y,z)=>[x-6.9960603727775,y-2.5,z-9.89]);
// Material grouping preserves the original tessellated solid; no geometric substitution.
const pos=potGeo.attributes.position,idx=potGeo.index;let start=0,last=-1;
for(let i=0;i<idx.count;i+=3){const role=[0,1,2].every(j=>pos.getZ(idx.getX(i+j))>=-2.001)?1:0;if(role!==last){if(i)potGeo.addGroup(start,i-start,last);start=i;last=role;}}
potGeo.addGroup(start,idx.count-start,last);
const jackGeo=data.meshes.jack.solids.map(s=>meshGeometry(s,(x,y,z)=>[x-.8,-z,y-12]));
const groups=[],caps=[];
function cylinder(parent,r,z0,z1,material){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,z1-z0,32),material);m.rotation.x=Math.PI/2;m.position.z=(z0+z1)/2;parent.add(m);return m;}
function box(parent,w,h,d,x,y,z,material){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);m.position.set(x,y,z);parent.add(m);return m;}
for(const q of data.lock.placements){
 const g=new THREE.Group();g.position.set(q.x_mm-159,149-q.y_mm,0);g.rotation.z=-THREE.MathUtils.degToRad(q.rot_deg||0);g.userData={...q,electrical:data.electrical[q.uid]};componentGroup.add(g);groups.push(g);
 if(q.kind==='pot'){
  g.add(new THREE.Mesh(potGeo,[bodyMat,shaftMat]));const cap=cylinder(g,1,1,11,capMat);cap.visible=false;caps.push(cap);
  g.userData.fidelity='Drawing-derived PTV09A-4F L20 STEP; common package geometry across B103/B104/B504. Body brown, insulated shaft green; color illustrative. Front seating at z=-2 is assumed; no cap selected.';
 }else if(q.kind==='jack'){
  jackGeo.forEach((geo,i)=>g.add(new THREE.Mesh(geo,i===0?blackMat:metalMat)));
  g.userData.fidelity='Jolin WQP518MA third-party STEP; port centre x=0.8, raw y axis toward front. Body face at z=-2 assumed. Nut omitted; nut selection and assembly not qualified.';
 }else if(q.kind==='octave'){
  const inst=data.selector.instances.find(i=>i.uid===q.uid),z=inst.pcb_z_mm;g.rotation.z=-THREE.MathUtils.degToRad(inst.rotation_deg);
  box(g,16.2,18.5,7.5,0,1.25,z+3.75,approxMat);cylinder(g,4.5,z+7.5,z+14.5,metalMat);cylinder(g,3,z+14.5,z+22.5,shaftMat);
  if(inst.extension_length_mm){cylinder(g,5,z+16,z+22.5,capMat);cylinder(g,3,z+22.5,z+35.5,capMat);}
  cylinder(g,4,1,10,capMat);
  g.userData.fidelity='ALPS SRBV160803: dimension envelope, not native CAD. Existing OSC-KNOB-8-R1 custom draft Ø8 cap, no purchased MPN. PCB z='+z+' mm; existing extension '+inst.extension_length_mm+' mm. No retention qualification.';
 }else if(q.kind==='switch'){
  box(g,7,13,9,0,0,-6.5,approxMat);cylinder(g,3,-2,3,metalMat);const lever=cylinder(g,1.2,3,12,metalMat);lever.rotation.y=.25;
  g.userData.fidelity='Toggle visual substitute only: body 7×13×9, stem Ø2.4; illustrative dimensions/pose, not exact CAD or clearance evidence.';
 }else if(q.kind==='button'){
  box(g,6,6,3.5,0,0,-3.75,approxMat);cylinder(g,1.75,-2,1.5,blackMat);
  g.userData.fidelity='Omron B3F-1020 visual substitute: nominal 6×6 body. Seating and actuator rendering illustrative; no manufacturer CAD.';
 }else{
  cylinder(g,data.params.indicator_window.diameter_mm/2,-2,.3,q.led_type==='clip'?mat('#88473e'):shaftMat);
  g.userData.fidelity='Locked LED window diameter; unlit lens visual substitute. Package, lead geometry and seating omitted.';
 }
}
function visibility(){panelGroup.visible=$('panel').checked;componentGroup.visible=$('components').checked;for(const g of groups)g.visible=$(g.userData.kind==='pot'?'pots':g.userData.kind==='jack'?'jacks':'others').checked;const d=Number($('caps').value);for(const c of caps){c.visible=d>0;c.scale.set(d/2,1,d/2);}draw();}
for(const id of ['panel','components','pots','jacks','others','caps'])$(id).onchange=visibility;
function preset(name){controls.target.set(0,0,0);camera.up.set(0,1,0);if(name==='front')camera.position.set(0,0,540);else if(name==='back')camera.position.set(0,0,-540);else camera.position.set(330,250,390);controls.update();}
for(const id of ['front','back','orbit'])$(id).onclick=()=>preset(id);
$('pot-detail').onclick=()=>{const g=groups.find(g=>g.userData.kind==='pot');controls.target.copy(g.position);camera.position.copy(g.position).add(new THREE.Vector3(36,22,44));controls.update();inspect(g);};
function inspect(g){const q=g.userData,e=q.electrical;$('inspect').textContent=`${q.uid} · ${q.ref}\n${e.mpn||e.value}\nFixed centre (${q.x_mm}, ${q.y_mm}) mm\n${q.fidelity}${q.kind==='pot'?'\nMechanical lock label: '+q.component+' (mechanical reference only); electrical selection above.':''}`;}
const ray=new THREE.Raycaster();let down;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const b=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2(2*(e.clientX-b.left)/b.width-1,1-2*(e.clientY-b.top)/b.height),camera);const hits=ray.intersectObjects(groups.filter(g=>g.visible&&componentGroup.visible),true).filter(h=>h.object.visible);const barrier=panelGroup.visible?ray.intersectObject(panel,false)[0]:null;if(hits.length&&(!barrier||hits[0].distance<barrier.distance)){let o=hits[0].object;while(!o.userData.uid&&o.parent)o=o.parent;if(o.userData.uid)inspect(o);}});
new ResizeObserver(()=>{const w=view.clientWidth,h=view.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();draw();}).observe(view);
let frames=0;
function draw(){renderer.render(scene,camera);frames++;}
controls.addEventListener('change',draw);
preset('orbit');visibility();$('inspect').textContent='438 fixed features loaded. Click a component for current electrical identity and model limitations.';

window.ComponentPreview=Object.freeze({features:()=>groups.map(g=>({uid:g.userData.uid,x:g.userData.x_mm,y:g.userData.y_mm,worldX:g.position.x,worldY:g.position.y,kind:g.userData.kind,mpn:g.userData.electrical.mpn})),state:()=>({frames,caps:caps.filter(c=>c.visible).length,panel:panelGroup.visible,components:componentGroup.visible,visible:groups.filter(g=>g.visible).length,triangles:renderer.info.render.triangles}),preset});
