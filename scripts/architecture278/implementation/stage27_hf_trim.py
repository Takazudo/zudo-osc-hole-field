"""Exact HF trim source candidate; no native or measured calibration claims."""
import argparse
import ast
import copy
import datetime
import re
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from stage25_correction import supplier_observation

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage27'
BASE='686cc59a6409e87c9df378d84661c2450a0c7e1c'
CORE_PRIMARY={'path': 'circuit/sources/ic-library/AS3340.pdf', 'physical_pdf_page_index': [0, 1], 'printed_page_label': ['1', '2'], 'revision': '2020 v.7', 'scope': 'Pin7 high-frequency tracking; pin13 linear input; Rs V/oct trim and RZ/RT compensation roles. Reference diagram is not as-built qualification.', 'sha256': '66108a3ddcc78a158d66974a497801ce6a429d465b338f6c8d656fd7ddce815e', 'url': 'https://www.alfatriode.lv/eng/sc/AS3340.pdf'}
PINS={'1':'/O1/HF_PIN','2':'/O1/LINEAR_REF','3':'AGND'}
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}

def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(p.read_text())
def dump(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(c,e):
    expected={'ref':'RVO1109','role':'oscillator:HF_TRIM','manufacturer':'Bourns','mpn':'TC33X-2-203E','supplier_code':'C720648',
        'package':'TC33X-2 3 mm SMD rotational-stop top adjustment','resistance_ohm':20000,'tolerance_fraction':.25,
        'minimum_resistance_max_fraction_TR':.02,'contact_resistance_variation_max_fraction':.05,
        'primary_power_W_at_70C':.15,'catalog_power_W':.1,'voltage_max_V':50,'temperature_C':[-40,100],
        'tempco_ppm_per_C':250,'adjustment_angle_deg':[250,290],'rotation_cycles_test':20,'rotation_test_TR_change_fraction':.1,
        'tool_cross_slot_mm':1.7,'shaft_push_force_less_than_N':4.9,'pins':PINS,
        'population':'EXACT_SOURCE_CANDIDATE_NOT_RELEASED','production_CAD_applied':False,'native':'NOT_RUN',
        'physical_coverage':'NEEDS BENCH','new_controls':0,'frequency_coverage_Hz':None,'tracking_acceptance':False,'order_ready':False}
    need(c==expected,'exact reviewed identity, ratings, role and physical boundary')
    o=e['supplier_observation']
    need(o['componentModelEn']==c['mpn'] and o['componentCode']==c['supplier_code'] and o['componentBrandEn']=='BOURNS','supplier identity')
    need(o['componentSpecificationEn']=='SMD-3P,3.8x3.6mm' and o['assemblyMode']=='smtWeld','supplier package/process')
    need(o['visible_services']=={'Assembly Type':['SMT Assembly'],'PCBA Type':['Economic and Standard']},'dated assembly declaration')
    need(o['stock_is_allocated'] is False and o['order_accepted'] is False,'no order promise')
    for key,url,authority in [('manufacturer','https://www.bourns.com/docs/Product-Datasheets/TC33.pdf','MANUFACTURER_PRIMARY'),
                              ('supplier','https://jlcpcb.com/partdetail/BOURNS-TC33X_2203E/C720648','DISTRIBUTOR_IDENTITY')]:
        r=e[key];need(r['url']==url and r['authority']==authority and r['availability']=='AVAILABLE','evidence authority')
        need(re.fullmatch(r'[0-9a-f]{64}',r['sha256']) is not None and r['sha256']!='0'*64,'valid byte hash')
        stamp=datetime.datetime.fromisoformat(r['retrieved_UTC'])
        need(stamp.tzinfo is not None and stamp.utcoffset()==datetime.timedelta(0) and stamp.date()==datetime.date(2026,10,17),'dated UTC retrieval')
    need(e['core_primary']==CORE_PRIMARY,'exact retained AS3340 primary identity')


def materialize(netlist,c):
    old=copy.deepcopy(netlist);packages=old['packages']
    need(len(packages)==250 and sum(len(p['pins']) for p in packages)==806 and sum(len(p['units']) for p in packages)==329,'complete original candidate graph')
    rows=[p for p in packages if p['ref']==c['ref']];need(len(rows)==1,'unique target')
    p=rows[0];need(p['pins']==PINS and p['attributes']['Role']==c['role'] and p['owner']=='rear-core','existing HF topology/access role')
    need(p['attributes']['MPN']==p['attributes']['Manufacturer']==p['attributes']['LCSC']=='','historical unresolved identity')
    p['attributes'].update(MPN=c['mpn'],Manufacturer=c['manufacturer'],LCSC=c['supplier_code'])
    validate_delta(netlist,old,c)
    return old


def validate_delta(before,after,c):
    expected=copy.deepcopy(before)
    row=next(p for p in expected['packages'] if p['ref']==c['ref'])
    row['attributes'].update(MPN=c['mpn'],Manufacturer=c['manufacturer'],LCSC=c['supplier_code'])
    need(after==expected,'no net/NC/unit/metadata/placement omission or extra selection')


def source_values():
    tree=ast.parse((ROOT/'design/spec/modules/oscillator.py').read_text());calls={}
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='b' and n.func.attr in ('r','trim'):
            try:args=[ast.literal_eval(a) for a in n.args]
            except (ValueError,TypeError):continue
            calls[args[0]]=args[1:]
    expected={'HF_TRIM':['20 kΩ','HF_PIN','LINEAR_REF','AGND'],
              'BASE_TRIM':['10 kΩ','BASE_REFN5','BASE_ADJ','BASE_REF5'],'BASE_FEED':['1 MΩ','BASE_ADJ','EXPO_SUM'],
              'RZ_FIXED':['24 kΩ','SCALE1','RZ_TRIM'],'RZ_TRIM':['10 kΩ','RZ_TRIM','AGND'],
              'RT':['5.72 kΩ','SCALE2','AGND'],'RS_FIXED':['1.5 kΩ','SCALE_PIN','SCALE_ADJ'],
              'SCALE_TRIM':['1 kΩ','SCALE_ADJ','AGND'],'LINEAR_REFERENCE':['1.2 MΩ','+12V','LINEAR_REF'],
              'LINEAR_FILTER':['470 Ω','LINEAR_REF','LINEAR_FILTER']}
    need(all(calls.get(k)==v for k,v in expected.items()),'actual oscillator source values/topology')
    return expected


def network(total,alpha,vhf,vw):
    need(all(type(v) in (float,int) and math.isfinite(v) for v in (total,alpha,vhf,vw)),'finite network inputs')
    need(15000<=total<=25000 and 0<alpha<1,'interior track model only; no ideal endpoint promise')
    top=(1-alpha)*total;bottom=alpha*total
    return {'R_HF_wiper_ohm':top,'R_wiper_ground_ohm':bottom,
            'core13_current_A':(vhf-vw)/top+(12-vw)/1200000-vw/bottom,
            'track_segment_power_W':(vhf-vw)**2/top+vw**2/bottom}


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed')
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed={'scripts/architecture278/implementation/'+n for n in ('stage27_hf_trim.py','test_stage27_hf_trim.py')}
    need(all(p.startswith(REL+'stage27/') or p in allowed for p in new),'out-of-scope addition')
    return BASE


def build(cache=False):
    c=read(OUT/'candidate.json');e=read(OUT/'evidence.json');validate(c,e)
    if cache:
        for key in ('manufacturer','supplier'):
            need(sha(ROOT/e[key]['raw_cache'])==e[key]['sha256'],'retained receipt bytes')
        need((ROOT/e['manufacturer']['raw_cache']).read_bytes().startswith(b'%PDF-'),'real PDF')
        need(supplier_observation((ROOT/e['supplier']['raw_cache']).read_text(),'C720648')==e['supplier_observation'],'supplier observation reproduction')
    need(sha(ROOT/e['core_primary']['path'])==e['core_primary']['sha256'],'retained core primary')
    source=read(ROOT/REL/'candidate-netlist.json');inventory=materialize(source,c)
    mech=read(ROOT/REL/'cluster-refinement-report.json')
    placement=next(p for p in mech['placements'] if p['ref']=='RVO1109')
    need(placement['rear_facing'] is True and placement['trim_tool_diameter_mm']==6 and placement['origin_mm']==[34.5,37.4],'retained rear access reservation')
    report={'status':'SOURCE_CANDIDATE_SELECTED_PHYSICAL_OPEN','candidate':c,'source_values':source_values(),
        'counts':{'packages':250,'pins':806,'units':329,'selected_HF_trim':1},'retained_placement':placement,
        'AO_stage26_inventory_sha256':sha(ROOT/REL/'stage26/candidate-inventory.json'),
        'analytical':{'track_total_ohm':[15000,25000],'endpoint_resistance_max_ohm_at_25k':500,
            'unloaded_ideal_Rth_max_ohm':6250,'nominal_base_current_A':[-5e-6,5e-6],
            'nominal_base_pitch_input_equivalence_V':[-.5,.5],'nominal_ideal_scale_series_ohm':[1500,2500],
            'nominal_ideal_RZ_series_ohm':[24000,34000],
            'HF_DC_equation':'(VHF-VW)/Rt + (12-VW)/1.2e6 = VW/Rb + Icore13',
            'HF_transient_branch':'470 ohm series 10 nF to AGND retained; capacitor open only in DC idealization',
            'segment_power_equation_W':'(VHF-VW)^2/Rt + VW^2/Rb',
            'counterfactual_example_not_operating_point':network(20000,.5,1,0),
            'coverage_Hz':None,'coverage_cents':None,'range_qualified':False,
            'conditions':'Nominal rails/fixed resistors and ideal source nodes for base/scale/RZ arithmetic; pot end resistance, component tolerances and loading preclude guaranteed endpoint or musical correction span. HF node voltage/core current require actual operating point.'},
        'power_discrepancy':'Manufacturer 0.15 W at 70 C versus catalog 0.1 W retained; no delivered-lot rating/process or segment dissipation qualification.',
        'next_boundary':'Physical rear-access/process review and actual base/scale/HF adjustment coverage on an assembled oscillator. DIN questions remain exactly in stage25/fabrication-request.md; no supplier contact.',
        'physical':'NOT_RUN','native_request':'NONE','preservation_baseline':protected()}
    files=[OUT/'candidate.json',OUT/'evidence.json',OUT/'README.md',ROOT/REL/'README.md',ROOT/REL/'candidate-netlist.json',
        ROOT/REL/'cluster-refinement-report.json',ROOT/REL/'stage26/acceptance-report.json',ROOT/REL/'stage26/candidate-inventory.json',
        ROOT/REL/'stage25/fabrication-request.md',ROOT/'design/spec/modules/oscillator.py',
        ROOT/'footprints/kicad/zudo-osc-hole-field.pretty/Potentiometer_Bourns_TC33X_Vertical.kicad_mod',
        ROOT/'doc/src/content/docs/architecture/osc-block-osc.mdx',Path(__file__),Path(__file__).with_name('test_stage27_hf_trim.py'),
        Path(__file__).with_name('check_source.py'),Path(__file__).with_name('stage25_correction.py'),Path(__file__).with_name('stage23_jlc.py')]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    report['inventory_sha256']=hashlib.sha256(dump(inventory).encode()).hexdigest()
    return inventory,report


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage27-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/check_source.py'],cwd=checkout,check=True)
            subprocess.run([sys.executable,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage26_acceptance.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage26 source checkpoint including historical checks')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage27/report.json',REL+'stage27/candidate-inventory.json'}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-cache','check-history','check-review'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.check_history:history()
    inv,rep=build(a.check_cache)
    for name,data in [('candidate-inventory.json',inv),('report.json',rep)]:
        path=OUT/name
        if a.check:need(path.read_text()==dump(data),'deterministic drift '+name)
        else:path.write_text(dump(data))
    if a.check_review:review()
    print('PASS exact HF source candidate; complete 250/806/329 graph; measured coverage NOT RUN')
if __name__=='__main__':main()
