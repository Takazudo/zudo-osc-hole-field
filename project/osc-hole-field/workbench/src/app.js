(function(){
'use strict';
const $=id=>document.getElementById(id),D=window.GRID_DATA,R=window.GridRenderer;
const defaults={px:17,py:14,labelModule:1.6,labelKnob:1.5,labelJack:1.6,labelSwitch:.85,separatorGap:.5,headings:true,grid:false,bodies:false,plugs:false,plugDia:12,relations:true,ledStyle:'line',switchLabels:'words',icons:{},values:{},signalValues:{},stageLevels:{},selected:null};
let s=structuredClone(defaults),tab='flat',zoom=1,lastGeometry='',saveTimer=null;
const byId=Object.fromEntries([...D.ports,...D.controls].map(q=>[q.uid,q]));
// Electrical IDs can be shared by a jack and its associated control; UI IDs cannot.
for(const q of D.controls)byId[q.id]=q;
const envs=Object.fromEntries(Array.from({length:6},(_,i)=>['E'+(i+1),new ARPreview.Voice()]));let envFrame=0,lastT=0;
const shHeld={H1:null,H2:null};const shVoices={H1:new SHSlew.Channel(),H2:new SHSlew.Channel()};let shFrame=0,shLast=0;const shHistory={H1:[],H2:[]};let exploded=false,hiddenPanel=false;
function voltage(id,v){s.signalValues[id]=Number(v)||0;}
function render(sync3d=true){
 const result=R.render(D,s);$('panel').innerHTML=result.svg;const dm=result.dimensions;
 $('size').textContent=`${dm.w} × ${dm.h} mm · 180 jacks · 144 controls`;
 for(let [key,id]of [['px','px-out'],['py','py-out'],['labelModule','module-out'],['labelKnob','knob-out'],['labelJack','jack-out'],['separatorGap','sep-out']])$(id).textContent=s[key].toFixed(2)+' mm';
 let warnings=[];if(s.px<17)warnings.push(`OCT: ${s.px-16.2<0?'overlap':'less than 0.8 mm nominal gap'} between 16.2 mm bodies.`);if(s.py<14)warnings.push('Tighter than the baseline: title/label, switch and underside checks required.');if(s.plugs&&s.plugDia>10.98)warnings.push('A barrel above 10.98 mm can obscure part of the nearby LED aperture.');if(s.plugs&&s.plugDia>=Math.min(s.px,s.py))warnings.push('Plug barrels touch or overlap on the smaller grid pitch.');if(Math.max(s.labelModule,s.labelKnob,s.labelJack)>1.8)warnings.push('Large-text trial: check all labels and adjacent glyphs at 100% size.');
 $('fit-warning').textContent=warnings.length?warnings.join(' '):'17 mm columns / 14 mm rows are a proposal. OCT body gap 0.8 mm; nut, shaft, button and connector stack still need exact fit checks.';
 $('status').classList.toggle('warn',!!warnings.length);$('status').textContent=`Grid locked to ${D.ports.length} screenshot cells; ${D.controls.length}/144 lower cells occupied. ${warnings.join(' ')||'Component diameters do not change with pitch.'}`;
 if(sync3d&&window.Grid3D){let key=`${s.px}/${s.py}`;if(key!==lastGeometry){window.Grid3D.rebuild(s);lastGeometry=key;}clearTimeout(saveTimer);saveTimer=setTimeout(()=>window.Grid3D.artwork(R.render(D,s,{artOnly:true}).svg),120);}
 window.REVIEW_STATE=s;window.RENDER_LAST=result;
}
function inspect(q,redraw=true){s.selected=q.uid;$('selected').textContent=D.blocks[q.block].name+' / '+q.label;let p=R.pos(q,s),d='';
 if(q.kind==='jack')d=`${q.direction==='in'?'INPUT':'OUTPUT'} · row ${q.row+1}, column ${q.col+1} · ${p.x.toFixed(2)}, ${p.y.toFixed(2)} mm. `;
 else d=`${q.kind} · control row ${q.row+1}, column ${q.col+1} · ${p.x.toFixed(2)}, ${p.y.toFixed(2)} mm. `;
 if(q.block.startsWith('H'))d+='S&H: rising trigger starts a short acquisition pulse; input is then held. SLEW smooths the captured target after storage. No hidden noise connection.';
 else if(q.block.startsWith('X'))d+='A/B selector is manual. Only the chosen source reaches OUT; inputs are not tied together.';
 else if(q.block.startsWith('B'))d+='Buffered multiple: one input → THREE separately buffered outputs.';
 else if(q.block.startsWith('M4'))d+='Four attenuverted sources are summed, then ATTEN CV controls post-sum gain. Clip detection must cover pre-VCA and final nodes.';
 else if(q.block.startsWith('A'))d+='OUT = gain × IN + manual OFFSET + OFFSET CV. This is a control contribution, not a normalized link.';
 else if(q.kind==='octave')d+='Selected SRBV160803: actual body 16.2 × 18.5 mm; cap and Z-stack remain open.';
 else if(q.kind==='pot')d+='Bourns PTV09A-4020F family: 6 mm capless actuator; 12 × 12 mm body reservation is not a footprint.';
 else d+='Select another port or actuator to review its column relationship.';
 $('details').textContent=d;if(redraw)render(false);
}
function setTab(v){tab=v;document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tab===v)));$('research').hidden=v!=='research';$('workspace').hidden=v==='research';$('flat-view').hidden=v==='three';$('three-view').hidden=!['three','split'].includes(v);$('views').classList.toggle('split',v==='split');if(['three','split'].includes(v)){window.Grid3D?.ensure(s);render();setTimeout(()=>window.Grid3D?.resize(),60);}}
function syncInputs(){for(let k of ['px','py','labelModule','labelKnob','labelJack','separatorGap','plugDia','switchLabels','ledStyle'])$(k).value=s[k];for(let k of ['grid','bodies','plugs','relations'])$(k).checked=s[k];populateIcons();syncSlewPanel();}
function download(name,content,mime='application/json'){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:mime}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
for(const k of ['px','py','labelModule','labelKnob','labelJack','separatorGap','plugDia'])$(k).addEventListener('input',()=>{s[k]=Number($(k).value);render();});
for(const k of ['grid','bodies','plugs','relations'])$(k).addEventListener('change',()=>{s[k]=$(k).checked;render();});
for(const k of ['ledStyle','switchLabels'])$(k).addEventListener('change',()=>{s[k]=$(k).value;render();});
$('preset').onchange=()=>{Object.assign(s,D.presets[$('preset').value]);syncInputs();render();};
$('zoom').onchange=()=>{zoom=Number($('zoom').value);$('panel').style.width=(zoom*100)+'%';};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
$('save').onclick=()=>download('zudo-grid-r21-settings.json',JSON.stringify({schema:'zudo-grid-review-v1',settings:s},null,2));
$('load').onclick=()=>$('loadfile').click();$('loadfile').onchange=async()=>{try{const obj=JSON.parse(await $('loadfile').files[0].text());if(obj.schema!=='zudo-grid-review-v1')throw Error('Not an R21 grid-settings file');const t=obj.settings;for(let k of ['px','py','labelModule','labelKnob','labelJack','separatorGap','plugDia']){if(typeof t[k]!=='number'||!Number.isFinite(t[k]))throw Error('Invalid setting '+k);}if(t.px<14||t.px>21||t.py<12||t.py>20)throw Error('Pitch out of supported review range');s={...structuredClone(defaults),...t};s.values=Object.fromEntries(Object.entries(t.values||{}).filter(([id,v])=>byId[id]&&Number.isFinite(v)));s.signalValues={};s.stageLevels={};syncInputs();render();}catch(e){$('status').textContent='Settings not loaded: '+e.message;}};
$('export').onclick=()=>download('zudo-grid-r21-panel.svg',R.render(D,s).svg,'image/svg+xml');
let drag=null;
$('panel').addEventListener('pointerdown',e=>{const item=e.target.closest('[data-id]');if(!item)return;const q=byId[item.dataset.id];if(!q)return;e.preventDefault();inspect(q,false);if(q.kind==='pot'||q.kind==='octave'){drag={id:q.id,y:e.clientY,start:R.state(q,s)};}
});
window.addEventListener('pointermove',e=>{if(!drag)return;const q=byId[drag.id],max=q.kind==='octave'?5:1;let v=Math.min(max,Math.max(0,drag.start+(drag.y-e.clientY)/150*max));s.values[q.id]=q.kind==='octave'?Math.round(v):v;aoDemo();syncSlewPanel();render(false);});
window.addEventListener('pointerup',()=>{if(drag){drag=null;render();}});
$('panel').addEventListener('click',e=>{const item=e.target.closest('[data-id]');if(!item)return;const q=byId[item.dataset.id];if(!q)return;inspect(q,false);if(q.kind==='switch'){const cho=e.target.closest('.state-choice');s.values[q.id]=cho?Number(cho.dataset.index):(Math.round(R.state(q,s))+1)%q.positions.length;abDemo();render();}if(q.kind==='button'){if(q.block.startsWith('E')){envs[q.block].trigger();$('env').value=q.block;startEnvelope();}else if(q.block.startsWith('H')){$('sh').value=q.block;sample();}}if(q.kind==='jack')render(false);});
$('panel').addEventListener('keydown',e=>{const item=e.target.closest('[data-id]');if(!item)return;const q=byId[item.dataset.id];if(!q)return;if(['ArrowUp','ArrowRight','ArrowDown','ArrowLeft'].includes(e.key)){e.preventDefault();const sign=['ArrowUp','ArrowRight'].includes(e.key)?1:-1;if(q.kind==='pot')s.values[q.id]=Math.max(0,Math.min(1,R.state(q,s)+sign*.025));else if(q.positions)s.values[q.id]=(Math.round(R.state(q,s))+sign+q.positions.length)%q.positions.length;aoDemo();abDemo();syncSlewPanel();render();document.querySelector(`[data-id="${CSS.escape(q.uid)}"]`)?.focus();}else if(['Enter',' '].includes(e.key)){e.preventDefault();item.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
$('panel').addEventListener('dblclick',e=>{const it=e.target.closest('[data-id]');if(it&&byId[it.dataset.id]?.kind==='pot'){s.values[byId[it.dataset.id].id]=.5;render();}});
$('volts').onclick=e=>{if(!e.target.hasAttribute('data-v')||!s.selected)return;voltage(byId[s.selected].id,Number(e.target.dataset.v));render();};$('led-demo').onchange=()=>{s.signalValues={};if($('led-demo').checked)D.ports.forEach((q,i)=>{if(q.led)voltage(q.id,[1,2.5,5,-2.5,0][i%5]);});render();};
const fams=Object.keys(D.blocks).map(b=>D.blocks[b].family).filter((x,i,a)=>a.indexOf(x)===i);$('iconFamily').innerHTML=fams.map(f=>`<option>${f}</option>`).join('');
function populateIcons(){const f=$('iconFamily').value,list=GRID_ICONS[f]||[{name:f+' symbol'}];$('iconChoice').innerHTML=list.map((x,i)=>`<option value="${i}">${String(i+1).padStart(2,'0')} · ${x.name}</option>`).join('');$('iconChoice').value=s.icons[f]||0;}
$('iconFamily').onchange=populateIcons;$('iconChoice').onchange=()=>{s.icons[$('iconFamily').value]=Number($('iconChoice').value);render();};
$('env').innerHTML=Object.keys(envs).map(k=>`<option value="${k}">ENV ${k.slice(1)}</option>`).join('');
function startEnvelope(){if(envFrame)return;lastT=performance.now();envFrame=requestAnimationFrame(tickEnvelope);}
function tickEnvelope(t){const dt=Math.min(.08,(t-lastT)/1000);lastT=t;let active=false;for(let [b,voice] of Object.entries(envs)){let get=k=>R.state(byId[b+'.'+k],s),mode=byId[b+'.MODE'].positions[Math.round(get('MODE'))];let snap=voice.advance(dt,{mode,curved:get('SHAPE')===1,rise:.25+get('RISE')*2.5,fall:.25+get('FALL')*2.5});s.stageLevels[b]=snap.lamps;active ||= snap.phase!=='idle';if($('env').value===b){$('envvalue').textContent=`${snap.phase.toUpperCase()} · ${(snap.level*5).toFixed(2)} V`;$('envmeter').value=snap.level*5;}for(let kind of ['rise','fall']){document.querySelectorAll(`[data-env="${b}"][data-stage="${kind}"]`).forEach(el=>el.setAttribute('opacity',snap.lamps[kind]**.65));}}
 envFrame=active?requestAnimationFrame(tickEnvelope):0;}
$('trigger-env').onclick=()=>{envs[$('env').value].trigger();startEnvelope();};$('idle-env').onclick=()=>{const b=$('env').value;envs[b]=new ARPreview.Voice();s.stageLevels[b]={rise:0,fall:0};render();};$('envgate').onchange=()=>{const b=$('env').value;s.values[b+'.MODE']=0;envs[b].setGate($('envgate').checked);render();startEnvelope();};
function slewPosition(b){return R.state(byId[b+'.SLEW'],s);}
function syncSlewPanel(){const b=$('sh').value,voice=shVoices[b];voice.setSlew(slewPosition(b));const snap=voice.snapshot();$('sh-slew').value=snap.position;$('sh-slew-out').textContent=`${Math.round(snap.position*100)}% · τ ${(1000*snap.tau).toFixed(1)} ms`;
$('sh-out').textContent=snap.sampled?`Held target ${snap.target.toFixed(3)} V → OUT ${snap.output.toFixed(3)} V`:'Not sampled · illustrative initial OUT 0 V';
const h=shHistory[b],end=h.length?h[h.length-1].t:0,start=Math.max(0,end-3),data=h.filter(p=>p.t>=start);const path=key=>data.map((p,i)=>`${i?'L':'M'}${(6+288*(p.t-start)/3).toFixed(2)},${(56-6*p[key]).toFixed(2)}`).join(' ');$('sh-target-path').setAttribute('d',path('target'));$('sh-slew-path').setAttribute('d',path('out'));}
function sample(){const b=$('sh').value,v=Number($('sh-input').value);shHeld[b]=v;voltage(b+'.IN',v);const ch=shVoices[b];ch.setSlew(slewPosition(b));const before=ch.snapshot();shHistory[b].push({t:ch.time,target:before.target??before.output,out:before.output});ch.sample(v);shHistory[b].push({t:ch.time,target:v,out:ch.output});s.selected='J:'+b+'.OUT';syncSlewPanel();render();startSlew();}
function advanceSlew(dt){for(const [b,ch] of Object.entries(shVoices)){ch.setSlew(slewPosition(b));const snap=ch.advance(dt);if(snap.sampled){voltage(b+'.OUT',snap.output);shHistory[b].push({t:ch.time,target:snap.target,out:snap.output});shHistory[b]=shHistory[b].filter(p=>p.t>=ch.time-3.1).slice(-600);}}syncSlewPanel();}
function startSlew(){if(shFrame)return;shLast=performance.now();shFrame=requestAnimationFrame(tickSlew);}
function tickSlew(t){const dt=Math.max(0,(t-shLast)/1000);shLast=t;advanceSlew(dt);render(false);shFrame=Object.values(shVoices).some(ch=>ch.sampled&&!ch.snapshot().settled)?requestAnimationFrame(tickSlew):0;}
$('sample').onclick=sample;$('sh-input').oninput=()=>{$('sh-in-out').textContent=Number($('sh-input').value).toFixed(2)+' V';voltage($('sh').value+'.IN',Number($('sh-input').value));render(false);};$('sh').onchange=syncSlewPanel;
$('sh-slew').oninput=()=>{s.values[$('sh').value+'.SLEW']=Number($('sh-slew').value);syncSlewPanel();render(false);startSlew();};
function abDemo(){const b=$('ab').value,which=Math.round(R.state(byId[b+'.SELECT'],s)),a=Number($('ab-a').value),bb=Number($('ab-b').value),v=which?bb:a;for(let [id,x]of [['IN-A',a],['IN-B',bb],['OUT',v]])voltage(b+'.'+id,x);$('ab-a-out').textContent=a.toFixed(1)+' V';$('ab-b-out').textContent=bb.toFixed(1)+' V';$('abvalue').textContent=`${which?'B':'A'} selected → ${v.toFixed(2)} V`;return v;}
$('ab-toggle').onclick=()=>{const q=byId[$('ab').value+'.SELECT'];s.values[q.id]=1-Math.round(R.state(q,s));abDemo();render();};for(let k of ['ab','ab-a','ab-b'])$(k).addEventListener('input',()=>{abDemo();render(false);});
$('ao').innerHTML=Array.from({length:6},(_,i)=>`<option value="A${String(i+1).padStart(2,'0')}">OFFSET ${i+1}</option>`).join('');
function aoDemo(){const b=$('ao').value,g=2*R.state(byId[b+'.ATTEN'],s)-1,o=10*R.state(byId[b+'.OFFSET'],s)-5,input=Number($('ao-in').value),cv=Number($('ao-cv').value),v=g*input+o+cv;$('ao-in-out').textContent=input.toFixed(2)+' V';$('ao-cv-out').textContent=cv.toFixed(2)+' V';$('ao-value').textContent=`g ${g.toFixed(2)} · offset ${o.toFixed(2)} V → ${Math.max(-10,Math.min(10,v)).toFixed(2)} V${Math.abs(v)>=10?' · CLIP':''}`;voltage(b+'.IN',input);voltage(b+'.OFFSET',cv);voltage(b+'.OUT',v);}
for(let k of ['ao','ao-in','ao-cv'])$(k).addEventListener('input',()=>{aoDemo();syncSlewPanel();render(false);});
const esc=GridRenderer.C?x=>String(x).replace(/[<>&"]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c])):String;
function showParts(){const filter=$('part-search').value.toLowerCase();$('parts').innerHTML=GRID_PARTS.filter(q=>JSON.stringify(q).toLowerCase().includes(filter)).map(q=>`<tr><td><strong>${esc(q.role)}</strong><br>${esc(q.quantity||'Circuit-dependent')}</td><td>${esc(q.mpn)}<br><span class="muted">${esc(q.code||'External procurement')}</span><br>${esc(q.status)}</td><td>${esc(q.recommendation)}<br><span class="muted">${esc(q.caveat)}</span></td><td>${q.sources.map(x=>`<a target="_blank" rel="noopener" href="${esc(x.url)}">${esc(x.label)}</a>`).join('<br>')}</td></tr>`).join('');}
$('part-search').oninput=showParts;showParts();
document.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>window.Grid3D?.camera(b.dataset.camera));$('explode').onclick=()=>{exploded=!exploded;window.Grid3D?.explode(exploded);};$('hide-panel').onclick=()=>{hiddenPanel=!hiddenPanel;window.Grid3D?.hidePanel(hiddenPanel);};$('save3d').onclick=()=>window.Grid3D?.savePNG();
window.getGridSettings=()=>s;window.refreshGrid=()=>render();window.setGridTab=setTab;window.gridDownload=download;window.GRID_TEST={byId,envs,shHeld,shVoices,advanceSlew,syncSlewPanel,state:()=>s,render,sample,abDemo};
syncInputs();render(false);abDemo();aoDemo();syncSlewPanel();
})();
