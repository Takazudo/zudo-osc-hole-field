"""Source-owned disposable O/EL ground definitions with independent inventories."""
import argparse
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.foil_stack import resolve_stack
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware


def source_contacts(board_id,key,partition,io):
    boards=[b for b in partition['boards'] if b['id']==board_id]
    if len(boards)!=1 or boards[0]['board_key']!=key:raise ValueError('source board/key differs')
    assigned=[p for p in partition['assignment']['components'] if p['board']==key and p['fitted']]
    refs={p['ref'] for p in assigned};fitted={p['ref'] for p in io['physical_packages'] if not p['dnp']}
    if len(refs)!=len(assigned) or not refs<=fitted:raise ValueError('source fitted package identities differ')
    own={(m['ref'],m['pin']) for crossing in io['allowed_crossings'] if crossing['net']=='AGND'
         for m in crossing['members'] if m['ref'] in refs}
    headers=[h for h in partition['connectors'] if h['board']==key]
    if len({h['pcb_reference'] for h in headers})!=len(headers):raise ValueError('duplicate source header')
    gh={(h['pcb_reference'],pin):h for h in headers for pin,net in h['pin_map'].items() if net=='AGND'}
    if own.intersection(gh):raise ValueError('own-load and GH inventories overlap')
    return own,gh


