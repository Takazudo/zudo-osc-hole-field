"""Independent five-card courtyard/fixture alternatives; no native or routing claim."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation'
BASE = '80000737f0a2fd97896ca654040ab65096aed352'
BASE_PATH = 'design/architecture-278/implementation/candidate-report.json'
OFFSETS = {'wave-scale':[0,0], 'core-timing':[0,-10], 'tune-octave-vee':[0,-38],
           'local-reference':[-24,-22], 'sine':[0,0], 'fm-pwm':[0,-6],
           'sync':[0,-10], 'pw-lfo':[0,-73]}

def overlap(a,b,gap=0):
    return a[0] < b[2]+gap-1e-8 and b[0] < a[2]+gap-1e-8 and a[1] < b[3]+gap-1e-8 and b[1] < a[3]+gap-1e-8

def shifted(box,dx,dy): return [box[0]+dx,box[1]+dy,box[2]+dx,box[3]+dy]

def rotate_box(box,width,height,quarter):
    for _ in range(quarter):
        box=[height-box[3],box[0],height-box[1],box[2]]
        width,height=height,width
    return box

def build():
    raw=subprocess.check_output(['git','show',BASE+':'+BASE_PATH],cwd=ROOT)
    baseline=json.loads(raw)
    packages=[]
    for p in baseline['rear_placements']:
        q=copy.deepcopy(p);dx,dy=OFFSETS[p['cluster']]
        for key in ('box_mm','reserved_box_mm'):q[key]=shifted(p[key],dx,dy)
        q['origin_mm']=[p['origin_mm'][0]+dx,p['origin_mm'][1]+dy]
        q['pads_mm']={pin:[[x+dx,y+dy] for x,y in coords] for pin,coords in p['pads_mm'].items()}
        packages.append(q)
    fixtures=[{'id':'DIN','box_mm':[2.5,7.5,17.5,107.5]}]
    fixture_centres={'support':([[6,4],[91,4],[6,111.5],[91,111.5]],3),
                     'guide':([[20,7.5],[92,80]],2),
                     'handle':([[30,111.5],[70,111.5]],3),
                     'probe':([[20,111.5],[45,111.5],[55,111.5],[80,111.5]],2)}
    for kind,(centres,radius) in fixture_centres.items():
        for i,(x,y) in enumerate(centres):
            fixtures.append({'id':kind+str(i+1),'box_mm':[x-radius,y-radius,x+radius,y+radius]})
    for i,x in enumerate((25,43,61,79)):
        fixtures.append({'id':'power'+str(i+1),'box_mm':[x,91,x+10,103]})
    objects=[{'id':p['ref'],'box_mm':p['reserved_box_mm']} for p in packages]+fixtures
    assert len(packages)==154 and len([p for p in packages if p['trim_tool_diameter_mm']])==6
    assert len({p['cluster'] for p in packages})==8
    # Every package/tool/fixture pair has at least the inherited 0.5 mm clearance.
    for i,a in enumerate(objects):
        assert .5<=a['box_mm'][0]<a['box_mm'][2]<=96.5 and .5<=a['box_mm'][1]<a['box_mm'][3]<=114.5,a
        for b in objects[i+1:]:assert not overlap(a['box_mm'],b['box_mm'],.5),(a['id'],b['id'])
    alternatives=[]
    specs=[('compact-103x115-original-origins',103,115,0,[(2,122),(107,122),(2,5),(107,5),(212,5)]),
           ('compact-97x115-three-columns',97,115,0,[(2,122),(101,122),(2,5),(101,5),(200,5)]),
           ('compact-115x97-two-columns',97,115,1,[(2,101),(119,101),(2,2),(119,2),(2,200)]),
           ('compact-103x120-extra-edge',103,120,0,[(2,124),(107,124),(2,2),(107,2),(212,2)])]
    for name,w,h,turn,origins in specs:
        rw,rh=(h,w) if turn%2 else (w,h)
        cards=[]
        for i,(x,y) in enumerate(origins):
            bounds=[x,y,x+rw,y+rh]
            assert .5<=x and .5<=y and bounds[2]<=317.5 and bounds[3]<=297.5
            transformed=[{'id':o['id'],'box_mm':shifted(rotate_box(o['box_mm'],w,h,turn),x,y)} for o in objects]
            cards.append({'instance':'O'+str(i+1),'origin_mm':[x,y],'box_mm':bounds,'rotation_degrees':90*turn,'objects':transformed})
        for i,a in enumerate(cards):
            for b in cards[i+1:]:assert not overlap(a['box_mm'],b['box_mm'],1),(a['instance'],b['instance'])
        alternatives.append({'id':name,'tile_mm':[rw,rh],'cards':cards,'package_count':770,'trim_count':30,
                             'scope':'All five source-equivalent rear courtyard/fixture sets; package Ref mapping and routing not generated'})
    return {'status':'MECHANICAL FEASIBILITY ONLY; no adoption, routed or physical fit acceptance',
            'baseline_commit':BASE,'baseline_report_sha256':hashlib.sha256(raw).hexdigest(),
            'compiler_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cluster_offsets_from_baseline_mm':OFFSETS,'local_tile_mm':[97,115],
            'local_packages':packages,'local_fixtures':fixtures,'alternatives':alternatives,
            'checks':{'local_pair_clearance_mm':.5,'board_edge_clearance_mm':.5,'card_relative_tolerance_allowance_mm':1,
                      'all_five_populated_rear_courtyard_counts':770,'six_trims_per_card':True},
            'unchanged_depth_proposal_mm':{'middle':50,'core':69.2,'cover':105,'rear_height_bound':5,'handle_projection':18,'withdrawal':40,'rear_workspace':100},
            'not_proven':['Front component/header/tail and selector occupied solids at their fixed centres.',
                          'Actual routed lengths/capacitance/complete signal and power-return paths; all-five electrical placement tradeoffs.',
                          'Connector flange/footprint/tail dimensions and mating misalignment; guide engagement before contact.',
                          'Exact support/handle/probe/strap/fastener geometry, power-tool corridors, formed strap bends and insulation.',
                          'Insertion/extraction force, stiffness, torque, discharge verification and complete swept service solids.',
                          'Five-card external reference and power distribution; remaining28functions occupied volumes.',
                          'Exact passive/HF-trim identities and heights; six physical trim screwdriver axes.',
                          'KiCad10.0.6 ERC/DRC/native solids and physical tests NOT RUN; no exact-run admission.']}

def svg(report):
    lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1294 330" width="1941" height="495">','<rect width="1294" height="330" fill="white"/>']
    for col,a in enumerate(report['alternatives']):
        dx=col*324
        lines.append(f'<g transform="translate({dx},20)" font-family="sans-serif" font-size="3"><text x="2" y="-8">{a["id"]}</text><rect width="318" height="298" fill="#fafafa" stroke="#555"/>')
        for card in a['cards']:
            x,y,xx,yy=card['box_mm'];lines.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="#eef5ee" stroke="#555" stroke-width=".3"/><text x="{x+1}" y="{y+4}">{card["instance"]}</text>')
            for o in card['objects']:
                x,y,xx,yy=o['box_mm'];color='#d9ae74' if o['id'].startswith(('DIN','power','support','guide','handle','probe')) else '#a5c5d2'
                lines.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="{color}" stroke="#555" stroke-width=".1"><title>{card["instance"]}:{o["id"]}</title></rect>')
        lines.append('</g>')
    return '\n'.join(lines+['<text x="2" y="327" font-family="sans-serif" font-size="4">Whole rear clusters and fixtures only; front/other functions, routing, exact solids and physical acceptance OPEN.</text></svg>'])+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    r=build();outputs={'mechanical-feasibility.json':json.dumps(r,indent=2,sort_keys=True)+'\n','mechanical-feasibility.svg':svg(r)}
    for name,data in outputs.items():
        p=OUT/name
        if args.check:assert p.read_text()==data,'stale '+name
        else:p.write_text(data)
    print('PASS:4 all-five rear courtyard/fixture alternatives;154packages/card;6trims/card;0.5mm local clearance. ROUTING/PHYSICAL NOT RUN.')
if __name__=='__main__':main()
