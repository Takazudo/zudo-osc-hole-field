"""Two local resistor-network candidate packages; scalar source, not native CAD."""
import argparse
import copy
import json
import math
from pathlib import Path
import assembly as a
import stage13_packages as geometry
import stage11_assessment as common

ROOT = a.ROOT
OUT = a.OUT / 'stage15'
need = common.need
FOOTPRINT = 'design/architecture-278/implementation/stage15/footprints/LT5400_MS8E_Candidate.kicad_mod'
PAIRS = [('1','8'),('2','7'),('3','6'),('4','5')]
REPLACED = ['R7121','R7122','R7123','R7124','R7125','R7126']


def read(name):
    return json.loads((OUT.parent / name).read_text())


def analyze(spec, prior, mech):
    need(spec['MPN'] == 'LT5400AIMS8E-2#PBF', 'exact A-grade I 100k identity')
    need(spec['EP_net'] == 'AGND', 'quiet local shield return required')
    need(spec['source']['sha256'] == '3bd808eb2c603ce009456913cfacdd9339f645dec08a8bfa8437a6dd5ea71028', 'reviewed primary bytes')
    need(set(spec['networks']) == {'RN7101','RN7102'}, 'exact two networks')
    g = spec['geometry']
    expected = {str(i+1):[x,2.17] for i,x in enumerate([-.975,-.325,.325,.975])}
    expected.update({str(8-i):[x,-2.17] for i,x in enumerate([-.975,-.325,.325,.975])})
    expected['9'] = [0,0]
    need(g['pads_mm'] == expected and g['courtyard_mm'] == [-2,-2.9,2,2.9], 'reviewed land orientation/envelope')
    need(g['body_max_including_flash_mm'] == [3.406,3.406,1.10], 'body plus flash allowance')
    need(a.c.footprint_pads(FOOTPRINT) == {k:[v] for k,v in expected.items()}, 'footprint pin/land parity')
    need(a.c.courtyard(FOOTPRINT) == g['courtyard_mm'], 'footprint courtyard parity')
    for node in a.c.sexpr((ROOT/FOOTPRINT).read_text()):
        if isinstance(node,list) and node and node[0]=='pad' and node[1]:
            need(list(map(float,a.c.field(node,'size'))) == g['pad_sizes_mm'][node[1]], 'land size parity')
    for pin,xy in expected.items():
        wh = g['pad_sizes_mm'][pin]
        need(wh == ([1.88,1.68] if pin=='9' else [.42,.9]), 'reviewed land size')
        need(a.inside([xy[0]-wh[0]/2,xy[1]-wh[1]/2,xy[0]+wh[0]/2,xy[1]+wh[1]/2],g['courtyard_mm']), 'land in courtyard')
    places = copy.deepcopy(prior['placements'])
    for ref in REPLACED:
        del places[ref]
    aliases = {}; elements = []; screens = []
    for ref, q in spec['networks'].items():
        expected_old = REPLACED[:4] if ref=='RN7101' else REPLACED[4:]
        need(q['replaces'] == expected_old, 'six exact original resistor functions')
        anchor = prior['placements'][expected_old[0]]
        need((q['board'],q['owner'],q['pad_depth_mm']) == (anchor['board'],anchor['owner'],anchor['conditional_pad_depth_mm']), 'network remains local')
        need(q['quarter_turn'] in range(4) and all(math.isfinite(v) for v in q['origin_mm']), 'finite pose')
        pins = {str(i):None for i in range(1,10)}; pins['9']='AGND'
        for i,(left,right) in enumerate(PAIRS):
            old = expected_old[i] if i<len(expected_old) else None
            if old:
                oldpins = prior['placements'][old]['pins']
                pins[left],pins[right] = oldpins['1'],oldpins['2']
                aliases[old+':1'] = ref+':'+left; aliases[old+':2'] = ref+':'+right
            elements.append({'ref':ref,'element':i+1,'pins':[left,right], 'nominal_ohm':100000,'replaces':old,'connected':old is not None})
        shape = a.face_shape({'box':g['courtyard_mm'],'pads':{k:[v] for k,v in expected.items()},'holes':[]}, 'rear')
        pads = {k:[a.transform(v,q['origin_mm'],q['quarter_turn']) for v in vs] for k,vs in shape['pads'].items()}
        box = a.box_transform(shape['box'],q['origin_mm'],q['quarter_turn'])
        need(a.inside(box,mech['boards'][q['board']]['outline_mm'],spec['board_edge_clearance_mm']), 'board edge clearance')
        places[ref] = {'ref':ref,'board':q['board'],'owner':q['owner'],'panel_uid':'','side':'rear','origin_mm':q['origin_mm'],'quarter_turn':q['quarter_turn'],'box_mm':box,'pads_mm':pads,'pads_xyz_mm':{k:[v+[q['pad_depth_mm']] for v in vs] for k,vs in pads.items()},'pins':pins,'conditional_pad_depth_mm':q['pad_depth_mm'],'units':[1,2,3,4],'source':FOOTPRINT,'candidate_MPN':spec['MPN'],'replaces':expected_old,'body_max_including_flash_mm':g['body_max_including_flash_mm']}
    for ref in spec['networks']:
        p = places[ref]; board = p['board']; obstacles=[]
        obstacles += [{'id':r,'box':v['box_mm']} for r,v in places.items() if r!=ref and v['board']==board]
        obstacles += [{'id':r,'box':v['box_mm']} for r,v in mech['headers'].items() if v['board']==board]
        obstacles += [{'id':v['id'],'box':geometry.around(v['xy_mm'],max(3,v['washer_diameter_mm']/2))} for v in mech['mounts'] if v.get('board')==board]
        if board=='A01-core':
            obstacles += prior['obstacles']
        # Keep actual terminal lands/through keepouts, irrespective of resistor removals.
        for name in ('terminal_lands','LED_wire_lands'):
            for v in mech.get(name,[]):
                if board=='A01-jack':
                    xy=v['xyz_mm'][:2]; obstacles.append({'id':v['id'],'box':geometry.around(xy,v['diameter_mm']/2)})
        for r,v in places.items():
            if v['board']==board:
                for i,b in enumerate(v.get('through_pad_keepouts_mm',[])):
                    obstacles.append({'id':r+':through:'+str(i),'box':b})
        distances = [{'id':v['id'],'clearance_mm':geometry.gap(p['box_mm'],v['box'])} for v in obstacles]
        need(all(not geometry.overlap(p['box_mm'],v['box']) for v in obstacles), 'network envelope collision '+ref)
        need(min(v['clearance_mm'] for v in distances)>=spec['courtyard_gap_mm'], 'network courtyard gap '+ref)
        screens.append({'ref':ref,'neighbors':distances,'minimum_mm':min(v['clearance_mm'] for v in distances)})
    need(len(places)==86 and sum(len(p['pins']) for p in places.values())==291, 'physical package/pad conservation')
    for ref,p in prior['placements'].items():
        if ref not in REPLACED: need(places[ref]==p, 'unrelated/fixed placement changed '+ref)
    frozen=prior['frozen_stage11_option_screen']['solids']
    intersections=[]
    for ref in spec['networks']:
        p=places[ref];z=p['conditional_pad_depth_mm']
        for solid in frozen:
            if geometry.overlap(p['box_mm'],solid['box_mm']) and z<solid['z_mm'][1] and solid['z_mm'][0]<z+1.1:
                intersections.append({'ref':ref,'solid':solid['id']})
    need(not intersections,'frozen support/strap/cassette intersection')
    occupied=read('stage4/occupied-report.json')
    reservations=[{'candidate':ref,'foreign_ref':p['ref'],'function':p['function_or_service'],'status':'Historical XY reservation; populated foreign Z volume unresolved, no free-space credit'} for ref in spec['networks'] for p in occupied['rows'] if p['function_or_service']!='A01' and geometry.overlap(places[ref]['box_mm'],p['historical_placement']['courtyard_mm'])]
    local=[]
    for old,new in aliases.items():
        ref,pin=new.split(':');amp='U7105' if ref=='RN7101' else 'U7106'
        net=places[ref]['pins'][pin]
        targets=[(k,v[0]) for k,v in places[amp]['pads_xyz_mm'].items() if places[amp]['pins'][k]==net]
        if targets:
            target,xyz=min(targets,key=lambda v:math.dist(places[ref]['pads_xyz_mm'][pin][0],v[1]))
            r,k=old.split(':')
            local.append({'from':new,'to':amp+':'+target,'net':net,'before_straight_floor_mm':math.dist(prior['placements'][r]['pads_xyz_mm'][k][0],xyz),'after_straight_floor_mm':math.dist(places[ref]['pads_xyz_mm'][pin][0],xyz),'actual_copper_mm':None})
    return {'status':'TWO LOCAL NETWORK CANDIDATES; NOT PHYSICAL ACCEPTANCE','placements':places,'endpoint_aliases':aliases,'elements':elements,'neighbor_screens':screens,'frozen_option_screen':{'solids':frozen,'intersections':intersections},'foreign_projection_reservations':reservations,'local_amplifier_pad_distances':local,'counts':{'packages_before':90,'packages_after':86,'source_pads_before':285,'source_pads_after':291,'removed_discrete_resistors':6,'fitted_networks':2,'active_network_elements':6,'unused_network_elements':2,'new_shield_return_pads':2},'exposed_pad':'Pin9 internally isolated from resistor terminals; connected to local AGND quiet AC shield per primary recommendation. Actual AGND noise/impedance unresolved; not a resistor common or DC load.', 'unused_elements':spec['unused_policy'],'footprint_status':'Source-derived candidate only. EP paste window1.5x1.3mm is engineering proposal; solder-mask/paste/voiding/assembly require later qualification. No 3D model claimed.', 'unknowns':['Complete obstacle-aware copper routing/DRC','All foreign-function occupied volumes remain reserved; no newly free space claimed','Mounted package thermal gradients and AGND shield quality','Package capacitance plus board/harness/input coupling and closed-loop stability','Assembly process and solder joint reliability'], 'hardware_acceptance':False,'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    files=[OUT/'package-input.json',OUT.parent/'stage13/package-report.json',OUT.parent/'stage10/mechanical-report.json',ROOT/FOOTPRINT,Path(__file__),Path(__file__).with_name('test_stage15_packages.py')]
    result=analyze(*[json.loads(p.read_text()) for p in files[:3]])
    files += [OUT.parent/'stage4/occupied-report.json',Path(geometry.__file__),Path(a.__file__)]
    result['source_sha256']={str(p.relative_to(ROOT)):common.digest(p) for p in files}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';dest=OUT/'package-report.json'
    if args.check:need(dest.read_text()==text,'stale Stage15 packages')
    else:dest.write_text(text)
    print('PASS Stage15 86 packages/291 pads; physical acceptance OPEN')

if __name__=='__main__':main()
