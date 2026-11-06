"""Reversible IDC service placement; no canonical geometry changes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OLD = HERE.parent/'standard-idc-assembly'
spec = importlib.util.spec_from_file_location('idc_geometry', OLD/'generate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def read(p):
    return json.loads(p.read_text())


def build():
    prior = read(OLD/'candidate.json')
    hybrid = read(HERE.parent/'hybrid-service-layout/proposal.json')
    populated = read(HERE.parent/'populated-a01-hybrid/layout.json')
    mechanical = read(ROOT/'design/architecture-278/implementation/stage10/mechanical-report.json')
    connectors = copy.deepcopy(prior['connectors'])
    moves = {'J17901': [218.5,299], 'J17902': [274,165.5],
             'J17904': [292,152], 'J17906': [258,152], 'J17903': [212,171.5]}
    ref_board = {c['ref']: c['board'] for c in populated['connectors']}
    for c in connectors:
        ref = c['ref']
        if ref in moves:
            old_xy = c['coordinates']['centre_mm']
            delta = [moves[ref][i]-old_xy[i] for i in (0,1)]
            c['coordinates']['centre_mm'] = moves[ref]
            for pin in c['coordinates']['pins']:
                pin['global_xy'] = [round(pin['global_xy'][i]+delta[i],6) for i in (0,1)]
            c['header_max_xy_mm'] = [round(v+delta[i%2],6) for i,v in enumerate(c['header_max_xy_mm'])]
    supports = []
    for s in hybrid['effective_support_solids']:
        s = copy.deepcopy(s)
        if s['id'] in ('control-left-lower','control-right-lower'):
            original = copy.deepcopy(s)
            for label,lo,hi,shift in [('top',287,289,0),('grip',289,307,-1 if 'left' in s['id'] else 1),('bottom',307,320,0)]:
                t=copy.deepcopy(original);t['id'] += '-'+label
                t['xy']=[s['xy'][0]+shift,lo,s['xy'][2]+shift,hi]
                supports.append(t)
        else:
            if s['id']=='control-mount-bridge':
                s['xy'][1]+=1;s['xy'][3]+=1
            supports.append(s)
    fasteners = copy.deepcopy(hybrid['control_fasteners'])
    for f in fasteners:
        f['xy'][1] += 1
    ids = {c['ref'] for c in connectors}
    known = [o for o in hybrid['known_obstacles'] if o['id'] not in ids]+supports
    # Actual new positions, all other IDC assemblies occupied to cover; add each
    # one's own 1mm allowance as well as the subject's allowance, conservatively.
    columns = [{'id': c['ref'], 'xy': g.grow(c['header_max_xy_mm'],1),
                'z': [c['face_z_mm'],105]} for c in connectors]
    for c in connectors:
        ref=c['ref'];board=ref_board[ref];face=c['face_z_mm']
        own_ids=['A01-controltab','A01-controlupper'] if board=='A01-control' else [board]
        others=[o for o in known if o['id'] not in own_ids]+[o for o in columns if o['id']!=ref]
        body=g.grow(c['header_max_xy_mm'],1);grip=g.grow(body,2)
        c['screens']={}
        for label,xy,delta in [('installed',body,0),('withdrawal15',body,15),('grip_withdrawal15',grip,15)]:
            limits=g.height_limit(xy,face,others,delta,1)
            c['screens'][label]={'xy_mm':xy,'withdrawal_mm':delta,
                'necessary_max_height_above_board_mm':limits[0]['height_mm'],
                'limiting_obstacles':[v['id'] for v in limits if v['height_mm']==limits[0]['height_mm']],
                'status':'NECESSARY_SCREEN_ONLY_ACTUAL_HEIGHT_AND_FULL_SWEEP_UNKNOWN'}
        c['same_board_grip_package_hits']=[r for r,p in populated['packages'].items()
            if p['board']==board and g.overlap(grip,p['box_mm'])]
        c['same_board_body_terminal_hits']=[v['id'] for v in mechanical['terminal_lands']
            if v['board']==board and g.overlap(body,g.footprint(v['xyz_mm'][:2],2.6,2.6,0))]
        c['unknown_neighbor_projection_refs']=sorted(o['ref'] for o in hybrid['unknown_obstacles'] if g.overlap(grip,o['xy']))
        c['known_tail_hits']=[o['id'] for o in others if g.overlap(body,o['xy']) and
            c['tail_z_screen_mm'][0]<=o['z'][1] and o['z'][0]<=c['tail_z_screen_mm'][1]]
        c['mount_tool_body_hits']=[]
        sites=([f['xy'] for f in fasteners] if board=='A01-control' else
               populated['boards'][board]['mounts_mm'])
        for xy in sites:
            if g.overlap(body,g.footprint(xy,6 if board=='A01-control' else 8,6 if board=='A01-control' else 8,0)):
                c['mount_tool_body_hits'].append(xy)
        # Board containment for nominal 1.6mm substrate; revised control tab is
        # a two-rectangle union. This candidate's body stays wholly in the tab.
        outline=([206.5,290,230.5,312] if board=='A01-control' else populated['boards'][board]['outline_mm'])
        c['body_with_allowance_within_board']=all([body[0]>=outline[0],body[1]>=outline[1],body[2]<=outline[2],body[3]<=outline[3]])
    by={c['ref']:c for c in connectors}
    # Analytic feasible Y intervals for fixed X and rotations, strict at contacts.
    half_grip=(g.mm(.338+.005)/2)+3
    half_other=(g.mm(.338+.005)/2)+1
    intervals={'middle_C_SIG_centre_y_mm_open':[round(152+half_other+half_grip,6),round(174-half_grip,6)],
        'jack_J_PWR_centre_y_mm_open':[round(163.64+half_grip,6),round(182-(half_grip-2),6)],
        'control_C_SIG_centre_y_mm_open':[round(291.1+half_grip,6),round(307-half_grip,6)],
        'control_left_inner_x_must_be_less_than':by['J17901']['screens']['grip_withdrawal15']['xy_mm'][0],
        'control_right_inner_x_must_be_greater_than':by['J17901']['screens']['grip_withdrawal15']['xy_mm'][2]}
    support_unknown=[{'support':s['id'],'ref':o['ref']} for s in supports
        for o in hybrid['unknown_obstacles'] if g.overlap(s['xy'],o['xy'])]
    files=[OLD/'candidate.json',OLD/'generate.py',HERE.parent/'hybrid-service-layout/proposal.json',
           HERE.parent/'populated-a01-hybrid/layout.json',ROOT/'design/architecture-278/implementation/stage10/mechanical-report.json',
           ROOT/'design/grid/placements.lock.json']
    return {'baseline':'2f30e91eaaea012dbf6eca5bff67ff088ba31d39','adopted':False,
        'status':'REVISED_SOURCE_CANDIDATE_NOT_INTEGRATED_FIT',
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'pin_maps':prior['pin_maps'],'connectors':connectors,'control_fasteners':fasteners,
        'effective_support_solids':supports,'support_unknown_projection_hits':support_unknown,
        'feasible_intervals':intervals,'board_planes_and_rear_24mm_stack':'UNCHANGED',
        'prior_negative_screens':{ref:read(OLD/'candidate.json')['connectors'][i]['screens']
            for i,ref in enumerate([c['ref'] for c in prior['connectors']]) if ref in ('J17901','J17902')},
        'prior_J_PWR_grip_package_hits':['R7105','R7107','R7108','R7109','R7135'],
        'rejected_control_rotation':{'centre_mm':[218.5,292.5],'rotation_deg':90,
            'reason':'header/through-hole reservation overlaps RV1308 courtyard and pads; not accepted'},
        'cable_routes':'INVALIDATED_BY_MOVED_ENDPOINTS; no new cable route or cut length established',
        'remaining':prior['unresolved'],
        'assumptions':prior['planning_assumptions']}


def svg(p):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="185 75 145 255">',
         '<rect x="185" y="75" width="145" height="255" fill="#fafafa"/>',
         '<style>text{font:2.8px sans-serif} .note{font:3px sans-serif}</style>',
         '<text class="note" x="188" y="80">Unadopted service placement — XY only</text>',
         '<text x="188" y="85">Blue: headers; dashed: grip; gray: supports</text>']
    def rect(b,color,dash=''):
        out.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" fill="{color}" fill-opacity=".25" stroke="{color}" stroke-width=".3" {dash}/>')
    for s in p['effective_support_solids']:rect(s['xy'],'#667788')
    rect([236,174,312,282],'#8c75b5')
    out.append('<text x="240" y="205">Core projection; gap remains 24 mm</text>')
    for c in p['connectors']:
        rect(c['header_max_xy_mm'],'#136ba3')
        rect(c['screens']['grip_withdrawal15']['xy_mm'],'#d56b10','stroke-dasharray="1 1"')
        x,y=c['coordinates']['centre_mm'];out.append(f'<text x="{x-6}" y="{y-1}">{c["ref"]}</text>')
    out.append('<text x="188" y="325">Unknown neighbor depths and cables NOT cleared</text></svg>')
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=build()
    (HERE/'candidate.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
    (HERE/'placement.svg').write_text(svg(p))
