/* Display-only hardware, keyed exclusively by immutable placement UIDs. */
(function(){
'use strict';
const NS='http://www.w3.org/2000/svg';
window.PanelHardware=Object.freeze({append(doc,svg,source,a){
 const g=doc.createElementNS(NS,'g');g.id='hardware-preview';g.setAttribute('pointer-events','none');
 const node=(parent,tag,attrs)=>{const e=doc.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));parent.append(e);return e;};
 const circle=(p,r,fill,stroke='#a7aca8',width=.2)=>node(p,'circle',{cx:0,cy:0,r,fill,stroke,'stroke-width':width});
 const hex=r=>Array.from({length:6},(_,i)=>`${r*Math.cos(i*Math.PI/3)},${r*Math.sin(i*Math.PI/3)}`).join(' ');
 for(const q of source.lock.placements){
  const category=q.kind==='jack'?'Jacks':q.kind==='pot'?'Knobs':q.kind==='led'?'LEDs':'Switches';
  if(!a.hardwareVisible||!a['hardware'+category])continue;
  const type={jack:'jack',pot:'knob',switch:'toggle',octave:'rotary',button:'button',led:'led'}[q.kind];
  const r={jack:4.15,pot:6,switch:4.04,octave:4,button:2.5,led:source.params.indicator_window.diameter_mm/2}[q.kind];
  const h=node(g,'g',{'data-hardware-uid':q.uid,'data-hardware-type':type,'data-preview-radius':r,transform:`translate(${q.x_mm} ${q.y_mm})`});
  const title=node(h,'title',{});title.textContent=`${q.ref} ${q.component||q.led_type}: ${type} illustration; ${q.kind==='led'?'locked window diameter, unlit appearance':'illustrative cap/nut/lever; not a fit specification'}`;
  if(type==='jack'){
   node(h,'polygon',{points:hex(r),fill:'#aeb4b2',stroke:'#e0e4df','stroke-width':.22});
   circle(h,3.15,'#d1d5d1','#727a76');circle(h,2.5,'#535c59','#edf0e8');circle(h,1.75,'#080b0b','#272e2b');
   node(h,'path',{d:'M-1.1,-1.1 Q0,-1.8 1.1,-1.1',fill:'none',stroke:'#a6aea8','stroke-width':.24});
  }else if(type==='knob'||type==='rotary'){
   circle(h,r,'#1c2426','#a4adac',.3);circle(h,r-.65,'#333e40','#546164',.15);
   for(let i=0;i<12;i++){const angle=i*Math.PI/6;node(h,'line',{x1:(r-.5)*Math.cos(angle),y1:(r-.5)*Math.sin(angle),x2:(r-.15)*Math.cos(angle),y2:(r-.15)*Math.sin(angle),stroke:'#82908d','stroke-width':.18});}
   node(h,'path',{d:`M0,-${r-.8} L0,-1`,stroke:type==='rotary'?'#d4b56b':'#faf8e8','stroke-width':.6,'stroke-linecap':'round'});
   if(type==='rotary')circle(h,.65,'#b79a59','none',0);
  }else if(type==='toggle'){
   node(h,'polygon',{points:hex(r),fill:'#9fa9a5',stroke:'#e2e6df','stroke-width':.2});circle(h,2.6,'#343e3c','#d7dcd5');
   node(h,'path',{d:'M0,0 L1.9,0',stroke:'#d3dcd8','stroke-width':1.8,'stroke-linecap':'round'});node(h,'circle',{cx:1.9,cy:0,r:.75,fill:'#f5f5eb'});
  }else if(type==='button'){
   circle(h,r,'#909b95','#d3d9ce');circle(h,1.9,'#923e34','#bd695a');node(h,'path',{d:'M-1,-.9 Q0,-1.4 1,-.9',stroke:'#e3a093',fill:'none','stroke-width':.2});
  }else{circle(h,r,q.led_type==='clip'?'#743d3b':'#a3aaa0','#c7cec0',.1);circle(h,r*.35,'#d6dbd2','none',0);}
 }
 svg.append(g);
}});
})();
