"""Run bounded ideal-model ngspice checks in the pinned KiCad oracle."""
from pathlib import Path
import json,re,subprocess,sys
from ._builder import ROOT,CELLS
DECKS={
 'bipolar_attenuverter':('attenuverter-ideal.cir',{'v(out0)':(-5,0.001),'v(out05)':(0,0.001),'v(out1)':(5,0.001)}),
 'magnitude_indicator':('magnitude-bridge-ideal.cir',{'@dledp[id]':(5/4990,2e-6),'@dledn[id]':(5/4990,2e-6)}),
 'gate_trigger_input':('gate-threshold-ideal.cir',{'rising':(1.471965,0.002),'falling':(.971509,0.002)}),
 'clip_detector':('clip-window-ideal.cir',{'negative':(-10,.002),'positive':(10,.002)}),
 'stage_indicator':('stage-mask-ideal.cir',{'@dledon[id]':(.0005,2e-5),'@dledoff[id]':(0,1e-6)}),
}
OUT=ROOT/'design/reports/spice/cells.json'

def measured(output,name):
 m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)',output,re.I)
 if not m:raise ValueError(f'{name} missing from ngspice output')
 return float(m[1])

def build():
 rows=[]
 vendor=json.loads((ROOT/'design/reports/spice/precision-output-vendor.json').read_text())
 if vendor['fail_count'] or len(vendor['cases'])!=12:raise AssertionError('precision vendor model target failure; run sweep_precision_vendor for case details')
 for id in CELLS:
  if id=='precision_output':
   rows.append({'id':id,'status':'PASS - TI MODEL ONLY','cases':len(vendor['cases']),'failed_cases':vendor['fail_count'],'report':'design/reports/spice/precision-output-vendor.json','limit':'TI OPAx197 Final 1.3 is applicable to OPA4197, but tolerance, board/cable parasitics and physical stability remain NOT RUN.'})
   continue
  if id not in DECKS:
   rows.append({'id':id,'status':'NOT RUN','reason':'No retained usable vendor/validated circuit model for the full cell; ideal checks cover only named topology cases. No hardware claim.'});continue
  name,expect=DECKS[id];deck='design/spec/cells/spice/'+name
  proc=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',deck],cwd=ROOT,text=True,capture_output=True)
  if proc.returncode:raise RuntimeError(f'{deck}: ngspice exit {proc.returncode}: {proc.stderr[-1000:]}')
  results={}
  for metric,(target,tolerance) in expect.items():
   value=measured(proc.stdout,metric)
   if abs(value-target)>tolerance:raise AssertionError(f'{deck}: {metric}={value}, target {target} ±{tolerance}')
   results[metric]={'value':value,'target':target,'tolerance':tolerance}
  rows.append({'id':id,'status':'PASS - IDEAL MODEL ONLY','deck':deck,'measurements':results,'limit':'Model transfer only; not vendor behavior, stability, tolerance, fault survival or bench qualification.'})
 sweep=json.loads((ROOT/'design/reports/spice/precision-output-sweep.json').read_text())
 failed=sum(x['model_target_10_percent']=='FAIL' for x in sweep['cases'])
 rows.append({'id':'precision_output_ideal_sweep','status':'FAIL - IDEAL MODEL OVERSHOOT TARGET','cases':len(sweep['cases']),'failed_cases':failed,'report':'design/reports/spice/precision-output-sweep.json','limit':'Diagnostic zero-delay high-gain source only; failure does not predict vendor amplifier or hardware response.'})
 rows.append({'id':'remote_buffer_cable_stability','status':'NOT RUN','reason':'No validated OPA4196 model and 300 mm harness parasitic characterization retained; ideal unity source would not establish phase margin.'})
 return {'schema_version':1,'standard_id':'OSC-ES-1','status':'Model-only evidence; all cells remain NEEDS BENCH','oracle':'KiCad 10.0.6 pinned image, ngspice-44.2','cells':rows}

def main(check=False):
 data=build();body=json.dumps(data,indent=2)+'\n'
 if check:
  if not OUT.is_file() or OUT.read_text()!=body:raise SystemExit('SPICE report drift')
 else:
  OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(body)
 print('Recorded: 5 passing ideal-model decks; revised precision TI model 12/12 pass; historical ideal diagnostic 6/12 fail; physical/remote stability NOT RUN')
if __name__=='__main__':main('--check' in sys.argv)
