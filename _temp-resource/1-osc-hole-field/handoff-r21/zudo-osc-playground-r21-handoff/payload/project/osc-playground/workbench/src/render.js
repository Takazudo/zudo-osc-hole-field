/* Pure grid renderer. Coordinates are millimetres; artwork never rescales hardware.
 * Used by the flat editor, exports, tests and the 3D panel face. */
(function(root){
'use strict';
const C={bg:'#101211',gold:'#c6a35e',white:'#edece5',dim:'#695935',red:'#ba3733'};
const esc=s=>String(s).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[x]));
const n=v=>Number(v.toFixed(4));
const circ=(x,y,r,fill,stroke='none',sw=.15,a='')=>`<circle cx="${n(x)}" cy="${n(y)}" r="${n(r)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" ${a}/>`;
const line=(x,y,x2,y2,stroke=C.gold,sw=.16,a='')=>`<line x1="${n(x)}" y1="${n(y)}" x2="${n(x2)}" y2="${n(y2)}" stroke="${stroke}" stroke-width="${sw}" ${a}/>`;
const rect=(x,y,w,h,fill,stroke='none',sw=.15,a='')=>`<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" ${a}/>`;
function dims(s){const jtop=22,div=jtop+10*s.py+4,ctop=div+12;return {w:18*s.px+12,h:ctop+8*s.py+8,jtop,ctop,div,margin:6};}
function pos(q,s){const d=dims(s);return {x:6+(q.col+.5)*s.px,y:(q.field==='jacks'?d.jtop:d.ctop)+(q.row+.5)*s.py};}
function corners(x,y,r,acc){let out='',l=acc?2.05:1.15;for(let sx of [-1,1])for(let sy of [-1,1]){out+=`<path d="M${x+sx*(r-l)},${y+sy*r}H${x+sx*r}V${y+sy*(r-l)}" fill="none" stroke="${acc?C.gold:C.white}" stroke-width="${acc?.42:.18}"/>`;}return out;}
function state(q,s){let v=s.values[q.id];if(v===undefined){if(q.kind==='octave')v=2;else if(q.kind==='switch')v=q.key==='MODE'?1:q.key==='VCO/LFO'?1:q.positions.length===3?1:0;else v=q.default_value??.5;}return v;}
function icon(f,s){let list=root.GRID_ICONS?.[f];if(list){return list[s.icons[f]||0]?.art||list[0].art;}const path=f==='SH'?'M2 19 H7 V13 H13 V7 H19 V16 H23':'M2 5 H9 M2 19 H9 M9 19 L18 12 H23 M9 5 L12 7';return `<g fill="none" stroke="currentColor" stroke-width="1.6"><path d="${path}"/></g>`;}
function titleName(b,D){return D.blocks[b].name;}
function render(D,s,options={}){
 let out=[],bounds=[],marks=[],d=dims(s),selected=s.selected,art=!!options.artOnly;
 const txt=(x,y,value,size,kind='fixed',bold=false,anchor='middle')=>{const w=String(value).length*size*.55;bounds.push({kind:'text',id:value,x0:x-(anchor==='middle'?w/2:anchor==='end'?w:0),x1:x+(anchor==='middle'?w/2:anchor==='end'?0:w),y0:y-size*.83,y1:y+size*.1});return `<text x="${n(x)}" y="${n(y)}" font-size="${size}" text-anchor="${anchor}" fill="${kind==='module'?C.gold:C.white}" font-weight="${bold?600:400}" class="label label-${kind}" data-label-kind="${kind}">${esc(value)}</text>`;};
 const wrap=(q)=>`<g class="item ${s.selected===q.uid?'is-selected':''}" data-id="${esc(q.uid)}" data-block="${q.block}" data-kind="${q.kind}" tabindex="0" role="${q.kind==='pot'?'slider':'button'}" aria-label="${esc(D.blocks[q.block].name+' '+q.label)}">`;
 function lamp(x,y,q,type){const level=type==='clip'?(s.signalValues[q.id]&&Math.abs(s.signalValues[q.id])>=10?1:0):Math.min(1,Math.abs(s.signalValues[q.id]||0)/5);return circ(x,y,.66,'#1a201c',C.dim,.16)+circ(x,y,.47,type==='clip'?'#ff5f50':C.white,'none',0,`opacity="${level**.65}" data-led="${esc(q.id)}" data-led-type="${type}"`);}
 function annotation(x,y,value){return txt(x,y,value,s.labelJack,'jack',true);}
 out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${d.w}mm" height="${d.h}mm" viewBox="0 0 ${d.w} ${d.h}" class="panel" role="img" aria-label="R21 user-grid panel"><style>text{font-family:Arial,Helvetica,sans-serif;pointer-events:none}.item{cursor:pointer;outline:none}.item:focus .focus,.item:hover .focus,.is-selected .focus{opacity:1}.focus{opacity:0}.label{stroke:none}</style>`);
 out.push(rect(0,0,d.w,d.h,C.bg),rect(2.2,2.2,d.w-4.4,d.h-4.4,'none',C.gold,.27,'rx="1.3"'));
 out.push(txt(8,9.2,'ZUDO / OSC PLAYGROUND',2.6,'fixed',true,'start'),txt(d.w-7,8.5,`R21 · ${d.w} × ${d.h} mm · ${s.px} / ${s.py} mm GRID`,1.45,'fixed',false,'end'));
 out.push(line(6,d.div,d.w-6,d.div,C.gold,.38));
 if(!art&&s.grid){for(const [field,rows] of [['jacks',10],['controls',8]])for(let r=0;r<rows;r++)for(let c=0;c<18;c++){const x=6+c*s.px,y=(field==='jacks'?d.jtop:d.ctop)+r*s.py;out.push(rect(x+.35,y+.35,s.px-.7,s.py-.7,'none','#474e4c',.1));} }
 const unique=new Map();
 for(const g of D.groups){let x=6+g.col*s.px,y=(g.field==='jacks'?d.jtop:d.ctop)+g.row*s.py,w=g.cols*s.px,h=g.rows*s.py;let p1=`${x+w},${y},${x+w},${y+h}`,p2=`${x},${y+h},${x+w},${y+h}`;unique.set(p1,[x+w,y,x+w,y+h]);unique.set(p2,[x,y+h,x+w,y+h]);
 if(!art&&selected&&D.blocks[g.block]&&D.ports.concat(D.controls).find(q=>q.uid===selected)?.block===g.block)out.push(rect(x+.3,y+.3,w-.6,h-.6,'#393121','none',0,'opacity=".5"'));
 if(s.headings){let first=D[g.field==='jacks'?'ports':'controls'].filter(q=>q.block===g.block&&q.col>=g.col&&q.col<g.col+g.cols&&q.row>=g.row&&q.row<g.row+g.rows).sort((a,b)=>a.row-b.row||a.col-b.col)[0],p=pos(first,s);let cy=g.field==='controls'&&g.row===0?p.y-8.8:g.field==='controls'&&g.block.startsWith('X')?p.y+5.75:p.y-5.6,fs=s.labelModule,title=titleName(g.block,D),total=title.length*fs*.55+2.3,left=x+w/2-total/2;out.push(`<g class="module-heading" data-block="${g.block}"><g transform="translate(${left} ${cy-1.22}) scale(.064)" color="${C.gold}">${icon(D.blocks[g.block].family,s)}</g>`,txt(left+2.1,cy,title,fs,'module',true,'start'),'</g>');}
 }
 for(const q of D.ports){const {x,y}=pos(q,s),r=q.nut_diameter_mm/2;
 if(!art&&s.bodies)out.push(rect(x-5,y-5,10,10,'#1b5f6140','#80aca0',.13,'class="body-envelope"'));
 out.push(wrap(q));marks.push({id:q.id,x0:x-4.9,x1:x+4.9,y0:y-4.9,y1:y+4.9});
 out.push(corners(x,y,4.6,q.accent));
 if(!art){out.push(circ(x,y,r,q.direction==='out'?C.red:'#282f2c',q.direction==='out'?'#ed6b63':'#a2aaa3',.20),circ(x,y,3.2,'#1a1f1d','#969b92',.24),circ(x,y,2.5,'#030809','#505b56',.18),circ(x-.55,y-.8,.35,'#111a1b'));}else{out.push(circ(x,y,3.10,C.bg));}
 out.push(annotation(x,y+6.25,q.label));
 if(q.led){const lx=x+6.15;out.push(line(x+4.82,y,lx-.7,y,C.gold,.17));if(s.ledStyle==='bracket')out.push(`<path d="M${lx-.9},${y-1}h-.35v${q.clip?4:2}h.35" fill="none" stroke="${C.gold}" stroke-width=".16"/>`);out.push(lamp(lx,y,q,'magnitude'));if(q.clip)out.push(lamp(lx,y+2.05,q,'clip'));}
 if(!art&&s.plugs)out.push(circ(x,y,s.plugDia/2,'none','#70bdb3',.13,'stroke-dasharray=".4 .4"'));
 if(!art)out.push(circ(x,y,5.3,'none',C.white,.32,'class="focus"'),circ(x,y,5,'transparent'));
 out.push('</g>');
 }
 for(const q of D.controls){const {x,y}=pos(q,s),v=state(q,s),angle=q.kind==='octave'?-135+v*54:-135+v*270;
 if(!art&&s.bodies){let w=q.kind==='octave'?16.2:q.kind==='switch'?8.13:q.kind==='button'?6:12,h=q.kind==='octave'?18.5:q.kind==='switch'?5.08:q.kind==='button'?6:12;out.push(rect(x-w/2,y-h/2,w,h,'#22493840','#73a28d',.13,'class="body-envelope"'));}
 out.push(wrap(q));
 if(['pot','octave'].includes(q.kind)){
 const r=q.diameter_mm/2;marks.push({id:q.id,x0:x-r-.85,x1:x+r+.85,y0:y-r-.85,y1:y+r+.85});out.push(corners(x,y,r+.55,q.accent));
 if(!art){out.push(`<g transform="rotate(${angle} ${x} ${y})">`);if(q.kind==='pot')out.push(`<path d="M${x-2.5981} ${y-1.5}A3 3 0 1 0 ${x+2.5981} ${y-1.5}Z" fill="#292f2d" stroke="#8a928a" stroke-width=".13"/>`);else out.push(circ(x,y,r,'#252b29','#9b9f92',.15));out.push(line(x,y-.2,x,y-r+.55,C.white,.30),'</g>');}
 else out.push(circ(x,y,3.15,C.bg));
 if(q.stage){let lv=s.stageLevels[q.block]?.[q.stage]||0;out.push(line(x+3.7,y,x+5.1,y,C.gold,.2),circ(x+5.9,y,.67,'#19201b',C.dim,.13),circ(x+5.9,y,.48,C.gold,'none',0,`opacity="${lv**.65}" data-stage="${q.stage}" data-env="${q.block}"`));}
 }else if(q.kind==='switch'){
 if(!art){let points=Array.from({length:6},(_,i)=>`${x+4.04*Math.cos(i*Math.PI/3)},${y+4.04*Math.sin(i*Math.PI/3)}`).join(' ');out.push(`<polygon points="${points}" fill="#454e48" stroke="#929b8a" stroke-width=".17"/>`,circ(x,y,2.8,'#212923','#a2ad9c',.17));let dx=q.positions.length===2?(v?2.2:-2.2):(v-1)*2.2;out.push(`<path d="M${x} ${y}L${x+dx} ${y}" stroke="#adb8a7" stroke-width="2.0" stroke-linecap="round"/>`,circ(x+dx,y,.73,'#e4e5d6'));}
 else out.push(circ(x,y,2.6,C.bg));
 let names=q.positions,fs=s.labelSwitch;
 for(let si=0;si<names.length;si++){let word=names[si];
 if(s.switchLabels==='symbols'&&q.key==='VCO/LFO')word=word==='VCO'?'≋':'∿';
 else if(s.switchLabels==='symbols'&&q.key==='SHAPE')word=word==='LINEAR'?'△':'∩';
 else if(s.switchLabels==='symbols'&&q.key==='STAGE')word=word==='RISE'?'↗':'↘';
 let xx=x+(names.length===2?(si===0?-4.75:4.75):(si-1)*5.0);
 out.push(`<g class="state-choice" data-index="${si}">`,txt(xx,y-4.7,word,fs,'switch',si===Math.round(v)),rect(xx-2.3,y-5.9,4.6,1.8,'transparent'),'</g>');
 }

 }else{
 out.push(circ(x,y,2.5,art?C.bg:'#25302e',C.gold,.23));if(!art)out.push(circ(x,y,1.85,'#3f4b46'));
 }
 if(!q.block.startsWith('X'))out.push(txt(x,y+5.75,q.label,s.labelKnob,'knob',q.accent));
 if(!art)out.push(circ(x,y,4.7,'none',C.white,.28,'class="focus"'),rect(x-4.9,y-4.8,9.8,9.6,'transparent'));
 out.push('</g>');
 }
 // Short relationship marks stay inside a module. No printed line crosses to another module.
 if(s.relations){for(const b of Object.values(D.blocks)){let pts=D.controls.filter(q=>q.block===b.id);if(['MIX5','MIX4'].includes(b.family)){let rows=pts.filter(q=>/^[1-5]±$/.test(q.key)),dest=pts.find(q=>q.key==='LEVEL'),p0=pos(rows[0],s),p1=pos(dest,s),x=p0.x-6;out.push(line(x,p0.y,x,p1.y,C.gold,.14));for(let q of rows.concat(dest)){let p=pos(q,s);out.push(line(x,p.y,p.x-4.2,p.y,C.gold,.14));}}
 }}
 // Single gutter line; clip segments around text and hardware ink.
 const clearance=s.separatorGap??.5,allBounds=bounds.concat(marks);let lines=[];
 for(let a of unique.values()){const vertical=a[0]===a[2],axis=vertical?a[0]:a[1];let intervals=[[vertical?a[1]:a[0],vertical?a[3]:a[2]]];for(const b of allBounds){let cross0=vertical?b.x0:b.y0,cross1=vertical?b.x1:b.y1;if(axis<cross0-clearance||axis>cross1+clearance)continue;let lo=(vertical?b.y0:b.x0)-clearance,hi=(vertical?b.y1:b.x1)+clearance;intervals=intervals.flatMap(([l,h])=>hi<=l||lo>=h?[[l,h]]:[[l,Math.min(lo,h)],[Math.max(hi,l),h]].filter(([u,v])=>v-u>.6));}for(let [lo,hi]of intervals){if(hi-lo<1.2)continue;lines.push(vertical?line(axis,lo,axis,hi,C.dim,.13):line(lo,axis,hi,axis,C.dim,.13));}}
 out.splice(5,0,`<g class="separators">${lines.join('')}</g>`);
 out.push(txt(d.w/2,d.h-3.8,'INTEGER CELLS / FIXED HARDWARE SCALE / FACTORY SOLDERING / MECHANICAL STACK NOT RELEASED',1.15,'fixed'));
 out.push('</svg>');
 return {svg:out.join(''),bounds,marks,dimensions:d};
}
root.GridRenderer={render,pos,dims,state,C};
})(typeof window==='undefined'?globalThis:window);