def generate(proposal_path,board_id,output):
    proposal_path=Path(proposal_path);output=Path(output)
    code_path=Path('scripts/pcbgen/generate_peripheral_ground.py')
    paths=[proposal_path,code_path,Path('scripts/pcbgen/foil_stack.py'),Path('scripts/pcbgen/definition.py'),Path('scripts/pcbgen/netlist.py')]
    code=code_path.read_bytes();raw=proposal_path.read_bytes();proposal=json.loads(raw)
    if 'source_ground_bridge' in proposal and proposal['source_ground_bridge']!={
        'source_xy_mm':[218,166],'native_xy_mm':[318,216],'net':'AGND',
        'layers':['F.Cu','B.Cu'],'diameter_mm':.7,'drill_mm':.3}:
        raise ValueError('unsupported source ground bridge declaration')
    rows=[r for r in proposal['boards'] if r['board_id']==board_id]
    if len(rows)!=1:raise ValueError('one exact peripheral source row required')
    row=rows[0];canonical=Path('design/boards')/(board_id+'.json');canonical_bytes=canonical.read_bytes();original=json.loads(canonical_bytes)
    if output.resolve()==canonical.resolve() or output.stem!=board_id or original['layers']!=2:
        raise ValueError('separate two-layer source definition required')
    paths += [canonical,Path(original['netlist']),Path(proposal['partition']),Path(proposal['io']),Path(proposal['project_template']),Path('design/grid/placements.lock.json')]
    retained={str(p):p.read_bytes() for p in paths}
    retained.update({str(proposal_path):raw,str(canonical):canonical_bytes,str(code_path):code})
    partition=json.loads(retained[proposal['partition']]);io=json.loads(retained[proposal['io']])
    own,gh=source_contacts(board_id,row['board_key'],partition,io)
    with tempfile.TemporaryDirectory(prefix='peripheral-source-') as temporary:
        frozen=Path(temporary)/'source.net';frozen.write_bytes(retained[original['netlist']])
        components,pin_nets=read_netlist(frozen)
    if len(components)!=row['footprints'] or len(own)!=row['own_ground_contacts'] or len(gh)!=row['GH_ground_contacts']:
        raise ValueError('complete peripheral source inventory count changed')
    expected=own|set(gh)
    if {(ref,pad) for (ref,pad),net in pin_nets.items() if net=='AGND'}!=expected:
        raise ValueError('netlist ground contacts differ from independent partition/io source')
    reference=tuple(row['reference'])
    if reference not in gh or gh[reference]['side']!='B.Cu':raise ValueError('named reference must be an actual B-side GH ground')
    definition=copy.deepcopy(original);t=proposal['foil_thickness_mm'];depth=original['thickness_mm']
    definition['stackup']=[{'layer':'F.Cu','role':'UNSELECTED prerequisite ground/signal foil','copper_oz':original['stackup'][0]['copper_oz'],
        'copper_thickness_mm':t,'nominal_midplane_depth_mm':t/2},
        {'layer':'dielectric-1','thickness_mm':depth-2*t,'material':'UNSELECTED conditional positive dielectric'},
        {'layer':'B.Cu','role':'UNSELECTED prerequisite ground/signal foil','copper_oz':original['stackup'][-1]['copper_oz'],
        'copper_thickness_mm':t,'nominal_midplane_depth_mm':depth-t/2}]
    resolve_stack(definition['stackup'],depth)
    classes=[]
    for name,nets in [('Default',[]),('Rails',['+12V','-12V','+5V']),('Ground',['AGND'])]:
        classes.append({'name':name,'nets':nets,'track_width_mm':proposal['class_track_width_mm'][name],
            'clearance_mm':proposal['clearance_mm'],'via_diameter_mm':proposal['via_diameter_mm'],'via_drill_mm':proposal['via_drill_mm']})
    definition['routing']={'min_track_width_mm':proposal['minimum_track_width_mm'],'net_classes':classes,
        'zones':[{'name':'ground_prerequisite','net':'AGND','layers':['F.Cu','B.Cu'],
            'clearance_mm':proposal['clearance_mm'],'min_thickness_mm':proposal['minimum_fill_neck_mm'],'pad_connection':'full'}]}
    if any(definition[k]!=value for k,value in original.items() if k not in ('routing','stackup')):
        raise ValueError('fixed source geometry changed')
    hardware=selected_hardware(load_definition(canonical),load_lock(Path('design/grid/placements.lock.json')))
    if len(hardware)!=row['fixed_hardware']:raise ValueError('fixed peripheral hardware count changed')
    identities=[]
    for c in components:
        fields=dict(c.fields)
        if not fields.get('KiCadOrientationDeg') or not fields.get('FootprintOriginMm'):
            raise ValueError('peripheral source lacks explicit native placement: '+c.ref)
        identities.append({'ref':c.ref,'footprint':c.footprint,'source_fields':fields,
            'pins':{pad:net for (ref,pad),net in pin_nets.items() if ref==c.ref}})
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(definition,indent=2,sort_keys=True)+'\n')
    load_definition(output)
    # No keepout exceptions. Any optional optical bridge is separately source-owned.
    rules='(version 1)\n';output.with_suffix('.kicad_dru').write_text(rules)
    if any(Path(name).read_bytes()!=data for name,data in retained.items()):raise ValueError('peripheral source changed during generation')
    sha=lambda b:hashlib.sha256(b).hexdigest()
    receipt={'status':proposal['status'],'board_id':board_id,'board_key':row['board_key'],'initial_stage':row['initial_stage'],
        'definition_sha256':sha(output.read_bytes()),'native_rule_sha256':sha(rules.encode()),
        'source_sha256':{name:sha(data) for name,data in retained.items()},'source_reference':{'ref':reference[0],'pad':reference[1],'side':'B.Cu','net':'AGND'},
        'source_packages':identities,'fixed_hardware':hardware,'own_ground_contacts':[{'ref':r,'pad':p} for r,p in sorted(own)],
        'GH_ground_contacts':[{'ref':r,'pad':p,'side':h['side'],'source_footprint_origin_mm':h['footprint_origin_mm'],
            'native_orientation_deg':h['kicad_orientation_deg']} for (r,p),h in sorted(gh.items())],
        'fixed_source_geometry_preserved':True,
        'no_added_tracks_vias_or_exceptions':not (board_id=='osc-stage-optical' and 'source_ground_bridge' in proposal),
        'source_added_copper':{'tracks':0,'vias':int(board_id=='osc-stage-optical' and 'source_ground_bridge' in proposal),'keepout_exceptions':0},
        'model_entry_allowed':False,'scope':'Source definition only. Actual native rule/parity/full source/connected-ground and physical/electrical gates remain mandatory.'}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('proposal',type=Path);parser.add_argument('board_id');parser.add_argument('output',type=Path)
    args=parser.parse_args();r=generate(args.proposal,args.board_id,args.output)
    print(r['board_id'],len(r['source_packages']),'fixed source packages;',len(r['own_ground_contacts'])+len(r['GH_ground_contacts']),'complete grounds; no model admission')
