/* Ideal post-sample RC lag. Not an LF398 analogue model or hardware qualification. */
(function(root){
'use strict';
const clamp=x=>Math.min(1,Math.max(0,x));
function tauFor(position){if(!Number.isFinite(position))throw new TypeError('SLEW must be finite');return (2200+500000*clamp(position))*0.0000005;}
class Channel {
 constructor(){this.target=0;this.output=0;this.sampled=false;this.position=0;this.time=0;}
 setSlew(position){if(!Number.isFinite(position))throw new TypeError('SLEW must be finite');this.position=clamp(position);return this;}
 sample(volts){if(!Number.isFinite(volts))throw new TypeError('Sample must be finite');this.target=volts;this.sampled=true;return this;}
 advance(dt){if(!Number.isFinite(dt)||dt<0)throw new RangeError('Nonnegative finite dt required');if(this.sampled){const a=-Math.expm1(-dt/tauFor(this.position));this.output+=a*(this.target-this.output);}this.time+=dt;return this.snapshot();}
 snapshot(){return {target:this.sampled?this.target:null,output:this.output,position:this.position,tau:tauFor(this.position),sampled:this.sampled,settled:this.sampled&&Math.abs(this.target-this.output)<0.00001};}
}
const api={Channel,tauFor};if(typeof module==='object'&&module.exports)module.exports=api;root.SHSlew=api;
})(typeof globalThis==='object'?globalThis:this);
