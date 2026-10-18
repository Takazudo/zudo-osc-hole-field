/* Appearance-only adapter for the existing GridRenderer. No layout import path. */
(function(){
'use strict';
const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const deepFreeze=o=>{if(o&&typeof o==='object'){Object.values(o).forEach(deepFreeze);Object.freeze(o);}return o;};
const source=deepFreeze(JSON.parse($('source-data').textContent));
window.GRID_ICONS=source.icons;
const base=deepFreeze({labelModule:source.profile.labelModule,labelKnob:source.profile.labelKnob,labelJack:source.profile.labelJack,labelSwitch:source.profile.labelSwitch,separatorGap:source.profile.separatorGap,lineWeight:1,font:'Arial',whiteVisible:true,goldVisible:true,whiteColor:'#edece5',goldColor:'#c6a35e',relations:true,ledStyle:'line',hardwareVisible:true,hardwareJacks:true,hardwareKnobs:true,hardwareSwitches:true,hardwareLEDs:true,exportMode:'artwork',icons:{},offsets:{}});
const limits={labelModule:[.8,2.6],labelKnob:[.8,2.6],labelJack:[.8,2.6],labelSwitch:[.6,1.6],separatorGap:[0,5],lineWeight:[.5,2]};
const diam=Object.fromEntries(source.lock.placements.filter(q=>q.kind!=='led').map(q=>[q.uid,q.hole_d_mm]));
let current=structuredClone(base),labels=[],selected='label-0000',zoom=1,tx=0,ty=0,isFit=true,drag=null;
const status=(s,error=false)=>{$('status').textContent=s;$('status').classList.toggle('error',error);};
function keys(o,allowed,name){if(!o||typeof o!=='object'||Array.isArray(o)||Object.getPrototypeOf(o)!==Object.prototype)throw Error(name+' must be an object');for(const k of Object.keys(o))if(!allowed.includes(k))throw Error('Unsupported '+name+' field: '+k);}
function validate(a){
 keys(a,Object.keys(base),'appearance');for(const k of Object.keys(a))if(a[k]===null)throw Error('Null appearance value: '+k);const out=structuredClone(base);
 for(const [k,[lo,hi]] of Object.entries(limits)){const v=a[k]??base[k];if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw Error('Out of range: '+k);out[k]=v;}
 for(const k of ['whiteVisible','goldVisible','relations','hardwareVisible','hardwareJacks','hardwareKnobs','hardwareSwitches','hardwareLEDs']){if(k in a&&typeof a[k]!=='boolean')throw Error('Invalid '+k);out[k]=a[k]??base[k];}
 for(const k of ['whiteColor','goldColor']){const v=a[k]??base[k];if(typeof v!=='string'||!/^#[0-9a-fA-F]{6}$/.test(v))throw Error('Invalid color');out[k]=v.toLowerCase();}
 out.exportMode=a.exportMode??base.exportMode;if(!['artwork','assembled'].includes(out.exportMode))throw Error('Unsupported export mode');
 out.font=a.font??base.font;if(!['Arial','Georgia','monospace'].includes(out.font))throw Error('Unsupported font');
 out.ledStyle=a.ledStyle??base.ledStyle;if(!['line','bracket'].includes(out.ledStyle))throw Error('Unsupported LED ornament');
 if(a.icons!==undefined){keys(a.icons,Object.keys(source.icons),'icons');for(const k of Object.keys(a.icons)){const i=a.icons[k];if(!Number.isInteger(i)||i<0||i>=source.icons[k].length)throw Error('Invalid icon index');out.icons[k]=i;}}
 if(a.offsets!==undefined){keys(a.offsets,labels.map(x=>x.id),'offsets');for(const [id,v] of Object.entries(a.offsets)){keys(v,['x','y'],'label offset');if(Object.keys(v).length!==2||!['x','y'].every(k=>typeof v[k]==='number'&&Number.isFinite(v[k])&&Math.abs(v[k])<=4))throw Error('Invalid label offset');out.offsets[id]={x:v.x,y:v.y};}}
 return out;
}
const envelope=()=>({schema:'zudo-current-panel-appearance-v1',geometrySHA256:source.geometrySHA256,appearance:structuredClone(current)});
function makeSvg(a,mode='assembled'){
 // Copy only appearance fields into the renderer. px/py and every mechanical input stay frozen.
 const s={...source.profile,labelModule:a.labelModule,labelKnob:a.labelKnob,labelJack:a.labelJack,labelSwitch:a.labelSwitch,separatorGap:a.separatorGap,relations:a.relations,ledStyle:a.ledStyle,icons:a.icons};
 let raw=GridRenderer.render(source.grid,s,{artOnly:true,apertureDiameters:diam}).svg.replace(/<text\b[^>]*>R21 ·[^<]*<\/text>/g,'').replace(/<text\b[^>]*>INTEGER CELLS \/[^<]*<\/text>/g,'');
 const doc=new DOMParser().parseFromString(raw,'image/svg+xml'),svg=doc.documentElement;
 svg.setAttribute('aria-label','Current panel appearance preview — locked geometry, not manufacturing output');
 svg.querySelectorAll('[tabindex],[role]').forEach(e=>{e.removeAttribute('tabindex');e.removeAttribute('role');});
 svg.querySelectorAll('text').forEach((e,i)=>{const id='label-'+String(i).padStart(4,'0');e.setAttribute('data-editor-label',id);e.style.fontFamily=a.font==='Arial'?'Arial,Helvetica,sans-serif':a.font;e.style.pointerEvents='auto';const o=a.offsets[id];if(o)e.setAttribute('transform',`translate(${o.x} ${o.y})`);});
 for(const e of svg.querySelectorAll('*')){
  let layer=null;
  for(const attr of ['fill','stroke','color']){const color=e.getAttribute(attr);if(color==='#edece5'){e.setAttribute(attr,a.whiteColor);layer='white';}else if(color==='#c6a35e'||color==='#695935'){if(a.goldColor!==base.goldColor)e.setAttribute(attr,a.goldColor);layer='gold';}}
  if(layer){e.setAttribute('data-ink-layer',layer);if(!(layer==='white'?a.whiteVisible:a.goldVisible))e.setAttribute('opacity','0');}
  const sw=e.getAttribute('stroke-width');if(sw!==null&&Number.isFinite(Number(sw)))e.setAttribute('stroke-width',String(Number((Number(sw)*a.lineWeight).toFixed(5))));
 }
 const g=doc.createElementNS(NS,'g');g.id='locked-features';
 for(const q of source.lock.placements){const c=doc.createElementNS(NS,'circle');for(const [k,v] of Object.entries({'data-uid':q.uid,'data-kind':q.kind,cx:q.x_mm,cy:q.y_mm,r:(q.kind==='led'?source.params.indicator_window.diameter_mm:q.hole_d_mm)/2,fill:q.kind==='led'?'#52564b':'#080a09'}))c.setAttribute(k,String(v));g.append(c);}
 svg.append(g);
 if(mode==='assembled')PanelHardware.append(doc,svg,source,a);
 const meta=doc.createElementNS(NS,'metadata');meta.id='appearance-settings';meta.textContent=JSON.stringify({schema:'zudo-current-panel-appearance-v1',geometrySHA256:source.geometrySHA256,appearance:a,exportMode:mode,hardwareIllustrations:mode==='assembled',previewOnly:true,sourceHashes:source.hashes});svg.prepend(meta);
 return svg;
}
function serialized(){return new XMLSerializer().serializeToString(makeSvg(current,current.exportMode))+'\n';}
function render(){
 const svg=makeSvg(current);$('panel').replaceChildren(document.importNode(svg,true));
 if(!labels.length){labels=Array.from(svg.querySelectorAll('text')).map(e=>({id:e.getAttribute('data-editor-label'),text:e.textContent,kind:e.dataset.labelKind,x:Number(e.getAttribute('x')),y:Number(e.getAttribute('y')),block:e.closest('[data-block]')?.getAttribute('data-block')||'Panel'}));for(const l of labels){const o=document.createElement('option');o.value=l.id;o.textContent=`${l.block} · ${l.text} (${l.kind})`;$('label-select').append(o);}}
 $('panel').querySelector(`[data-editor-label="${selected}"]`)?.classList.add('chosen');applyView();occlusions();
}
function occlusions(){
 const hardware=Array.from($('panel').querySelectorAll('[data-hardware-uid]')).filter(e=>e.dataset.hardwareType!=='led').map(e=>e.getBoundingClientRect());
 const covered=Array.from($('panel').querySelectorAll('text')).filter(e=>e.getAttribute('opacity')!=='0').filter(e=>{const b=e.getBoundingClientRect();return hardware.some(h=>b.left<h.right&&b.right>h.left&&b.top<h.bottom&&b.bottom>h.top);});
 $('occlusion').textContent=`${covered.length} label bounds overlap illustrative hardware. Use detail view or turn hardware off to edit covered text. This is a conservative visual screen, not a fit check.`;
 $('occlusion').title=covered.map(e=>e.textContent).join(', ');
}
function applyView(){$('panel').style.width='318px';$('panel').style.height='298px';$('panel').style.transform=`translate(${tx}px,${ty}px) scale(${zoom})`;$('zoom-value').textContent=Math.round(zoom/fitScale()*100)+'%';}
function fitScale(){return Math.max(.1,Math.min(($('viewport').clientWidth-36)/318,($('viewport').clientHeight-36)/298));}
function fit(){isFit=true;zoom=fitScale();tx=($('viewport').clientWidth-318*zoom)/2;ty=($('viewport').clientHeight-298*zoom)/2;applyView();}
function zoomAt(f,x=$('viewport').clientWidth/2,y=$('viewport').clientHeight/2){const next=Math.max(fitScale()*.5,Math.min(fitScale()*6,zoom*f));tx=x-(x-tx)*next/zoom;ty=y-(y-ty)*next/zoom;zoom=next;isFit=false;applyView();}
function field(container,id,title,min,max,step,value,onchange){const d=document.createElement('div');d.className='field';const label=document.createElement('label');label.htmlFor=id;label.textContent=title;const output=document.createElement('output');output.id=id+'-value';const input=document.createElement('input');Object.assign(input,{id,type:'range',min,max,step,value});input.oninput=()=>{onchange(Number(input.value));sync();render();status('Appearance updated. All 438 feature centres and diameters remain fixed.');};d.append(label,output,input);$(container).append(d);}
for(const [k,title] of [['labelModule','Module headings'],['labelKnob','Control labels'],['labelJack','Jack labels'],['labelSwitch','Switch words']])field('type-controls',k,title,...limits[k],.05,current[k],v=>current[k]=v);
field('line-controls','separatorGap','Separator clearance',0,5,.1,current.separatorGap,v=>current.separatorGap=v);
field('line-controls','lineWeight','Line weight ×',.5,2,.05,1,v=>current.lineWeight=v);
for(const axis of ['x','y'])field('offset-controls','offset-'+axis,axis==='x'?'Label horizontal':'Label vertical',-4,4,.1,0,v=>{const old=current.offsets[selected]||{x:0,y:0};current.offsets[selected]={...old,[axis]:v};});
for(const f of Object.keys(source.icons)){const o=document.createElement('option');o.value=f;o.textContent=f;$('icon-family').append(o);}
function iconChoices(){const f=$('icon-family').value;$('icon-choice').replaceChildren();source.icons[f].forEach((a,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${String(i+1).padStart(2,'0')} · ${a.name}`;$('icon-choice').append(o);});$('icon-choice').value=current.icons[f]||0;}
function sync(){for(const k of ['Visible','Jacks','Knobs','Switches','LEDs'])$('hardware'+k).checked=current['hardware'+k];$('export-mode').value=current.exportMode;for(const k of Object.keys(limits)){$(k).value=current[k];$(k+'-value').textContent=current[k].toFixed(2);}for(const a of ['x','y']){const v=current.offsets[selected]?.[a]||0;$('offset-'+a).value=v;$('offset-'+a+'-value').textContent=v.toFixed(1);}$('label-select').value=selected;$('font').value=current.font;$('led-style').value=current.ledStyle;$('relations').checked=current.relations;for(const l of ['white','gold']){$(l+'-visible').checked=current[l+'Visible'];$(l+'-color').value=current[l+'Color'];}iconChoices();}
function choose(id){selected=id;sync();render();}
$('label-select').onchange=()=>choose($('label-select').value);
$('clear-offset').onclick=()=>{delete current.offsets[selected];sync();render();status('Selected label offset reset.');};
$('icon-family').onchange=iconChoices;$('icon-choice').onchange=()=>{current.icons[$('icon-family').value]=Number($('icon-choice').value);render();};
for(const [id,key] of [['font','font'],['led-style','ledStyle']])$(id).onchange=()=>{current[key]=$(id).value;render();};
for(const key of ['relations','white','gold']){const id=key==='relations'?key:key+'-visible',prop=key==='relations'?key:key+'Visible';$(id).onchange=()=>{current[prop]=$(id).checked;render();};}
for(const l of ['white','gold'])$(l+'-color').oninput=()=>{current[l+'Color']=$(l+'-color').value;render();};
function download(name,blob){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),2000);}
for(const k of ['Visible','Jacks','Knobs','Switches','LEDs'])$('hardware'+k).onchange=()=>{current['hardware'+k]=$('hardware'+k).checked;render();};
$('export-mode').onchange=()=>{current.exportMode=$('export-mode').value;};
$('save').onclick=()=>{download('zudo-current-panel-appearance-v1.json',new Blob([JSON.stringify(envelope(),null,2)+'\n'],{type:'application/json'}));status('Appearance settings saved. Geometry is not included as editable data.');};
function loadPreset(obj){keys(obj,['schema','geometrySHA256','appearance'],'preset');if(obj.schema!=='zudo-current-panel-appearance-v1')throw Error('Unsupported settings version; historical geometry presets are not accepted');if(obj.geometrySHA256!==source.geometrySHA256)throw Error('Preset belongs to a different geometry revision');const next=validate(obj.appearance);current=next;sync();render();status('Appearance settings loaded. Locked geometry verified.');}
$('load').onclick=()=>$('loadfile').click();$('loadfile').onchange=async()=>{try{const f=$('loadfile').files[0];if(!f)return;if(f.size>1000000)throw Error('Settings file exceeds 1 MB');loadPreset(JSON.parse(await f.text()));}catch(e){status('Settings rejected: '+e.message,true);}finally{$('loadfile').value='';}};
$('reset').onclick=()=>{current=structuredClone(base);sync();render();fit();status('Restored audited appearance baseline.');};
$('svg-export').onclick=()=>{download('zudo-current-panel-'+current.exportMode+'-preview.svg',new Blob([serialized()],{type:'image/svg+xml'}));status(current.exportMode==='assembled'?'Assembled SVG preview exported — illustrative hardware included.':'Clean artwork SVG preview exported — no hardware illustrations; not manufacturing output.');};
$('png-export').onclick=async()=>{const button=$('png-export');button.disabled=true;$('busy').textContent='Rendering PNG…';let u;try{await document.fonts.ready;const svg=makeSvg(current,current.exportMode),scale=Number($('png-scale').value);svg.setAttribute('width',318*scale);svg.setAttribute('height',298*scale);u=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));const im=new Image();await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=()=>reject(Error('SVG could not be rasterized'));im.src=u;});const canvas=document.createElement('canvas');canvas.width=318*scale;canvas.height=298*scale;canvas.getContext('2d').drawImage(im,0,0);const blob=await new Promise(r=>canvas.toBlob(r,'image/png'));if(!blob)throw Error('PNG encoding failed');download('zudo-current-panel-'+current.exportMode+'-preview.png',blob);status(`PNG preview exported at ${canvas.width} × ${canvas.height}. Save settings separately for reproducibility.`);}catch(e){status('PNG export failed: '+e.message,true);}finally{if(u)URL.revokeObjectURL(u);button.disabled=false;$('busy').textContent='';}};
$('fit').onclick=fit;$('zoom-in').onclick=()=>zoomAt(1.25);$('zoom-out').onclick=()=>zoomAt(.8);
$('detail').onclick=()=>{const l=labels.find(l=>l.id===selected),o=current.offsets[selected]||{x:0,y:0};zoom=fitScale()*3;tx=$('viewport').clientWidth/2-(l.x+o.x)*zoom;ty=$('viewport').clientHeight/2-(l.y+o.y)*zoom;isFit=false;applyView();};
const vp=$('viewport');vp.onpointerdown=e=>{if(e.button!==0)return;const t=e.target.closest('[data-editor-label]');if(t){choose(t.getAttribute('data-editor-label'));return;}drag={x:e.clientX,y:e.clientY,tx,ty};vp.setPointerCapture(e.pointerId);vp.classList.add('panning');};vp.onpointermove=e=>{if(drag){tx=drag.tx+e.clientX-drag.x;ty=drag.ty+e.clientY-drag.y;isFit=false;applyView();}};vp.onpointerup=vp.onpointercancel=()=>{drag=null;vp.classList.remove('panning');};vp.addEventListener('wheel',e=>{if(e.ctrlKey||e.metaKey){e.preventDefault();const b=vp.getBoundingClientRect();zoomAt(e.deltaY<0?1.1:1/1.1,e.clientX-b.left,e.clientY-b.top);}}, {passive:false});vp.onkeydown=e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(e.key)){e.preventDefault();if(e.key==='0')fit();else if(['+','=','-'].includes(e.key))zoomAt(e.key==='-'?.8:1.25);else{tx+=e.key==='ArrowLeft'?30:e.key==='ArrowRight'?-30:0;ty+=e.key==='ArrowUp'?30:e.key==='ArrowDown'?-30:0;isFit=false;applyView();}}};new ResizeObserver(()=>{if(isFit)fit();}).observe(vp);
render();sync();fit();
// Narrow testing/automation surface: imports still traverse the exact UI validator.
window.PanelAppearance=Object.freeze({settings:envelope,load:loadPreset,svg:serialized,baseline:()=>structuredClone(base),geometry:()=>Array.from($('panel').querySelectorAll('#locked-features circle')).map(e=>Object.fromEntries(['data-uid','data-kind','cx','cy','r'].map(k=>[k,e.getAttribute(k)])))});
})();
