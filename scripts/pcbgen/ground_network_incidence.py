"""Exact source incidence for ground wires and every fitted return contact.

This is topology, not an electrical solution. No board is an ideal node and
no omitted operator, own-load current or physical contact law defaults to zero.
"""
import argparse
import hashlib
import json
from pathlib import Path


def unique(rows,key,label):
    result={r[key]:r for r in rows}
    if len(result)!=len(rows):raise ValueError('duplicate '+label)
    return result


def build(partition,io,loom,wire_evidence):
    boards=unique(partition['boards'],'board_key','source board')
    packages=unique(io['physical_packages'],'ref','physical package')
    assignments=unique(partition['assignment']['components'],'ref','package assignment')
    connectors=unique(partition['connectors'],'id','header identity')
    routes=unique(loom['routes'],'id','loom route')
    terminals=unique(partition['load_side_terminals'],'reference','main terminal')
    harnesses=unique(partition['harnesses'],'id','harness identity')
    counts=partition['counts']
    if len(boards)!=counts['boards'] or len(connectors)!=counts['headers'] or len(harnesses)!=counts['harnesses']:
        raise ValueError('ground network inventory differs from source declared counts')
    contacts={};own={b:set() for b in boards};edges=[]
    def contact(board,ref,pad,kind,**metadata):
        if board not in boards:raise ValueError('contact has no exact source board')
        key=f'{board}:{ref}:{pad}'
        value={'id':key,'board':board,'ref':ref,'pad':pad,'net':'AGND','kind':kind,**metadata}
        if key in contacts:
            if contacts[key]!=value:raise ValueError('conflicting ground contact identity '+key)
        else:contacts[key]=value
        return key
    # Source current contacts are derived independently of native/model ports.
    for crossing in io['allowed_crossings']:
        if crossing['net']!='AGND':continue
        for member in crossing['members']:
            ref=member['ref'];package=packages.get(ref);assignment=assignments.get(ref)
            if package is None or assignment is None:raise ValueError('ground source member lacks physical package assignment')
            if bool(package['dnp'])==bool(assignment['fitted']):raise ValueError('source fitted/DNP assignment differs')
            if package['dnp']:continue
            board=assignment['board'];key=contact(board,ref,member['pin'],'fitted_source_contact',
                symbol=package['symbol'],instance=package['instance'],decouples_ref=package.get('decouples_ref'))
            own[board].add(key)
    used_headers=set();wire=wire_evidence['proposal']
    for harness in harnesses.values():
        if len(harness['header_ids'])!=2 or len(set(harness['header_ids']))!=2:
            raise ValueError('harness requires two distinct source headers')
        ends=[connectors[h] for h in harness['header_ids']]
        if set(h['board'] for h in ends)!=set(harness['boards']):raise ValueError('harness board/header mismatch')
        if any(h['id'] in used_headers for h in ends):raise ValueError('physical header belongs to more than one harness')
        used_headers.update(harness['header_ids'])
        grounds=[{pin for pin,net in h['pin_map'].items() if net=='AGND'} for h in ends]
        if grounds[0]!=grounds[1] or len(grounds[0])!=harness['return_contacts']:
            raise ValueError('ground wire endpoints differ from exact pin map/count')
        route=routes[harness['id']]
        if route['wire_mpn']!='Alpha Wire 6821 BK005':raise ValueError('ground harness has unsupported wire identity')
        if not 0<route['centreline_length_mm']<=route['cut_length_max_mm']:
            raise ValueError('ground harness has invalid lower/upper physical lengths')
        for pin in sorted(grounds[0],key=int):
            nodes=[contact(h['board'],h['pcb_reference'],pin,'GH_terminal',
                header_id=h['id'],side=h['side'],source_footprint_origin_mm=h['footprint_origin_mm'],
                source_native_angle_deg=h['kicad_orientation_deg'],header_mpn=h['header_mpn'],
                housing_mpn=h['housing_mpn'],contact_mpn=h['contact_mpn']) for h in ends]
            edges.append({'id':harness['id']+':AGND:'+pin,'kind':'GH_wire','harness_id':harness['id'],
                'from_contact':nodes[0],'to_contact':nodes[1],
                'incidence':{nodes[0]:-1,nodes[1]:1},'wire_mpn':route['wire_mpn'],
                'wire_lower_requirement_ohm':route['centreline_length_mm']/1000*wire['wire_minimum_resistance_for_parallel_path_bounds_ohm_per_m'],
                'wire_upper_hot_requirement_ohm':route['cut_length_max_mm']/1000*wire['wire_hot_resistance_ceiling_ohm_per_m'],
                'two_assembled_contacts_upper_allowance_ohm':.1,
                'candidate_added_PCB_contact_denominator_ohm':0.,
                'physical_trace_status':'OPEN: scalar source resistance bounds do not supply full solder/lead/current and potential trace gluing.'})
    if used_headers!=set(connectors):raise ValueError('source header has no unique harness')
    power=partition['power']['load_distribution']
    power_wires=unique(partition['load_side_wires'],'id','main wire identity')
    for row in power_wires.values():
        if row['net']!='AGND':continue
        if row['wire_mpn']!=power['wire'] or not 0<row['maximum_length_mm']<=power['max_wire_length_mm']:
            raise ValueError('main ground wire differs from exact source wire/length contract')
        if len(row['terminal_refs'])!=2 or len(set(row['terminal_refs']))!=2:raise ValueError('main wire needs two distinct terminals')
        ends=[terminals[r] for r in row['terminal_refs']]
        if any(t['net']!='AGND' for t in ends) or len({t['board'] for t in ends})!=2:
            raise ValueError('main ground wire net/board mismatch')
        nodes=[contact(t['board'],t['reference'],str(t['manufacturer_pin']),'main_terminal',
            side=t['side'],source_center_mm=t['center_mm'],land_mm=t['copper_land_mm']) for t in ends]
        edges.append({'id':row['id'],'kind':'main_wire','from_contact':nodes[0],'to_contact':nodes[1],
            'incidence':{nodes[0]:-1,nodes[1]:1},'wire_mpn':row['wire_mpn'],
            'whole_wire_and_two_terminations_upper_requirement_ohm':power['max_wire_length_mm']/1000*power['hot_resistance_requirement_ohm_per_m']+power['combined_termination_resistance_ohm'],
            'physical_trace_status':'OPEN: finite nineteen-support whole-wire class is unselected; each actual branch geometry and both board traces must be composed.'})
    if len({e['id'] for e in edges})!=len(edges):raise ValueError('duplicate physical ground wire')
    if sum(e['kind']=='GH_wire' for e in edges)!=counts['wired_return_conductors']:
        raise ValueError('ground conductor count differs from source complete inventory')
    utility=[e for e in edges if e['kind']=='GH_wire' and {contacts[e['from_contact']]['board'],contacts[e['to_contact']]['board']}=={'JL','P'}]
    if len(utility)!=4:raise ValueError('all four JL/P utility returns are mandatory')
    if sum(e['kind']=='main_wire' for e in edges)!=9:raise ValueError('nine independent main ground wires required')
    return {'status':'SOURCE INCIDENCE ONLY; no joined operator, source/current class or electrical acceptance',
        'contacts':list(contacts.values()),'wire_edges':edges,
        'board_source_ids':{b:r['id'] for b,r in boards.items()},
        'board_fitted_package_refs':{b:sorted(r for r,a in assignments.items() if a['board']==b and a['fitted']) for b in boards},
        'board_own_load_contacts':{b:sorted(rows) for b,rows in own.items()},
        'counts':{'source_own_load_contacts':{b:len(rows) for b,rows in own.items()},
            'contacts':len(contacts),'GH_ground_wires':sum(e['kind']=='GH_wire' for e in edges),
            'main_ground_wires':9,'JL_P_utility_ground_wires':4},
        'wire_sign_convention':'Positive wire current flows from_contact to to_contact; PCB injection is -I at from and +I at to. Every incidence column sums exactly to zero.',
        'external_current_condition':'Normal proposed total variation of actual load/source boundary currents must be explicitly bounded and globally balanced. Source rail maxima alone do not bound reactive discharge, input leakage, passive contact redistribution or external circulation.',
        'balancing_boundaries':{'physical_source':'CN301/XB301 remain deliberately abstract/non-energizable under the accepted source contract; this incidence artifact adds no physical bridge or ideal K node.',
            'nominal_coupling_queries':'Each named K main in the matrix is a mathematical balancing contact for an explicitly stated unit source pair, not an inferred physical source-inlet location.',
            'joined_requirement':'Provide every external source/return contact functional and its signed current, including K/P/rest-network own loads. The global external-current vector must sum to zero. A potential gauge carries no implicit balancing current.'},
        'operator_requirements':'Every PCB retains a finite conductor operator and compatible full physical contact traces. Missing P/rest-network or K own-load operators are OPEN, never ideal or zero. Candidate observation is +J-GH minus its actual remote GH, including the four P endpoints.'}


