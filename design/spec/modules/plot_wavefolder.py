"""Render required PNGs from oracle traces; matplotlib3.9.2 in disposable venv.

Run .circuit-cache/wavefolder-plot/bin/python -m design.spec.modules.plot_wavefolder
after run_wavefolder_spice. No generated waveform values are invented here.
"""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from design.spec.modules.wavefolder import ROOT
CACHE=ROOT/'.circuit-cache/wavefolder-spice'
ASSETS=ROOT/'doc/public/assets/osc-hole-field'
REPORT=ROOT/'design/reports/spice/wavefolder.json'

def rows(stem):return [[float(v) for v in line.split()] for line in (CACHE/(stem+'.txt')).read_text().splitlines()[1:]]

def main():
 report=json.loads(REPORT.read_text());plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.25})
 fig,axes=plt.subplots(1,3,figsize=(15,4.6),sharex=True,sharey=True)
 for ax,bias in zip(axes,(-5,0,5)):
  for fold,color in zip((.25,1.5,3,5),('#2563eb','#059669','#d97706','#dc2626')):
   stem=f'wavefolder-dc-f{str(fold).replace(".","p")}-b{str(bias).replace("-","n")}'
   data=rows(stem);ax.plot([r[0] for r in data],[r[1] for r in data],label=f'FOLD {fold/5:g}',color=color,lw=1.5)
  ax.set(title=f'Injected manual bias {bias/10:+.1f} V',xlabel='Buffered IN (V)',xlim=(-5,5),ylim=(-3.2,3.2));ax.axhline(0,color='#64748b',lw=.6);ax.legend(fontsize=8,loc='upper left')
 axes[0].set_ylabel('PRE_AC internal voltage (V)')
 fig.suptitle('Wavefolder static transfer — model only, before AC coupling\nFOLD is normalized manual position; BIAS CV = 0 V',fontsize=12)
 fig.tight_layout();p=ASSETS/'wavefolder-transfer-model.png';fig.savefig(p,dpi=160,metadata={'Software':'matplotlib '+matplotlib.__version__});plt.close(fig)
 data=[r for r in rows('wavefolder-sine-transient') if r[0]>=.76]
 # Downsample only for rendering; measurements use the complete oracle trace.
 step=max(1,len(data)//6000);data=data[::step]
 import math
 fig,axes=plt.subplots(2,1,figsize=(12,6),sharex=True)
 axes[0].plot([1000*r[0] for r in data],[5*math.sin(2*math.pi*100*r[0]) for r in data],label='Applied IN fixture',color='#64748b',lw=1)
 axes[0].plot([1000*r[0] for r in data],[r[1] for r in data],label='PRE_AC internal',color='#d97706',lw=1.2)
 axes[1].plot([1000*r[0] for r in data],[r[5] for r in data],label='OUT jack into 100 kΩ',color='#2563eb',lw=1.2)
 for ax in axes:ax.set_ylabel('Voltage (V)');ax.legend(loc='upper right');ax.axhline(0,color='#64748b',lw=.6)
 axes[1].set_xlabel('Time (ms)')
 fig.suptitle('100 Hz sine, ±5 V IN; maximum FOLD, +0.25 V bias, full LEVEL — model only\nAC-coupled OUT after settling; ideal amplifiers and generic diodes',fontsize=12)
 fig.tight_layout();q=ASSETS/'wavefolder-transient-model.png';fig.savefig(q,dpi=160,metadata={'Software':'matplotlib '+matplotlib.__version__});plt.close(fig)
 receipts={'schema_version':1,'status':'Rendered from retained oracle trace files; model only','renderer':'matplotlib '+matplotlib.__version__,'report_sha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),'plot_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'images':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (p,q)}}
 (ROOT/'design/reports/spice/wavefolder-plots.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print('Rendered',p.name,q.name)
if __name__=='__main__':main()
