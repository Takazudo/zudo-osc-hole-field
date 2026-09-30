"""Ideal-opamp transfer check for the proposed six identical AO channels."""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
from design.spec.cells._builder import ROOT

DIR=ROOT/'design/spec/modules/spice'
OUT=ROOT/'design/reports/spice/offset.json'


def run_case(gain, signal, manual, cv):
    alpha=(gain+1)/2
    deck=DIR/f'offset-g{gain:+g}-in{signal:+g}-m{manual:+g}-cv{cv:+g}.cir'
    text=f'''AO ideal-opamp transfer model, no rail saturation
VIN input 0 DC {signal}
VMAN manual 0 DC {manual}
VCV cv 0 DC {cv}
EWIPER wiper 0 input 0 {alpha}
RATTIN input att_sum 100k
RATTFB att att_sum 100k
EATT att 0 wiper att_sum 1e6
RSUMA att sum_node 100k
RSUMM manual sum_node 100k
RSUMC cv sum_node 100k
RSUMFB sum_neg sum_node 100k
ESUM sum_neg 0 0 sum_node 1e6
RRESTIN sum_neg restore_node 100k
RRESTFB out restore_node 100k
EREST out 0 0 restore_node 1e6
.control
op
print v(att) v(sum_neg) v(out)
quit
.endc
.end
'''
    deck.write_text(text)
    p=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(deck.relative_to(ROOT))],cwd=ROOT,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    vals={name:float(value) for name,value in re.findall(r'v\((att|sum_neg|out)\)\s*=\s*([-+\d.eE]+)',p.stdout+p.stderr)}
    if len(vals)!=3:raise ValueError((deck,vals,p.stdout,p.stderr))
    expected=gain*signal+manual+cv
    assert abs(vals['out']-expected)<.001,(gain,signal,manual,cv,vals,expected)
    return {'deck':str(deck.relative_to(ROOT)),'gain_setting':gain,'input_V':signal,'manual_V':manual,'offset_CV_V':cv,'expected_linear_V':expected,'model_output_V':round(vals['out'],6),'status':'PASS - ideal linear topology only'}


def main():
    from design.spec.modules.offset import family
    parts=family().parts
    def value(role):
        return next(p.value for p in parts if p.attributes.get('Role')==role)
    for role in ('offset:R_SUM_ATTEN','offset:R_SUM_MANUAL','offset:R_SUM_CV',
                 'offset:R_SUM_FB','offset:R_RESTORE_IN','offset:R_RESTORE_FB'):
        assert value(role)=='100 kΩ',(role,value(role))
    assert value('bipolar_attenuverter:R_IN')=='100000 Ω'
    assert value('bipolar_attenuverter:R_FB')=='100000 Ω'
    DIR.mkdir(parents=True,exist_ok=True)
    rows=[]
    for gain,signal,manual,cv in [(-1,1,0,0),(0,1,0,0),(1,1,0,0),
                                  (-1,-5,-5,-5),(1,5,5,5),(1,1,2,-3),
                                  (-.5,4,1,-2)]:
        rows.append(run_case(gain,signal,manual,cv))
    report={'schema_version':1,'module':'offset','status':'PASS - ideal linear transfer only',
            'oracle':'pinned KiCad 10 ngspice','runs':rows,
            'limits':'Ideal opamps have unlimited rails; ±15 V endpoint cases demonstrate the mathematical demand, not realizable output. Pot taper/contact, source impedance, tolerances, offset, drift and clipping are excluded.'}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+'\n')
    print('AO ideal transfer cases:',len(rows),'PASS')


if __name__=='__main__':main()
