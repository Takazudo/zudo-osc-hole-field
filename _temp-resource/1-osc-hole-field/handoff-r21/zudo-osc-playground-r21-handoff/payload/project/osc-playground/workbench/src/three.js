import * as T from '__THREE__';
import {OrbitControls} from '__ORBIT__';
/* Nominal assembly model, not imported manufacturer CAD. No copper/netlist is implied. */
const $=id=>document.getElementById(id),D=window.GRID_DATA,R=window.GridRenderer;
let world=null,settings=null,panelGroup=null,faceMaterial=null,texture=null,root=null,layers=[],exploded=false,hidePanel=false,artToken=0,pendingSVG='',lastKey='',running=false,frames=0;
const mats={pcb:new T.MeshStandardMaterial({color:0x17493c,roughness:.86}),core:new T.MeshStandardMaterial({color:0x163b37,roughness:.82}),black:new T.MeshStandardMaterial({color:0x151b19,roughness:.68}),metal:new T.MeshStandardMaterial({color:0x9da89f,roughness:.44,metalness:.6}),gold:new T.MeshStandardMaterial({color:0xc6a35e,roughness:.35,metalness:.7}),red:new T.MeshStandardMaterial({color:0xb83d37,roughness:.5}),white:new T.MeshStandardMaterial({color:0xecefe2,roughness:.4}),cap:new T.MeshStandardMaterial({color:0x775a30,roughness:.8})};
function geoBox(g,w,h,z,x,y,zz,mat=mats.black){let o=new T.Mesh(new T.BoxGeometry(w,h,z),mat);o.position.set(x,y,zz);g.add(o);return o;}
function cyl(g,r,h,x,y,z,mat=mats.metal,segments=20){let o=new T.Mesh(new T.CylinderGeometry(r,r,h,segments),mat);o.rotation.x=Math.PI/2;o.position.set(x,y,z);g.add(o);return o;}
function xy(p){let d=R.dims(settings);return [p.x-d.w/2,d.h/2-p.y];}
function newLayer(name,z,lift){let g=new T.Group();g.name=name;g.position.z=z;g.userData={z,lift};root.add(g);layers.push(g);return g;}
function boardRect(name,x0,y0,w,h,z,lift){let g=newLayer(name,z,lift),a=xy({x:x0+w/2,y:y0+h/2});geoBox(g,w,h,1.6,a[0],a[1],-.8,mats.pcb);return g;}
function panelShape(){let d=R.dims(settings),s=new T.Shape();s.moveTo(-d.w/2,-d.h/2);s.lineTo(d.w/2,-d.h/2);s.lineTo(d.w/2,d.h/2);s.lineTo(-d.w/2,d.h/2);s.closePath();for(const q of [...D.ports,...D.controls]){let p=R.pos(q,settings),[x,y]=xy(p),r=q.kind==='jack'?3.1:q.kind==='switch'?2.6:q.kind==='button'?2.5:3.15;let hole=new T.Path();hole.absarc(x,y,r,0,Math.PI*2,true);s.holes.push(hole);}return s;}
function uvAbsolute(g){const a=g.attributes.position,uv=g.attributes.uv,d=R.dims(settings);for(let i=0;i<a.count;i++)uv.setXY(i,(a.getX(i)+d.w/2)/d.w,(a.getY(i)+d.h/2)/d.h);uv.needsUpdate=true;}
function label(g,text,x,y,z){const c=document.createElement('canvas');c.width=512;c.height=96;let k=c.getContext('2d');k.clearRect(0,0,512,96);k.fillStyle='#d4d8c5';k.font='bold 27px sans-serif';k.textAlign='center';k.fillText(text,256,60);let tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;let m=new T.Mesh(new T.PlaneGeometry(58,10.8),new T.MeshBasicMaterial({map:tx,transparent:true,depthWrite:false}));m.position.set(x,y,z);g.add(m);}
function chip(g,name,x,y,w,h,height,pins=14){let a=xy({x,y});geoBox(g,w,h,height,a[0],a[1],height/2,mats.black);let cnt=pins/2;for(let i=0;i<cnt;i++){const yy=a[1]-h*.39+i*(h*.78/(cnt-1));for(let side of [-1,1])geoBox(g,1.1,.3,.2,a[0]+side*(w/2+.5),yy,.12,mats.metal);}let dot=cyl(g,.35,.06,a[0]-w*.28,a[1]+h*.27,height+.04,mats.white,12);dot.name=name;return g;}
function disposeScene(){if(!root)return;root.traverse(o=>{o.geometry?.dispose();for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m?.map?.isTexture&&m!==faceMaterial)m.map.dispose();});root.removeFromParent();layers=[];}
function build(s){settings=structuredClone(s);if(!world)return;disposeScene();root=new T.Group();world.scene.add(root);let d=R.dims(settings),px=s.px,py=s.py,c=d.ctop;lastKey=`${px}/${py}`;
 panelGroup=newLayer('Front panel',0,115);faceMaterial=new T.MeshStandardMaterial({color:0xffffff,roughness:.72,metalness:.12});let shape=panelShape();let topGeo=new T.ShapeGeometry(shape,12);uvAbsolute(topGeo);let top=new T.Mesh(topGeo,faceMaterial);top.position.z=1.6;panelGroup.add(top);
 // Extruded sidewalls only: there is no nearly-coplanar cap underneath the artwork.
 let ext=new T.ExtrudeGeometry(shape,{depth:1.6,bevelEnabled:false,curveSegments:12});let invisible=new T.MeshBasicMaterial({visible:false});panelGroup.add(new T.Mesh(ext,[invisible,mats.black]));
 let J=boardRect('J · jack board',6,22,18*px,10*py,-10,68);
 let O=boardRect('O · octave strip',7,c-3.5,5*px-2,py+7,-10.6,52);
 let OS=boardRect('OS · OSC selectors',7,c+py+3.6,5*px-2,2*py-3.8,-11.5,48);
 let OP=boardRect('OP · OSC pots',7,c+3*py+.1,5*px-2,5*py-1.1,-13,43);
 let MP=newLayer('MP · filters, mixers, folders',-13,43);
 // Shared L-shaped pot board. Space below FILTER is used by two small UI strips.
 let mshape=new T.Shape(),points=[[6+5*px,c],[6+12*px,c],[6+12*px,c+8*py],[6+8*px,c+8*py],[6+8*px,c+6*py],[6+5*px,c+6*py]];points.forEach((p,i)=>{let a=xy({x:p[0]+.25,y:p[1]+.25});i?mshape.lineTo(...a):mshape.moveTo(...a);});mshape.closePath();let mpmesh=new T.Mesh(new T.ExtrudeGeometry(mshape,{depth:1.6,bevelEnabled:false}),mats.pcb);mpmesh.position.z=-1.6;MP.add(mpmesh);
 let ES=boardRect('ES · envelope selectors',6+12*px,c,6*px,3*py,-11.5,48);
 let ET=boardRect('ET · envelope triggers',6+12*px,c+3*py+1,6*px,py-2,-4.5,75);
 let EP=boardRect('EP · envelope / offset pots',6+12*px,c+4*py+1,6*px,4*py-2,-13,43);
 let UT=boardRect('UT · S&H buttons',6+5*px,c+6*py+1,2*px,py-2,-4.5,75);
 let UP=boardRect('UP · two S&H slew pots / local lag circuits',6+7*px+.5,c+6*py+1,px-1,2*py-2,-13,43);
 let US=boardRect('US · A/B selectors',6+5*px,c+7*py+1,2*px,py-2,-11.5,48);
 for(const q of D.ports){let p=R.pos(q,s),[x,y]=xy(p);geoBox(J,9.5,10,8,x,y,4,mats.black);cyl(J,2.9,5.2,x,y,10.55,mats.metal);cyl(J,4.15,1.35,x,y,12.3,q.direction==='out'?mats.red:mats.black);cyl(J,2.48,.12,x,y,13.04,mats.black);cyl(J,1.65,.13,x,y,13.11,mats.black);}
 for(const q of D.controls){let p=R.pos(q,s),[x,y]=xy(p),b;
 if(q.block.startsWith('O'))b=q.kind==='octave'?O:q.kind==='switch'?OS:OP;
 else if(q.block.startsWith('E'))b=q.kind==='switch'?ES:q.kind==='button'?ET:EP;
 else if(q.block.startsWith('A'))b=EP;
 else if(q.block.startsWith('H'))b=q.kind==='pot'?UP:UT;else if(q.block.startsWith('X'))b=US;else b=MP;
 if(q.kind==='pot'){geoBox(b,10,10,6.8,x,y,3.4,mats.black);cyl(b,3,12.5,x,y,13.05,mats.black);}
 else if(q.kind==='octave'){geoBox(b,16.2,18.5,7.5,x,y,3.75,mats.black);cyl(b,3.0,12.5,x,y,13.75,mats.metal);cyl(b,4,5,x,y,19.2,mats.black);}
 else if(q.kind==='switch'){geoBox(b,8.13,5.08,8.64,x,y,4.32,mats.black);cyl(b,2.5,5.5,x,y,10.8);cyl(b,4.04,1.5,x,y,13.85,mats.metal,6);let lever=new T.Mesh(new T.CylinderGeometry(.9,.95,9,12),mats.metal);lever.rotation.x=Math.PI/2;let v=R.state(q,s);lever.rotation.z=(v===1&&q.positions.length===3)?0:(v===0?-.24:.24);lever.position.set(x,y,18.6);b.add(lever);}
 else {geoBox(b,6,6,5,x,y,2.5,mats.black);cyl(b,2.5,4.0,x,y,6.1,mats.black);}
 }
 const K=newLayer('K · core / new utility allocation',-24,0),kx=12,ky=16,kw=d.w-24,kh=d.h-28;
 let ks=new T.Shape();let kp=[[kx,ky],[kx+kw,ky],[kx+kw,ky+kh],[kx,ky+kh]];kp.forEach((p,i)=>{let a=xy({x:p[0],y:p[1]});i?ks.lineTo(...a):ks.moveTo(...a);});ks.closePath();let hh=new T.Path(),hp=[[18,25],[18,123],[142,123],[142,25]];hp.forEach((p,i)=>{let a=xy({x:p[0],y:p[1]});i?hh.lineTo(...a):hh.moveTo(...a);});hh.closePath();ks.holes.push(hh);let km=new T.Mesh(new T.ExtrudeGeometry(ks,{depth:1.6,bevelEnabled:false}),mats.core);km.position.z=-1.6;K.add(km);
 // The following are package allocations, not a complete BOM or native CAD placement.
 const alloc=[];function place(id,xx,yy,w,h,z,pins){chip(K,id,xx,yy,w,h,z,pins);alloc.push({id,x:xx,y:yy,w,h,height:z,kind:'package allocation; no netlist'});}
 for(let i=0;i<5;i++){let xx=27+i*24;place('OSC'+(i+1)+' / AS3340D',xx,146,3.9,9.9,1.75,16);place('OSC'+(i+1)+' / shaping TL074',xx,162,3.9,8.65,1.75,14);}
 for(let i=0;i<6;i++){let xx=160+i*23;place('ENV'+(i+1)+' / analogue allocation',xx,47,3.9,8.65,1.75,14);place('ENV'+(i+1)+' / comparator',xx,62,3.9,5,1.75,8);}
 for(let i=0;i<3;i++){let xx=164+i*33;place('VCF'+(i+1)+' / LM13700',xx,94,3.9,9.9,1.75,16);place('VCF'+(i+1)+' / TL074',xx+13,105,3.9,8.65,1.75,14);}
 for(let i=0;i<2;i++){let xx=154+i*30;place('S&H'+(i+1)+' / LF398M',xx,145,3.9,8.65,1.75,14);let a=xy({x:xx+7,y:144});geoBox(K,2,1.25,1.2,...a,.6,mats.cap);place('MULT / OPA4197 '+i,xx,165,4.4,5,1.2,14);}
 place('S&H / CD74HC221',218,147,3.9,9.9,1.75,16);place('S&H / LM393',234,147,3.9,5,1.75,8);place('A/B / buffers',260,151,3.9,8.65,1.75,14);place('A/B / buffers',278,151,3.9,8.65,1.75,14);
 for(let i=0;i<4;i++)place('MIX analogue allocation '+i,50+i*30,194,3.9,8.65,1.75,14);
 for(let i=0;i<6;i++)place('AO/output allocation '+i,160+i*23,197,3.9,8.65,1.75,14);
 // Sparse supporting-space markers, deliberately not pretending to be a full passive BOM.
 for(const q of alloc){for(let j=0;j<4;j++){let [x,y]=xy({x:q.x-5+j*3,y:q.y+7});geoBox(K,1.6,.8,.6,x,y,.3,mats.cap);}}
 for(let cc of [22,d.w/2,d.w-30]){let [x,y]=xy({x:cc,y:d.h-20});geoBox(K,20,5,5,x,y,2.5,mats.black);}
 let P=boardRect('P/B · power pocket reservation',25,31,110,85,-32,12),a=xy({x:79,y:72});label(P,'zudo-pd · ENVELOPE ONLY',a[0],a[1],.15);geoBox(P,30,30,11,a[0]-25,a[1]+15,5.5,mats.black);geoBox(P,27,40,1.6,a[0]+26,a[1],11.1,mats.pcb);
 let kl=xy({x:d.w/2,y:d.h-40});label(K,'CORE / PACKAGE ALLOCATION ONLY',kl[0],kl[1],.15);
 // Under the new pot strip: local RC high-impedance nodes must not cross connectors.
 // Back-side envelopes only; this is not an accepted routed footprint arrangement.
 {let xx=6+7.5*px,yy=c+7*py,a=xy({x:xx,y:yy});geoBox(UP,4.4,5,1.2,...a,-2.2,mats.black);alloc.push({id:'SLEW dual-cell / OPA4197IPWR',board:'UP',x:xx,y:yy,w:4.4,h:5,height:1.2,face:'rear',kind:'package allocation; no netlist'});
 for(let channel=0;channel<2;channel++)for(let k=0;k<5;k++){let p=xy({x:xx-5+k*2.5,y:yy+(channel?8:-8)});geoBox(UP,1.6,3.2,1.2,...p,-2.2,mats.cap);}}
 window.GRID_3D_ALLOCATION=alloc;window.GRID_3D_LAYERS=layers.map(g=>({name:g.name,z:g.userData.z}));applyPose();if(pendingSVG)artwork(pendingSVG);else artwork(R.render(D,s,{artOnly:true}).svg);camera('iso');dirty();
}
function applyPose(){for(const g of layers)g.position.z=g.userData.z+(exploded?g.userData.lift:0);if(panelGroup)panelGroup.visible=!hidePanel;dirty();}
function dirty(){if(!world||running)return;running=true;requestAnimationFrame(draw);}
function draw(){if(!world)return;const moved=world.controls.update();world.renderer.render(world.scene,world.camera);frames++;window.GRID_3D_FRAME=frames;running=false;if(moved)dirty();}
function resize(){if(!world)return;const el=$('three'),w=el.clientWidth,h=Math.max(460,el.clientHeight);world.renderer.setSize(w,h,false);world.camera.aspect=w/h;world.camera.updateProjectionMatrix();dirty();}
function ensure(s){if(!world){try{const el=$('three'),renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.6));renderer.setClearColor(0x26302e);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;el.replaceChildren(renderer.domElement);const scene=new T.Scene(),camera=new T.PerspectiveCamera(32,1,10,2400);camera.up.set(0,0,1);scene.add(new T.HemisphereLight(0xfafbe8,0x536b62,2.8));let key=new T.DirectionalLight(0xffffff,2.9);key.position.set(-250,-100,600);scene.add(key);let fill=new T.DirectionalLight(0xe1eaf6,1.5);fill.position.set(300,250,200);scene.add(fill);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.12;controls.minDistance=70;controls.maxDistance=1500;controls.addEventListener('change',dirty);world={renderer,scene,camera,controls};new ResizeObserver(resize).observe(el);build(s);resize();window.GRID_3D_READY=true;}catch(e){$('three').textContent='3D unavailable: '+e.message+'. The flat editor and SVG exports still work.';console.error(e);}}else{settings=structuredClone(s);if(lastKey!==`${s.px}/${s.py}`)build(s);resize();}}
function artwork(svg){pendingSVG=svg;if(!world||!faceMaterial)return;let token=++artToken,url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'})),im=new Image();im.onload=()=>{URL.revokeObjectURL(url);if(token!==artToken)return;const d=R.dims(settings),c=document.createElement('canvas');c.width=Math.round(d.w*6);c.height=Math.round(d.h*6);let ctx=c.getContext('2d');ctx.drawImage(im,0,0,c.width,c.height);texture?.dispose();texture=new T.CanvasTexture(c);texture.colorSpace=T.SRGBColorSpace;texture.anisotropy=world.renderer.capabilities.getMaxAnisotropy();faceMaterial.map=texture;faceMaterial.needsUpdate=true;dirty();};im.onerror=()=>{URL.revokeObjectURL(url);console.warn('Panel texture could not load');};im.src=url;}
function camera(name){if(!world)return;let d=R.dims(settings),target=new T.Vector3(0,0,exploded?25:-9),dist=Math.max(d.w,d.h)*(exploded?2.65:2.28);world.controls.target.copy(target);let vector=name==='top'?new T.Vector3(0,-.001,1):name==='side'?new T.Vector3(1,-.03,.03):name==='rear'?new T.Vector3(0,.001,-1):new T.Vector3(1,-1.25,1.7);world.camera.position.copy(target).add(vector.normalize().multiplyScalar(dist));world.camera.up.set(0,0,1);if(name==='top'||name==='rear')world.camera.up.set(0,1,0);world.controls.update();dirty();}
window.Grid3D={ensure,rebuild(s){settings=structuredClone(s);if(world&&lastKey!==`${s.px}/${s.py}`)build(s);},artwork,resize,camera,explode(v){exploded=v;applyPose();camera('iso');},hidePanel(v){hidePanel=v;applyPose();},savePNG(){if(world){world.renderer.render(world.scene,world.camera);const a=document.createElement('a');a.download='zudo-grid-r20-assembly.png';a.href=world.renderer.domElement.toDataURL('image/png');a.click();}},state(){return{ready:!!world,frames,lastKey,exploded,hidePanel,corePlane:-24};}};
if(['three','split'].includes(document.querySelector('[data-tab][aria-pressed="true"]')?.dataset.tab))ensure(window.getGridSettings());
