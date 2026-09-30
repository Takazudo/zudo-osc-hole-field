"""Diagnostic load/cable sweep using an intentionally ideal high-gain amplifier."""
from pathlib import Path
import itertools,json,re,subprocess
from ._builder import ROOT
DECK=ROOT/'design/spec/cells/spice/precision-output-sweep.cir'
OUT=ROOT/'design/reports/spice/precision-output-sweep.json'
LOADS={'open':1e12,'100k':1e5,'10k':1e4}
CAPS={'0':0,'100p':1e-10,'1n':1e-9,'5n':5e-9}

def deck():
 lines=['OSC-ES-1 dual feedback diagnostic; ideal zero-delay 100000 V/V source, not OPA4197','']
 cases=[]
 for n,((lname,load),(cname,cap)) in enumerate(itertools.product(LOADS.items(),CAPS.items()),1):
  tag=str(n);cases.append((tag,lname,cname))
  lines += [f'Vsig{tag} sig{tag} 0 PULSE(-5 5 0 1u 1u 500u 1m)',f'Eamp{tag} drive{tag} 0 sig{tag} fb{tag} 1e5',f'Risoa{tag} drive{tag} mid{tag} 499',f'Risob{tag} mid{tag} jack{tag} 499',f'Rfb{tag} jack{tag} fb{tag} 10k',f'Cfast{tag} drive{tag} fb{tag} 100p',f'Rload{tag} jack{tag} 0 {load:g}']
  if cap:lines.append(f'Cload{tag} jack{tag} 0 {cap:g}')
 lines+=['.control','tran 1u 2m']
 for tag,_,_ in cases:
  lines += [f'meas tran pmax{tag} MAX v(jack{tag}) FROM=0 TO=450u',f'meas tran nmin{tag} MIN v(jack{tag}) FROM=500u TO=950u',f'meas tran pset{tag} FIND v(jack{tag}) AT=400u',f'meas tran nset{tag} FIND v(jack{tag}) AT=900u']
 lines+=['quit','.endc','.end','']
 return '\n'.join(lines),cases

def metric(output,name):
 m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)',output,re.I)
 if not m:raise ValueError(name+' missing')
 return float(m[1])

def run(check=False):
 body,cases=deck()
 if check and DECK.read_text()!=body:raise SystemExit('precision sweep deck drift')
 if not check:DECK.write_text(body)
 proc=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',DECK.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,text=True)
 if proc.returncode:raise RuntimeError(proc.stderr[-1000:])
 rows=[]
 for tag,load,cap in cases:
  vals={x:metric(proc.stdout,x+tag) for x in ('pmax','nmin','pset','nset')}
  overshoot=max(0,(vals['pmax']-5)/10,(-5-vals['nmin'])/10)*100
  rows.append({'load':load,'cable_capacitance':cap,'positive_peak_V':vals['pmax'],'negative_peak_V':vals['nmin'],'positive_settled_V':vals['pset'],'negative_settled_V':vals['nset'],'step_overshoot_percent':round(overshoot,3),'model_target_10_percent': 'FAIL' if overshoot>10 else 'PASS - IDEAL MODEL ONLY'})
 report={'schema_version':1,'status':'DIAGNOSTIC MODEL ONLY - NOT HARDWARE QUALIFICATION','amplifier':'ideal zero-delay dependent source, open-loop gain 100000 V/V; no OPA4197 frequency, slew, output-current or saturation behavior','conditions':'100 pF local feedback; two 499 Ω isolation resistors; 10 kΩ remote DC feedback; ±5 V steps; 0/100 pF/1 nF/5 nF cable; open/100 kΩ/10 kΩ loads','target':'at most 10% overshoot, settle within 1 mV by 1 ms, no sustained oscillation','vendor_model':'NOT RUN - validated OPA4197 dynamic macromodel unavailable','cases':rows}
 text=json.dumps(report,indent=2)+'\n'
 if check:
  if OUT.read_text()!=text:raise SystemExit('precision sweep report drift')
 else:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(text)
 failures=sum(r['model_target_10_percent']=='FAIL' for r in rows)
 print(f'Historical ideal diagnostic: {len(rows)} cases, {failures} overshoot failures; revised TI model is checked separately, physical bench NOT RUN')
 if failures:raise SystemExit(1)
if __name__=='__main__':
 import sys
 run('--check' in sys.argv)
