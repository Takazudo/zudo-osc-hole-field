"""Check the captured post-hold RC endpoints against ideal ngspice."""
from pathlib import Path
import json,math,re,subprocess,sys
from .sample_hold import ROOT
DECK=ROOT/'design/spec/modules/spice/sample-hold-slew-ideal.cir'
OUT=ROOT/'design/reports/spice/sample_hold.json'
CASES={'fast':('f10','f90',2200),'center':('c10','c90',252200),'slow':('s10','s90',502200)}

def extract(output,name):
 m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*([0-9.eE+-]+)',output)
 if not m:raise ValueError(name+' missing from ngspice output')
 return float(m[1])

def build():
 proc=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',DECK.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,text=True)
 if proc.returncode:raise RuntimeError(proc.stderr[-1000:])
 rows=[]
 for position,(t10,t90,resistance) in CASES.items():
  actual=extract(proc.stdout,t90)-extract(proc.stdout,t10)
  expected=math.log(9)*resistance*500e-9
  error=abs(actual-expected)/expected
  if error>0.01:raise AssertionError(f'{position} 10-90% time {actual} vs {expected}')
  rows.append({'position':position,'r_min_ohm':2200,'r_pot_ohm':resistance-2200,'c_lag_F':500e-9,'calculated_10_90_s':round(expected,9),'ngspice_10_90_s':round(actual,9),'relative_error_percent':round(error*100,5),'status':'PASS - IDEAL RC MODEL ONLY'})
 return {'schema_version':1,'module':'sample_hold','status':'Unvalidated ideal model; no IC, tolerance or physical qualification','oracle':'KiCad 10.0.6 pinned image, ngspice-44.2','deck':DECK.relative_to(ROOT).as_posix(),'instances':'H1 and H2 share this topology; one representative deck run','cases':rows,'not_run':[{'check':'LF398 acquisition, hold-step and hot droop','status':'NOT RUN','reason':'No validated LF398 model and physical capacitor/leakage characterization retained.'},{'check':'CD74HC221 70 µs pulse and trigger/button overlap','status':'NOT RUN','reason':'No validated timing/logic model or bench observation; 0.7 R C is a datasheet planning relation at 4.5 V.'},{'check':'OPA4197 output and remote cable stability','status':'NOT RUN','reason':'Issue #49 revised fixed output network passes 12/12 TI OPAx197 model cases; physical cable, board parasitics, component tolerance and temperature checks remain open.'}]}

def main(check=False):
 body=json.dumps(build(),indent=2)+'\n'
 if check:
  if not OUT.is_file() or OUT.read_text()!=body:raise SystemExit('sample-hold SPICE report drift')
 else:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(body)
 print('PASS: ideal RC 10–90% fast/center/slow within 1%; device and bench models NOT RUN')
if __name__=='__main__':main('--check' in sys.argv)
