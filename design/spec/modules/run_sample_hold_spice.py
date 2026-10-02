"""Check the captured post-hold RC endpoints against ideal ngspice."""
from pathlib import Path
import json,math,re,subprocess,sys
from .sample_hold import ROOT, family
from .sample_hold_model_contract import model_contract
DECK=ROOT/'design/spec/modules/spice/sample-hold-slew-ideal.cir'
OUT=ROOT/'design/reports/spice/sample_hold.json'
FACTS=ROOT/'.claude/skills/component-bourns-ptv09a-4020f-b504/facts.json'
CASES=(('fast','f',0),('center','c',.5),('slow','s',1))
FAST_REGULARIZER_OHM=.001

def deck(projection):
 rows=['OSC-ES-1 H1/H2 post-hold lag: ideal pre/post buffers, source-derived equivalent bank',
       'Vheld held 0 PULSE(0 5 10m 1u 1u 3 6)', 'Epre pre 0 held 0 1']
 for position,short,fraction in CASES:
  pot=projection['r_pot_nominal_ohm']*fraction if fraction else FAST_REGULARIZER_OHM
  rows += [f'Rmin_{position} pre r{position} {projection["r_min_ohm"]:.17g}',
           f'Rpot_{position} r{position} lag{position} {pot:.17g}',
           f'C{position} lag{position} 0 {projection["c_lag_F"]:.17g}',
           f'Epost_{position} out{position} 0 lag{position} 0 1',
           f'Rload_{position} out{position} 0 100k']
 rows += ['.control', 'tran 20u 2']
 for position,short,_ in CASES:
  rows += [f'meas tran {short}10 WHEN v(out{position})=0.5 RISE=1',
           f'meas tran {short}90 WHEN v(out{position})=4.5 RISE=1']
 return '\n'.join(rows+['quit','.endc','.end'])+'\n'

def extract(output,name):
 m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*([0-9.eE+-]+)',output)
 if not m:raise ValueError(name+' missing from ngspice output')
 value=float(m[1])
 if not math.isfinite(value):raise ValueError(name+' must be finite')
 return value

def timing_error(output,short,expected):
 t10=extract(output,short+'10');t90=extract(output,short+'90')
 if not (0<=t10<t90):raise ValueError('lag thresholds must have increasing nonnegative times')
 if not math.isfinite(expected) or expected<=0:raise ValueError('invalid analytic RC time')
 actual=t90-t10
 error=abs(actual-expected)/expected
 if not math.isfinite(actual) or not math.isfinite(error):raise ValueError('nonfinite RC timing/error')
 if error>0.01:raise AssertionError(f'10-90% time {actual} vs {expected}')
 return actual,error

def require_success(proc):
 text=proc.stdout+'\n'+proc.stderr
 if proc.returncode or re.search(r'(?im)^\s*(?:(?:fatal\s+)?error\b|doanalyses\b|.*\b(?:simulation|run)\b.*\baborted\b)',text):
  raise RuntimeError(text[-2000:])

def build(check=False):
 projection=model_contract(family().parts,json.loads(FACTS.read_text()))
 body=deck(projection)
 if check:
  if not DECK.is_file() or DECK.read_text()!=body:raise SystemExit('sample-hold SPICE deck drift')
 else:DECK.write_text(body)
 proc=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',DECK.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,text=True)
 require_success(proc)
 rows=[]
 for position,short,fraction in CASES:
  resistance=projection['r_min_ohm']+fraction*projection['r_pot_nominal_ohm']
  expected=math.log(9)*resistance*projection['c_lag_F']
  actual,error=timing_error(proc.stdout,short,expected)
  rows.append({'position':position,'nominal_pot_fraction':fraction,'r_min_ohm':projection['r_min_ohm'],'r_pot_ohm':fraction*projection['r_pot_nominal_ohm'],'c_lag_F':projection['c_lag_F'],'calculated_10_90_s':round(expected,9),'ngspice_10_90_s':round(actual,9),'relative_error_percent':round(error*100,5),'status':'PASS - IDEAL RC MODEL ONLY'})
 return {'schema_version':1,'module':'sample_hold','status':'Unvalidated ideal model; no IC, tolerance or physical qualification','oracle':'KiCad 10.0.6 pinned image, ngspice-44.2','deck':DECK.relative_to(ROOT).as_posix(),'instances':'H1 and H2 share this topology; one representative deck run','source_projection':projection,'fast_endpoint_numerical_rheostat_ohm':FAST_REGULARIZER_OHM,'cases':rows,'not_run':[{'check':'LF398 acquisition, hold-step and hot droop','status':'NOT RUN','reason':'No validated LF398 model and physical capacitor/leakage characterization retained.'},{'check':'CD74HC221 70 µs pulse and trigger/button overlap','status':'NOT RUN','reason':'No validated timing/logic model or bench observation; 0.7 R C is a datasheet planning relation at 4.5 V.'},{'check':'OPA4197 output and remote cable stability','status':'NOT RUN','reason':'Issue #49 revised fixed output network passes 12/12 TI OPAx197 model cases; physical cable, board parasitics, component tolerance and temperature checks remain open.'}]}

def main(check=False):
 body=json.dumps(build(check=check),indent=2)+'\n'
 if check:
  if not OUT.is_file() or OUT.read_text()!=body:raise SystemExit('sample-hold SPICE report drift')
 else:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(body)
 print('PASS: ideal RC 10–90% fast/center/slow within 1%; device and bench models NOT RUN')
if __name__=='__main__':main('--check' in sys.argv)