def bind_native_contacts(graph,natives):
    """Exact contact binding; native passing-receipt authority is separate."""
    result={}
    for board,native in natives.items():
        if native['board_id']!=graph['board_source_ids'][board]:
            raise ValueError('native board differs from exact source board identity')
        if native['coordinate_frame']['source_to_native_translation_mm']!=[100,50]:
            raise ValueError('unexpected native/source coordinate frame')
        expected={r['id']:r for r in graph['contacts'] if r['board']==board}
        pads=[r for r in native['items'] if 'ref' in r]
        physical={(r['ref'],r['pad']):r for r in pads}
        if len(physical)!=len(pads) or len({r['uuid'] for r in pads})!=len(pads):
            raise ValueError('duplicate native pad identity/UUID')
        fitted=set(graph['board_fitted_package_refs'][board])
        actual_own={(r['ref'],r['pad']) for r in pads if r['ref'] in fitted and r['net']=='AGND'}
        expected_own={(r['ref'],r['pad']) for r in expected.values() if r['kind']=='fitted_source_contact'}
        if actual_own!=expected_own:raise ValueError('native/source own-load ground contact sets differ')
        main=set(native['main_rail_members']['AGND']);bindings=[]
        for key,row in expected.items():
            pad=physical.get((row['ref'],row['pad']))
            if pad is None or pad['net']!='AGND' or pad['uuid'] not in main:
                raise ValueError('source ground contact absent, foreign or disconnected: '+key)
            if 'side' in row and set(pad['copper'])!={row['side']}:
                raise ValueError('ground terminal physical face differs: '+key)
            bindings.append({'id':key,'uuid':pad['uuid'],'native_xy_mm':pad['xy_mm'],'layers':list(pad['copper'])})
        result[board]={'board_id':native['board_id'],'board_sha256':native['board_sha256'],
            'contact_count':len(bindings),'bindings':bindings}
    return {'status':'Native/source contact binding only; requires separate successful board authority and physical trace class',
        'boards':result,'missing_native_boards':sorted(set(graph['board_own_load_contacts'])-set(natives))}


def generate(output):
    code=Path(__file__).read_bytes()
    names=['design/partition/partition.json','design/reports/io-partition.json','design/partition/loom-candidate.json','design/partition/harness-wire-evidence.json']
    raw={n:Path(n).read_bytes() for n in names};result=build(*(json.loads(raw[n]) for n in names))
    result['source_sha256']={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}
    result['generator_sha256']=hashlib.sha256(code).hexdigest()
    if any(Path(n).read_bytes()!=b for n,b in raw.items()):raise ValueError('ground incidence source changed during generation')
    if Path(__file__).read_bytes()!=code:raise ValueError('ground incidence generator changed during generation')
    Path(output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();r=generate(a.output);print(json.dumps(r['counts'],indent=2))
