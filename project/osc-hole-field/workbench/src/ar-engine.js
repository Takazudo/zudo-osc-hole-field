/* R12 educational envelope model, NOT circuit firmware or an analog simulation.
 * Normalized envelope level is separate from the time controls and stage gates.
 * Pure engine is also loaded by the offline Node tests. */
(function(root){
  'use strict';
  const bound=(v,a,b)=>Math.max(a,Math.min(b,v));
  function lamps(phase,level){
    const n=bound(Number.isFinite(level)?level:0,0,1);
    return {rise:phase==='rise'?n:0,fall:phase==='fall'?n:0};
  }
  class Voice {
    constructor(){this.phase='idle';this.level=0;this.elapsed=0;this.startLevel=0;this.gate=false;this.mode='AR';}
    begin(phase){this.phase=phase;this.startLevel=this.level;this.elapsed=0;}
    trigger(){this.begin('rise');}
    setGate(high){const rising=!!high&&!this.gate;this.gate=!!high;if(rising)this.trigger();}
    advance(dt,cfg){
      const mode=['AR','ASR','LOOP'].includes(cfg.mode)?cfg.mode:'AR';
      if(mode!==this.mode&&this.phase==='sustain'&&mode!=='ASR')this.begin('fall');
      this.mode=mode;
      if(this.phase==='sustain'&&!this.gate)this.begin('fall');
      // Gate release during attack of ASR releases from the present level.
      if(mode==='ASR'&&!this.gate&&this.phase==='rise'&&this.elapsed>0)this.begin('fall');
      if(mode==='LOOP'&&this.phase==='idle')this.begin('rise');
      let remaining=Math.max(0,Number.isFinite(dt)?dt:0);
      for(let guard=0;guard<64&&remaining>0;guard++){
        if(this.phase==='idle'){this.level=0;break;}
        if(this.phase==='sustain'){this.level=1;break;}
        const phase=this.phase,duration=Math.max(.005,phase==='rise'?cfg.rise:cfg.fall);
        const step=Math.min(remaining,Math.max(0,duration-this.elapsed));
        this.elapsed+=step;remaining-=step;
        const p=bound(this.elapsed/duration,0,1),curve=cfg.curved;
        this.level=phase==='rise'?this.startLevel+(1-this.startLevel)*(curve?1-(1-p)**3:p):this.startLevel*(curve?(1-p)**3:1-p);
        if(this.elapsed+1e-10<duration)break;
        if(phase==='rise'){
          this.level=1;
          if(mode==='ASR'&&this.gate)this.begin('sustain');else this.begin('fall');
        }else{
          this.level=0;this.begin(mode==='LOOP'?'rise':'idle');
        }
      }
      return this.snapshot();
    }
    snapshot(){return {phase:this.phase,level:this.level,lamps:lamps(this.phase,this.level)};}
  }
  const api={Voice,lamps};root.ARPreview=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
