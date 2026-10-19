"""Additive architecture comparison; no production outputs or adoption."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from design.spec.modules import offset, mult
from scripts.schgen.core import designator
HERE = Path(__file__).resolve().parent

def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

def grow(a, d):
    return [a[0]-d, a[1]-d, a[2]+d, a[3]+d]

def inventory(module, rear_all=False):
    fs, instances = module.specification(); f = fs[0]; inst = instances[0]
    packages = {}; nets = defaultdict(set)
    for p in f.parts:
        if not p.on_board or not p.footprint: continue
        region = ('front' if p.panel_refs else 'rear') if rear_all else p.attributes['BoardRegion']
        ref = designator(p, inst)
        row = packages.setdefault(ref, {'region': region, 'value': p.value, 'footprint': p.footprint,
                                        'mpn': p.attributes.get('MPN',''), 'units': []})
        if row['region'] != region: raise ValueError('split package '+ref)
        row['units'].append({'key':p.key, 'unit':p.unit, 'pins':p.pins})
        for net in p.pins.values():
            if net is not None: nets[net].add(region)
    crossing = {n:sorted(r) for n,r in sorted(nets.items()) if len(r)>1}
    return {'instances':[i.name for i in instances], 'packages':packages, 'crossing_nets':crossing,
            'declared_sensitive_net_regions':{n:sorted(nets[n]) for n in f.sensitive_nets},
            'region_counts':{r:sum(p['region']==r for p in packages.values()) for r in sorted({p['region'] for p in packages.values()})}}

def build():
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())
    whole=json.loads((ROOT/'design/architecture-278/implementation/stage36/whole-layout-review/view-data.json').read_text())
    ids=[f'A{i:02}' for i in range(1,7)]+['B1','B2']
    markers=[p for p in lock['placements'] if p['block'] in ids]
    boxes=[]
    # Capacity trial only: six identical29-package boards, not six A01 stacks.
    for i in range(6):
        x=180+(i%3)*45;y=180+(i//3)*50
        boxes.append({'id':ids[i]+' core','xy':[x,y,x+40,y+45],'z':[74,75.6],
                      'status':'UNALLOCATED CAPACITY TRIAL; not populated/routed'})
    obstacles=[b for b in whole['boxes'] if b['block'] not in ids]
    hits=[{'core':a['id'],'reservation':b['name'],'xy':b['xy'],'z':b['z'],
           'status':'OCCUPIED/UNKNOWN projection; no clearance credit from conceptual z'}
          for a in boxes for b in obstacles if overlap(grow(a['xy'],2),b['xy'])]
    headers=json.loads((ROOT/'design/reports/connectors.json').read_text())['headers']
    touched=[h for h in headers if any(any(str(p['net']).startswith('/'+i+'/') for i in ids) for p in h['pins'])]
    # Wire bundles identified by paired end IDs; no assumption that global power belongs solely to these families.
    bundles=sorted({h['id'].rsplit('-',1)[0] for h in touched})
    sources=['design/grid/placements.lock.json','design/partition/partition.json','design/reports/connectors.json',
             'design/architecture-278/implementation/stage36/whole-layout-review/view-data.json',
             'design/architecture-278/implementation/stage36/idc-service-placement/candidate.json']
    sources+= [str(p.relative_to(ROOT)) for p in sorted((ROOT/'design/spec').rglob('*.py'))]
    sources+=['scripts/schgen/core.py']
    pinouts={
        'AO-C10':['REF5','AGND','REFN5','AGND','IN_REMOTE','AGND','Cc045d2_W','AGND','C38cac0_W','AGND'],
        'AO-J10':['IN_BUFFER','AGND','OFFSET_BUFFER','AGND','REF5','AGND','REFN5','AGND','SUM_NEG','AGND'],
        'P8':['+12V','AGND','-12V','AGND','+5V','AGND',None,None],
        'P8-core':['+12V','AGND','-12V','AGND',None,'AGND',None,None]}
    return {'baseline':'c3bbcf0c890aff329bb7a3374cc51cd38c072929','adopted':False,
            'recommendation':'DEVELOP conservative family reuse; DO NOT ADOPT hardware architecture yet',
            'families':{'AO':inventory(offset),'MULT':inventory(mult)},
            'rejected_passive_front':{'AO':inventory(offset,True),'MULT':inventory(mult,True)},
            'pinouts':{k:{str(i+1):n for i,n in enumerate(v)} for k,v in pinouts.items()},
            'pinout_status':'NEW PROJECT-SPECIFIC PROPOSAL; NOT plug-compatible with Stage36 or Eurorack',
            'fixed_markers':markers,'rear_capacity_trials':boxes,'clearance_allowance_mm':2,
            'trial_pair_hits':[[a['id'],b['id']] for i,a in enumerate(boxes) for b in boxes[i+1:] if overlap(grow(a['xy'],2),grow(b['xy'],2))],
            'occupied_unknown_projection_hits':hits,
            'unmodeled_occupied':['KEEP_K1402_INCUMBENT','incumbent core unless separately removed','foreign component heights and tails','cables and strain support','mounts and tools','complete service sweep'],
            'integrated_fit':'BLOCKED / UNKNOWN; empty trial pair screen is not fit',
            'baseline_signal_headers':[h['id'] for h in touched],'baseline_signal_bundles':bundles,
            'comparison':{'baseline':{'whole_instrument_boards':10,'whole_instrument_unique_designs':10,'family_exclusive_boards':0,'signal_header_ends_touching_families':len(touched),'signal_bundles_touching_families':len(bundles),'power_count':'shared; not attributed'},
              'individual':{'family_boards':20,'unique_designs':4,'signal_cables':12,'power_cables':14,'all_cables':26,'header_ends_including_distribution':52,'socket_terminations':52,'mating_actions':52,'core_mount_sites_trial':24},
              'shared_strips':{'family_boards':10,'unique_designs':4,'signal_cables':12,'power_cables':14,'all_cables':26,'header_ends_including_distribution':52,'socket_terminations':52,'mating_actions':52,'core_mount_sites_trial':24}},
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}

def svg(data):
    s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 405">',
       '<rect width="760" height="405" fill="#fafafa"/>',
       '<g font-family="sans-serif" fill="#222"><text x="15" y="23" font-size="16">AO / MULT reuse: proposal only — integrated fit BLOCKED</text>',
       '<text x="15" y="45" font-size="11">Panel XY (mm); unchanged markers. Red: occupied/unknown foreign projections.</text>',
       '<g transform="translate(15,60)"><rect width="318" height="298" fill="white" stroke="#333"/>']
    for h in data['occupied_unknown_projection_hits']:
        x,y,x2,y2=h['xy'];s.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="#d44" opacity="0.035"/>')
    for b in data['rear_capacity_trials']:
        x,y,x2,y2=b['xy'];s.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="#fdc" stroke="#a60"/><text x="{x+2}" y="{y+13}" font-size="8">{b["id"]}</text>')
    for p in data['fixed_markers']:
        s.append(f'<circle cx="{p["x_mm"]}" cy="{p["y_mm"]}" r="2" fill="#246"/>')
    s+=['</g>','<g font-size="13">']
    lines=['Conservative AO: repeated core29 packages', 'Active jack59 packages → AO-J10 → core', 'Two fixed pots → AO-C10 → core', 'Individual front boards OR shared six-channel strips', '', 'MULT: repeat entire active jack board36 packages', 'Power-only P8; no added analog transport', '', 'Six40×45 rear trials: 3 columns × 2 rows', '2mm allowance; no trial-to-trial overlap', 'Foreign reservations remain occupied/unknown', 'No populated capacity, support or service proof', '', 'Passive front / all-electronics rear: rejected for now', 'Output sense and LED feedback cross cables', 'No claim of lower cost or qualified hardware']
    for i,line in enumerate(lines):s.append(f'<text x="350" y="{75+i*18}">{line}</text>')
    return '\n'.join(s+['</g></g></svg>'])+'\n'

if __name__=='__main__':
    d=build();(HERE/'proposal.json').write_text(json.dumps(d,indent=2)+'\n');(HERE/'comparison.svg').write_text(svg(d))
